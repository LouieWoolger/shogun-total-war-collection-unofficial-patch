"""Opt-in tests of the compiled, packaged Windows installer.

Set SHOGUN_INSTALLER to the installer EXE. No real game or live install is used.
These tests catch lost diagnostics and packaging/integration failures that a
standalone helper test cannot detect.
"""
from __future__ import annotations

import os
import ctypes
import hashlib
from pathlib import Path
import subprocess

import pytest
from test_patcher import make_clean_game, AUDIO_PATCHES, UNIT_PATCHES, SHUTDOWN_PATCHES, assert_group_state

INSTALLER = os.environ.get("SHOGUN_INSTALLER")
pytestmark = pytest.mark.skipif(not INSTALLER, reason="Set SHOGUN_INSTALLER to test packaged installer")


@pytest.fixture(autouse=True)
def cleanup_fixture_registrations(tmp_path: Path):
    # Lifecycle-enabled packages register every successful synthetic install.
    # Delete only keys newly created by this test under its own temporary root.
    from test_uninstaller_runtime import cleanup_owned_registrations, patch_registrations
    before = set(patch_registrations())
    yield
    cleanup_owned_registrations(tmp_path, before)


def invoke(tmp_path: Path, game: Path, fixes: str = "recommended", *, installer=None, env=None):
    logs = tmp_path / "logs 日本"
    # NSIS /D= consumes the remaining command line, including spaces, unquoted.
    installer = installer or INSTALLER
    command = f'"{installer}" /S /LOGDIR="{logs}" /FIXES={fixes} /D={game}'
    result = subprocess.run(
        command, executable=str(installer),
        capture_output=True, timeout=60, env=env,
    )
    sessions = list(logs.glob("*/installer.log"))
    assert len(sessions) == 1, "Installer must leave one discoverable session log after exiting"
    return result, sessions[0], sessions[0].read_text(encoding="utf-16")


def test_missing_target_leaves_durable_diagnostic(tmp_path: Path):
    result, log, text = invoke(tmp_path, tmp_path / "missing game 日本")
    assert result.returncode != 0
    assert "phase=target-validation" in text
    assert "error=target_missing" in text
    assert "version=" in text and "target=" in text
    assert not (tmp_path / "missing game 日本").exists()
    source = Path(__file__).resolve().parents[1]
    for name, relative in (("LICENSE.txt", "LICENSE"),
                           ("MinGW-w64-runtime.txt", "licenses/MinGW-w64-runtime.txt")):
        assert (log.parent / name).read_bytes() == (source / relative).read_bytes()


def test_helper_rejection_is_retained_without_mutation(tmp_path: Path):
    game = tmp_path / "unsupported 日本"
    game.mkdir()
    original = b"unsupported executable fixture"
    (game / "ShogunM.exe").write_bytes(original)
    result, log, text = invoke(tmp_path, game, "historical")
    assert result.returncode != 0
    assert "phase=helper" in text and "child_exit=2" in text
    helper = (log.parent / "helper.log").read_text(encoding="utf-8")
    assert "error=" in helper
    assert (game / "ShogunM.exe").read_bytes() == original
    assert not (game / "ShogunM.exe.unofficial-patch.bak").exists()


def test_invalid_option_is_reported_before_mutation(tmp_path: Path):
    game = make_clean_game(tmp_path)
    original = (game / "ShogunM.exe").read_bytes()
    result, log, text = invoke(tmp_path, game, "not-a-fix")
    assert result.returncode != 0
    assert "error=unknown_fix" in (log.parent / "helper.log").read_text(encoding="utf-8")
    assert (game / "ShogunM.exe").read_bytes() == original


