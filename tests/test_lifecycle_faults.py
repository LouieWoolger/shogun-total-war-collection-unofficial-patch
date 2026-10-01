"""Opt-in Win32 failure/interruption evidence for the durable patch lifecycle.

Requires SHOGUN_INSTALLER, SHOGUN_FIX_PATCHER and SHOGUN_FRIDA_FAULTS=1.
Uses synthetic fixtures, the production package's generated uninstaller, and
Frida hooks in one HANDLE-owned x86 helper process. No production failure
switches, live game files, broad process cleanup, or machine ACL changes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from test_patcher import KAWANAKAJIMA_BDF
from test_transaction_faults import fault_apply
from test_uninstaller_runtime import (
    INSTALLER, STATE_DIRECTORY, UNINSTALLER_NAME, cleanup_owned_registrations,
    fixture_game, install, inventory, patch_registrations, registrations_for,
    uninstall,
)


TRANSACTION_DIRECTORY = ".unofficial-shogun-patch-lifecycle"
pytestmark = pytest.mark.skipif(
    os.name != "nt" or not INSTALLER or os.environ.get("SHOGUN_FRIDA_FAULTS") != "1",
    reason="Set SHOGUN_INSTALLER and SHOGUN_FRIDA_FAULTS=1 on Windows",
)


@pytest.fixture(autouse=True)
def cleanup_test_entries(tmp_path: Path):
    before = set(patch_registrations())
    yield
    cleanup_owned_registrations(tmp_path, before)


def prepared_game(root: Path, *, already_installed: bool) -> tuple[Path, Path, dict[str, str]]:
    game = fixture_game(root)
    original = inventory(game)
    install(root / "prepare", game, "historical")
    generated = root / "uninstaller from production package.exe"
    shutil.copy2(game / UNINSTALLER_NAME, generated)
    if not already_installed:
        result, text = uninstall(root / "reset-clean", game)
        assert result.returncode == 0, text
        assert inventory(game) == original
    return game, generated, original


def record(root: Path, result: dict) -> None:
    (root / "injected-events.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


def live_file_script(filename: str, *, operation="deny-write") -> str:
    """Hook an exact allowlisted basename only outside the task journal/stage."""
    head = r"""
let triggered = false;
const liveFile = path => path.toLowerCase().endsWith(FILENAME.toLowerCase()) &&
    !path.toLowerCase().includes('\\.unofficial-shogun-patch-lifecycle\\');
""".replace("FILENAME", json.dumps("\\" + filename))
    if operation == "crash-after-replace":
        return head + r"""
Interceptor.attach(k.getExportByName('ReplaceFileW'), {
    onEnter(args) { this.live = liveFile(args[0].readUtf16String()); },
    onLeave(result) {
        if (!triggered && this.live && result.toInt32() !== 0) {
            triggered = true;
            send({event:'crash-checkpoint'});
            Thread.sleep(2);
        }
    }
});
"""
    if operation == "deny-delete":
        return head + r"""
const address = k.getExportByName('DeleteFileW');
const original = new NativeFunction(address, 'int', ['pointer'], 'stdcall');
Interceptor.replace(address, new NativeCallback(function(path) {
    if (!triggered && liveFile(path.readUtf16String())) {
        triggered = true;
        setError(5); send({event:'live-delete-refused'}); return 0;
    }
    return original(path);
}, 'int', ['pointer'], 'stdcall'));
"""
    return head + r"""
const replaceAddress = k.getExportByName('ReplaceFileW');
const replaceOriginal = new NativeFunction(replaceAddress, 'int',
    ['pointer','pointer','pointer','uint32','pointer','pointer'], 'stdcall');
Interceptor.replace(replaceAddress, new NativeCallback(function(a,b,c,d,e,f) {
    if (!triggered && liveFile(a.readUtf16String())) {
        triggered = true;
        setError(5); send({event:'live-write-refused'}); return 0;
    }
    return replaceOriginal(a,b,c,d,e,f);
}, 'int', ['pointer','pointer','pointer','uint32','pointer','pointer'], 'stdcall'));
const moveAddress = k.getExportByName('MoveFileExW');
const moveOriginal = new NativeFunction(moveAddress, 'int', ['pointer','pointer','uint32'], 'stdcall');
Interceptor.replace(moveAddress, new NativeCallback(function(a,b,c) {
    if (!triggered && liveFile(b.readUtf16String())) {
        triggered = true;
        setError(5); send({event:'live-write-refused'}); return 0;
    }
    return moveOriginal(a,b,c);
}, 'int', ['pointer','pointer','uint32'], 'stdcall'));
"""


REGISTRY_WRITE_DENIAL = r"""
const advapi = Process.getModuleByName('advapi32.dll');
const address = advapi.getExportByName('RegSetValueExW');
const original = new NativeFunction(address, 'int',
    ['pointer','pointer','uint32','uint32','pointer','uint32'], 'stdcall');
