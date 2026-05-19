from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PATCHER = PROJECT / "build" / "shogun-fix-patcher.exe"
EXE_SIZE = 7_319_552
SHARED_BACKUP = "ShogunM.exe.unofficial-patch.bak"
LEGACY_EXE_BACKUPS = [
    "ShogunM.exe.historical-campaign-reinforcement-fix.bak",
    "ShogunM.exe.throne-room-audio-fix.bak",
    "ShogunM.exe.unit-cost-training-upkeep-fix.bak",
    "ShogunM.exe.harvest-report-restoration-fix.bak",
]


AUDIO_PATCHES = [
    (0x001B7CCB, "8B4E6085C974", "E9102F160090"),
    (0x001B80D2, "8A451884C07532", "E9492B16009090"),
    (0x001B7916, "8A451884C07407B801000000EB05", "E91C331600909090909090909090"),
    (
        0x0031ABE0,
        "00" * 0x78,
        "8B4E6085C975348B4E5485C974238D44241050518B01FF502085C07C148B5424108B7C24148B46408B764429C219F77C05E9E4D0E9FFE9EAD0E9FFE9B2D0E9FF837D6000740C8A451884C07505E9A7D4E9FFE9D4D4E9FF837D600074078A451884C0740AB801000000E9DBCCE9FFB888130000E9D1CCE9FF",
    ),
    (0x00198FA5, "A9FF0000007505E82FF8FFFF", "E9AE1C180090909090909090"),
    (
        0x0031AC58,
        "00" * 0x20,
        "A9FF00000075148B0D8079C90085C974058039007505E86DDBE7FFE939E3E7FF",
    ),
]


UNIT_PATCHES = [
    (0x001364BC, "A16004C700", "B83C000000"),
    (0x00135792, "8BC683C4045E5FC38BF690909090", "E937541E00909090909090909090"),
    (0x0031ABCE, "00" * 18, "8BC66BC03C99F73D6004C70083C4045E5FC3"),
    (0x0015C550, "83F864", "83F87F"),
    (0x0015C57E, "83F864", "83F87F"),
    (0x0017CAEE, "83F864", "83F87F"),
    (0x001BFA08, "83FA64", "83FA7F"),
    (0x002E3213, "83F864", "83F87F"),
]


HARVEST_FRAME_ID_SETUP = (
    "33C9"
    "898C2480020000"
    "898C2484020000"
    "C78424880200000E000000"
    "B80D000000"
    "8984248C020000"
    "89842490020000"
)

HARVEST_AUDIO_CAVE_TAIL = (
    "9C608B0D1C88C20085"
    "C974116A01E8E6D2E2FFC7051C88C200"
    "000000006A68E8C415FEFF83C40485C0"
    "742689C631D2885601895604895608C6"
    "460C018D9424640200005289F1E8AED5"
    "E9FF89351C88C200619D31C9E9A5F0E2FF"
)

RESTORED_HARVEST_CODE_CAVE = HARVEST_FRAME_ID_SETUP + ("90" * 9) + HARVEST_AUDIO_CAVE_TAIL

HARVEST_PATCHES = [
    (0x00149D7F, "6032F100", "8033F100"),
    (
        0x00149D88,
        HARVEST_FRAME_ID_SETUP,
        "E9F30E1D00" + ("90" * 41),
    ),
    (0x0031AC80, "00" * 0x91, RESTORED_HARVEST_CODE_CAVE),
]


HISTORICAL_PATCH_STUB = (
    "8B542404"
    "8B816C800000"
    "8902"
    "8B8170800000"
    "894204"
    "8B4110"
    "3B8124780000"
    "7E06"
    "8B8124780000"
    "894208"
    "8A8120780000"
    "88420C"
    "8B8138780000"
    "894210"
    "C20400"
)

