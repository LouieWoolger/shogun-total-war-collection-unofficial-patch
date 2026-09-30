"""Opt-in native transaction failures on synthetic game fixtures only.

Install pytest and frida in the Python environment, build the helper, then run
in PowerShell:
    $env:SHOGUN_FRIDA_FAULTS='1'; python -m pytest tests/test_transaction_faults.py
SHOGUN_FIX_PATCHER can select a helper built outside the repository. Requires a
Windows host able to spawn/instrument a local x86 child with Frida. No game
installation, proprietary executable, or production fault switch is used.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

import pytest
import test_patcher as fixtures

pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.environ.get("SHOGUN_FRIDA_FAULTS") != "1",
    reason="Set SHOGUN_FRIDA_FAULTS=1 on Windows to run native Frida fault tests",
)


def manifest(game: Path, *, transaction: bool = False) -> dict[str, str]:
    return {
        str(path.relative_to(game)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in game.rglob("*")
        if path.is_file() and (transaction or ".unofficial-patch-transaction" not in path.parts)
    }


def ordinary_apply(game: Path, selection: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(fixtures.PATCHER), "--target", str(game), "--apply", selection],
        capture_output=True, text=True, encoding="utf-8", timeout=20,
    )


COMMON_SCRIPT = r"""
if (Process.arch !== 'ia32') throw new Error('Expected compiled x86 helper');
send({event:'architecture', value:Process.arch});
const k = Process.getModuleByName('kernel32.dll');
const setError = new NativeFunction(k.getExportByName('SetLastError'),
    'void', ['uint32'], 'stdcall');
Interceptor.attach(Process.getModuleByName('ntdll.dll').getExportByName('NtTerminateProcess'), {
    onEnter(args) {
        send({event:'exit', code:args[1].toUInt32()});
        Thread.sleep(0.05); // Deliver the native exit status before process teardown.
    }
});
"""


def fault_apply(game: Path, script: str, *, log: Path | None = None) -> dict:
    """Bound one exact spawned child; cleanup uses its process HANDLE, not a name.

    Keeping the handle prevents a recycled PID from becoming a cleanup target.
    Frida's PID is used only to attach to its freshly spawned suspended child.
    """
    frida = pytest.importorskip("frida", reason="Install frida for opt-in native fault tests")
    assert fixtures.PATCHER.is_file(), "Build the helper or set SHOGUN_FIX_PATCHER"
    device = frida.get_local_device()
    args = [str(fixtures.PATCHER), "--target", str(game), "--apply", "historical,kawanakajima"]
    if log is not None:
        args += ["--log", str(log)]
    pid = device.spawn(args, stdio="pipe")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x00100001, False, pid)  # SYNCHRONIZE | PROCESS_TERMINATE
    if not handle:
        # This child is still suspended: it cannot exit and recycle its PID.
        device.kill(pid)
        raise ctypes.WinError(ctypes.get_last_error())
    done = threading.Event()
    messages: list[dict] = []
    output: list[str] = []
    killed: list[bool] = []
    session = None
    hook = None

    def on_message(message, _data):
        messages.append(message)
        if message.get("payload", {}).get("event") == "crash-checkpoint":
            killed.append(bool(kernel32.TerminateProcess(handle, 99)))

    def on_output(output_pid, _fd, data):
        if output_pid == pid:
            output.append(data.decode("utf-8", errors="replace"))

    device.on("output", on_output)
    try:
        session = device.attach(pid)
        session.on("detached", lambda *_args: done.set())
        hook = session.create_script(COMMON_SCRIPT + script)
        hook.on("message", on_message)
        hook.load()
        device.resume(pid)
        assert done.wait(20), "Instrumented helper exceeded its bounded timeout"
        assert kernel32.WaitForSingleObject(handle, 3000) == 0, "Child did not exit after detachment"
        errors = [message for message in messages if message.get("type") == "error"]
        assert not errors, errors
        payloads = [message["payload"] for message in messages if message.get("type") == "send"]
        assert {"event": "architecture", "value": "ia32"} in payloads
        return {
            "text": "".join(output), "events": payloads, "killed": killed,
            "exit_codes": [item["code"] for item in payloads if item.get("event") == "exit"],
        }
    finally:
        device.off("output", on_output)
        try:
            if kernel32.WaitForSingleObject(handle, 0) == 258:  # WAIT_TIMEOUT: our exact child still lives.
                assert kernel32.TerminateProcess(handle, 98), "Exact child cleanup failed"
                assert kernel32.WaitForSingleObject(handle, 3000) == 0, "Exact child cleanup timed out"
        finally:
            kernel32.CloseHandle(handle)
        if session is not None and not done.is_set():
            try:
                session.detach()
            except (frida.InvalidOperationError, frida.ProcessNotFoundError):
                pass


LATER_COMMIT_FAILURE = r"""
const address = k.getExportByName('ReplaceFileW');
const original = new NativeFunction(address, 'int',
    ['pointer','pointer','pointer','uint32','pointer','pointer'], 'stdcall');