let refused = false;
Interceptor.replace(address, new NativeCallback(function(a,b,c,d,e,f) {
    if (!refused && b.readUtf16String() === 'DisplayVersion') {
        refused = true; send({event:'registration-write-refused'}); return 5;
    }
    return original(a,b,c,d,e,f);
}, 'int', ['pointer','pointer','uint32','uint32','pointer','uint32'], 'stdcall'));
"""


REGISTRY_DELETE_DENIAL = r"""
const advapi = Process.getModuleByName('advapi32.dll');
const address = advapi.getExportByName('RegDeleteKeyW');
const original = new NativeFunction(address, 'int', ['pointer','pointer'], 'stdcall');
let refused = false;
Interceptor.replace(address, new NativeCallback(function(a,b) {
    if (!refused && b.readUtf16String().includes('UnofficialShogunPatch-')) {
        refused = true; send({event:'registration-delete-refused'}); return 5;
    }
    return original(a,b);
}, 'int', ['pointer','pointer'], 'stdcall'));
"""


@pytest.mark.parametrize("already_installed", [False, True], ids=["fresh", "upgrade"])
def test_registration_write_failure_rolls_back_game_and_last_removal_path(tmp_path: Path, already_installed: bool):
    game, generated, original = prepared_game(tmp_path, already_installed=already_installed)
    before = inventory(game)
    entry = registrations_for(game)
    result = fault_apply(game, REGISTRY_WRITE_DENIAL, log=tmp_path / "helper.log",
                         arguments=["--apply", "historical,kawanakajima", "--uninstaller", str(generated)])
    record(tmp_path, result)
    assert {"event": "registration-write-refused"} in result["events"]
    assert result["exit_codes"] == [2]
    assert inventory(game) == before
    assert registrations_for(game) == entry
    if already_installed:
        result, text = uninstall(tmp_path / "retry-remove", game)
        assert result.returncode == 0, text
        assert inventory(game) == original
    else:
        install(tmp_path / "retry-install", game, "recommended")
        result, text = uninstall(tmp_path / "retry-remove", game)
        assert result.returncode == 0, text
        assert inventory(game) == original


def test_uninstaller_write_failure_rolls_back_every_game_change(tmp_path: Path):
    game, generated, original = prepared_game(tmp_path, already_installed=False)
    result = fault_apply(game, live_file_script(UNINSTALLER_NAME), log=tmp_path / "helper.log",
                         arguments=["--apply", "historical,kawanakajima", "--uninstaller", str(generated)])
    record(tmp_path, result)
    assert {"event": "live-write-refused"} in result["events"]
    assert result["exit_codes"] == [2]
    assert inventory(game) == original
    assert not registrations_for(game)
    install(tmp_path / "retry-install", game, "recommended")
    result, text = uninstall(tmp_path / "retry-remove", game)
    assert result.returncode == 0, text
    assert inventory(game) == original


@pytest.mark.parametrize("operation", ["upgrade", "uninstall"])
def test_killed_midcommit_keeps_uninstaller_and_recovers_without_original_installer(tmp_path: Path, operation: str):
    game, generated, original = prepared_game(tmp_path, already_installed=True)
    entry = registrations_for(game)
    arguments = (["--uninstall"] if operation == "uninstall" else
                 ["--apply", "historical,kawanakajima", "--uninstaller", str(generated)])
    # Upgrade modifies the BDF because the historical executable is already
    # patched; uninstall restores ShogunM.exe. Both are live commit boundaries.
    filename = "ShogunM.exe" if operation == "uninstall" else "4th Kawanakajima.bdf"
    result = fault_apply(game, live_file_script(filename, operation="crash-after-replace"),
                         log=tmp_path / "helper.log", arguments=arguments)
    record(tmp_path, result)
    assert result["killed"] == [True]
    assert (game / TRANSACTION_DIRECTORY / "journal.bin").is_file()
    assert (game / UNINSTALLER_NAME).is_file()
    assert (game / STATE_DIRECTORY / "state.bin").is_file()
    assert registrations_for(game) == entry
    # The original downloaded installer is not invoked for recovery/removal.
    result, text = uninstall(tmp_path / "retry-using-installed-removal", game)
    assert result.returncode == 0, text
    assert inventory(game) == original
    assert not registrations_for(game)


@pytest.mark.parametrize("fault", ["registration", "uninstaller"])
def test_final_cleanup_failure_keeps_a_registered_retry_path(tmp_path: Path, fault: str):
    game, _, original = prepared_game(tmp_path, already_installed=True)
    script = (REGISTRY_DELETE_DENIAL if fault == "registration" else
              live_file_script(UNINSTALLER_NAME, operation="deny-delete"))
    expected = "registration-delete-refused" if fault == "registration" else "live-delete-refused"
    result = fault_apply(game, script, log=tmp_path / "helper.log", arguments=["--uninstall"])
    record(tmp_path, result)
    assert {"event": expected} in result["events"]
    assert result["exit_codes"] == [2]
    assert (game / UNINSTALLER_NAME).is_file()
    assert (game / STATE_DIRECTORY / "state.bin").is_file()
    assert len(registrations_for(game)) == 1
    result, text = uninstall(tmp_path / "retry-cleanup", game)
    assert result.returncode == 0, text
    assert inventory(game) == original
    assert not registrations_for(game)


JOURNAL_DISK_FULL = r"""
const journals = new Set();
let refused = false;
Interceptor.attach(k.getExportByName('CreateFileW'), {
    onEnter(args) {
        this.journal = args[0].readUtf16String().includes('\\.unofficial-shogun-patch-lifecycle\\journal.bin');
    },
    onLeave(result) { if (this.journal && result.toInt32() !== -1) journals.add(result.toString()); }
});
const address = k.getExportByName('WriteFile');
const original = new NativeFunction(address, 'int', ['pointer','pointer','uint32','pointer','pointer'], 'stdcall');
Interceptor.replace(address, new NativeCallback(function(h,b,n,w,o) {
    if (!refused && journals.has(h.toString())) {
        refused = true; w.writeU32(0); setError(112); send({event:'journal-disk-full'}); return 0;
    }
    return original(h,b,n,w,o);
}, 'int', ['pointer','pointer','uint32','pointer','pointer'], 'stdcall'));
"""


def test_disk_full_before_mutation_preserves_previous_installation(tmp_path: Path):
    game, generated, original = prepared_game(tmp_path, already_installed=True)
    before = inventory(game)
    entry = registrations_for(game)
    result = fault_apply(game, JOURNAL_DISK_FULL, log=tmp_path / "helper.log",
                         arguments=["--apply", "historical,kawanakajima", "--uninstaller", str(generated)])
    record(tmp_path, result)
    assert {"event": "journal-disk-full"} in result["events"]
    assert result["exit_codes"] == [2]
    assert inventory(game) == before
    assert registrations_for(game) == entry
    result, text = uninstall(tmp_path / "retry-remove", game)
    assert result.returncode == 0, text
    assert inventory(game) == original


HOLD_UNINSTALL_COMMIT = r"""
let held = false;
Interceptor.attach(k.getExportByName('ReplaceFileW'), {
    onEnter(args) {
        const path = args[0].readUtf16String();
        if (!held && path.endsWith('\\ShogunM.exe') &&
            !path.includes('\\.unofficial-shogun-patch-lifecycle\\')) {
            held = true;
            send({event:'hold-live-commit'});
            Thread.sleep(10);
        }
    }
});
"""


def test_concurrent_same_target_is_refused_while_another_target_can_remove(tmp_path: Path):
    game, _, original = prepared_game(tmp_path / "active", already_installed=True)
    other, _, other_original = prepared_game(tmp_path / "independent", already_installed=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        active = pool.submit(fault_apply, game, HOLD_UNINSTALL_COMMIT,
                             log=tmp_path / "helper.log", arguments=["--uninstall"])
        deadline = time.monotonic() + 10
        while not (game / ".unofficial-shogun-patch.lock").exists():
            assert not active.done(), "Primary removal finished before acquiring its lifecycle lock"
            assert time.monotonic() < deadline, "Primary removal never acquired its lifecycle lock"
            time.sleep(0.02)
        result, text = uninstall(tmp_path / "competing-remove", game)
        assert result.returncode != 0, text
        assert "error=" in text
        assert len(registrations_for(game)) == 1
        result, text = uninstall(tmp_path / "independent-remove", other)
        assert result.returncode == 0, text
        assert inventory(other) == other_original
        assert not active.done(), "Independent removal must complete while the first target is still held"
        completed = active.result(timeout=20)
    record(tmp_path, completed)
    assert {"event": "hold-live-commit"} in completed["events"]
    assert completed["exit_codes"] == [0]
    assert inventory(game) == original
    assert not registrations_for(game)


UNKNOWN_TRANSACTION_FILE_AND_ARCHIVE_DENIAL = r"""
const taskNullPointer = ptr(0);
const create = new NativeFunction(k.getExportByName('CreateFileW'), 'pointer',
    ['pointer','uint32','uint32','pointer','uint32','uint32','pointer'], 'stdcall');