def manifest(game: Path):
    return {str(p.relative_to(game)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in game.rglob("*") if p.is_file()}


@pytest.mark.parametrize("fixes", ["historical", "retraining-drag", "throne", "unit", "harvest",
                                   "ammo", "kawanakajima", "odawara", "advisor", "dgvoodoo",
                                   "recommended", "all", "shutdown"])
def test_packaged_options_and_reapplication(tmp_path: Path, fixes: str):
    game = make_clean_game(tmp_path)
    result, log, text = invoke(tmp_path, game, fixes)
    assert result.returncode == 0, text + (log.parent / "helper.log").read_text(encoding="utf-8")
    assert_group_state(game / "ShogunM.exe", SHUTDOWN_PATCHES,
                       patched=fixes in ("recommended", "all", "shutdown"))
    helper = (log.parent / "helper.log").read_text(encoding="utf-8")
    assert "phase=complete result=0" in helper
    assert (log.parent / "helper-console.log").read_text(encoding="utf-8") == helper
    assert "helper_sha256=" in helper and "before_sha256=" in helper
    if fixes in ("dgvoodoo", "recommended", "all"):
        vendor = Path(__file__).resolve().parents[1] / "vendor" / "dgvoodoo2"
        for name in ("DDraw.dll", "D3DImm.dll", "D3D9.dll", "dgVoodoo.conf"):
            assert (game / name).read_bytes() == (vendor / name).read_bytes()
    else:
        assert not (game / "DDraw.dll").exists()
    if fixes in ("harvest", "advisor"):
        assert_group_state(game / "ShogunM.exe", AUDIO_PATCHES, patched=True)
    if fixes == "historical":
        assert_group_state(game / "ShogunM.exe", AUDIO_PATCHES, patched=False)
        assert_group_state(game / "ShogunM.exe", UNIT_PATCHES, patched=False)
    if fixes == "all":
        assert len(helper) > 2048, "Exercise output beyond the old nsExec stack buffer"
    first = manifest(game)
    again_root = tmp_path / "second-run"
    again_root.mkdir()
    result, _, _ = invoke(again_root, game, fixes)
    assert result.returncode == 0
    assert manifest(game) == first


def test_locked_executable_preserves_game_and_backups(tmp_path: Path):
    game = make_clean_game(tmp_path)
    before = manifest(game)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
                                 ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(game / "ShogunM.exe"), 0x80000000, 1, None, 3, 0, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        result, log, text = invoke(tmp_path, game, "historical")
    finally:
        kernel.CloseHandle(handle)
    assert result.returncode != 0
    assert "error=" in (log.parent / "helper.log").read_text(encoding="utf-8")
    assert manifest(game) == before


def test_unusable_requested_log_folder_falls_back(tmp_path: Path):
    # An existing file cannot serve as a directory. Failure evidence must still
    # survive outside an unwritable target/requested location.
    blocked = tmp_path / "blocked-log-location"
    blocked.write_bytes(b"keep")
    default = Path(os.environ["LOCALAPPDATA"]) / "Unofficial Shogun Patch" / "Logs"
    before = set(default.glob("*/installer.log"))
    target = tmp_path / "missing"
    command = f'"{INSTALLER}" /S /LOGDIR="{blocked}" /D={target}'
    result = subprocess.run(command, executable=INSTALLER, capture_output=True, timeout=60)
    new = set(default.glob("*/installer.log")) - before
    assert result.returncode != 0 and len(new) == 1
    text = new.pop().read_text(encoding="utf-16")
    assert "error=target_missing" in text and str(target) in text
    assert blocked.read_bytes() == b"keep" and not target.exists()


def test_read_only_target_is_not_silently_changed(tmp_path: Path):
    game = make_clean_game(tmp_path)
    target = game / "ShogunM.exe"
    before = manifest(game)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong]
    kernel.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
    kernel.GetFileAttributesW.restype = ctypes.c_ulong
    original_attributes = kernel.GetFileAttributesW(str(target))
    assert original_attributes != 0xFFFFFFFF
    assert kernel.SetFileAttributesW(str(target), original_attributes | 1)
    try:
        result, log, text = invoke(tmp_path, game, "historical")
        assert result.returncode != 0
        assert "error=" in (log.parent / "helper.log").read_text(encoding="utf-8")
        assert manifest(game) == before
        assert kernel.GetFileAttributesW(str(target)) & 1
    finally:
        assert kernel.SetFileAttributesW(str(target), original_attributes)