Interceptor.replace(address, new NativeCallback(function(a,b,c,d,e,f) {
    const path = a.readUtf16String();
    if (path.endsWith('4th Kawanakajima.bdf') && !path.includes('\\.unofficial-patch-transaction\\')) {
        setError(5);
        send({event:'later-commit-refused'});
        return 0;
    }
    return original(a,b,c,d,e,f);
}, 'int', ['pointer','pointer','pointer','uint32','pointer','pointer'], 'stdcall'));
"""


def test_later_native_commit_failure_restores_all_files_and_backups(tmp_path: Path):
    game = fixtures.make_clean_game(tmp_path)
    before = manifest(game)

    result = fault_apply(game, LATER_COMMIT_FAILURE)

    assert {"event": "later-commit-refused"} in result["events"]
    assert result["exit_codes"] == [2]
    assert "transaction_committed_file=0" in result["text"]  # Executable committed before the BDF fault.
    assert "rollback=complete" in result["text"]
    assert manifest(game) == before
    assert not (game / ".unofficial-patch-transaction").exists()


CRASH_AFTER_EXECUTABLE = r"""
Interceptor.attach(k.getExportByName('ReplaceFileW'), {
    onEnter(args) { this.crash = args[0].readUtf16String().endsWith('ShogunM.exe'); },
    onLeave(result) {
        if (this.crash && result.toInt32() !== 0) {
            send({event:'crash-checkpoint'});
            Thread.sleep(2); // Hold the next commit until the host terminates this exact child.
        }
    }
});
"""


@pytest.mark.parametrize("external_edit", [False, True], ids=["recover", "refuse-drift"])
def test_interrupted_commit_recovers_or_preserves_unknown_external_edit(tmp_path: Path, external_edit: bool):
    game = fixtures.make_clean_game(tmp_path)
    original = (game / "ShogunM.exe").read_bytes()

    interrupted = fault_apply(game, CRASH_AFTER_EXECUTABLE)

    assert interrupted["killed"] == [True]
    transaction = game / ".unofficial-patch-transaction"
    assert (transaction / "journal.bin").is_file()
    assert (game / "ShogunM.exe").read_bytes() != original
    if external_edit:
        exe = game / "ShogunM.exe"
        edited = bytearray(exe.read_bytes())
        edited[0x500] ^= 1  # Outside every patch-owned range.
        exe.write_bytes(edited)
    before_retry = manifest(game)
    snapshots = manifest(transaction)

    retry = ordinary_apply(game, "unit")

    if external_edit:
        assert retry.returncode == 2
        assert "transaction_recovery_target_changed" in retry.stderr
        assert manifest(game) == before_retry
        assert (transaction / "journal.bin").is_file()
        after_snapshots = manifest(transaction)
        assert {k: v for k, v in snapshots.items() if k.startswith("rollback")} == {
            k: v for k, v in after_snapshots.items() if k.startswith("rollback")
        }
    else:
        assert retry.returncode == 0, retry.stdout + retry.stderr
        assert "phase=recover" in retry.stderr
        fixtures.assert_group_state(game / "ShogunM.exe", fixtures.HISTORICAL_PATCHES, patched=False)
        fixtures.assert_group_state(game / "ShogunM.exe", fixtures.UNIT_PATCHES, patched=True)
        assert (game / fixtures.SHARED_BACKUP).read_bytes() == original
        assert not transaction.exists()


def diagnostic_failure_script(checkpoint: str, native_write: bool) -> str:
    return r"""
const logs = new Set();
let failed = false;
Interceptor.attach(k.getExportByName('CreateFileW'), {
    onEnter(args) { this.log = args[0].readUtf16String().endsWith('helper.log'); },
    onLeave(result) { if (this.log) logs.add(result.toString()); }
});
const writeAddress = k.getExportByName('WriteFile');
const originalWrite = new NativeFunction(writeAddress, 'int',
    ['pointer','pointer','uint32','pointer','pointer'], 'stdcall');
Interceptor.replace(writeAddress, new NativeCallback(function(h,b,n,w,o) {
    if (logs.has(h.toString())) {
        if (b.readUtf8String(n).includes(CHECKPOINT)) failed = true;
        if (failed && NATIVE_WRITE) {
            w.writeU32(0); setError(112); send({event:'log-write-refused'}); return 0;
        }
    }
    return originalWrite(h,b,n,w,o);
}, 'int', ['pointer','pointer','uint32','pointer','pointer'], 'stdcall'));
const flushAddress = k.getExportByName('FlushFileBuffers');
const originalFlush = new NativeFunction(flushAddress, 'int', ['pointer'], 'stdcall');
Interceptor.replace(flushAddress, new NativeCallback(function(h) {
    if (logs.has(h.toString()) && failed && !NATIVE_WRITE) {
        setError(112); send({event:'log-flush-refused'}); return 0;
    }
    return originalFlush(h);
}, 'int', ['pointer'], 'stdcall'));
""".replace("CHECKPOINT", json.dumps(checkpoint)).replace("NATIVE_WRITE", "true" if native_write else "false")


@pytest.mark.parametrize("after_commit", [False, True], ids=["before-commit", "after-commit"])
def test_diagnostic_io_failure_returns_truthful_status_and_preserves_recovery(tmp_path: Path, after_commit: bool):
    game = fixtures.make_clean_game(tmp_path)
    before = manifest(game)
    script = diagnostic_failure_script("phase=complete" if after_commit else "phase=stage", not after_commit)

    result = fault_apply(game, script, log=tmp_path / "helper.log")

    assert result["exit_codes"] == [3]
    assert "error=diagnostic_write_failed" in result["text"]
    assert "result=3" in result["text"]
    if after_commit:
        assert {"event": "log-flush-refused"} in result["events"]
        assert "game_changes=committed" in result["text"]
        fixtures.assert_group_state(game / "ShogunM.exe", fixtures.HISTORICAL_PATCHES, patched=True)
        fixtures.assert_kawanakajima_bdf_patched(game)
        transaction = game / ".unofficial-patch-transaction"
        assert (transaction / "journal.bin").is_file()
        completed = manifest(game)
        retry = ordinary_apply(game, "historical,kawanakajima")
        assert retry.returncode == 0, retry.stdout + retry.stderr
        assert manifest(game) == completed
        assert not transaction.exists()
    else:
        assert {"event": "log-write-refused"} in result["events"]
        assert "game_changes=none" in result["text"]
        assert manifest(game) == before
        assert not (game / ".unofficial-patch-transaction").exists()
