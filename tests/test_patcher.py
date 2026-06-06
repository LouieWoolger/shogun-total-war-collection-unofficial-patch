from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PATCHER = PROJECT / "build" / "shogun-fix-patcher.exe"
EXE_SIZE = 7_319_552
SHARED_BACKUP = "ShogunM.exe.unofficial-patch.bak"
SIDE_CAR_BACKUP = ".unofficial-patch.bak"
KAWANAKAJIMA_BDF = (
    Path("Battle")
    / "batinit"
    / "Historical Battles"
    / "4th Kawanakajima"
    / "4th Kawanakajima.bdf"
)
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


AMMO_PATCHES = [
    (0x002367C0, "741B", "9090"),
    (0x002367C5, "7416", "9090"),
    (0x002367CA, "7401", "9090"),
    (0x00237AEA, "0F849F0A0000", "909090909090"),
    (0x00237AF3, "0F84960A0000", "909090909090"),
    (0x00237AFC, "0F847E0A0000", "909090909090"),
]

ALL_PATCHES = AUDIO_PATCHES + UNIT_PATCHES + HARVEST_PATCHES + HISTORICAL_PATCHES + AMMO_PATCHES


ORIGINAL_KAWANAKAJIMA_BDF = """//
// Battle description file
//

Predefined::true
Title::"Takeda_Kawanakajima_Title_Label"
Author::"Takeda_Kawanakajima_Author_Label"
Rating::"Takeda_Kawanakajima_Rating_Label"
Description::"Takeda_Kawanakajima_Description_Label"
Conditions::"Takeda_Kawanakajima_Conditions_Label"

MapName::"4th Kawanakajima"
BattleType::BATTLE_TYPE_HISTORICAL
Deployement::false
Season::summer
WeatherSequenceId::12

Player::"Takeda Shingen_xzy" 5 5 LOCAL "Takeda Shingen" 0 true
\t17383 8289 180
Player::"Uesugi Kenshin_xzy" 7 7 ARTIFICIAL "Uesugi Kenshin" 0 false
\t26582 37363 40

TerminatingTrigger::"BATTLE_PLAYER_WON" 1 5
TerminatingTrigger::"BATTLE_PLAYER_LOST" 2 5

TerminatingTriggerGroup::1 1 SUCCESS_FINISHED_SEQUENCE ATTACKER ""
TerminatingTriggerGroup::2 1 FAILURE_FINISHED_SEQUENCE ATTACKER ""
"""

FIXED_KAWANAKAJIMA_BDF = ORIGINAL_KAWANAKAJIMA_BDF.replace(
    'Player::"Takeda Shingen_xzy" 5 5 LOCAL "Takeda Shingen" 0 true',
    'Player::"Takeda Shingen_xzy" 5 5 LOCAL "Takeda Shingen" 0 false',
).replace(
    'Player::"Uesugi Kenshin_xzy" 7 7 ARTIFICIAL "Uesugi Kenshin" 0 false',
    'Player::"Uesugi Kenshin_xzy" 7 7 ARTIFICIAL "Uesugi Kenshin" 0 true',
).replace(
    'TerminatingTriggerGroup::1 1 SUCCESS_FINISHED_SEQUENCE ATTACKER ""',
    'TerminatingTriggerGroup::1 1 SUCCESS_FINISHED_SEQUENCE DEFENDER ""',
).replace(
    'TerminatingTriggerGroup::2 1 FAILURE_FINISHED_SEQUENCE ATTACKER ""',
    'TerminatingTriggerGroup::2 1 FAILURE_FINISHED_SEQUENCE DEFENDER ""',
)


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
    bdf = game / KAWANAKAJIMA_BDF
    bdf.parent.mkdir(parents=True)
    bdf.write_text(ORIGINAL_KAWANAKAJIMA_BDF, encoding="ascii")
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


def assert_kawanakajima_bdf_patched(game: Path) -> None:
    bdf = game / KAWANAKAJIMA_BDF
    assert bdf.read_text(encoding="ascii") == FIXED_KAWANAKAJIMA_BDF