HISTORICAL_PATCHES = [
    (0x000AD6E3, "E87863F7FF", "E8D8C3AA00"),
    (0x006F8AC0, "00" * (len(HISTORICAL_PATCH_STUB) // 2), HISTORICAL_PATCH_STUB),
]


ALL_PATCHES = AUDIO_PATCHES + UNIT_PATCHES + HARVEST_PATCHES + HISTORICAL_PATCHES


def write_bytes(blob: bytearray, offset: int, hex_bytes: str) -> None:
    payload = bytes.fromhex(hex_bytes)
    blob[offset : offset + len(payload)] = payload


def read_bytes(path: Path, offset: int, hex_bytes: str) -> bytes:
    expected_length = len(bytes.fromhex(hex_bytes))
    with path.open("rb") as handle:
        handle.seek(offset)
        return handle.read(expected_length)


def make_clean_game(tmp_path: Path) -> Path:
    game = tmp_path / "Total War Shogun 1 Gold"
    game.mkdir()
    blob = bytearray(EXE_SIZE)
    for offset, original, _patched in ALL_PATCHES:
        write_bytes(blob, offset, original)
    exe = game / "ShogunM.exe"
    exe.write_bytes(blob)
    return game


def run_patcher(*args: str, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PATCHER), "--target", str(target), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_group_state(exe: Path, patches: list[tuple[int, str, str]], patched: bool) -> None:
    for offset, original, patched_bytes in patches:
        expected = patched_bytes if patched else original
        assert read_bytes(exe, offset, expected) == bytes.fromhex(expected)


def assert_only_shared_exe_backup(game: Path, expected_bytes: bytes) -> None:
    backup = game / SHARED_BACKUP
    assert backup.exists()
    assert backup.read_bytes() == expected_bytes
    for legacy_backup in LEGACY_EXE_BACKUPS:
        assert not (game / legacy_backup).exists()


def test_apply_recommended_fixes_patches_selected_groups_and_creates_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    result = run_patcher("--apply", "historical,throne,unit", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=True)
    assert_group_state(exe, HARVEST_PATCHES, patched=False)
    assert_only_shared_exe_backup(game, original_bytes)
    assert result.stdout.count("backup_created=") == 1


def test_apply_all_fixes_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    first = run_patcher("--apply", "historical,throne,unit,harvest", target=game)
    after_first = exe.read_bytes()
    second = run_patcher("--apply", "historical,throne,unit,harvest", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == after_first
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=True)
    assert_group_state(exe, HARVEST_PATCHES, patched=True)
    assert_only_shared_exe_backup(game, original_bytes)
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0


def test_harvest_applies_audio_dependency_when_audio_is_not_selected(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    result = run_patcher("--apply", "harvest", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, HARVEST_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=False)
    assert_group_state(exe, HISTORICAL_PATCHES, patched=False)
    assert_only_shared_exe_backup(game, original_bytes)
    assert result.stdout.count("backup_created=") == 1


def test_unsupported_bytes_fail_before_writes_or_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    write_bytes(blob, AUDIO_PATCHES[0][0], "909090909090")
    exe.write_bytes(blob)

    result = run_patcher("--apply", "throne", target=game)

    assert result.returncode != 0
    assert "unsupported" in (result.stdout + result.stderr).lower()
    assert not (game / SHARED_BACKUP).exists()
    for legacy_backup in LEGACY_EXE_BACKUPS:
        assert not (game / legacy_backup).exists()
    assert read_bytes(exe, UNIT_PATCHES[0][0], UNIT_PATCHES[0][1]) == bytes.fromhex(UNIT_PATCHES[0][1])


def test_locked_executable_fails_before_writes_or_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = ctypes.c_void_p
    invalid_handle = ctypes.c_void_p(-1).value
    handle = kernel32.CreateFileW(
        str(exe),
        0x80000000,  # GENERIC_READ
        0x00000001,  # FILE_SHARE_READ
        None,
        3,  # OPEN_EXISTING
        0,
        None,
    )
    assert handle not in (0, None, invalid_handle)

    try:
        result = run_patcher("--apply", "historical", target=game)
    finally:
        kernel32.CloseHandle(handle)

    assert result.returncode != 0
    assert "open_write_failed" in result.stderr
    assert exe.read_bytes() == original_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_locked_already_patched_executable_succeeds_without_new_writes(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    first = run_patcher("--apply", "historical", target=game)
    patched_bytes = exe.read_bytes()
    backup_bytes = (game / SHARED_BACKUP).read_bytes()
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = ctypes.c_void_p
    invalid_handle = ctypes.c_void_p(-1).value
    handle = kernel32.CreateFileW(
        str(exe),
        0x80000000,  # GENERIC_READ
        0x00000001,  # FILE_SHARE_READ
        None,
        3,  # OPEN_EXISTING
        0,
        None,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    assert handle not in (0, None, invalid_handle)

    try:
        second = run_patcher("--apply", "historical", target=game)
    finally:
        kernel32.CloseHandle(handle)

    assert second.returncode == 0, second.stdout + second.stderr
    assert "already_patched=historical" in second.stdout
    assert exe.read_bytes() == patched_bytes
    assert (game / SHARED_BACKUP).read_bytes() == backup_bytes
    assert len(list(game.glob("ShogunM.exe*.bak"))) == 1


def test_partial_patch_state_fails_verify_and_apply_without_repairing(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    write_bytes(blob, HISTORICAL_PATCHES[0][0], HISTORICAL_PATCHES[0][2])
    exe.write_bytes(blob)
    partial_bytes = exe.read_bytes()

    verify = run_patcher("--verify", target=game)
    apply = run_patcher("--apply", "historical", target=game)

    assert verify.returncode != 0
    assert "historical=partial" in verify.stdout
    assert apply.returncode != 0
    assert "partial" in (apply.stdout + apply.stderr).lower()
    assert exe.read_bytes() == partial_bytes
    assert not (game / SHARED_BACKUP).exists()
    for legacy_backup in LEGACY_EXE_BACKUPS:
        assert not (game / legacy_backup).exists()


def test_verify_reports_clean_and_patched_states(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)

    clean = run_patcher("--verify", target=game)
    applied = run_patcher("--apply", "historical", target=game)
    patched = run_patcher("--verify", target=game)

    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "historical=clean" in clean.stdout
    assert "unit=clean" in clean.stdout
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert patched.returncode == 0, patched.stdout + patched.stderr
    assert "historical=patched" in patched.stdout
    assert "unit=clean" in patched.stdout