const write = new NativeFunction(k.getExportByName('WriteFile'), 'int',
    ['pointer','pointer','uint32','pointer','pointer'], 'stdcall');
const close = new NativeFunction(k.getExportByName('CloseHandle'), 'int', ['pointer'], 'stdcall');
const note = 'unrelated transaction-folder note must survive';
let added = false;
Interceptor.attach(k.getExportByName('ReplaceFileW'), {
    onEnter(args) { this.path = args[0].readUtf16String(); },
    onLeave(result) {
        if (!added && result.toInt32() !== 0 && this.path.endsWith('\\ShogunM.exe') &&
            !this.path.includes('\\.unofficial-shogun-patch-lifecycle\\')) {
            added = true;
            const parent = this.path.slice(0, -'\\ShogunM.exe'.length);
            const path = Memory.allocUtf16String(parent + '\\.unofficial-shogun-patch-lifecycle\\' + NOTE_RELATIVE);
            const handle = create(path, 0x40000000, 0, taskNullPointer, 1, 0x80, taskNullPointer);
            if (handle.toInt32() === -1) throw new Error('Could not create test-owned transaction note');
            const buffer = Memory.allocUtf8String(note), written = Memory.alloc(4);
            const ok = write(handle, buffer, note.length, written, taskNullPointer);
            close(handle);
            if (!ok || written.readU32() !== note.length) throw new Error('Could not write transaction note');
            send({event:'unknown-transaction-file-created'});
        }
    }
});
const moveAddress = k.getExportByName('MoveFileExW');
const originalMove = new NativeFunction(moveAddress, 'int', ['pointer','pointer','uint32'], 'stdcall');
Interceptor.replace(moveAddress, new NativeCallback(function(a,b,c) {
    if (a.readUtf16String().endsWith('\\.unofficial-shogun-patch-lifecycle')) {
        setError(5); send({event:'cleanup-archive-rename-refused'}); return 0;
    }
    return originalMove(a,b,c);
}, 'int', ['pointer','pointer','uint32'], 'stdcall'));
""".replace("NOTE_RELATIVE", json.dumps(str(Path("stage") / KAWANAKAJIMA_BDF.parent / "user-note.txt")))


def test_cleanup_archive_failure_keeps_journal_and_preserves_unknown_content_on_retry(tmp_path: Path):
    game, _, original = prepared_game(tmp_path, already_installed=True)
    result = fault_apply(game, UNKNOWN_TRANSACTION_FILE_AND_ARCHIVE_DENIAL,
                         log=tmp_path / "helper.log", arguments=["--uninstall"])
    record(tmp_path, result)
    assert {"event": "unknown-transaction-file-created"} in result["events"]
    assert {"event": "cleanup-archive-rename-refused"} in result["events"]
    assert result["exit_codes"] == [2]
    transaction = game / TRANSACTION_DIRECTORY
    assert (transaction / "journal.bin").is_file(), "Cleanup failure must leave a valid retry journal"
    note = (transaction / "stage" / KAWANAKAJIMA_BDF.parent / "user-note.txt").read_bytes()
    assert (game / UNINSTALLER_NAME).is_file()
    assert len(registrations_for(game)) == 1
    result, text = uninstall(tmp_path / "retry-cleanup", game)
    assert result.returncode == 0, text
    assert not registrations_for(game)
    archives = list(game.glob("Unofficial Shogun Patch recovery *"))
    assert archives
    assert any(path.read_bytes() == note for root in archives for path in root.rglob("*") if path.is_file())
    after = {name: digest for name, digest in inventory(game).items()
             if not name.startswith("Unofficial Shogun Patch recovery ")}
    assert after == original


def new_state_parent_substitution_script(outside: Path, displaced: Path) -> str:
    """Attempt an NTFS junction substitution at the newly-created parent boundary."""
    return r"""
