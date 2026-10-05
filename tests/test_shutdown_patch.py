"""Execute the installed x86 repair, including its calling convention.

These are instruction-level tests of helper output, not gameplay evidence.
The fake IME/destructor boundaries keep Windows dependencies out of emulation.
"""
import struct
import functools
import json
import subprocess
import sys
from pathlib import Path

import pytest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EBX,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_EIP,
)

from test_patcher import (make_clean_game, run_patcher, SHUTDOWN_PATCHES,
                          SHARED_BACKUP, assert_group_state)

BASE = 0x400000
FILTER = 0x6F88A0
OWNER = 0xC99480
OUTER = 0x1000100
INNER = 0x1000200
STACK = 0x2000800
RETURN = 0x3000000
NONVOLATILE = (UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)


@pytest.fixture
def installed(tmp_path):
    game = make_clean_game(tmp_path)
    # Old helpers accept recommended, so the before test reaches the actual
    # unsafe instructions instead of failing on an unknown command-line flag.
    result = run_patcher('--apply', 'recommended', target=game)
    assert result.returncode == 0, result.stdout + result.stderr
    return game / 'ShogunM.exe'


def isolated_x86(test):
    """Keep native emulation isolated; a crashed child fails the test.

    Unicorn's Windows initialization intentionally probes memory (upstream FAQ,
    issue1841). Pytest's process-wide faulthandler mislabels the handled probe
    as fatal. A plain child avoids that noise without catching guest failures
    or changing the game's exception handling.
    """
    @functools.wraps(test)
    def run(installed, **parameters):
        result = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).resolve()), test.__name__,
             str(installed), json.dumps(parameters)],
            capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    return run


def machine(blob):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(BASE, 0xB00000)
    uc.mem_write(BASE, blob)
    for address in (0x1000000, 0x2000000, RETURN):
        uc.mem_map(address, 0x1000)
    for i, register in enumerate(NONVOLATILE):
        uc.reg_write(register, 0xABC01000 + i)
    uc.reg_write(UC_X86_REG_ESP, STACK)
    return uc


def word(uc, address):
    return struct.unpack('<I', uc.mem_read(address, 4))[0]


def assert_nonvolatile(uc):
    assert [uc.reg_read(r) for r in NONVOLATILE] == [0xABC01000 + i for i in range(4)]


def call_filter(uc, owner):
    uc.reg_write(UC_X86_REG_ECX, owner)
    uc.reg_write(UC_X86_REG_ESP, STACK)
    uc.mem_write(STACK, struct.pack('<6I', RETURN, 0x111, 0x7C, 0xFFFFFFF0, 0x444, 0x555))
    uc.emu_start(FILTER, RETURN, count=100)
    assert uc.reg_read(UC_X86_REG_EIP) == RETURN
    assert uc.reg_read(UC_X86_REG_ESP) == STACK + 24
    assert_nonvolatile(uc)


@isolated_x86
def test_late_window_message_without_owner_continues_normal_processing(installed):
    # Page zero is deliberately unmapped: the old forwarding method faults.
    uc = machine(installed)
    call_filter(uc, 0)
    assert uc.reg_read(UC_X86_REG_EAX) == 1


@pytest.mark.parametrize('result', [0, 1, 0x12345601])
@isolated_x86
def test_live_filter_keeps_arguments_result_and_calling_convention(installed, result):
    uc = machine(installed)
    uc.mem_write(OUTER, struct.pack('<I', INNER))
    uc.mem_write(0x6F9BC0, b'\xB8' + struct.pack('<I', result) + b'\xC2\x14\x00')
    seen = []
    def inspect_call(uc, address, size, data):
        if address == 0x6F9BC0:
            seen.append((uc.reg_read(UC_X86_REG_ECX),
                         bytes(uc.mem_read(uc.reg_read(UC_X86_REG_ESP) + 4, 20))))
    uc.hook_add(UC_HOOK_CODE, inspect_call)
    call_filter(uc, OUTER)
    assert seen == [(INNER, struct.pack('<5I', 0x111, 0x7C, 0xFFFFFFF0, 0x444, 0x555))]
    assert uc.reg_read(UC_X86_REG_EAX) == result