def assert_kawanakajima_backup(game: Path, expected_text: str = ORIGINAL_KAWANAKAJIMA_BDF) -> None:
    backup = game / f"{KAWANAKAJIMA_BDF}{SIDE_CAR_BACKUP}"
    assert backup.exists()
    assert backup.read_text(encoding="ascii") == expected_text


def test_apply_recommended_fixes_patches_selected_groups_and_creates_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    result = run_patcher("--apply", "recommended", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=False)
    assert_group_state(exe, HARVEST_PATCHES, patched=False)
    assert_group_state(exe, AMMO_PATCHES, patched=True)
    assert_kawanakajima_bdf_patched(game)
    assert_only_shared_exe_backup(game, original_bytes)
    assert_kawanakajima_backup(game)
    assert result.stdout.count("backup_created=") == 2


def test_apply_all_fixes_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    first = run_patcher("--apply", "historical,throne,unit,harvest,ammo,kawanakajima", target=game)
    after_first = exe.read_bytes()
    second = run_patcher("--apply", "historical,throne,unit,harvest,ammo,kawanakajima", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == after_first
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=True)
    assert_group_state(exe, HARVEST_PATCHES, patched=True)
    assert_group_state(exe, AMMO_PATCHES, patched=True)
    assert_kawanakajima_bdf_patched(game)
    assert_only_shared_exe_backup(game, original_bytes)
    assert_kawanakajima_backup(game)
    assert first.stdout.count("backup_created=") == 2
    assert second.stdout.count("backup_created=") == 0


def test_kawanakajima_fix_patches_battle_roles_and_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    first = run_patcher("--apply", "kawanakajima", target=game)
    after_first = (game / KAWANAKAJIMA_BDF).read_text(encoding="ascii")
    second = run_patcher("--apply", "kawanakajima", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert after_first == FIXED_KAWANAKAJIMA_BDF
    assert_kawanakajima_bdf_patched(game)
    assert_kawanakajima_backup(game)
    assert "patched=kawanakajima" in first.stdout
    assert "already_patched=kawanakajima" in second.stdout
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0
    assert exe.read_bytes() == original_exe
    assert not (game / SHARED_BACKUP).exists()


def test_ammo_fix_patches_campaign_and_historical_special_cases(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    result = run_patcher("--apply", "ammo", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, AMMO_PATCHES, patched=True)
    assert_group_state(exe, HISTORICAL_PATCHES, patched=False)
    assert_group_state(exe, AUDIO_PATCHES, patched=False)
    assert_group_state(exe, UNIT_PATCHES, patched=False)
    assert_group_state(exe, HARVEST_PATCHES, patched=False)
    assert_only_shared_exe_backup(game, original_bytes)
    assert result.stdout.count("backup_created=") == 1


def test_partial_ammo_patch_state_fails_without_repairing(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, patched in (AMMO_PATCHES[2], AMMO_PATCHES[5]):
        write_bytes(blob, offset, patched)
    exe.write_bytes(blob)
    partial_bytes = exe.read_bytes()

    result = run_patcher("--apply", "ammo", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == partial_bytes
    assert not (game / SHARED_BACKUP).exists()


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


def test_partial_kawanakajima_bdf_fails_without_repairing_or_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    bdf = game / KAWANAKAJIMA_BDF
    partial = ORIGINAL_KAWANAKAJIMA_BDF.replace(
        'Player::"Takeda Shingen_xzy" 5 5 LOCAL "Takeda Shingen" 0 true',
        'Player::"Takeda Shingen_xzy" 5 5 LOCAL "Takeda Shingen" 0 false',
    )
    bdf.write_text(partial, encoding="ascii")

    result = run_patcher("--apply", "kawanakajima", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert bdf.read_text(encoding="ascii") == partial
    assert not (game / f"{KAWANAKAJIMA_BDF}{SIDE_CAR_BACKUP}").exists()
    assert not (game / SHARED_BACKUP).exists()


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
    assert "ammo=clean" in clean.stdout
    assert "kawanakajima=clean" in clean.stdout
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert patched.returncode == 0, patched.stdout + patched.stderr
    assert "historical=patched" in patched.stdout
    assert "unit=clean" in patched.stdout
    assert "ammo=clean" in patched.stdout
    assert "kawanakajima=clean" in patched.stdout