const taskNullPointer = ptr(0);
const destination = OUTSIDE;
const displaced = Memory.allocUtf16String(DISPLACED);
const mkdir = new NativeFunction(k.getExportByName('CreateDirectoryW'), 'int', ['pointer','pointer'], 'stdcall');
const move = new NativeFunction(k.getExportByName('MoveFileExW'), 'int', ['pointer','pointer','uint32'], 'stdcall');
const create = new NativeFunction(k.getExportByName('CreateFileW'), 'pointer',
    ['pointer','uint32','uint32','pointer','uint32','uint32','pointer'], 'stdcall');
const control = new NativeFunction(k.getExportByName('DeviceIoControl'), 'int',
    ['pointer','uint32','pointer','uint32','pointer','uint32','pointer','pointer'], 'stdcall');
const close = new NativeFunction(k.getExportByName('CloseHandle'), 'int', ['pointer'], 'stdcall');
let attempted = false;
Interceptor.attach(k.getExportByName('CreateDirectoryW'), {
    onEnter(args) { this.path = args[0].readUtf16String(); },
    onLeave(result) {
        if (attempted || result.toInt32() === 0 ||
            !this.path.endsWith('\\.unofficial-shogun-patch') ||
            this.path.includes('\\.unofficial-shogun-patch-lifecycle\\')) return;
        attempted = true;
        send({event:'new-state-parent-checkpoint'});
        const path = Memory.allocUtf16String(this.path);
        if (!move(path, displaced, 8)) {
            send({event:'state-parent-replacement-blocked'});
            return;
        }
        if (!mkdir(path, taskNullPointer)) throw new Error('Could not create task-owned junction placeholder');
        const handle = create(path, 0x40000000, 0, taskNullPointer, 3, 0x02200000, taskNullPointer);
        if (handle.toInt32() === -1) throw new Error('Could not open task-owned junction placeholder');
        const substitute = '\\??\\' + destination;
        const substituteBytes = substitute.length * 2, printBytes = destination.length * 2;
        const dataBytes = 8 + substituteBytes + 2 + printBytes + 2;
        const reparse = Memory.alloc(8 + dataBytes), written = Memory.alloc(4);
        reparse.writeU32(0xa0000003);
        reparse.add(4).writeU16(dataBytes);
        reparse.add(6).writeU16(0);
        reparse.add(8).writeU16(0);
        reparse.add(10).writeU16(substituteBytes);
        reparse.add(12).writeU16(substituteBytes + 2);
        reparse.add(14).writeU16(printBytes);
        reparse.add(16).writeUtf16String(substitute);
        reparse.add(16 + substituteBytes + 2).writeUtf16String(destination);
        const ok = control(handle, 0x900a4, reparse, 8 + dataBytes, taskNullPointer, 0, written, taskNullPointer);
        close(handle);
        if (!ok) throw new Error('Could not set task-owned junction reparse data');
        send({event:'state-parent-replaced-by-junction'});
    }
});
""".replace("OUTSIDE", json.dumps(str(outside))).replace("DISPLACED", json.dumps(str(displaced)))


def test_new_state_parent_cannot_redirect_committed_baselines_outside_target(tmp_path: Path):
    game, generated, original = prepared_game(tmp_path, already_installed=False)
    outside = tmp_path / "unrelated external directory"
    outside.mkdir()
    (outside / "personal-file.bin").write_bytes(b"external data must remain exactly unchanged")
    outside_before = inventory(outside)
    displaced = tmp_path / "displaced test-created parent"
    script = new_state_parent_substitution_script(outside, displaced)
    try:
        result = fault_apply(game, script, log=tmp_path / "helper.log",
                             arguments=["--apply", "historical,kawanakajima", "--uninstaller", str(generated)])
        record(tmp_path, result)
        assert {"event": "new-state-parent-checkpoint"} in result["events"]
        assert inventory(outside) == outside_before, "No baseline or other game bytes may escape through the substituted parent"
        replaced = {"event": "state-parent-replaced-by-junction"} in result["events"]
        if replaced:
            assert result["exit_codes"] == [2]
            assert not registrations_for(game)
        else:
            assert {"event": "state-parent-replacement-blocked"} in result["events"]
            assert result["exit_codes"] == [0]
    finally:
        state = game / STATE_DIRECTORY
        if state.exists() and state.lstat().st_file_attributes & 0x400:
            state.rmdir()  # Remove only the exact reparse point this test created.
    if replaced:
        install(tmp_path / "retry-install", game, "historical,kawanakajima")
    result, text = uninstall(tmp_path / "remove", game)
    assert result.returncode == 0, text
    assert inventory(game) == original
    assert inventory(outside) == outside_before