def test_unicode_temp_and_game_paths(tmp_path: Path):
    source = make_clean_game(tmp_path)
    game = tmp_path / "日本語のゲーム"
    source.rename(game)
    temp = tmp_path / "一時ファイル"
    temp.mkdir()
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
    result, log, text = invoke(tmp_path, game, "historical", env=env)
    assert result.returncode == 0
    assert str(game) in text
    helper = (log.parent / "helper.log").read_text(encoding="utf-8")
    assert "日本語のゲーム" in helper and "phase=complete result=0" in helper


def test_helper_log_rejection_keeps_raw_child_explanation(tmp_path: Path):
    game = make_clean_game(tmp_path)
    before = (game / "ShogunM.exe").read_bytes()
    logs = game / "logs-inside-game"
    command = f'"{INSTALLER}" /S /FIXES=historical /LOGDIR="{logs}" /D={game}'
    result = subprocess.run(command, executable=INSTALLER, capture_output=True, timeout=60)
    assert result.returncode != 0
    sessions = list(logs.glob("*/installer.log"))
    assert len(sessions) == 1
    assert "child_exit=2" in sessions[0].read_text(encoding="utf-16")
    assert "error=unsafe_log" in (sessions[0].parent / "helper-console.log").read_text(encoding="utf-8")
    assert (game / "ShogunM.exe").read_bytes() == before
    assert not (game / "ShogunM.exe.unofficial-patch.bak").exists()


@pytest.fixture(scope="module")
def invalid_helper_installer(tmp_path_factory):
    makensis = os.environ.get("SHOGUN_MAKENSIS")
    if not makensis:
        pytest.skip("Set SHOGUN_MAKENSIS to exercise native helper launch failure")
    root = tmp_path_factory.mktemp("invalid-helper-package")
    helper = root / "invalid-helper.exe"
    helper.write_bytes(b"Deliberately not a PE executable; test fixture only.")
    output = root / "invalid-helper-installer.exe"
    source = Path(__file__).resolve().parents[1] / "installer.nsi"
    result = subprocess.run([makensis, f"/DPATCHER_FILE={helper}",
                             f"/DOUTPUT_FILE={output}", str(source)],
                            capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    # CreateProcess can display a system modal for this intentionally malformed
    # image before subprocess can start its timeout. Suppress that dialog only
    # for the error-code probe, then restore the test process's error mode before
    # exercising the real NSIS launcher.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetErrorMode.argtypes = [ctypes.c_uint]
    kernel.SetErrorMode.restype = ctypes.c_uint
    previous_mode = kernel.SetErrorMode(0x8003)
    try:
        with pytest.raises(OSError) as native:
            subprocess.run([str(helper)], capture_output=True, timeout=10)
    finally:
        kernel.SetErrorMode(previous_mode)
    assert native.value.winerror
    return output, native.value.winerror


def test_helper_never_started_has_native_error_and_durable_log(tmp_path: Path, invalid_helper_installer):
    game = make_clean_game(tmp_path)
    before = manifest(game)
    installer, native_error = invalid_helper_installer
    result, log, text = invoke(tmp_path, game, "historical", installer=installer)
    assert result.returncode != 0
    assert f"error=helper_start_failed native_error={native_error}" in text
    assert not (log.parent / "helper.log").exists()
    assert manifest(game) == before


def test_invalid_temp_directory_preserves_extraction_diagnostic(tmp_path: Path):
    game = make_clean_game(tmp_path)
    before = manifest(game)
    blocked = tmp_path / "not-a-directory"
    blocked.write_bytes(b"keep")
    env = dict(os.environ, TEMP=str(blocked), TMP=str(blocked))
    result, log, text = invoke(tmp_path, game, "historical", env=env)
    # NSIS itself may select a fallback temp directory; either a fully successful
    # install or an explicit extraction failure is valid, never silent success.
    if result.returncode:
        assert "extraction" in text and "error=" in text
        assert manifest(game) == before
    else:
        assert "result=success" in text and (log.parent / "helper.log").exists()
    assert blocked.read_bytes() == b"keep"