@pytest.mark.parametrize('present', [False, True])
@isolated_x86
def test_cleanup_detaches_before_destructor_and_late_callback(installed, present):
    uc = machine(installed)
    uc.mem_write(OWNER, struct.pack('<I', OUTER if present else 0))
    uc.mem_write(0x5BB940, b'\xC2\x04\x00')
    seen = []
    def inspect_destructor(uc, address, size, data):
        if address == 0x5BB940:
            seen.append((word(uc, OWNER), uc.reg_read(UC_X86_REG_ECX),
                         word(uc, uc.reg_read(UC_X86_REG_ESP) + 4)))
    uc.hook_add(UC_HOOK_CODE, inspect_destructor)
    uc.emu_start(0x5BBE0C, 0x5BBE1D, count=100)
    assert uc.reg_read(UC_X86_REG_EIP) == 0x5BBE1D
    assert seen == ([(0, OUTER, 1)] if present else [])
    assert word(uc, OWNER) == 0
    assert uc.reg_read(UC_X86_REG_ESP) == STACK
    assert_nonvolatile(uc)
    # Model the actual outer storage becoming inaccessible after destruction.
    uc.mem_unmap(0x1000000, 0x1000)
    call_filter(uc, word(uc, OWNER))
    assert uc.reg_read(UC_X86_REG_EAX) == 1


def test_shutdown_only_is_repeatable_and_preserves_original_backup(tmp_path):
    game = make_clean_game(tmp_path)
    exe = game / 'ShogunM.exe'
    original = exe.read_bytes()
    result = run_patcher('--apply', 'shutdown', target=game)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, SHUTDOWN_PATCHES, patched=True)
    patched = exe.read_bytes()
    expected = bytearray(original)
    for offset, _, replacement in SHUTDOWN_PATCHES:
        expected[offset:offset + len(bytes.fromhex(replacement))] = bytes.fromhex(replacement)
    assert patched == expected
    assert (game / SHARED_BACKUP).read_bytes() == original
    repeat = run_patcher('--apply', 'shutdown', target=game)
    assert repeat.returncode == 0, repeat.stdout + repeat.stderr
    assert exe.read_bytes() == patched
    assert (game / SHARED_BACKUP).read_bytes() == original
    verified = run_patcher('--verify', target=game)
    assert verified.returncode == 0
    assert 'shutdown=patched' in verified.stdout


@pytest.mark.parametrize('mask', range(1, 7))
def test_incomplete_shutdown_group_is_rejected_without_changes(tmp_path, mask):
    game = make_clean_game(tmp_path)
    exe = game / 'ShogunM.exe'
    data = bytearray(exe.read_bytes())
    for i, (offset, _, replacement) in enumerate(SHUTDOWN_PATCHES):
        if mask & (1 << i):
            data[offset:offset + len(bytes.fromhex(replacement))] = bytes.fromhex(replacement)
    exe.write_bytes(data)
    result = run_patcher('--apply', 'shutdown', target=game)
    assert result.returncode != 0
    assert 'partial_state' in result.stderr + result.stdout
    assert exe.read_bytes() == data
    assert not (game / SHARED_BACKUP).exists()


@pytest.mark.parametrize('site', range(3))
def test_unknown_shutdown_bytes_are_rejected_without_changes(tmp_path, site):
    game = make_clean_game(tmp_path)
    exe = game / 'ShogunM.exe'
    data = bytearray(exe.read_bytes())
    data[SHUTDOWN_PATCHES[site][0]] = 0xCC
    exe.write_bytes(data)
    result = run_patcher('--apply', 'shutdown', target=game)
    assert result.returncode != 0
    assert exe.read_bytes() == data
    assert not (game / SHARED_BACKUP).exists()


if __name__ == '__main__':
    globals()[sys.argv[1]].__wrapped__(Path(sys.argv[2]).read_bytes(), **json.loads(sys.argv[3]))
