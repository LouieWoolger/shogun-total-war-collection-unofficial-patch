from __future__ import annotations

import ctypes
import os
import struct
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PATCHER = Path(os.environ.get("SHOGUN_FIX_PATCHER", PROJECT / "build" / "shogun-fix-patcher.exe"))
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
ODAWARA_BDF = (
    Path("Battle")
    / "batinit"
    / "Historical Campaigns"
    / "Toyotomi Hideyoshi 1536"
    / "Odawara"
    / "Odawara.bdf"
)
ODAWARA_MAP = Path("Battle") / "Maps" / "odawara (toyotomi).jjm"
LEGACY_EXE_BACKUPS = [
    "ShogunM.exe.historical-campaign-reinforcement-fix.bak",
    "ShogunM.exe.throne-room-audio-fix.bak",
    "ShogunM.exe.unit-cost-training-upkeep-fix.bak",
    "ShogunM.exe.harvest-report-restoration-fix.bak",
]
DGVOODOO_CONF = "dgVoodoo.conf"

UNSAFE_DGVOODOO_CONF = (
    "DefaultEnumeratedResolutions        = all\r\n"
    "ExtraEnumeratedResolutions          = \r\n"
    "EnumeratedResolutionBitdepths       = all\r\n"
    "PreservedSetting                    = true\r\n"
)

FIXED_DGVOODOO_CONF = (
    "DefaultEnumeratedResolutions        = classics\r\n"
    "ExtraEnumeratedResolutions          = 1280x720,1600x900,1920x1080,2560x1440,max_16_9\r\n"
    "EnumeratedResolutionBitdepths       = all\r\n"
    "PreservedSetting                    = true\r\n"
)


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


ODAWARA_ROUTED_SOLDIER_DESTINATION_CAVE = (
    "8B458C"
    "8B4DE4"
    "803D00C0D20001"
    "757B"
    "83B9A87F000004"
    "7572"
    "81FA00280000"
    "7D6A"
    "817B10C01F0000"
    "7C61"
    "817B1400080000"
    "7C58"
    "817B1400980000"
    "7F4F"
    "8B7B14"
    "33C0"
    "8B5310"
    "81FA00280000"
    "7D05"
    "BA00280000"
    "8B0DF8987200"
    "2B4B14"
    "3BCF"
    "7D17"
    "8BF9"
    "A1F8987200"
    "8B5310"
    "81FA00280000"
    "7D05"
    "BA00280000"
    "8B0DF4987200"
    "2B4B10"
    "3BCF"
    "7D09"
    "8B15F4987200"
    "8B4314"
    "8916"
    "894604"
    "E9CD57D1FF"
    + ("90" * 12)
)

ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE = (
    "8B1520BFD200"
    "A124BFD200"
    "8B4DE4"
    "803D00C0D20001"
    "757B"
    "83B9A87F000004"
    "7572"
    "81FA00280000"
    "7D6A"
    "817B10C01F0000"
    "7C61"
    "817B1400080000"
    "7C58"
    "817B1400980000"
    "7F4F"
    "8B7B14"
    "33C0"
    "8B5310"
    "81FA00280000"
    "7D05"
    "BA00280000"
    "8B0DF8987200"
    "2B4B14"
    "3BCF"
    "7D17"
    "8BF9"
    "A1F8987200"
    "8B5310"
    "81FA00280000"
    "7D05"
    "BA00280000"
    "8B0DF4987200"
    "2B4B10"
    "3BCF"
    "7D09"
    "8B15F4987200"
    "8B4314"
    "8916"
    "894604"
    "E94D58D1FF"
    + ("90" * 4)
)

ODAWARA_MAP_NAME_GUARD_CAVE = (
    "568D742404"
    "813E6F646177"
    "7532"
    "817E0461726120"
    "7529"
    "817E0828746F79"
    "7520"
    "817E0C6F746F6D"
    "7517"
    "66817E106929"
    "750F"
    "807E1200"
    "7509"
    "C60500C0D20001"
    "EB07"
    "C60500C0D20000"
    "5E"
    "BB01000000"
    "E94A87D9FF"
    + ("90" * 15)
)

ODAWARA_PATCHES = [
    (0x000B3656, "BB01000000", "E965782600"),
    (
        0x0031AEC0,
        "00" * (len(ODAWARA_MAP_NAME_GUARD_CAVE) // 2),
        ODAWARA_MAP_NAME_GUARD_CAVE,
    ),
    (0x000305D9, "89168B458C894604", "E9A2A72E00909090"),
    (
        0x0031AD80,
        "00" * (len(ODAWARA_ROUTED_SOLDIER_DESTINATION_CAVE) // 2),
        ODAWARA_ROUTED_SOLDIER_DESTINATION_CAVE,
    ),
    (
        0x000306F9,
        "A120BFD20089068B1524BFD200895604",
        "E922A72E00" + ("90" * 11),
    ),
    (
        0x0031AE20,
        "00" * (len(ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE) // 2),
        ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE,
    ),
]


ADVISOR_RANDOM_CAVE = (
    "52"          # push edx
    "51"          # push ecx
    "0F31"        # rdtsc
    "59"          # pop ecx
    "3201"        # xor al, byte ptr [ecx]
    "326101"      # xor ah, byte ptr [ecx+1]
    "30E0"        # xor al, ah
    "30D0"        # xor al, dl
    "C0C003"      # rol al, 3
    "00F0"        # add al, dh
    "FE01"        # inc byte ptr [ecx]
    "304101"      # xor byte ptr [ecx+1], al
    "0FB6C0"      # movzx eax, al
    "5A"          # pop edx
    "C3"          # ret
    + ("90" * 35)
)


ADVISOR_RANDOM_PATCHES = [
    (0x00198833, "E8A8300200", "E8E8261800"),
    (0x00198854, "E887300200", "E8C7261800"),
    (0x001988EA, "E8F12F0200", "E831261800"),
    (0x00198976, "E8652F0200", "E8A5251800"),
    (0x001989F6, "E8E52E0200", "E825251800"),
    (0x0031AF20, "00" * (len(ADVISOR_RANDOM_CAVE) // 2), ADVISOR_RANDOM_CAVE),
]


RETRAINING_DRAG_HOVER_DESCRIPTOR_CAVE = (
    "85F6"          # test esi, esi
    "0F44742410"    # cmovz esi, [esp+0x10] (live type-7 descriptor)
    "8B16"          # mov edx, [esi]
    "8B5224"        # mov edx, [edx+0x24]
    "E94A92DEFF"    # jmp 0x005041BB (resume original virtual call)
)

RETRAINING_DRAG_TARGET_DESCRIPTOR_CAVE = (
    "85DB"          # test ebx, ebx
    "0F445C2414"    # cmovz ebx, [esp+0x14] (live type-7 descriptor)
    "8B13"          # mov edx, [ebx]
    "8B5224"        # mov edx, [edx+0x24]
    "E95AE7DEFF"    # jmp 0x005096DC (resume original virtual call)
)

RETRAINING_DRAG_ACTION_DESCRIPTOR_CAVE = (
    "85C9"          # test ecx, ecx
    "0F444C2408"    # cmovz ecx, [esp+0x08] (live type-7 descriptor)
    "8B01"          # mov eax, [ecx]
    "8B4024"        # mov eax, [eax+0x24]
    "E90DCBE2FF"    # jmp 0x00547AA0 (resume original virtual call)
)

RETRAINING_DRAG_DROP_DESCRIPTOR_CAVE = (
    "0F445C2440"    # cmovz ebx, [esp+0x40] (drop descriptor)
    "E9E4C8E2FF"    # jmp 0x00547881 (native owner validation)
)

RETRAINING_DRAG_SOURCE_PROVINCE_CHECK_CAVE = (
    "0FB74128"      # movzx eax, word [ecx+0x28] (unit id)
    "C1E004"        # shl eax, 4
    "8B802882DE00"  # mov eax, [eax+0x00DE8228] (source army)
    "85C0"          # test eax, eax
    "740A"          # jz missing_source_army
    "8A158005C700"  # mov dl, [0x00C70580] (selected province id)
    "3A5025"        # cmp dl, [eax+0x25] (source army province id)
    "C3"            # ret
    "85E4"          # missing_source_army: test esp, esp (ZF=0, eax remains null)
    "C3"            # ret
)

RETRAINING_DRAG_ARMY_DROP_CAVE = (
    "3B5C2440"      # cmp ebx, [esp+0x40] (fallback descriptor?)
    "750E"          # jne native_castle_path
    "89D9"          # mov ecx, ebx (fallback descriptor)
    "E8D5FFFFFF"    # call 0x0071AF9D (source province check)
    "7510"          # jne restore_queue
    "A18005C700"    # mov eax, [0x00C70580] (selected province id)
    "8B357C03C700"  # native_castle_path: mov esi, [0x00C7037C]
    "E9FEC8E2FF"    # jmp 0x005478D8 (native same-province withdrawal path)
    "E832FDFFFF"    # restore_queue: call 0x0071AD11
    "E9C2C9E2FF"    # jmp 0x005479A6 (handler epilogue)
)

RETRAINING_DRAG_NO_TARGET_CAVE = (
    "E8B4FFFFFF"    # call 0x0071AF9D (resolve source army)
    "85C0"          # test eax, eax
    "0F84D387E4FF"  # jz 0x005637C4 (generic cleanup)
    "E81BFDFFFF"    # call 0x0071AD11 (restore one queue entry)
    "E9C987E4FF"    # jmp 0x005637C4 (generic cleanup)
)

RETRAINING_DRAG_REQUEUE_HELPER_CAVE = (
    "0FB64025"      # movzx eax, byte [eax+0x25] (source province id)
    "A38005C700"    # mov [0x00C70580], eax (restore selected province)
    "6A01"          # push 1 (internal restore: suppress a synthetic player event)
    "50"            # push eax (source province)
    "FF35B87BC900"  # push [0x00C97BB8] (release y)
    "FF35B47BC900"  # push [0x00C97BB4] (release x)
    "51"            # push ecx (live type-7 descriptor)
    "8B0DB803C700"  # mov ecx, [0x00C703B8] (Unit Training panel)
    "E83B0BE1FF"    # call 0x0052B870 (native queue insertion)
    "C3"            # ret
)

MARKER_FREE_RETRAINING_DRAG_PROVINCE_DROP_CAVE = (
    "8B882C82DE00"
    "85C9"
    "0F853684E1FF"
    "8B802882DE00"
    "85C0"
    "0F84AD84E1FF"
    "0FB65025"
    "3B5358"
    "750C"
    "E970EE8300"
    "90909090909090"
    "89E9"
    "E8A3FFFFFF"
    "E91DEF8300"
)

RETRAINING_DRAG_PROVINCE_DROP_CAVE = (
    "8B882C82DE00"  # mov ecx, [eax+0x00DE822C] (ordinary UI object fallback)
    "8B802882DE00"  # mov eax, [eax+0x00DE8228] (current unit model)
    "85C0"          # test eax, eax
    "7414"          # jz ordinary object check
    "83784404"      # cmp dword [eax+0x44], 4 (active retraining state)
    "750E"          # jne ordinary object check
    "0FB65025"      # movzx edx, byte [eax+0x25] (source province id)
    "3B5358"        # cmp edx, [ebx+0x58] (final target province id)
    "7512"          # jne invalid destination rollback
    "E976EE8300"    # jmp 0x00F59BD0 (accepted retraining lifecycle + event 2)
    "85C9"          # ordinary object check: test ecx, ecx
    "0F851884E1FF"  # jnz 0x0053317A (unchanged ordinary type-7 path)
    "E99884E1FF"    # jmp 0x005331FF (fail closed with neither object)
    "89E9"          # invalid: mov ecx, ebp (current live descriptor)
    "E8A3FFFFFF"    # call 0x0071AD11 (restore current queue entry once)
    "E91DEF8300"    # jmp 0x00F59C90 (event 7 once and native cleanup)
)

RETRAINING_DRAG_RIGHT_CLICK_HOOK = "E9C00EA5009090"
RETRAINING_DRAG_SUCCESS_SOUND_HOOK = "E98F6AA20090909090"
MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE = (
    "608B0424C74044000000008B068B402C89F1FFD069C0840200008B157C03C700"
    "01D089C1E8D1B85DFF61E940F35AFF000000000000000FB76D28C1E5048BAD28"
    "82DE008B0D8005C700C1E1022B0D8005C700C1E1032B0D8005C70089CAC1E202"
    "C1E10529D1030D7C03C70031C0505055E895B65DFFC745440000000089D9E877"
    "B85DFF506A02E80B2660FF83C40458E9D1955DFF000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000089D9E82DB85DFFE993955DFF0000000000000000000000000000"
    "000000000000000000000000000000000000000000006A07E8992560FF83C404"
    "E960955DFF0000000000000000000000"
)

RETRAINING_RIGHT_CLICK_SUCCESS_TAIL = "E87200000061E93BF35AFF0000"
RETRAINING_RIGHT_CLICK_SOUND_HELPER = "6A02E8EF2560FF83C404C3"
CASTLE_TARGET_RETRAINING_DRAG_EXTENDED_CAVE = (
    MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE[: 0x29 * 2]
    + RETRAINING_RIGHT_CLICK_SUCCESS_TAIL
    + MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE[0x36 * 2 : 0xA0 * 2]
    + RETRAINING_RIGHT_CLICK_SOUND_HELPER
    + MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE[(0xA0 + 0x0B) * 2 :]
)
RETRAINING_DRAG_EXTENDED_CAVE = (
    "E9A1010000"  # right-click/castle discriminator at 0x00F59D40
    + CASTLE_TARGET_RETRAINING_DRAG_EXTENDED_CAVE[5 * 2 :]
)
QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE = RETRAINING_DRAG_EXTENDED_CAVE
RETRAINING_UNIT_PROXY_TERMINAL_HELPER = (
    "5D"              # pop ebp (restore classifier caller state)
    "C70424D0345600"  # mov dword [esp], 0x005634D0 (dispatcher cleanup)
    "E9A4010000"      # jmp 0x00F59DF6 (event 7 then one queue restore)
)
RETRAINING_UNIT_PROXY_CLASSIFIER = (
    "8138E020F100"    # cmp dword [eax], 0x00F120E0 (unit/banner proxy)
    "0F857E000000"    # jne 0x00F59CF6 (unchanged native fallback)
    "83C070"          # add eax, 0x70 (inline containing army)
    "8138E0C7F000"    # cmp dword [eax], 0x00F0C7E0 (army vtable)
    "0F856F000000"    # jne 0x00F59CF6 (fail closed)
    "E907030000"      # jmp 0x00F59F93 (model/province/capacity classifier)
)
_terminal_extended = bytearray.fromhex(RETRAINING_DRAG_EXTENDED_CAVE)
_terminal_extended[0xAB:0xB8] = bytes.fromhex(RETRAINING_UNIT_PROXY_TERMINAL_HELPER)
_terminal_extended[0xD2:0xF2] = bytes.fromhex(RETRAINING_UNIT_PROXY_CLASSIFIER)
RETRAINING_DRAG_EXTENDED_CAVE = _terminal_extended.hex().upper()

RETRAINING_CASTLE_QUEUE_GATE_HOOK = "E8B9669F00"
RETRAINING_CASTLE_LIVE_DESCRIPTOR_HOOK = "E9A110A500" + ("90" * 9)
CASTLE_TARGET_RETRAINING_CASTLE_QUEUE_GATE_CAVE = (
    "A18C7BC900"      # mov eax, [0x00C97B8C] (active release transaction)
    "85C0"            # test eax, eax
    "7435"            # jz native queue insertion
    "8B4034"          # mov eax, [eax+0x34] (final target object)
    "85C0"            # test eax, eax
    "742E"            # jz native queue insertion
    "8138A0CFF000"    # cmp dword [eax], 0x00F0CFA0 (castle target vtable)
    "7526"            # jne native queue insertion
    "8B442404"        # mov eax, [esp+4] (held type-7 descriptor)
    "0FB75028"        # movzx edx, word [eax+0x28] (stable unit id)
    "81FAFFFF0000"    # cmp edx, 0xFFFF
    "7416"            # je native queue insertion
    "C1E204"          # shl edx, 4
    "8B922882DE00"    # mov edx, [edx+0x00DE8228] (unit model)
    "85D2"            # test edx, edx
    "7409"            # jz native queue insertion
    "837A4404"        # cmp dword [edx+0x44], 4 (active retraining)
    "7503"            # jne native queue insertion
    "C21400"          # ret 0x14 (consume synthetic five-argument insertion)
    "E9831B5DFF"      # native: jmp 0x0052B870
)
DIRECT_TARGET_RETRAINING_CASTLE_QUEUE_GATE_CAVE = (
    "A18C7BC900"      # mov eax, [0x00C97B8C] (active release transaction)
    "85C0"            # test eax, eax
    "7443"            # jz native queue insertion
    "8B4034"          # mov eax, [eax+0x34] (final target object)
    "85C0"            # test eax, eax
    "743C"            # jz native queue insertion
    "8138A0CFF000"    # cmp dword [eax], 0x00F0CFA0 (castle target)
    "740E"            # je retraining validation
    "8138E0C7F000"    # cmp dword [eax], 0x00F0C7E0 (army target)
    "752C"            # jne native queue insertion
    "83786010"        # cmp dword [eax+0x60], 16 (army unit capacity)
    "7D26"            # jge native queue insertion/requeue
    "8B442404"        # mov eax, [esp+4] (held type-7 descriptor)
    "0FB75028"        # movzx edx, word [eax+0x28] (stable unit id)
    "81FAFFFF0000"    # cmp edx, 0xFFFF
    "7416"            # je native queue insertion
    "C1E204"          # shl edx, 4
    "8B922882DE00"    # mov edx, [edx+0x00DE8228] (unit model)
    "85D2"            # test edx, edx
    "7409"            # jz native queue insertion
    "837A4404"        # cmp dword [edx+0x44], 4 (active retraining)
    "7503"            # jne native queue insertion
    "C21400"          # ret 0x14 (suppress synthetic queue insertion)
    "E9751B5DFF"      # native: jmp 0x0052B870
)
FULL_ARMY_REJECT_RETRAINING_CASTLE_QUEUE_GATE_CAVE = (
    DIRECT_TARGET_RETRAINING_CASTLE_QUEUE_GATE_CAVE.replace(
        "837860107D26", "837860107D2B"
    )
)
RETRAINING_CASTLE_QUEUE_GATE_CAVE = (
    FULL_ARMY_REJECT_RETRAINING_CASTLE_QUEUE_GATE_CAVE.replace(
        "8138A0CFF000740E", "8138A0CFF0007464"
    )
)
RETRAINING_FULL_ARMY_REJECT_SOUND_STUB = "E9F6000000"
RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE = (
    "8BB82C82DE00"    # mov edi, [eax+0x00DE822C] (normal UI descriptor)
    "85FF"            # test edi, edi
    "7512"            # jnz native same-province comparison
    "8BB82882DE00"    # mov edi, [eax+0x00DE8228] (unit model)
    "85FF"            # test edi, edi
    "740D"            # jz stock null-descriptor path
    "837F4404"        # cmp dword [edi+0x44], 4
    "7507"            # jne stock null-descriptor path
    "89EF"            # mov edi, ebp (live held descriptor)
    "E947EF5AFF"      # resume: jmp 0x00508C68
    "E968F45AFF"      # null: jmp 0x0050918E
)
CASTLE_TARGET_RETRAINING_CASTLE_TARGET_CAVE = (
    CASTLE_TARGET_RETRAINING_CASTLE_QUEUE_GATE_CAVE
    + ("00" * 0x13)
    + RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE
    + ("00" * (4 + 0x16))
)
DIRECT_TARGET_RETRAINING_CASTLE_TARGET_CAVE = (
    DIRECT_TARGET_RETRAINING_CASTLE_QUEUE_GATE_CAVE
    + ("00" * 5)
    + RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE
    + ("00" * (4 + 0x16))
)
FULL_ARMY_REJECT_RETRAINING_CASTLE_TARGET_CAVE = (
    FULL_ARMY_REJECT_RETRAINING_CASTLE_QUEUE_GATE_CAVE
    + RETRAINING_FULL_ARMY_REJECT_SOUND_STUB
    + RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE
    + ("00" * (4 + 0x16))
)
RETRAINING_CASTLE_CAPACITY_GATE_HELPER = (
    "8B4064"        # mov eax, [eax+0x64] (castle garrison army)
    "85C0"          # test eax, eax
    "74C9"          # jz 0x00F59CF6 (native queue insertion)
    "83786010"      # cmp dword [eax+0x60], 16
    "7DC3"          # jge 0x00F59CF6 (retain/requeue the card)
    "EB9B"          # jmp 0x00F59CD0 (validate active retraining model)
)
RETRAINING_CASTLE_DEFERRED_CAPACITY_HELPER = (
    "EBA8"          # jmp 0x00F59CD0 (let native castle insertion decide capacity)
    + ("90" * 13)
)
NATIVE_CASTLE_RETRAINING_CASTLE_TARGET_CAVE = (
    RETRAINING_CASTLE_QUEUE_GATE_CAVE
    + RETRAINING_FULL_ARMY_REJECT_SOUND_STUB
    + RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE
    + RETRAINING_CASTLE_CAPACITY_GATE_HELPER
    + ("00" * 0x0B)
)
FULL_CASTLE_REQUEUE_RETRAINING_CASTLE_TARGET_CAVE = (
    RETRAINING_CASTLE_QUEUE_GATE_CAVE
    + RETRAINING_FULL_ARMY_REJECT_SOUND_STUB
    + RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE
    + RETRAINING_CASTLE_DEFERRED_CAPACITY_HELPER
    + ("00" * 0x0B)
)

RETRAINING_FOREIGN_ARMY_QUEUE_GATE_JUMP = (
    "E9C4020000"  # jmp 0x00F59F93 (model/province/capacity classifier)
    "90"          # replace the complete prior CMP/JGE pair
)
RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE = (
    "837D6010"      # cmp dword [ebp+0x60], 16
    "0F8CED7F5AFF"  # jl 0x00501D1F (native detach/insert commit)
    "E92F825AFF"    # jmp 0x00501F66 (already requeued full target)
)
RETRAINING_CASTLE_TARGET_CAVE = (
    FULL_CASTLE_REQUEUE_RETRAINING_CASTLE_TARGET_CAVE[: 0x20 * 2]
    + RETRAINING_FOREIGN_ARMY_QUEUE_GATE_JUMP
    + FULL_CASTLE_REQUEUE_RETRAINING_CASTLE_TARGET_CAVE[0x26 * 2 : 0x7E * 2]
    + RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE
    + ("00" * (0x96 - 0x7E - len(RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE) // 2))
)
QUEUE_POSITION_RETRAINING_CASTLE_TARGET_CAVE = RETRAINING_CASTLE_TARGET_CAVE
_terminal_castle = bytearray.fromhex(RETRAINING_CASTLE_TARGET_CAVE)
_terminal_castle[0x1E:0x20] = bytes.fromhex("75A2")
RETRAINING_CASTLE_TARGET_CAVE = _terminal_castle.hex().upper()

DIRECT_TARGET_RETRAINING_DIRECT_TARGET_CAVE = (
    "50A18C7BC90085C0740F8B403485C074088138A0CFF0007435"
    "58608B0424C74044000000008B068B402C89F1FFD069C0840200008B157C03C700"
    "01D089C1E811B75DFFE8B2FEFFFF61E97BF15AFF"
    "588B56640FB74528E941EF5AFF"
    "85C07418506A02E8892460FF83C404588B9424A4000000E93BEF5AFF"
    "89F8EB9F"
    "8BB82C82DE0085FF75168BB82882DE0085FF7411837F4404750B89DF85FF7405"
    "E93F7F5AFFE981815AFF"
    "506A02E8432460FF83C40458E970815AFF"
    + ("00" * (0x2C0 - 0xB6))
)
RETRAINING_FULL_ARMY_REJECT_SOUND_HELPER = "9C606A07E8312460FF83C404619DE9EDFEFFFF"
FULL_ARMY_REJECT_RETRAINING_DIRECT_TARGET_CAVE = (
    DIRECT_TARGET_RETRAINING_DIRECT_TARGET_CAVE[: 0xB6 * 2]
    + RETRAINING_FULL_ARMY_REJECT_SOUND_HELPER
    + ("00" * (0x2C0 - 0xC9))
)
RETRAINING_FULL_CASTLE_POPUP_HELPER = (
    "9C606A05E81E2460FF83C4046A23E8142460FF83C40481ECD40000008D4C2434"
    "68A0CAF000E8ED6275FF8B15107FC9008B52148D4C24488B358077DD00566A00"
    "5250E860E574FF89C1E8B95174FF89C68D4C246856E81D1374FF8D4C247056"
    "E8131374FF8D4C2468E8EA1374FF898424C00000008D4C247868C0CAF000E895"
    "6275FF8B15107FC9008B52148D8C248C0000008B358077DD00566A005250E805"
    "E574FF89C1E85E5174FF89C68D8C24AC00000056E8BF1274FF8D8C24B40000"
    "0056E8B21274FF8D8C24AC000000E8861374FF8B9424C00000008914248944"
    "2404C7442408FFFFFFFF31C08844240C89442410E861785FFF8D8C24B4000000"
    "E8951274FF8D8C24AC000000E8895958FF8D8C248C000000E82DF474FF8D4C"
    "2478E824F474FF8D4C2470E86B1274FF8D4C2468E8625958FF8D4C2448E809"
    "F474FF8D4C2434E800F474FF81C4D4000000619DE9ACEF5AFF"
)
NATIVE_CASTLE_RETRAINING_DIRECT_TARGET_CAVE = (
    FULL_ARMY_REJECT_RETRAINING_DIRECT_TARGET_CAVE[: 0x5D * 2]
    + "746A"  # failed castle insertion enters the native full-castle popup helper
    + FULL_ARMY_REJECT_RETRAINING_DIRECT_TARGET_CAVE[0x5F * 2 : 0x60 * 2]
    + "6A05"  # successful castle insertion uses native castle event 5
    + FULL_ARMY_REJECT_RETRAINING_DIRECT_TARGET_CAVE[0x62 * 2 : 0xC9 * 2]
    + RETRAINING_FULL_CASTLE_POPUP_HELPER
    + ("00" * (0x2C0 - 0xC9 - len(RETRAINING_FULL_CASTLE_POPUP_HELPER) // 2))
)
RETRAINING_FULL_CASTLE_REQUEUE_ENTRY = "E952010000" + ("90" * 4)
RETRAINING_FULL_CASTLE_REQUEUE_HELPER = (
    "9C60"              # preserve EFLAGS and every GPR
    "8BB424F4000000"    # mov esi, [esp+0xF4] (handler argument 0)
    "8B0DB803C700"      # mov ecx, [0x00C703B8] (training panel)
    "6A00"              # native queue insert arg4
    "FF358005C700"      # arg3: selected/source province
    "FF762C"            # arg2: held descriptor coordinate/state
    "FF7628"            # arg1: stable unit id field
    "56"                # arg0: authoritative held descriptor
    "E8ED185DFF"        # call 0x0052B870 (callee ret 0x14)
    "619D"              # restore the insertion-time register/flag context
    "9C60"              # recreate the popup helper's saved context
    "6A05"              # native castle event 5
    "E8A22260FF"        # call 0x0055C230
    "E97FFEFFFF"        # jmp 0x00F59E12 (existing popup body)
)
FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE = (
    NATIVE_CASTLE_RETRAINING_DIRECT_TARGET_CAVE[: 0xC9 * 2]
    + RETRAINING_FULL_CASTLE_REQUEUE_ENTRY
    + NATIVE_CASTLE_RETRAINING_DIRECT_TARGET_CAVE[(0xC9 + 9) * 2 : 0x220 * 2]
    + RETRAINING_FULL_CASTLE_REQUEUE_HELPER
    + ("00" * (0x2C0 - 0x220 - len(RETRAINING_FULL_CASTLE_REQUEUE_HELPER) // 2))
)

FOREIGN_ARMY_GUARD_V1_RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER = (
    "89C1"              # mov ecx, eax (exact target army)
    "8B442404"          # mov eax, [esp+4] (held descriptor)
    "0FB75028"          # movzx edx, word [eax+0x28] (stable id)
    "6683FAFF"          # cmp dx, 0xffff
    "7424"              # je native queue insertion
    "C1E204"            # shl edx, 4
    "8B922882DE00"      # mov edx, [edx+0x00DE8228] (model)
    "85D2"              # test edx, edx
    "7417"              # je native queue insertion
    "837A4404"          # cmp dword [edx+0x44], 4 (retraining)
    "7511"              # jne native queue insertion
    "8A4125"            # mov al, [ecx+0x25] (target province)
    "3A4225"            # cmp al, [edx+0x25] (source province)
    "7509"              # jne native queue insertion
    "83796010"          # cmp dword [ecx+0x60], 16
    "7D08"              # jge full-target event-7/requeue helper
    "C21400"            # ret 0x14 (valid room-bearing source target)
    "E92AFDFFFF"        # jmp 0x00F59CF6 (one native queue insertion)
    "E925FEFFFF"        # jmp 0x00F59DF6 (event 7 then native queue)
)
FOREIGN_ARMY_GUARD_V1_RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD = (
    "817D00E0C7F000"  # cmp dword [ebp], 0x00F0C7E0 (army vtable)
    "7517"            # jne unchanged non-army commit
    "8B902882DE00"    # mov edx, [eax+0x00DE8228] (authoritative model)
    "85D2"            # test edx, edx
    "7417"            # je safe cleanup
    "8A4D25"          # mov cl, [ebp+0x25] (target province)
    "3A4A25"          # cmp cl, [edx+0x25] (source province)
    "750A"            # jne native event-7 rejection
    "E937FDFFFF"      # jmp 0x00F59D28 (capacity commit gate)
    "E9297D5AFF"      # jmp 0x00501D1F (unchanged non-army commit)
    "E9B07D5AFF"      # jmp 0x00501DAB (native event 7, no detach)
    "E9667F5AFF"      # jmp 0x00501F66 (safe cleanup)
)
FOREIGN_ARMY_GUARD_V1_RETRAINING_DIRECT_TARGET_CAVE = (
    FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE[: 0x9B * 2]
    + "E9F1010000"  # flawed first candidate entered 0x00F59FD1
    + FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE[0xA0 * 2 : 0x253 * 2]
    + FOREIGN_ARMY_GUARD_V1_RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER
    + FOREIGN_ARMY_GUARD_V1_RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD
)

RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER = (
    "55"                # push ebp (preserve the gate caller's frame register)
    "89C5"              # mov ebp, eax (exact target army)
    "8B442408"          # mov eax, [esp+8] (held descriptor after PUSH EBP)
    "0FB75028"          # movzx edx, word [eax+0x28] (stable id)
    "6642"              # inc dx (compact 0xffff test)
    "7426"              # jz native queue insertion
    "4A"                # dec edx (restore the valid zero-extended id)
    "C1E204"            # shl edx, 4
    "8B922882DE00"      # mov edx, [edx+0x00DE8228] (model)
    "85D2"              # test edx, edx
    "7418"              # jz native queue insertion
    "837A4404"          # cmp dword [edx+0x44], 4 (retraining)
    "7512"              # jne native queue insertion
    "8A4525"            # mov al, [ebp+0x25] (target province)
    "3A4225"            # cmp al, [edx+0x25] (source province)
    "7510"              # jne terminal event-7/requeue path
    "837D6010"          # cmp dword [ebp+0x60], 16
    "7D0A"              # jge full-target event-7/requeue helper
    "5D"                # pop ebp (restore caller state)
    "C21400"            # ret 0x14 (valid room-bearing source target)
    "5D"                # generic/native fallback: restore caller EBP
    "E928FDFFFF"        # jmp 0x00F59CF6 (unchanged stock insertion)
    "E972FCFFFF"        # terminal active rejection: jmp 0x00F59C45
    "90"                # preserve the complete six-byte rejection block
)
RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD = (
    "817D00E0C7F000"  # cmp dword [ebp], 0x00F0C7E0 (army vtable)
    "0F853E7D5AFF"    # jne 0x00501D1F (unchanged non-army commit)
    "8B902882DE00"    # mov edx, [eax+0x00DE8228] (authoritative model)
    "85D2"            # test edx, edx
    "0F84777F5AFF"    # je 0x00501F66 (safe cleanup)
    "8A4D25"          # mov cl, [ebp+0x25] (target province)
    "3A4A25"          # cmp cl, [edx+0x25] (source province)
    "0F85B07D5AFF"    # jne 0x00501DAB (native event 7, no detach)
    "E928FDFFFF"      # jmp 0x00F59D28 (capacity commit gate)
)
RETRAINING_DIRECT_TARGET_CAVE = (
    FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE[: 0x9B * 2]
    + "E9F4010000"  # resolved descriptor/model now enters the commit guard
    + FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE[0xA0 * 2 : 0x253 * 2]
    + RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER
    + RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD
)
_queue_position_direct = bytearray.fromhex(RETRAINING_DIRECT_TARGET_CAVE)
_queue_position_direct[0x27C:0x27E] = bytes.fromhex("750A")
_queue_position_direct[0x288:0x28E] = bytes.fromhex("5DE944FBFFFF")
_queue_position_direct[0x28E:0x294] = bytes.fromhex("5DE922FEFFFF")
QUEUE_POSITION_RETRAINING_DIRECT_TARGET_CAVE = _queue_position_direct.hex().upper()
_terminal_direct = bytearray.fromhex(RETRAINING_DIRECT_TARGET_CAVE)
_terminal_direct[0xC4:0xC9] = bytes.fromhex("E909FDFFFF")
RETRAINING_DIRECT_TARGET_CAVE = _terminal_direct.hex().upper()

# Target-taxonomy revision expected by the next migration.  Keep these as
# independently assembled byte contracts so the preceding v8 output must fail
# before production patch definitions are changed.
TARGET_TAXONOMY_LIVE_DESCRIPTOR_HOOK = "8BB82C82DE0085FF0F840410A500"
TARGET_TAXONOMY_LIVE_DESCRIPTOR_FALLBACK = (
    "8BB82882DE0085FF740D837F4404750789EFE9E5EF5AFFE906F55AFF"
    + ("90" * 8)
)
TARGET_TAXONOMY_QUEUE_CLASSIFIER = (
    "8B4424040FB750286642747C4AC1E2048B822882DE0085C0746E837844047568"
    "5589C50FB6922282DE00A18C7BC90085C074548B403485C0744D3B4424087447"
    "3B05B403C700743F3B05B803C70074373B05BC03C700742F8138E020F1007510"
    "83C0708138E0C7F0007517E979020000528B10817A08106152005A740AE96702"
    "0000E914FFFFFF5DEBC2"
    + ("90" * 0x0C)
)
TARGET_TAXONOMY_SEMANTIC_HELPER = (
    "8138E0C7F00074358138A0CFF00075548A70253A7525754C8B406485C0744181"
    "38E0C7F000753D0FB7405A6640743148C1E0043A902282DE007529EB238A7025"
    "3A7525751F950FB7455A6640741648C1E0043A902282DE00750A837D60107D04"
    "5DC21400E949FCFFFF"
    + ("90" * 4)
)
TARGET_TAXONOMY_DIRECT_COMMIT = "E93F7F5AFF"

# Shared payload/target policy for both per-frame hover feedback and the final
# release gate.  These bytes are independently assembled in the task evidence
# so tests can reject a stale jump, divergent hover rule, or partial cave.
SHARED_PAYLOAD_TARGET_POLICY = (
    "55837948070F85E20000000FB7512866420F84D60000004AC1E2048BAA2882DE00"
    "85ED0F84C4000000837D44040F85BA00000085C00F84B200000039C80F84AA0000"
    "003B05B403C7000F849E0000003B05B803C7000F84920000003B05BC03C7000F84"
    "860000008A8A2282DE008138E020F100750D83C0708138E0C7F0007569EB148138"
    "E0C7F000740C8138A0CFF000754CB502EB02B5018A50253A5525754980FD027511"
    "8B506485D2742D813AE0C7F0007535EB08837860107D2D89C20FB7525A66427507"
    "80FD02740EEB1C4AC1E2043A8A2282DE0075100FB6C55DC38B10817A0810615200"
    "740431C05DC3B8030000005DC3"
)
SHARED_RELEASE_POLICY_WRAPPER = (
    "5551A18C7BC90085C074058B4034EB0231C08B4C240CE8E5FEFFFF83F803740F"
    "85C07405595DC2140059E916EFFFFF595DE93A0B5DFF"
)
SHARED_HOVER_POLICY_WRAPPER = (
    "8B158C7BC9008B6A3089E989D8E88EFEFFFF83F803740785C00F95C0EB0A558B"
    "338B560C89D9FFD28B2D8C7BC900884554E9F83A62FF"
)
SHARED_POLICY_CAVE = (
    SHARED_PAYLOAD_TARGET_POLICY
    + ("90" * (0x100 - len(bytes.fromhex(SHARED_PAYLOAD_TARGET_POLICY))))
    + SHARED_RELEASE_POLICY_WRAPPER
    + ("90" * (0x60 - len(bytes.fromhex(SHARED_RELEASE_POLICY_WRAPPER))))
    + SHARED_HOVER_POLICY_WRAPPER
    + ("90" * (0xA0 - len(bytes.fromhex(SHARED_HOVER_POLICY_WRAPPER))))
)
SHARED_RELEASE_CLASSIFIER_FORWARD = "E951100000" + ("90" * (0x96 - 5))
RETIRED_TARGET_TAXONOMY_SEMANTIC_HELPER = "90" * 0x6D
RETRAINING_HOVER_POLICY_ORIGINAL = (
    "8B158C7BC9008B6A30558B338B560C8BCBFFD28B2D8C7BC900884554"
)
RETRAINING_HOVER_POLICY_HOOK = "E9E9C49D00" + ("90" * (0x1C - 5))

RETRAINING_QUEUE_POSITION_CAPTURE_HOOK = (
    "E809EBA200"        # call 0x00F59B00
    "90"                # cover both displaced MOV instructions
)
RETRAINING_QUEUE_POSITION_CAVE = (
    "8B55008B45048915F8AFF500A3FCAFF500C3"
    "FF742414FF742414FF742414FF742414FF742414E8451D5DFF9C50A1F8AFF500"
    "8B088B54240C8B52286639510C74088B0939C175F4EB408B15FCAFF50039017505"
    "3951047431395004752C390275288B018B5104394804751E390A751A8950048902"
    "A1F8AFF5008B15FCAFF5008901895104894804890A31C0A3F8AFF500A3FCAFF500"
    "589DC21400"
)

# Exact repeat/right-click revision that used 0x00F5A000 as a transient byte.
# Runtime evidence proved that address belongs to live game data, so it is only
# accepted as an upgrade source and is never emitted by the final patch.
REPEAT_RC_RETRAINING_DRAG_PROVINCE_CAVE = (
    "0FB64025A38005C7006A0150FF35B87BC900FF35B47BC900518B0DB803C700E8"
    "3B0BE1FFC38B882C82DE0085C90F853684E1FF8B802882DE0085C00F84AD84E1"
    "FF0FB650253B5358750CC60500A0F50001E91F84E1FF89E9E8A3FFFFFFE91DEF"
    "830090909090909090909090909090"
)
REPEAT_RC_RETRAINING_DRAG_EXTENDED_CAVE = (
    "60C60500A0F500528B0424C74044000000008B068B402C89F1FFD069C0840200"
    "008B157C03C70001D089C1E8CAB85DFF61E939F35AFF00000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000089D9E82DB85DFF50A000A0F500C60500A0F500523C0158750A6A"
    "02E8B02560FF83C404E977955DFF0000000000000000C60500A0F500526A07E8"
    "922560FF83C404E959955DFF00000000"
)

# Exact audio/full-capacity revision that immediately preceded the repeatable
# lifecycle/right-click correction.  It must remain migratable but must not be
# reported as the new final state.
AUDIO_FULL_RETRAINING_DRAG_EXTENDED_CAVE = (
    "6089C784C07564C7042478000000E8F2267AFF89C585ED74698B068B402C89F1"
    "FFD050FF766C89E9E8B94E5AFF8BBC24C40000000FB7475A6A016A005089E9E8"
    "525D5AFF84C074298B068B402C89F1FFD069C0840200008B157C03C70001D06A"
    "006A005589C1E84F865DFF61E9E0F05AFF5589E06A0250E8BA0A62FF83C40883"
    "C404616A07E80C2660FF83C404E9DDF25AFF0000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000089D9E82DB85DFF803D00A0F50001751250B052880500A0F50058"
    "6A02E8AF2560FF83C404E976955DFF000000000000006A07E8992560FF83C404"
    "E960955DFF0000000000000000000000"
)

RETRAINING_DRAG_LIFECYCLE_CAVE = (
    RETRAINING_DRAG_HOVER_DESCRIPTOR_CAVE
    + RETRAINING_DRAG_TARGET_DESCRIPTOR_CAVE
    + RETRAINING_DRAG_ACTION_DESCRIPTOR_CAVE
    + RETRAINING_DRAG_DROP_DESCRIPTOR_CAVE
    + RETRAINING_DRAG_SOURCE_PROVINCE_CHECK_CAVE
    + RETRAINING_DRAG_ARMY_DROP_CAVE
    + RETRAINING_DRAG_NO_TARGET_CAVE
    + ("90" * 5)
)

RETRAINING_DRAG_PROVINCE_CAVE = (
    RETRAINING_DRAG_REQUEUE_HELPER_CAVE
    + RETRAINING_DRAG_PROVINCE_DROP_CAVE
    + ("90" * 13)
)

MARKER_FREE_RETRAINING_DRAG_PROVINCE_CAVE = (
    RETRAINING_DRAG_REQUEUE_HELPER_CAVE
    + MARKER_FREE_RETRAINING_DRAG_PROVINCE_DROP_CAVE
    + ("90" * 13)
)

PREVIOUS_RETRAINING_DRAG_HOVER_GUARD_CAVE = "85F60F841F92DEFF8B168B5224E94992DEFF"
PREVIOUS_RETRAINING_DRAG_TARGET_GUARD_CAVE = "85DB0F84F4E8DEFF8B138B5224E94AE7DEFF"
PREVIOUS_RETRAINING_DRAG_ACTION_GUARD_CAVE = "85C90F8431CBE2FF8B018B4024E9EECAE2FF"

PREVIOUS_RETRAINING_DRAG_PATCHES = [
    (0x001041B6, "8B168B5224", "E9A56D2100"),
    (0x0031AF60, "00" * 18, PREVIOUS_RETRAINING_DRAG_HOVER_GUARD_CAVE),
    (0x001096D7, "8B138B5224", "E9A4182100"),
    (0x0031AF80, "00" * 18, PREVIOUS_RETRAINING_DRAG_TARGET_GUARD_CAVE),
    (0x00147A9B, "8B018B4024", "E900351D00"),
    (0x0031AFA0, "00" * 18, PREVIOUS_RETRAINING_DRAG_ACTION_GUARD_CAVE),
]

CASTLE_TARGET_RETRAINING_DRAG_PATCHES_CORE = [
    (0x001041B6, "8B168B5224", "E9A56D2100"),
    (0x001096D7, "8B138B5224", "E995182100"),
    (0x00147A9B, "8B018B4024", "E9E2341D00"),
    (0x0014787B, "0F8423010000", "E913371D0090"),
    (0x001478D2, "8B357C03C700", "E9E4361D0090"),
    (0x00163807, "A1B803C700", "E9D8771B00"),
    (0x0013316C, "8B882C82DE0085C9", "E9C57B1E00909090"),
    (0x0031AD11, "00" * 0x6F, RETRAINING_DRAG_PROVINCE_CAVE),
    (0x0031AF60, "00" * 0xA0, RETRAINING_DRAG_LIFECYCLE_CAVE),
    (0x00108CD5, "8B56640FB74528", RETRAINING_DRAG_RIGHT_CLICK_HOOK),
    (0x001331CC, "8BCBE8C1220000EB2A", RETRAINING_DRAG_SUCCESS_SOUND_HOOK),
    (
        0x006F8B9A,
        "00" * (len(CASTLE_TARGET_RETRAINING_DRAG_EXTENDED_CAVE) // 2),
        CASTLE_TARGET_RETRAINING_DRAG_EXTENDED_CAVE,
    ),
    (0x001635EC, "E87F82FCFF", RETRAINING_CASTLE_QUEUE_GATE_HOOK),
    (
        0x00108C5A,
        "8BB82C82DE0085FF0F8426050000",
        RETRAINING_CASTLE_LIVE_DESCRIPTOR_HOOK,
    ),
    (0x006F8CAA, "00" * 0x96, CASTLE_TARGET_RETRAINING_CASTLE_TARGET_CAVE),
    (0x00000264, "60000040", "60000060"),
    (0x006F9000, "00", "00"),
]

RETRAINING_DIRECT_TARGET_ORIGINAL_PATCHES = [
    (0x00101D11, "8BB82C82DE0085FF", "8BB82C82DE0085FF"),
    (0x00101D84, "E9DD010000", "E9DD010000"),
    (0x00108CEB, "8B9424A4000000", "8B9424A4000000"),
    (0x006F8D40, "00" * 0x2C0, "00" * 0x2C0),
]

CASTLE_TARGET_RETRAINING_DRAG_PATCHES = (
    CASTLE_TARGET_RETRAINING_DRAG_PATCHES_CORE
    + RETRAINING_DIRECT_TARGET_ORIGINAL_PATCHES
)

RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in CASTLE_TARGET_RETRAINING_DRAG_PATCHES
]
RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    RETRAINING_DRAG_EXTENDED_CAVE,
)
RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    RETRAINING_CASTLE_TARGET_CAVE,
)
RETRAINING_DRAG_PATCHES[17] = (
    0x00101D11,
    "8BB82C82DE0085FF",
    "E9A580A500909090",
)
RETRAINING_DRAG_PATCHES[18] = (
    0x00101D84,
    "E9DD010000",
    "E95C80A500",
)
RETRAINING_DRAG_PATCHES[19] = (
    0x00108CEB,
    "8B9424A4000000",
    "E9AB10A5009090",
)
RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    RETRAINING_DIRECT_TARGET_CAVE,
)
RETRAINING_DRAG_PATCHES.extend(
    [
        (
            0x0012AFF2,
            "8B55008B4504",
            RETRAINING_QUEUE_POSITION_CAPTURE_HOOK,
        ),
        (
            0x006F8B00,
            "00" * 0x9A,
            RETRAINING_QUEUE_POSITION_CAVE,
        ),
        (
            0x006F9FF8,
            "00" * 8,
            "00" * 8,
        ),
    ]
)

# Exact final bytes from the immediately preceding target-taxonomy-v8
# revision.  The next revision must recognize these only as a migration
# source, never as its own final state.
TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched) for offset, original, patched in RETRAINING_DRAG_PATCHES
]

# Exact full-castle-requeue revision that preceded the foreign-army
# transaction guard. It remains a supported in-place migration source and
# must never be reported as the final revision.
FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    FULL_CASTLE_REQUEUE_RETRAINING_CASTLE_TARGET_CAVE,
)
FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE,
)

# The first foreign-army guard candidate preserved the target in ECX at the
# preliminary queue gate, corrupting the native queue insertion's this
# pointer. It is accepted only as an exact migration source.
FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    QUEUE_POSITION_RETRAINING_CASTLE_TARGET_CAVE,
)
FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    FOREIGN_ARMY_GUARD_V1_RETRAINING_DIRECT_TARGET_CAVE,
)

# Exact native-castle revision reported as final before capacity-by-unit-size
# exposed the missing post-failure requeue transaction. With the same other
# options its SHA-256 is
# 1C71AD74CB43A60E1CA6362D0CA5E34A8A42962E7A373BCD656633820158264C.
NATIVE_CASTLE_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
NATIVE_CASTLE_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
NATIVE_CASTLE_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    NATIVE_CASTLE_RETRAINING_CASTLE_TARGET_CAVE,
)
NATIVE_CASTLE_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    NATIVE_CASTLE_RETRAINING_DIRECT_TARGET_CAVE,
)

# Exact direct-target revision immediately before full-army rejection gained
# native event 7. It must remain migratable but must not be reported as final.
DIRECT_TARGET_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
DIRECT_TARGET_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
DIRECT_TARGET_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    DIRECT_TARGET_RETRAINING_CASTLE_TARGET_CAVE,
)
DIRECT_TARGET_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    DIRECT_TARGET_RETRAINING_DIRECT_TARGET_CAVE,
)

# Exact direct-target/full-army-rejection revision immediately before native
# castle event-5 parity and stock-equivalent full-castle modal rejection. With
# the same other options its SHA-256 is
# 47A09DD580445081762B96E3CB247DA60E5FEB0D78C43F4B0C2E1752EC210EC3.
FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    FULL_ARMY_REJECT_RETRAINING_CASTLE_TARGET_CAVE,
)
FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    FULL_ARMY_REJECT_RETRAINING_DIRECT_TARGET_CAVE,
)

# Exact right-click-success-sound revision immediately before source-castle
# normalization.  With the same other options its SHA-256 is
# 8492022685CDF07412FF06C6D2F61FF99F464530FFC55DFECF5AF81910ABE210.
RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in CASTLE_TARGET_RETRAINING_DRAG_PATCHES
]
for _index in (12, 13, 14):
    _offset, _original, _patched = RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES[_index]
    RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES[_index] = (_offset, _original, _original)

MODEL_STATE_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES
]
MODEL_STATE_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE,
)

CURRENT_RETRAINING_DRAG_PROVINCE_CAVE = (
    "0FB64025A38005C7006A0150FF35B87BC900FF35B47BC900518B0DB803C700E8"
    "3B0BE1FFC38B882C82DE0085C90F853684E1FF8B802882DE0085C00F84AD84E1"
    "FF0FB650253B53580F842784E1FF89E9E8ABFFFFFFE99484E1FF909090909090"
    "909090909090909090909090909090"
)

CURRENT_RETRAINING_DRAG_PATCHES = [
    (0x001041B6, "8B168B5224", "E9A56D2100"),
    (0x001096D7, "8B138B5224", "E995182100"),
    (0x00147A9B, "8B018B4024", "E9E2341D00"),
    (0x0014787B, "0F8423010000", "E913371D0090"),
    (0x001478D2, "8B357C03C700", "E9E4361D0090"),
    (0x00163807, "A1B803C700", "E9D8771B00"),
    (0x0013316C, "8B882C82DE0085C9", "E9C57B1E00909090"),
    (0x0031AD11, "00" * 0x6F, CURRENT_RETRAINING_DRAG_PROVINCE_CAVE),
    (0x0031AF60, "00" * 0xA0, RETRAINING_DRAG_LIFECYCLE_CAVE),
    (0x00108CD5, "8B56640FB74528", "8B56640FB74528"),
    (0x001331CC, "8BCBE8C1220000EB2A", "8BCBE8C1220000EB2A"),
    (0x006F8B9A, "00" * 0x110, "00" * 0x110),
    (0x001635EC, "E87F82FCFF", "E87F82FCFF"),
    (
        0x00108C5A,
        "8BB82C82DE0085FF0F8426050000",
        "8BB82C82DE0085FF0F8426050000",
    ),
    (0x006F8CAA, "00" * 0x96, "00" * 0x96),
    (0x00000264, "60000040", "60000040"),
    (0x006F9000, "00", "00"),
] + RETRAINING_DIRECT_TARGET_ORIGINAL_PATCHES

AUDIO_FULL_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES
]
AUDIO_FULL_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    AUDIO_FULL_RETRAINING_DRAG_EXTENDED_CAVE,
)
AUDIO_FULL_RETRAINING_DRAG_PATCHES[7] = (
    0x0031AD11,
    "00" * 0x6F,
    REPEAT_RC_RETRAINING_DRAG_PROVINCE_CAVE,
)
AUDIO_FULL_RETRAINING_DRAG_PATCHES[16] = (0x006F9000, "00", "52")

REPEAT_RC_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES
]
REPEAT_RC_RETRAINING_DRAG_PATCHES[7] = (
    0x0031AD11,
    "00" * 0x6F,
    REPEAT_RC_RETRAINING_DRAG_PROVINCE_CAVE,
)
REPEAT_RC_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    REPEAT_RC_RETRAINING_DRAG_EXTENDED_CAVE,
)
REPEAT_RC_RETRAINING_DRAG_PATCHES[16] = (0x006F9000, "00", "52")

MARKER_FREE_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES
]
MARKER_FREE_RETRAINING_DRAG_PATCHES[7] = (
    0x0031AD11,
    "00" * 0x6F,
    MARKER_FREE_RETRAINING_DRAG_PROVINCE_CAVE,
)
MARKER_FREE_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE,
)

# Every revision predating queue-position preservation has stock bytes at the
# removal hook and canonical zero-fill in the newly owned executable cave.
_QUEUE_POSITION_CLEAN_PATCHES = [
    (0x0012AFF2, "8B55008B4504", "8B55008B4504"),
    (0x006F8B00, "00" * 0x9A, "00" * 0x9A),
    (0x006F9FF8, "00" * 8, "00" * 8),
]
for _legacy_retraining_revision in (
    FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES,
    FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES,
    NATIVE_CASTLE_RETRAINING_DRAG_PATCHES,
    DIRECT_TARGET_RETRAINING_DRAG_PATCHES,
    FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES,
):
    _legacy_retraining_revision[21:] = _QUEUE_POSITION_CLEAN_PATCHES
for _legacy_retraining_revision in (
    CASTLE_TARGET_RETRAINING_DRAG_PATCHES,
    RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES,
    MODEL_STATE_RETRAINING_DRAG_PATCHES,
    CURRENT_RETRAINING_DRAG_PATCHES,
    AUDIO_FULL_RETRAINING_DRAG_PATCHES,
    REPEAT_RC_RETRAINING_DRAG_PATCHES,
    MARKER_FREE_RETRAINING_DRAG_PATCHES,
):
    _legacy_retraining_revision.extend(_QUEUE_POSITION_CLEAN_PATCHES)

# The immediately preceding working foreign-army guard had the correct
# single-requeue transaction but restored the card at the current queue head.
FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    QUEUE_POSITION_RETRAINING_CASTLE_TARGET_CAVE,
)
_v2_direct = bytearray.fromhex(QUEUE_POSITION_RETRAINING_DIRECT_TARGET_CAVE)
_v2_direct[0x289:0x28E] = bytes.fromhex("E928FDFFFF")
FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    _v2_direct.hex().upper(),
)
FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES[21:] = _QUEUE_POSITION_CLEAN_PATCHES

# Exact queue-position-preserving revision that immediately preceded terminal
# rejection of unit/banner proxy targets. It remains a supported migration
# source and must never be reported as the final revision.
QUEUE_POSITION_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
QUEUE_POSITION_RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    QUEUE_POSITION_RETRAINING_DRAG_EXTENDED_CAVE,
)
QUEUE_POSITION_RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    QUEUE_POSITION_RETRAINING_CASTLE_TARGET_CAVE,
)
QUEUE_POSITION_RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    QUEUE_POSITION_RETRAINING_DIRECT_TARGET_CAVE,
)

# Final target-taxonomy revision.  The queue insertion gate is now the single
# pre-transaction classifier for active retraining releases.  It permits only
# same-province, same-owner field armies or castles; inert panel/UI objects
# retain native cancellation, and every other interactive target reaches the
# existing terminal event-7 plus position-preserving one-requeue path.
_target_taxonomy_extended = bytearray.fromhex(RETRAINING_DRAG_PATCHES[11][2])
_target_taxonomy_extended[0xD2:0xF6] = bytes.fromhex(
    TARGET_TAXONOMY_LIVE_DESCRIPTOR_FALLBACK
)
RETRAINING_DRAG_EXTENDED_CAVE = _target_taxonomy_extended.hex().upper()
RETRAINING_CASTLE_TARGET_CAVE = TARGET_TAXONOMY_QUEUE_CLASSIFIER
_target_taxonomy_direct = bytearray.fromhex(RETRAINING_DRAG_PATCHES[20][2])
_target_taxonomy_direct[0x9B:0xA0] = bytes.fromhex(TARGET_TAXONOMY_DIRECT_COMMIT)
_target_taxonomy_direct[0x253:0x2C0] = bytes.fromhex(
    TARGET_TAXONOMY_SEMANTIC_HELPER
)
RETRAINING_DIRECT_TARGET_CAVE = _target_taxonomy_direct.hex().upper()

RETRAINING_DRAG_PATCHES[11] = (
    0x006F8B9A,
    "00" * 0x110,
    RETRAINING_DRAG_EXTENDED_CAVE,
)
RETRAINING_DRAG_PATCHES[13] = (
    0x00108C5A,
    "8BB82C82DE0085FF0F8426050000",
    TARGET_TAXONOMY_LIVE_DESCRIPTOR_HOOK,
)
RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    RETRAINING_CASTLE_TARGET_CAVE,
)
RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    RETRAINING_DIRECT_TARGET_CAVE,
)

# Exact target-taxonomy revision that exposed the two follow-up regressions:
# ordinary unfinished queue entries jumped into the middle of an instruction,
# while hover used the native owner-only army validator instead of the release
# policy.  It remains an exact migration source and is not the new final state.
TARGET_TAXONOMY_FINAL_RETRAINING_DRAG_PATCHES = [
    (offset, original, patched)
    for offset, original, patched in RETRAINING_DRAG_PATCHES
]
TARGET_TAXONOMY_FINAL_RETRAINING_DRAG_PATCHES.extend(
    [
        (
            0x0017E872,
            RETRAINING_HOVER_POLICY_ORIGINAL,
            RETRAINING_HOVER_POLICY_ORIGINAL,
        ),
        (0x006F9C00, "00" * 0x200, "00" * 0x200),
        (0x0000028C, "400000C0", "400000C0"),
    ]
)

# New final: the queue gate forwards on a complete instruction boundary, the
# obsolete duplicated semantic helper is retired, and both hover and release
# call the same pure payload/target policy in a separately preflighted cave.
RETRAINING_CASTLE_TARGET_CAVE = SHARED_RELEASE_CLASSIFIER_FORWARD
_shared_policy_direct = bytearray.fromhex(RETRAINING_DIRECT_TARGET_CAVE)
_shared_policy_direct[0x253:0x2C0] = bytes.fromhex(
    RETIRED_TARGET_TAXONOMY_SEMANTIC_HELPER
)
RETRAINING_DIRECT_TARGET_CAVE = _shared_policy_direct.hex().upper()
RETRAINING_DRAG_PATCHES[14] = (
    0x006F8CAA,
    "00" * 0x96,
    RETRAINING_CASTLE_TARGET_CAVE,
)
RETRAINING_DRAG_PATCHES[20] = (
    0x006F8D40,
    "00" * 0x2C0,
    RETRAINING_DIRECT_TARGET_CAVE,
)
RETRAINING_DRAG_PATCHES.extend(
    [
        (
            0x0017E872,
            RETRAINING_HOVER_POLICY_ORIGINAL,
            RETRAINING_HOVER_POLICY_HOOK,
        ),
        (0x006F9C00, "00" * 0x200, SHARED_POLICY_CAVE),
        (0x0000028C, "400000C0", "400000E0"),
    ]
)

ALL_PATCHES = (
    AUDIO_PATCHES
    + UNIT_PATCHES
    + HARVEST_PATCHES
    + HISTORICAL_PATCHES
    + AMMO_PATCHES
    + ODAWARA_PATCHES
    + ADVISOR_RANDOM_PATCHES
    + RETRAINING_DRAG_PATCHES
)


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


ORIGINAL_ODAWARA_BDF = """//
// Battle description file
//

Predefined::true
Title::"Hideyoshi_Odawara_Title_Label"
Author::"Klaude Thomas"
Rating::"New_Hideyoshi_Odawara_Rating_Label"
Description::"New_Hideyoshi_Odawara_Description_Label"
Conditions::"New_Hideyoshi_Odawara_Conditions_Label"

IntroFMV::""
OutroFMV::"xtro_hid.mpg"
OutroSubtitles::"Hideyoshi campaign victory"

MapName::"odawara (toyotomi)"
BattleType::BATTLE_TYPE_HISTORICAL
Deployement::false
Season::summer
WeatherSequenceId::3

Player::"Toyotomi Hideyoshi_xzy" 3 3 LOCAL "Toyotomi" 0 false 19784 37884 180
Player::"Hojo_xzy" 6 6 ARTIFICIAL "Hojo" 0 true 20376 2982 0

TerminatingTrigger::"BATTLE_PLAYER_LOST_A_PERCENTAGE_OF_TROOPS" 1 90 true 6
TerminatingTrigger::"BATTLE_PLAYER_KILL_ENEMY_GENERAL" 2 3 3
TerminatingTrigger::"BATTLE_PLAYER_TIMEOUT" 3 7 3
TerminatingTrigger::"BATTLE_PLAYER_LOST_A_PERCENTAGE_OF_TROOPS" 4 60 true 3

TerminatingTriggerGroup::1 1 SUCCESS_FINISHED_SEQUENCE DEFENDER ""
TerminatingTriggerGroup::2 1 LOST DEFENDER "ODAWARA"
TerminatingTriggerGroup::3 1 LOST DEFENDER "ODAWARA"
TerminatingTriggerGroup::4 1 LOST DEFENDER "ODAWARA"
"""

ORIGINAL_ODAWARA_MAP = (
    b"odawara map header\x00"
    + b"\x01cwallsec\n"
    + struct.pack("<fiiii", 1.0, 0, 8128, -1307, 3072)
    + b"\x01cent_open\n"
    + struct.pack("<fiiii", 1.0, 0, 8128, -1307, 17408)
    + b"\x00odawara map tail"
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
    odawara_bdf = game / ODAWARA_BDF
    odawara_bdf.parent.mkdir(parents=True)
    odawara_bdf.write_text(ORIGINAL_ODAWARA_BDF, encoding="ascii")
    odawara_map = game / ODAWARA_MAP
    odawara_map.parent.mkdir(parents=True)
    odawara_map.write_bytes(ORIGINAL_ODAWARA_MAP)
    return game


def run_patcher(*args: str, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PATCHER), "--target", str(target), *args],
        text=True,
        encoding="utf-8",
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


def assert_odawara_bdf_unchanged(game: Path) -> None:
    bdf = game / ODAWARA_BDF
    assert bdf.read_text(encoding="ascii") == ORIGINAL_ODAWARA_BDF


def assert_no_odawara_bdf_backup(game: Path) -> None:
    assert not (game / f"{ODAWARA_BDF}{SIDE_CAR_BACKUP}").exists()


def assert_no_odawara_map_backup(game: Path) -> None:
    assert not (game / f"{ODAWARA_MAP}{SIDE_CAR_BACKUP}").exists()


def assert_odawara_map_unchanged(game: Path) -> None:
    assert (game / ODAWARA_MAP).read_bytes() == ORIGINAL_ODAWARA_MAP


def test_apply_recommended_fixes_patches_selected_groups_and_creates_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    result = run_patcher("--apply", "recommended", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=False)
    assert_group_state(exe, HARVEST_PATCHES, patched=False)
    assert_group_state(exe, AMMO_PATCHES, patched=True)
    assert_group_state(exe, ODAWARA_PATCHES, patched=True)
    assert_kawanakajima_bdf_patched(game)
    assert_odawara_bdf_unchanged(game)
    assert_no_odawara_bdf_backup(game)
    assert_odawara_map_unchanged(game)
    assert_no_odawara_map_backup(game)
    assert_only_shared_exe_backup(game, original_bytes)
    assert_kawanakajima_backup(game)
    assert result.stdout.count("backup_created=") == 2


def test_single_fix_succeeds_with_unselected_partial_retraining_state(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    offset, _original, patched = RETRAINING_DRAG_PATCHES[0]
    write_bytes(blob, offset, patched)
    exe.write_bytes(blob)
    partial = exe.read_bytes()

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert read_bytes(exe, offset, patched) == bytes.fromhex(patched)
    assert_only_shared_exe_backup(game, partial)


def test_single_fix_does_not_require_unselected_battle_data(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    (game / KAWANAKAJIMA_BDF).unlink()

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(game / "ShogunM.exe", HISTORICAL_PATCHES, patched=True)


def test_single_fix_preserves_unselected_custom_wrapper_config(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    config = game / DGVOODOO_CONF
    custom = b"third-party wrapper config\n"
    config.write_bytes(custom)

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert config.read_bytes() == custom
    assert not (game / f"{DGVOODOO_CONF}{SIDE_CAR_BACKUP}").exists()


def test_directory_at_backup_path_fails_before_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()
    (game / SHARED_BACKUP).mkdir()

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode != 0
    assert "backup" in result.stderr
    assert exe.read_bytes() == before


def test_empty_backup_fails_before_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()
    backup = game / SHARED_BACKUP
    backup.write_bytes(b"")

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode != 0
    assert "backup" in result.stderr
    assert exe.read_bytes() == before
    assert backup.read_bytes() == b""


def test_wrong_size_executable_backup_fails_before_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()
    backup = game / SHARED_BACKUP
    backup.write_bytes(b"diagnostics accidentally saved as an executable backup")

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode != 0
    assert "invalid_backup" in result.stderr
    assert exe.read_bytes() == before


def test_unreadable_transaction_journal_preserves_target_and_evidence(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()
    transaction = game / ".unofficial-patch-transaction"
    transaction.mkdir()
    journal = transaction / "journal.bin"
    journal.write_bytes(b"truncated unknown journal")
    snapshot = transaction / "saved-evidence.bin"
    snapshot.write_bytes(b"preserve recovery evidence")

    result = run_patcher("--apply", "historical", target=game)

    assert result.returncode != 0
    assert "unfinished_transaction" in result.stderr
    assert exe.read_bytes() == before
    assert journal.read_bytes() == b"truncated unknown journal"
    assert snapshot.read_bytes() == b"preserve recovery evidence"


def test_helper_log_keeps_full_unicode_target_and_success_state(tmp_path: Path) -> None:
    root = tmp_path / "日本"
    root.mkdir()
    game = make_clean_game(root)
    log = tmp_path / "helper.log"

    result = run_patcher("--apply", "recommended", "--log", str(log), target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    text = log.read_text(encoding="utf-8")
    assert str(game / "ShogunM.exe") in text
    assert "version=1.3.1" in text
    assert "phase=complete" in text
    assert "before_sha256=" in text and "after_sha256=" in text
    assert len(text) > 1024


def test_helper_log_cannot_append_to_game_executable(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()

    result = run_patcher("--apply", "historical", "--log", str(exe), target=game)

    assert result.returncode != 0
    assert "unsafe_log" in result.stderr
    assert exe.read_bytes() == before


def test_wrapper_payload_is_applied_with_executable_selection(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    payload = PROJECT / "vendor" / "dgvoodoo2"
    original = (game / "ShogunM.exe").read_bytes()

    result = run_patcher("--apply", "historical,dgvoodoo-resolution", "--payload", str(payload), target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(game / "ShogunM.exe", HISTORICAL_PATCHES, patched=True)
    assert_only_shared_exe_backup(game, original)
    for name in ("DDraw.dll", "D3DImm.dll", "D3D9.dll", "dgVoodoo.conf"):
        assert (game / name).read_bytes() == (payload / name).read_bytes()


def test_invalid_wrapper_payload_fails_without_selected_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    before = exe.read_bytes()
    payload = tmp_path / "payload"
    payload.mkdir()
    for name in ("DDraw.dll", "D3DImm.dll", "D3D9.dll", "dgVoodoo.conf"):
        (payload / name).write_bytes(b"untrusted payload")

    result = run_patcher("--apply", "historical", "--payload", str(payload), target=game)

    assert result.returncode == 2
    assert "error=invalid_payload" in result.stderr
    assert exe.read_bytes() == before
    assert not (game / SHARED_BACKUP).exists()


def test_apply_all_fixes_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_bytes = exe.read_bytes()

    first = run_patcher("--apply", "historical,retraining-drag,throne,unit,harvest,ammo,kawanakajima,odawara", target=game)
    after_first = exe.read_bytes()
    second = run_patcher("--apply", "historical,retraining-drag,throne,unit,harvest,ammo,kawanakajima,odawara", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == after_first
    assert_group_state(exe, HISTORICAL_PATCHES, patched=True)
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert_group_state(exe, AUDIO_PATCHES, patched=True)
    assert_group_state(exe, UNIT_PATCHES, patched=True)
    assert_group_state(exe, HARVEST_PATCHES, patched=True)
    assert_group_state(exe, AMMO_PATCHES, patched=True)
    assert_group_state(exe, ODAWARA_PATCHES, patched=True)
    assert_kawanakajima_bdf_patched(game)
    assert_odawara_bdf_unchanged(game)
    assert_no_odawara_bdf_backup(game)
    assert_odawara_map_unchanged(game)
    assert_no_odawara_map_backup(game)
    assert_only_shared_exe_backup(game, original_bytes)
    assert_kawanakajima_backup(game)
    assert first.stdout.count("backup_created=") == 2
    assert second.stdout.count("backup_created=") == 0


def test_dgvoodoo_resolution_config_patch_bounds_enumerated_modes_and_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()
    config = game / DGVOODOO_CONF
    config.write_bytes(UNSAFE_DGVOODOO_CONF.encode("ascii"))

    first = run_patcher("--apply", "dgvoodoo-resolution", target=game)
    after_first = config.read_bytes().decode("ascii")
    second = run_patcher("--apply", "dgvoodoo-resolution", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert after_first == FIXED_DGVOODOO_CONF
    assert config.read_bytes().decode("ascii") == FIXED_DGVOODOO_CONF
    backup = game / f"{DGVOODOO_CONF}{SIDE_CAR_BACKUP}"
    assert backup.exists()
    assert backup.read_bytes().decode("ascii") == UNSAFE_DGVOODOO_CONF
    assert "patched=dgvoodoo-resolution" in first.stdout
    assert "already_patched=dgvoodoo-resolution" in second.stdout
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0
    assert exe.read_bytes() == original_exe
    assert not (game / SHARED_BACKUP).exists()


def test_dgvoodoo_resolution_config_patch_skips_clean_installs_without_wrapper_config(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    result = run_patcher("--apply", "dgvoodoo-resolution", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped=dgvoodoo-resolution reason=missing_config" in result.stdout
    assert not (game / DGVOODOO_CONF).exists()
    assert not (game / f"{DGVOODOO_CONF}{SIDE_CAR_BACKUP}").exists()
    assert exe.read_bytes() == original_exe


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


def test_odawara_fix_hooks_routed_soldier_destinations_without_changing_map_assets_and_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    first = run_patcher("--apply", "odawara", target=game)
    after_first = exe.read_bytes()
    second = run_patcher("--apply", "odawara", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == after_first
    assert_group_state(exe, ODAWARA_PATCHES, patched=True)
    assert_odawara_bdf_unchanged(game)
    assert_no_odawara_bdf_backup(game)
    assert_odawara_map_unchanged(game)
    assert_no_odawara_map_backup(game)
    assert "patched group=odawara patch=OdawaraRoutedSoldierDestinationHook" in first.stdout
    assert "patched group=odawara patch=OdawaraRoutedSoldierDestinationCodeCave" in first.stdout
    assert "patched group=odawara patch=OdawaraGlobalRoutedDestinationHook" in first.stdout
    assert "patched group=odawara patch=OdawaraGlobalRoutedDestinationCodeCave" in first.stdout
    assert "already_patched=odawara" in second.stdout
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0
    assert_only_shared_exe_backup(game, original_exe)


def test_advisor_random_quote_patch_hooks_rng_calls_and_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    first = run_patcher("--apply", "advisor", target=game)
    after_first = exe.read_bytes()
    second = run_patcher("--apply", "advisor", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == after_first
    assert_group_state(exe, ADVISOR_RANDOM_PATCHES, patched=True)
    assert_group_state(exe, ODAWARA_PATCHES, patched=False)
    assert "patched group=advisor patch=AdvisorRandomMilitaryCategoryHook" in first.stdout
    assert "patched group=advisor patch=AdvisorRandomByteCodeCave" in first.stdout
    assert "already_patched=advisor" in second.stdout
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0
    assert_only_shared_exe_backup(game, original_exe)


def test_advisor_selection_applies_required_voice_audio_fix(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)

    result = run_patcher("--apply", "advisor", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(game / "ShogunM.exe", ADVISOR_RANDOM_PATCHES, patched=True)
    assert_group_state(game / "ShogunM.exe", AUDIO_PATCHES, patched=True)


def test_retraining_drag_fix_uses_native_lifecycle_and_is_idempotent(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    first = run_patcher("--apply", "retraining-drag", target=game)
    patched_exe = exe.read_bytes()
    second = run_patcher("--apply", "retraining-drag", target=game)

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert exe.read_bytes() == patched_exe
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert "patched group=retraining-drag patch=RetrainingDragHoverDescriptorFallbackHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragTargetDescriptorFallbackHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragActionDescriptorFallbackHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragDropDescriptorFallbackHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragSourceProvinceGateHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragNoTargetReleaseHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragProvinceTargetHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragProvinceCodeCave" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingDragLifecycleCodeCave" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingCastleQueueInsertionGateHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingCastleLiveDescriptorHook" in first.stdout
    assert "patched group=retraining-drag patch=RetrainingCastleTargetCodeCave" in first.stdout
    assert "already_patched=retraining-drag" in second.stdout
    assert first.stdout.count("backup_created=") == 1
    assert second.stdout.count("backup_created=") == 0
    assert_only_shared_exe_backup(game, original_exe)


def test_retraining_drag_backup_restores_exact_original_bytes(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    original_exe = exe.read_bytes()

    applied = run_patcher("--apply", "retraining-drag", target=game)
    backup = game / SHARED_BACKUP
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert exe.read_bytes() != original_exe
    assert backup.read_bytes() == original_exe

    exe.write_bytes(backup.read_bytes())

    assert exe.read_bytes() == original_exe
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=False)


def test_previous_retraining_guard_candidate_is_detected_and_upgraded_without_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, previous in PREVIOUS_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, previous)
    exe.write_bytes(blob)
    previous_bytes = exe.read_bytes()

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=previous" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_previous=retraining-drag" in upgraded.stdout
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert exe.read_bytes() != previous_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_previous_retraining_guard_upgrade_preserves_existing_shared_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, previous in PREVIOUS_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, previous)
    exe.write_bytes(blob)
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    upgraded = run_patcher("--apply", "retraining-drag", target=game)

    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout


def test_corrected_drag_revision_is_detected_and_upgraded_to_final_preserving_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, corrected_drag in CURRENT_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, corrected_drag)
    exe.write_bytes(blob)
    prior_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=current" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_current=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != prior_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_audio_full_capacity_revision_is_detected_and_upgraded_without_replacing_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, audio_full in AUDIO_FULL_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, audio_full)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=audio-full" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_audio_full=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_audio_full_capacity_revision_upgrade_does_not_create_backup_from_patched_image(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, audio_full in AUDIO_FULL_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, audio_full)
    exe.write_bytes(blob)

    upgraded = run_patcher("--apply", "retraining-drag", target=game)

    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_audio_full=retraining-drag" in upgraded.stdout
    assert "backup_created=" not in upgraded.stdout
    assert not (game / SHARED_BACKUP).exists()
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)


def test_repeat_right_click_revision_is_detected_and_upgraded_without_replacing_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, repeat_rc in REPEAT_RC_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, repeat_rc)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=repeat-rc" in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_repeat_rc=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_marker_free_revision_is_detected_and_upgraded_without_replacing_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, marker_free in MARKER_FREE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, marker_free)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=marker-free" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_marker_free=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_model_state_revision_is_detected_and_upgraded_to_castle_target_final(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, model_state in MODEL_STATE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, model_state)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=model-state" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_model_state=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_model_state_revision_upgrade_does_not_backup_patched_image(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, model_state in MODEL_STATE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, model_state)
    exe.write_bytes(blob)

    upgraded = run_patcher("--apply", "retraining-drag", target=game)

    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_model_state=retraining-drag" in upgraded.stdout
    assert "backup_created=" not in upgraded.stdout
    assert not (game / SHARED_BACKUP).exists()
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)


def test_right_click_sound_revision_is_detected_and_upgraded_to_castle_target_final(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, right_click_sound in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, right_click_sound)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=right-click-sound" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_right_click_sound=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_right_click_sound_revision_upgrade_does_not_backup_patched_image(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, right_click_sound in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, right_click_sound)
    exe.write_bytes(blob)

    upgraded = run_patcher("--apply", "retraining-drag", target=game)

    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_right_click_sound=retraining-drag" in upgraded.stdout
    assert "backup_created=" not in upgraded.stdout
    assert not (game / SHARED_BACKUP).exists()
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)


def test_castle_target_revision_is_detected_and_upgraded_to_direct_target_final(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, castle_target in CASTLE_TARGET_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, castle_target)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=castle-target" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_castle_target=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_direct_target_revision_is_detected_and_upgraded_to_full_army_reject_final(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, direct_target in DIRECT_TARGET_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, direct_target)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=direct-target" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_direct_target=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_full_army_reject_revision_is_detected_and_upgraded_to_native_castle_final(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, full_army_reject in FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, full_army_reject)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=full-army-reject" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_full_army_reject=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_native_castle_revision_is_detected_and_upgraded_to_foreign_army_guard_final(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, native_castle in NATIVE_CASTLE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, native_castle)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=native-castle" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_native_castle=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_full_castle_requeue_revision_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, old_final in FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, old_final)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=full-castle-requeue" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_full_castle_requeue=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_foreign_army_guard_v1_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, candidate in FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, candidate)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=foreign-army-guard-v1" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_foreign_army_guard_v1=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_foreign_army_guard_v2_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, candidate in FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, candidate)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=foreign-army-guard-v2" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_foreign_army_guard_v2=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_queue_position_revision_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, candidate in QUEUE_POSITION_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, candidate)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=queue-position" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_queue_position=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_mixed_foreign_army_guard_v1_and_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, candidate in FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, candidate)
    final_direct = bytes.fromhex(RETRAINING_DRAG_PATCHES[20][2])
    candidate_direct = bytes.fromhex(FOREIGN_ARMY_GUARD_V1_RETRAINING_DRAG_PATCHES[20][2])
    assert final_direct != candidate_direct
    blob[RETRAINING_DRAG_PATCHES[20][0] + 0x253] = final_direct[0x253]
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_foreign_army_guard_v2_and_queue_position_final_fails_closed(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, candidate in FOREIGN_ARMY_GUARD_V2_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, candidate)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[21][0], RETRAINING_DRAG_PATCHES[21][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_full_castle_requeue_and_foreign_army_guard_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, old_final in FULL_CASTLE_REQUEUE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, old_final)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[14][0], RETRAINING_DRAG_PATCHES[14][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_native_castle_and_full_castle_requeue_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, native_castle in NATIVE_CASTLE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, native_castle)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[14][0], RETRAINING_DRAG_PATCHES[14][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_full_army_reject_and_native_castle_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, old_final in FULL_ARMY_REJECT_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, old_final)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[14][0], RETRAINING_DRAG_PATCHES[14][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_direct_target_and_full_army_reject_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, direct_target in DIRECT_TARGET_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, direct_target)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[14][0], RETRAINING_DRAG_PATCHES[14][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_full_army_reject_helper_byte_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    blob[0x006F8D40 + 0xB6] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_castle_deferred_capacity_branch_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    blob[0x006F8CAA + 0x7C] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_full_castle_requeue_entry_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    blob[0x006F8D40 + 0xC9] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_full_castle_requeue_helper_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    blob[0x006F8D40 + 0x220] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_full_castle_popup_helper_byte_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    blob[0x006F8D40 + 0xD2] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_castle_target_and_direct_target_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, castle_target in CASTLE_TARGET_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, castle_target)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[17][0], RETRAINING_DRAG_PATCHES[17][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_model_state_and_right_click_sound_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, model_state in MODEL_STATE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, model_state)
    old_cave = bytes.fromhex(MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE)
    final_cave = bytes.fromhex(RETRAINING_DRAG_EXTENDED_CAVE)
    first_difference = next(
        index for index, (old, final) in enumerate(zip(old_cave, final_cave)) if old != final
    )
    blob[0x006F8B9A + first_difference] = final_cave[first_difference]
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_right_click_sound_helper_byte_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, model_state in MODEL_STATE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, model_state)
    blob[0x006F8B9A + 0xA0] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "unsupported" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_marker_free_and_right_click_sound_final_revision_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, marker_free in MARKER_FREE_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, marker_free)
    final_cave = bytes.fromhex(RETRAINING_DRAG_PROVINCE_CAVE)
    marker_free_cave = bytes.fromhex(MARKER_FREE_RETRAINING_DRAG_PROVINCE_CAVE)
    first_difference = next(
        index
        for index, (old, final) in enumerate(zip(marker_free_cave, final_cave))
        if old != final
    )
    blob[0x0031AD11 + first_difference] = final_cave[first_difference]
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_audio_full_and_new_final_retraining_state_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, audio_full in AUDIO_FULL_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, audio_full)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[11][0], RETRAINING_DRAG_PATCHES[11][2])
    # Keep one byte from the superseded cave so this is neither exact revision.
    old_cave = bytes.fromhex(AUDIO_FULL_RETRAINING_DRAG_EXTENDED_CAVE)
    first_difference = next(
        index
        for index, (old, final) in enumerate(zip(old_cave, bytes.fromhex(RETRAINING_DRAG_EXTENDED_CAVE)))
        if old != final
    )
    blob[0x006F8B9A + first_difference] = old_cave[first_difference]
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_right_click_sound_and_castle_target_final_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, right_click_sound in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, right_click_sound)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[12][0], RETRAINING_DRAG_PATCHES[12][2])
    exe.write_bytes(blob)
    mixed = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mixed
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_castle_target_hook_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    blob[0x001635EC + 2] ^= 0x01
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "unsupported" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_castle_target_cave_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, right_click_sound in RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, right_click_sound)
    blob[0x006F8CAA + 0x55] = 0xCC
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "unsupported" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_corrected_drag_and_final_revision_fails_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, corrected_drag in CURRENT_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, corrected_drag)
    external_marker_offset, _external_marker_original, _external_marker_final = RETRAINING_DRAG_PATCHES[16]
    write_bytes(blob, external_marker_offset, "52")
    exe.write_bytes(blob)
    mixed_bytes = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == mixed_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_mixed_previous_and_final_retraining_states_fail_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, previous in PREVIOUS_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, previous)
    write_bytes(blob, RETRAINING_DRAG_PATCHES[4][0], RETRAINING_DRAG_PATCHES[4][2])
    exe.write_bytes(blob)
    mixed_bytes = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == mixed_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_retraining_drag_partial_state_fails_without_mutation_or_backup(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    write_bytes(blob, RETRAINING_DRAG_PATCHES[0][0], RETRAINING_DRAG_PATCHES[0][2])
    exe.write_bytes(blob)
    partial_bytes = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == partial_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_retraining_drag_unsupported_bytes_fail_closed(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    write_bytes(blob, RETRAINING_DRAG_PATCHES[0][0], "9090909090")
    exe.write_bytes(blob)
    unsupported_bytes = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert "unsupported" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == unsupported_bytes
    assert not (game / SHARED_BACKUP).exists()


def test_retraining_drag_hook_and_code_cave_targets_are_instruction_exact() -> None:
    image_base = 0x00400000
    expected_hooks = (
        (0, "8B168B5224", 0x0071AF60),
        (1, "8B138B5224", 0x0071AF71),
        (2, "8B018B4024", 0x0071AF82),
        (3, "0F8423010000", 0x0071AF93),
        (4, "8B357C03C700", 0x0071AFBB),
        (5, "A1B803C700", 0x0071AFE4),
        (6, "8B882C82DE0085C9", 0x0071AD36),
    )

    for hook_index, displaced, cave_va in expected_hooks:
        hook_offset, original, patched = RETRAINING_DRAG_PATCHES[hook_index]
        hook_va = image_base + hook_offset
        hook_rel = struct.unpack("<i", bytes.fromhex(patched)[1:5])[0]

        assert original == displaced
        assert hook_va + 5 + hook_rel == cave_va

    province_cave_offset, province_cave_original, province_cave = RETRAINING_DRAG_PATCHES[7]
    assert image_base + province_cave_offset == 0x0071AD11
    assert province_cave_original == "00" * 0x6F
    assert len(bytes.fromhex(province_cave)) == 0x6F

    cave_offset, cave_original, cave = RETRAINING_DRAG_PATCHES[8]
    assert image_base + cave_offset == 0x0071AF60
    assert cave_original == "00" * 0xA0
    assert len(bytes.fromhex(cave)) == 0xA0

    cave_bytes = bytes.fromhex(cave)
    resume_sites = (
        (0x0C, 0x0071AF60 + 0x11, 0x005041BB),
        (0x1D, 0x0071AF60 + 0x22, 0x005096DC),
        (0x2E, 0x0071AF60 + 0x33, 0x00547AA0),
        (0x38, 0x0071AF60 + 0x3D, 0x00547881),
        (0x75, 0x0071AF60 + 0x7A, 0x005478D8),
        (0x7F, 0x0071AF60 + 0x84, 0x005479A6),
        (0x96, 0x0071AF60 + 0x9B, 0x005637C4),
    )
    for displacement_offset, next_va, target_va in resume_sites:
        assert cave_bytes[displacement_offset] == 0xE9
        rel = struct.unpack("<i", cave_bytes[displacement_offset + 1 : displacement_offset + 5])[0]
        assert next_va + rel == target_va

    primary_relative_fields = (
        (0x64, 0x0071AF60 + 0x68, 0x0071AF9D),
        (0x7B, 0x0071AF60 + 0x7F, 0x0071AD11),
        (0x85, 0x0071AF60 + 0x89, 0x0071AF9D),
        (0x8D, 0x0071AF60 + 0x91, 0x005637C4),
        (0x92, 0x0071AF60 + 0x96, 0x0071AD11),
    )
    for displacement_offset, next_va, target_va in primary_relative_fields:
        rel = struct.unpack("<i", cave_bytes[displacement_offset : displacement_offset + 4])[0]
        assert next_va + rel == target_va

    province_cave_bytes = bytes.fromhex(province_cave)
    province_relative_fields = (
        (0x20, 0x0071AD11 + 0x24, 0x0052B870),
        (0x45, 0x0071AD11 + 0x49, 0x00F59BD0),
        (0x4D, 0x0071AD11 + 0x51, 0x0053317A),
        (0x52, 0x0071AD11 + 0x56, 0x005331FF),
        (0x59, 0x0071AD11 + 0x5D, 0x0071AD11),
        (0x5E, 0x0071AD11 + 0x62, 0x00F59C90),
    )
    for displacement_offset, next_va, target_va in province_relative_fields:
        rel = struct.unpack("<i", province_cave_bytes[displacement_offset : displacement_offset + 4])[0]
        assert next_va + rel == target_va


def test_target_taxonomy_v8_queue_gate_remains_an_exact_migration_contract() -> None:
    image_base = 0x00400000
    queue_hook_offset, queue_hook_original, queue_hook = (
        TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[12]
    )
    descriptor_hook_offset, descriptor_hook_original, descriptor_hook = (
        TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[13]
    )
    cave_offset, cave_original, cave_hex = TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[14]
    cave = bytes.fromhex(cave_hex)
    cave_base = 0x00F59CAA  # .rdata raw 0x006F8CAA maps to RVA 0x00B59CAA

    assert queue_hook_offset == 0x001635EC
    assert queue_hook_original == "E87F82FCFF"  # complete original call 0x0052B870
    assert queue_hook == RETRAINING_CASTLE_QUEUE_GATE_HOOK
    assert bytes.fromhex(queue_hook)[0] == 0xE8
    queue_rel = struct.unpack("<i", bytes.fromhex(queue_hook)[1:5])[0]
    assert image_base + queue_hook_offset + 5 + queue_rel == 0x00F59CAA

    assert descriptor_hook_offset == 0x00108C5A
    assert descriptor_hook_original == "8BB82C82DE0085FF0F8426050000"
    assert descriptor_hook == RETRAINING_CASTLE_LIVE_DESCRIPTOR_HOOK
    assert bytes.fromhex(descriptor_hook)[0] == 0xE9
    descriptor_rel = struct.unpack("<i", bytes.fromhex(descriptor_hook)[1:5])[0]
    assert image_base + descriptor_hook_offset + 5 + descriptor_rel == 0x00F59D00
    assert bytes.fromhex(descriptor_hook)[5:] == b"\x90" * 9

    assert cave_offset == 0x006F8CAA
    assert cave_original == "00" * 0x96
    assert len(cave) == 0x96
    stock_gate = bytes.fromhex(RETRAINING_CASTLE_QUEUE_GATE_CAVE)
    assert cave[:0x1E] == stock_gate[:0x1E]
    proxy_rel = struct.unpack("<b", cave[0x1F:0x20])[0]
    assert cave_base + 0x20 + proxy_rel == 0x00F59C6C
    assert cave[0x20:0x26] == bytes.fromhex(RETRAINING_FOREIGN_ARMY_QUEUE_GATE_JUMP)
    assert cave[0x26:0x51] == stock_gate[0x26:]
    assert cave[0x51:0x56] == bytes.fromhex(RETRAINING_FULL_ARMY_REJECT_SOUND_STUB)
    assert cave[0x56:0x7C] == bytes.fromhex(RETRAINING_CASTLE_LIVE_DESCRIPTOR_CAVE)
    assert cave[0x7C:0x7E] == bytes.fromhex("EBA8")
    assert cave[0x7E:0x8D] == bytes.fromhex(RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE)
    assert cave[0x8D:] == b"\x00" * 0x09

    # A castle target reaches active-retraining validation without guessing
    # capacity from its slot count. The native insertion result is authoritative
    # for both the 16-slot and total-unit-size limits.
    gate = cave[:0x51]
    castle_test = gate.index(bytes.fromhex("8138A0CFF000"))
    assert gate[castle_test + 6 : castle_test + 8] == bytes.fromhex("7464")
    castle_helper_target = cave_base + castle_test + 8 + struct.unpack(
        "<b", gate[castle_test + 7 : castle_test + 8]
    )[0]
    assert castle_helper_target == 0x00F59D26
    assert bytes.fromhex("8138E0C7F000") in gate
    army_gate = gate[0x20:0x26]
    assert army_gate[0] == 0xE9
    army_gate_rel = struct.unpack("<i", army_gate[1:5])[0]
    assert cave_base + 0x25 + army_gate_rel == 0x00F59F93
    assert army_gate[5] == 0x90
    assert bytes.fromhex("837860107D2B") not in gate
    assert bytes.fromhex("8B922882DE00") in gate
    assert bytes.fromhex("837A4404") in gate
    assert gate.count(bytes.fromhex("C21400")) == 1
    assert gate[-5] == 0xE9
    native_rel = struct.unpack("<i", gate[-4:])[0]
    assert cave_base + len(gate) + native_rel == 0x0052B870

    full_army_stub = cave[0x51:0x56]
    assert full_army_stub[0] == 0xE9
    full_army_rel = struct.unpack("<i", full_army_stub[1:5])[0]
    assert cave_base + 0x56 + full_army_rel == 0x00F59DF6

    deferred_capacity = cave[0x7C:0x7E]
    assert deferred_capacity == bytes.fromhex("EBA8")
    deferred_target = 0x00F59D26 + 2 + struct.unpack("<b", deferred_capacity[1:2])[0]
    assert deferred_target == 0x00F59CD0
    capacity_commit = cave[0x7E:0x8D]
    assert capacity_commit == bytes.fromhex(RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE)
    assert bytes.fromhex(RETRAINING_CASTLE_CAPACITY_GATE_HELPER) == bytes.fromhex(
        NATIVE_CASTLE_RETRAINING_DRAG_PATCHES[14][2]
    )[0x7C:0x8B]

    # With no synthetic card, only an active retraining model may substitute
    # the live held descriptor.  The handler then resumes at its unchanged
    # target/source-province comparison; null/non-retraining cases retain the
    # stock null-descriptor continuation.
    fallback = cave[0x56:0x7C]
    assert fallback.startswith(bytes.fromhex("8BB82C82DE0085FF7512"))
    assert bytes.fromhex("8BB82882DE0085FF740D837F4404750789EF") in fallback
    assert fallback[0x1C] == 0xE9
    resume_rel = struct.unpack("<i", fallback[0x1D:0x21])[0]
    assert 0x00F59D00 + 0x21 + resume_rel == 0x00508C68
    assert fallback[0x21] == 0xE9
    null_rel = struct.unpack("<i", fallback[0x22:0x26])[0]
    assert 0x00F59D00 + 0x26 + null_rel == 0x0050918E

    # This gate only controls queue ownership. Native army/castle handlers own
    # placement and post-commit sound; invalid classes retain native behavior.
    assert bytes.fromhex("6A02") not in cave
    assert bytes.fromhex("6A07") not in cave
    assert RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES[12][2] == queue_hook_original
    assert RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES[13][2] == descriptor_hook_original
    assert RIGHT_CLICK_SOUND_RETRAINING_DRAG_PATCHES[14][2] == cave_original


def test_retraining_drag_lifecycle_caves_use_native_castle_and_queue_paths() -> None:
    assert RETRAINING_DRAG_HOVER_DESCRIPTOR_CAVE.startswith("85F60F44742410")
    assert RETRAINING_DRAG_TARGET_DESCRIPTOR_CAVE.startswith("85DB0F445C2414")
    assert RETRAINING_DRAG_ACTION_DESCRIPTOR_CAVE.startswith("85C90F444C2408")
    assert RETRAINING_DRAG_DROP_DESCRIPTOR_CAVE.startswith("0F445C2440")
    assert "8B802882DE00" in RETRAINING_DRAG_SOURCE_PROVINCE_CHECK_CAVE
    assert "3A5025" in RETRAINING_DRAG_SOURCE_PROVINCE_CHECK_CAVE
    assert "E832FDFFFF" in RETRAINING_DRAG_ARMY_DROP_CAVE
    assert RETRAINING_DRAG_NO_TARGET_CAVE.endswith("E9C987E4FF")
    assert RETRAINING_DRAG_REQUEUE_HELPER_CAVE.startswith("0FB64025A38005C7006A01")
    assert RETRAINING_DRAG_REQUEUE_HELPER_CAVE.endswith("E83B0BE1FFC3")
    assert RETRAINING_DRAG_PROVINCE_DROP_CAVE.startswith("8B882C82DE008B802882DE0085C07414")
    assert "83784404" in RETRAINING_DRAG_PROVINCE_DROP_CAVE
    assert "0FB650253B5358" in RETRAINING_DRAG_PROVINCE_DROP_CAVE
    assert "7512E976EE830085C90F851884E1FFE99884E1FF" in RETRAINING_DRAG_PROVINCE_DROP_CAVE
    assert "E8A3FFFFFF" in RETRAINING_DRAG_PROVINCE_DROP_CAVE
    assert RETRAINING_DRAG_PROVINCE_DROP_CAVE.index("83784404") < RETRAINING_DRAG_PROVINCE_DROP_CAVE.index("85C90F85")


def test_target_taxonomy_v8_withdrawal_cave_remains_an_exact_migration_contract() -> None:
    v8_extended = TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[11][2]
    cave = bytes.fromhex(v8_extended)
    base = 0x00F59B9A

    assert RETRAINING_DRAG_RIGHT_CLICK_HOOK == "E9C00EA5009090"
    assert RETRAINING_DRAG_SUCCESS_SOUND_HOOK == "E98F6AA20090909090"
    assert len(cave) == 0x110
    assert v8_extended.count("6A02") == 2
    assert v8_extended.count("6A07") == 1
    assert "C7404400000000" in RETRAINING_DIRECT_TARGET_CAVE  # committed field fallback
    assert RETRAINING_DRAG_EXTENDED_CAVE.count("535494") == 0  # no embedded absolute call target bytes
    assert "E8D1B85DFF" in RETRAINING_DRAG_EXTENDED_CAVE  # right-click sub_535494 refresh
    assert "E877B85DFF" in RETRAINING_DRAG_EXTENDED_CAVE  # accepted-drag sub_535494 refresh
    assert "E82DB85DFF" in RETRAINING_DRAG_EXTENDED_CAVE  # ordinary displaced sub_535494 call

    # The shared stock hook now discriminates right-click/panel release from an
    # exact castle target before either path changes placement state.
    assert cave[0] == 0xE9
    right_click_rel = struct.unpack("<i", cave[1:5])[0]
    assert base + 5 + right_click_rel == 0x00F59D40

    call_sites = (
        (0x24, 0x00535494),
        (0x29, 0x00F59C3A),
        (0x70, 0x005352A4),
        (0x7E, 0x00535494),
        (0x86, 0x0055C230),
        (0xA2, 0x0055C230),
        (0xC8, 0x00535494),
        (0xF8, 0x0055C230),
    )
    for call_offset, target in call_sites:
        assert cave[call_offset] == 0xE8
        rel = struct.unpack("<i", cave[call_offset + 1 : call_offset + 5])[0]
        assert base + call_offset + 5 + rel == target

    # The retired in-place right-click body remains unreachable so all existing
    # helper offsets stay stable for the province-drag and invalid-drop paths.
    assert bytes.fromhex("84C07564") not in cave
    assert cave[0x29:0x36] == bytes.fromhex(RETRAINING_RIGHT_CLICK_SUCCESS_TAIL)
    assert cave[0xA0:0xAB] == bytes.fromhex(RETRAINING_RIGHT_CLICK_SOUND_HELPER)
    right_click_continuation = struct.unpack("<i", cave[0x30:0x34])[0]
    assert base + 0x34 + right_click_continuation == 0x00508F09
    assert cave[0xAB:0xB8] == bytes.fromhex(RETRAINING_UNIT_PROXY_TERMINAL_HELPER)
    assert cave[0xB8:0xC6] == b"\x00" * 0x0E

    # Accepted retraining drops run an operation-local copy of the native
    # lifecycle and emit event 2 directly. Successful right-clicks reach the
    # sound-only helper after refresh. The displaced ordinary path is a
    # sound-neutral wrapper; the invalid path emits event 7 exactly once.
    assert cave[0x36:0x43] == bytes.fromhex("0FB76D28C1E5048BAD2882DE00")
    assert cave[0x7C:0x8B] == bytes.fromhex("89D9E877B85DFF506A02E80B2660FF")
    assert cave[0xC6:0xD2] == bytes.fromhex("89D9E82DB85DFFE993955DFF")
    assert cave[0xD2:0xF2] == bytes.fromhex(RETRAINING_UNIT_PROXY_CLASSIFIER)
    assert cave[0xF2:0xF6] == b"\x00" * 4
    assert cave[0xF6:0x105] == bytes.fromhex("6A07E8992560FF83C404E960955DFF")
    assert bytes.fromhex(RETRAINING_RIGHT_CLICK_SOUND_HELPER) not in bytes.fromhex(
        MODEL_STATE_RETRAINING_DRAG_EXTENDED_CAVE
    )
    assert RETRAINING_DRAG_PATCHES[15] == (0x00000264, "60000040", "60000060")
    assert RETRAINING_DRAG_PATCHES[16] == (0x006F9000, "00", "00")


def test_retraining_sound_paths_gate_success_failure_and_ordinary_cancellation() -> None:
    cave = bytes.fromhex(RETRAINING_DRAG_EXTENDED_CAVE)
    province_cave = bytes.fromhex(RETRAINING_DRAG_PROVINCE_CAVE)
    cave_base = 0x00F59B9A
    province_base = 0x0071AD11

    # Source-province drag retains exactly one direct event-2 dispatch.
    assert cave[0x84:0x86] == bytes.fromhex("6A02")
    assert cave[0x86] == 0xE8
    assert cave_base + 0x8B + struct.unpack("<i", cave[0x87:0x8B])[0] == 0x0055C230

    # Different-province rollback jumps directly to event 7, bypassing both
    # the accepted-drag path and the right-click-only sound helper.
    assert province_cave[0x5D] == 0xE9
    invalid_target = province_base + 0x62 + struct.unpack(
        "<i", province_cave[0x5E:0x62]
    )[0]
    assert invalid_target == 0x00F59C90
    assert cave[0xF6:0xF8] == bytes.fromhex("6A07")

    # Ordinary type-7 cancellation retains its displaced refresh and jumps to
    # native cleanup without either injected event-2 sequence.
    assert cave[0xC6:0xD2] == bytes.fromhex("89D9E82DB85DFFE993955DFF")
    assert bytes.fromhex("6A02") not in cave[0xC6:0xF6]


def test_target_taxonomy_v8_direct_cave_remains_an_exact_migration_contract() -> None:
    image_base = 0x00400000
    direct_base = 0x00F59D40
    expected_hooks = (
        (17, "8BB82C82DE0085FF", 0x00F59DBB),
        (18, "E9DD010000", 0x00F59DE5),
        (19, "8B9424A4000000", 0x00F59D9B),
    )
    for index, displaced, target in expected_hooks:
        offset, original, patched = RETRAINING_DRAG_PATCHES[index]
        payload = bytes.fromhex(patched)
        assert original == displaced
        assert payload[0] == 0xE9
        rel = struct.unpack("<i", payload[1:5])[0]
        assert image_base + offset + 5 + rel == target
        assert payload[5:] == b"\x90" * (len(bytes.fromhex(original)) - 5)

    cave_offset, cave_original, cave_hex = TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[20]
    cave = bytes.fromhex(cave_hex)
    assert cave_offset == 0x006F8D40
    assert cave_original == "00" * 0x2C0
    assert len(cave) == 0x2C0
    assert cave[0xB6:0xC4] == bytes.fromhex(RETRAINING_FULL_ARMY_REJECT_SOUND_HELPER)[:0x0E]
    reject_queue_rel = struct.unpack("<i", cave[0xC5:0xC9])[0]
    assert direct_base + 0xC9 + reject_queue_rel == 0x00F59B12
    assert cave[0xC9:0xD2] == bytes.fromhex(RETRAINING_FULL_CASTLE_REQUEUE_ENTRY)
    assert cave[0xD2:0x21D] == bytes.fromhex(RETRAINING_FULL_CASTLE_POPUP_HELPER)[9:]
    assert cave[0x21D:0x220] == b"\x00" * 3
    assert cave[0x220:0x253] == bytes.fromhex(RETRAINING_FULL_CASTLE_REQUEUE_HELPER)
    assert cave[0x253:0x294] == bytes.fromhex(RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER)
    assert cave[0x294:] == bytes.fromhex(RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD)

    # Right-click/panel release takes the existing committed field-withdrawal
    # lifecycle; exact castle release replays the displaced native setup.
    assert cave[:0x1A] == bytes.fromhex(
        "50A18C7BC90085C0740F8B403485C074088138A0CFF000743558"
    )
    assert cave[0x4E:0x5B] == bytes.fromhex("588B56640FB74528E941EF5AFF")
    castle_resume = struct.unpack("<i", cave[0x57:0x5B])[0]
    assert direct_base + 0x5B + castle_resume == 0x00508CDC

    # Native castle insertion returns success in EAX. Nonzero success emits the
    # same native event 5 used by an ordinary army-to-castle transfer. Zero
    # enters queue restoration before the stock-equivalent modal; it cannot
    # reach the right-click/source-terrain outside-field fallback.
    assert cave[0x5B:0x5F] == bytes.fromhex("85C0746A")
    castle_failure_target = direct_base + 0x5F + struct.unpack("<b", cave[0x5E:0x5F])[0]
    assert castle_failure_target == 0x00F59E09
    assert cave[0x60:0x62] == bytes.fromhex("6A05")
    assert cave[0x62] == 0xE8
    castle_sound_rel = struct.unpack("<i", cave[0x63:0x67])[0]
    assert direct_base + 0x67 + castle_sound_rel == 0x0055C230
    assert cave[0x77:0x7B] == bytes.fromhex("89F8EB9F")

    # Initial entries use the live held descriptor only when the registry model
    # is still state 4; later entries retain the registry descriptor. Both join
    # the exact army through the unchanged native handler.
    assert cave[0x7B:0x83] == bytes.fromhex("8BB82C82DE0085FF")
    assert bytes.fromhex("8BB82882DE0085FF7411837F4404750B89DF") in cave[0x83:0x9B]
    descriptor_resume = struct.unpack("<i", cave[0x9C:0xA0])[0]
    assert direct_base + 0xA0 + descriptor_resume == 0x00F59FD4
    descriptor_fail = struct.unpack("<i", cave[0xA1:0xA5])[0]
    assert direct_base + 0xA5 + descriptor_fail == 0x00501F66

    # The direct-army sound hook replaces the native epilogue jump only after
    # the target vfunc returned, so full/requeued paths never reach event 2.
    assert cave[0xA5:0xA8] == bytes.fromhex("506A02")
    assert cave[0xA8] == 0xE8
    army_sound_rel = struct.unpack("<i", cave[0xA9:0xAD])[0]
    assert direct_base + 0xAD + army_sound_rel == 0x0055C230
    army_resume = struct.unpack("<i", cave[0xB2:0xB6])[0]
    assert direct_base + 0xB6 + army_resume == 0x00501F66

    # Exact full-army capacity rejection emits native event 7 once and then
    # enters the position-preserving native insertion helper. It cannot reach
    # either post-commit event-2 site.
    reject_base = direct_base + 0xB6
    reject = cave[0xB6:0xC9]
    assert reject[:4] == bytes.fromhex("9C606A07")  # preserve flags and all GPRs
    assert reject[4] == 0xE8
    reject_sound_rel = struct.unpack("<i", reject[5:9])[0]
    assert reject_base + 9 + reject_sound_rel == 0x0055C230
    assert reject[9:14] == bytes.fromhex("83C404619D")
    assert reject[14] == 0xE9
    reject_requeue_rel = struct.unpack("<i", reject[15:19])[0]
    assert reject_base + 19 + reject_requeue_rel == 0x00F59B12
    assert bytes.fromhex("6A02") not in reject

    # The shared fallback remains unchanged for right-click and source-terrain
    # capacity fallback. A direct castle failure no longer reaches it.
    assert cave[0x3E] == 0xE8
    refresh_rel = struct.unpack("<i", cave[0x3F:0x43])[0]
    assert direct_base + 0x43 + refresh_rel == 0x00535494
    assert cave[0x43] == 0xE8
    helper_rel = struct.unpack("<i", cave[0x44:0x48])[0]
    assert direct_base + 0x48 + helper_rel == 0x00F59C3A

    # The old popup entry is now a complete-instruction near jump into the
    # requeue transaction. It cannot fall through to an overwritten CALL tail.
    popup_base = direct_base + 0xC9
    entry = cave[0xC9:0xD2]
    assert entry[0] == 0xE9
    entry_rel = struct.unpack("<i", entry[1:5])[0]
    assert popup_base + 5 + entry_rel == 0x00F59F60
    assert entry[5:] == b"\x90" * 4

    # The failure helper preserves the original handler context, calls the
    # same native five-argument queue insertion used by working rejection
    # paths, restores that context, then recreates the popup save frame and
    # dispatches event 5. Restoration precedes every sound and modal call.
    requeue_base = direct_base + 0x220
    requeue = cave[0x220:0x253]
    assert requeue == bytes.fromhex(RETRAINING_FULL_CASTLE_REQUEUE_HELPER)
    assert requeue.startswith(bytes.fromhex("9C608BB424F4000000"))
    assert bytes.fromhex("8B0DB803C7006A00FF358005C700FF762CFF762856") in requeue
    queue_call = requeue.index(bytes.fromhex("E8ED185DFF"))
    queue_rel = struct.unpack("<i", requeue[queue_call + 1 : queue_call + 5])[0]
    assert requeue_base + queue_call + 5 + queue_rel == 0x0052B870
    assert requeue[queue_call + 5 : queue_call + 11] == bytes.fromhex("619D9C606A05")
    sound_call = requeue.index(bytes.fromhex("E8A22260FF"))
    sound_rel = struct.unpack("<i", requeue[sound_call + 1 : sound_call + 5])[0]
    assert requeue_base + sound_call + 5 + sound_rel == 0x0055C230
    assert queue_call < sound_call
    requeue_resume = struct.unpack("<i", requeue[-4:])[0]
    assert requeue_base + len(requeue) + requeue_resume == 0x00F59E12

    # The remaining in-place helper reproduces event 35, localization, modal,
    # exact temporary-object cleanup, then the consumed castle epilogue.
    popup = cave[0xD2:0x21D]
    popup_body_base = direct_base + 0xD2
    popup_original = bytes.fromhex(RETRAINING_FULL_CASTLE_POPUP_HELPER)
    assert popup == popup_original[9:]
    assert popup.startswith(bytes.fromhex("83C4046A23"))
    assert bytes.fromhex("6A02") not in popup + requeue
    assert bytes.fromhex("6A07") not in popup + requeue
    popup_calls = (
        (0x05, 0x0055C230),
        (0x1C, 0x006B0120),
        (0x74, 0x006B0120),
        (0xE8, 0x00551760),
    )
    for call_offset, target in popup_calls:
        assert popup[call_offset] == 0xE8
        rel = struct.unpack("<i", popup[call_offset + 1 : call_offset + 5])[0]
        assert popup_body_base + call_offset + 5 + rel == target
    assert bytes.fromhex("68A0CAF000") in popup  # Add Unit_ct_xzy
    assert bytes.fromhex("68C0CAF000") in popup  # No room_ct_xzy
    assert bytes.fromhex("C7442408FFFFFFFF31C08844240C89442410") in popup
    assert popup[-5] == 0xE9
    popup_resume_rel = struct.unpack("<i", popup[-4:])[0]
    assert popup_body_base + len(popup) + popup_resume_rel == 0x00508F09

    # Exactly one direct-castle event 5 is reachable per branch: the committed
    # success site or the native full-castle popup helper, never both.
    assert cave.count(bytes.fromhex("6A05")) == 2
    assert cave.count(bytes.fromhex("6A23")) == 1


def test_target_taxonomy_v8_proxy_rejection_remains_an_exact_migration_contract() -> None:
    extended = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[11][2])
    castle = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[14][2])
    direct = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[20][2])
    extended_base = 0x00F59B9A
    castle_base = 0x00F59CAA
    direct_base = 0x00F59D40

    # Unit/banner targets expose vtable 0x00F120E0 and embed the authoritative
    # army object at +0x70. The preliminary gate normalizes only that verified
    # shape before entering the existing model-first classifier.
    proxy_classifier = extended[0xD2:0xF2]
    assert proxy_classifier == bytes.fromhex(
        "8138E020F1000F857E00000083C0708138E0C7F0000F856F000000E907030000"
    )
    assert proxy_classifier.startswith(bytes.fromhex("8138E020F100"))
    assert bytes.fromhex("83C0708138E0C7F000") in proxy_classifier
    classifier_jump = struct.unpack("<i", proxy_classifier[-4:])[0]
    assert extended_base + 0xF2 + classifier_jump == 0x00F59F93

    proxy_branch = castle[0x1E:0x20]
    assert proxy_branch[0] == 0x75
    assert castle_base + 0x20 + struct.unpack("<b", proxy_branch[1:])[0] == 0x00F59C6C

    # Active retraining province mismatch and full-capacity rejection share a
    # terminal helper. It restores EBP, rewrites the preliminary call's return
    # to the dispatcher's normal cleanup, and enters the existing event-7 path.
    terminal_helper = extended[0xAB:0xB8]
    assert terminal_helper == bytes.fromhex("5DC70424D0345600E9A4010000")
    assert struct.unpack("<I", terminal_helper[4:8])[0] == 0x005634D0
    event7_rel = struct.unpack("<i", terminal_helper[9:13])[0]
    assert extended_base + 0xB8 + event7_rel == 0x00F59DF6

    province_reject = direct[0x27C:0x27E]
    assert province_reject == bytes.fromhex("7510")
    assert direct_base + 0x27E + struct.unpack("<b", province_reject[1:])[0] == 0x00F59FCE

    generic_reject = direct[0x288:0x28E]
    assert generic_reject[0] == 0x5D
    assert generic_reject[1] == 0xE9
    generic_rel = struct.unpack("<i", generic_reject[2:6])[0]
    assert direct_base + 0x28E + generic_rel == 0x00F59CF6

    terminal_reject = direct[0x28E:0x294]
    assert terminal_reject == bytes.fromhex("E972FCFFFF90")
    terminal_rel = struct.unpack("<i", terminal_reject[1:5])[0]
    assert direct_base + 0x293 + terminal_rel == 0x00F59C45

    # Event 7 remains native and exactly once. Its tail now enters the queue
    # position helper, so no second stock pass can insert or reorder the card.
    event7_helper = direct[0xB6:0xC9]
    assert event7_helper.count(bytes.fromhex("6A07")) == 1
    assert event7_helper[-5] == 0xE9
    queue_rel = struct.unpack("<i", event7_helper[-4:])[0]
    assert direct_base + 0xC9 + queue_rel == 0x00F59B12
    assert bytes.fromhex("6A02") not in terminal_helper + event7_helper
    assert bytes.fromhex("6A05") not in terminal_helper + event7_helper
    assert bytes.fromhex("6A23") not in terminal_helper + event7_helper


def test_hover_and_release_share_one_pure_payload_target_policy() -> None:
    extended = bytes.fromhex(RETRAINING_DRAG_PATCHES[11][2])
    castle = bytes.fromhex(RETRAINING_DRAG_PATCHES[14][2])
    direct = bytes.fromhex(RETRAINING_DRAG_PATCHES[20][2])
    hover_hook = bytes.fromhex(RETRAINING_DRAG_PATCHES[24][2])
    shared = bytes.fromhex(RETRAINING_DRAG_PATCHES[25][2])
    old_extended = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[11][2])
    old_final_direct = bytes.fromhex(
        TARGET_TAXONOMY_FINAL_RETRAINING_DRAG_PATCHES[20][2]
    )

    # The normal descriptor load remains inline. Only its null case enters the
    # relocated model-state fallback, leaving ordinary queue entries unchanged.
    assert RETRAINING_DRAG_PATCHES[13][2] == TARGET_TAXONOMY_LIVE_DESCRIPTOR_HOOK
    assert extended[0xD2:0xF6] == bytes.fromhex(
        TARGET_TAXONOMY_LIVE_DESCRIPTOR_FALLBACK
    )
    assert extended[:0xD2] == old_extended[:0xD2]
    assert extended[0xF6:] == old_extended[0xF6:]

    # The old queue classifier now forwards on a complete five-byte boundary;
    # the ordinary/non-retraining return is a complete JMP to native 0x52B870,
    # never the stale 0xF59CF6 mid-instruction address.
    assert castle == bytes.fromhex(SHARED_RELEASE_CLASSIFIER_FORWARD)
    classifier_rel = struct.unpack("<i", castle[1:5])[0]
    assert 0x00F59CAA + 5 + classifier_rel == 0x00F5AD00
    assert bytes.fromhex("EBC2") not in castle

    # The former duplicated semantic helper has no callers and is fully
    # retired.  The later accepted direct-army commit remains byte-identical.
    assert direct[0x253:0x2C0] == bytes.fromhex(
        RETIRED_TARGET_TAXONOMY_SEMANTIC_HELPER
    )
    assert direct[:0x253] == old_final_direct[:0x253]
    assert direct[0x9B:0xA0] == bytes.fromhex(TARGET_TAXONOMY_DIRECT_COMMIT)

    # The hook covers the complete original hover validator/write sequence and
    # reaches the only per-frame wrapper in the shared cave.
    assert RETRAINING_DRAG_PATCHES[24][0] == 0x0017E872
    assert RETRAINING_DRAG_PATCHES[24][1] == RETRAINING_HOVER_POLICY_ORIGINAL
    assert len(hover_hook) == 0x1C and hover_hook[0] == 0xE9
    hover_hook_rel = struct.unpack("<i", hover_hook[1:5])[0]
    assert 0x0057E872 + 5 + hover_hook_rel == 0x00F5AD60

    assert RETRAINING_DRAG_PATCHES[25][0] == 0x006F9C00
    assert RETRAINING_DRAG_PATCHES[25][1] == "00" * 0x200
    assert len(shared) == 0x200
    policy = shared[:0xF4]
    release = shared[0x100:0x136]
    hover = shared[0x160:0x196]
    assert policy == bytes.fromhex(SHARED_PAYLOAD_TARGET_POLICY)
    assert release == bytes.fromhex(SHARED_RELEASE_POLICY_WRAPPER)
    assert hover == bytes.fromhex(SHARED_HOVER_POLICY_WRAPPER)
    assert shared[0xF4:0x100] == b"\x90" * 0x0C
    assert shared[0x136:0x160] == b"\x90" * 0x2A
    assert shared[0x196:] == b"\x90" * (0x200 - 0x196)

    # One pure policy owns payload type/state, cancellation fallbacks, proxy
    # normalization, province, registry owner, and army capacity. It has no
    # call instruction and therefore cannot mutate queue or gameplay state.
    for required in (
        "83794807",          # descriptor type 7
        "0FB751286642",      # stable id with 0xffff sentinel handling
        "8BAA2882DE00",      # authoritative registry model
        "837D4404",          # active retraining model state
        "8138E020F100",      # unit/banner proxy
        "83C0708138E0C7F000",# canonical field army
        "8138A0CFF000",      # castle
        "8A50253A5525",      # target/source province comparison
        "3A8A2282DE00",      # registry owner comparison
        "83786010",          # field-army slot capacity
        "817A0810615200",    # native inert/cancellation family
    ):
        assert bytes.fromhex(required) in policy
    assert b"\xE8" not in policy
    assert policy.count(bytes.fromhex("B803000000")) == 1
    assert policy.count(bytes.fromhex("31C0")) == 1
    assert policy.count(bytes.fromhex("0FB6C5")) == 1

    # Both wrappers call exactly the same policy entry. Release classification
    # 3 reaches native queue handling, 0 reaches event-7/requeue, and 1/2 use
    # the existing committed transaction. Hover classification 3 invokes the
    # stock virtual validator, while 0/1/2 become the cursor highlight byte.
    release_call = release.index(b"\xE8")
    release_rel = struct.unpack("<i", release[release_call + 1 : release_call + 5])[0]
    assert 0x00F5AD00 + release_call + 5 + release_rel == 0x00F5AC00
    release_invalid = release.index(b"\xE9", release_call + 5)
    invalid_rel = struct.unpack("<i", release[release_invalid + 1 : release_invalid + 5])[0]
    assert 0x00F5AD00 + release_invalid + 5 + invalid_rel == 0x00F59C45
    release_native = release.rindex(b"\xE9")
    native_rel = struct.unpack("<i", release[release_native + 1 : release_native + 5])[0]
    assert 0x00F5AD00 + release_native + 5 + native_rel == 0x0052B870

    hover_call = hover.index(b"\xE8")
    hover_rel = struct.unpack("<i", hover[hover_call + 1 : hover_call + 5])[0]
    assert 0x00F5AD60 + hover_call + 5 + hover_rel == 0x00F5AC00
    assert bytes.fromhex("83F803") in hover
    assert bytes.fromhex("0F95C0") in hover
    assert bytes.fromhex("FFD2") in hover
    hover_resume = hover.rindex(b"\xE9")
    hover_resume_rel = struct.unpack(
        "<i", hover[hover_resume + 1 : hover_resume + 5]
    )[0]
    assert 0x00F5AD60 + hover_resume + 5 + hover_resume_rel == 0x0057E88E

    assert RETRAINING_DRAG_PATCHES[26] == (
        0x0000028C,
        "400000C0",
        "400000E0",
    )

    # The later direct-army hook commits only after the operation-local queue
    # policy has accepted the immutable final target.
    commit_rel = struct.unpack("<i", direct[0x9C:0xA0])[0]
    assert 0x00F59DDB + 5 + commit_rel == 0x00501D1F


def test_target_taxonomy_v8_revision_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, old_final in TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, old_final)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=target-taxonomy-v8" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_target_taxonomy_v8=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_target_taxonomy_final_revision_is_detected_and_upgraded_without_replacing_backup(
    tmp_path: Path,
) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, old_final in TARGET_TAXONOMY_FINAL_RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, old_final)
    exe.write_bytes(blob)
    old_bytes = exe.read_bytes()
    backup = game / SHARED_BACKUP
    sentinel = exe.read_bytes()
    backup.write_bytes(sentinel)

    detected = run_patcher("--verify", target=game)
    upgraded = run_patcher("--apply", "retraining-drag", target=game)
    verified = run_patcher("--verify", target=game)

    assert detected.returncode == 0, detected.stdout + detected.stderr
    assert "retraining-drag=target-taxonomy-final" in detected.stdout
    assert "retraining-drag=patched" not in detected.stdout
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert "upgraded_from_target_taxonomy_final=retraining-drag" in upgraded.stdout
    assert exe.read_bytes() != old_bytes
    assert_group_state(exe, RETRAINING_DRAG_PATCHES, patched=True)
    assert backup.read_bytes() == sentinel
    assert "backup_created=" not in upgraded.stdout
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "retraining-drag=patched" in verified.stdout


def test_target_taxonomy_v8_foreign_army_guard_remains_an_exact_migration_contract() -> None:
    castle = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[14][2])
    direct = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[20][2])
    castle_base = 0x00F59CAA
    direct_base = 0x00F59D40

    # The preliminary army decision moves into a model-first classifier. The
    # province mismatch is tested before capacity, so a full foreign army takes
    # the same single native queue-restoration branch as a room-bearing one.
    queue_gate = castle[0x20:0x26]
    assert queue_gate[0] == 0xE9
    assert castle_base + 0x25 + struct.unpack("<i", queue_gate[1:5])[0] == 0x00F59F93
    assert queue_gate[5] == 0x90

    queue_helper = direct[0x253:0x294]
    assert queue_helper == bytes.fromhex(RETRAINING_FOREIGN_ARMY_QUEUE_GATE_HELPER)
    assert queue_helper.startswith(bytes.fromhex("5589C58B442408"))
    assert bytes.fromhex("89C1") not in queue_helper
    assert queue_helper.index(bytes.fromhex("3A4225")) < queue_helper.index(
        bytes.fromhex("837D6010")
    )
    foreign_branch = queue_helper.index(bytes.fromhex("7510"))
    foreign_target = 0x00F59F93 + foreign_branch + 2 + struct.unpack(
        "<b", queue_helper[foreign_branch + 1 : foreign_branch + 2]
    )[0]
    assert foreign_target == 0x00F59FCE
    assert queue_helper[0x35:0x3B] == bytes.fromhex("5DE928FDFFFF")
    native_queue_rel = struct.unpack("<i", queue_helper[0x37:0x3B])[0]
    assert 0x00F59FC9 + 5 + native_queue_rel == 0x00F59CF6
    assert queue_helper[0x3B:] == bytes.fromhex("E972FCFFFF90")
    terminal_rel = struct.unpack("<i", queue_helper[0x3C:0x40])[0]
    assert direct_base + 0x293 + terminal_rel == 0x00F59C45
    assert queue_helper.count(bytes.fromhex("5D")) == 2

    # After descriptor resolution the committed path independently rechecks
    # the exact army/model provinces. A mismatch reaches stock event 7 at
    # 0x00501DAB; it cannot reach detach 0x005352A0 or the event-2 hook.
    descriptor_guard_jump = direct[0x9B:0xA0]
    assert descriptor_guard_jump[0] == 0xE9
    assert direct_base + 0xA0 + struct.unpack("<i", descriptor_guard_jump[1:])[0] == 0x00F59FD4
    commit_guard = direct[0x294:]
    assert commit_guard == bytes.fromhex(RETRAINING_DIRECT_FOREIGN_ARMY_COMMIT_GUARD)
    assert commit_guard.startswith(bytes.fromhex("817D00E0C7F000"))
    assert bytes.fromhex("8B902882DE00") in commit_guard
    assert bytes.fromhex("8A4D253A4A25") in commit_guard
    province_equal_jump = commit_guard.index(bytes.fromhex("E928FDFFFF"))
    assert 0x00F59FD4 + province_equal_jump + 5 + struct.unpack(
        "<i", commit_guard[province_equal_jump + 1 : province_equal_jump + 5]
    )[0] == 0x00F59D28
    reject_jump = commit_guard.index(bytes.fromhex("0F85B07D5AFF"))
    assert 0x00F59FD4 + reject_jump + 6 + struct.unpack(
        "<i", commit_guard[reject_jump + 2 : reject_jump + 6]
    )[0] == 0x00501DAB

    capacity = castle[0x7E:0x8D]
    assert capacity == bytes.fromhex(RETRAINING_DIRECT_ARMY_CAPACITY_COMMIT_GATE)
    room_rel = struct.unpack("<i", capacity[6:10])[0]
    assert 0x00F59D28 + 10 + room_rel == 0x00501D1F
    full_cleanup_rel = struct.unpack("<i", capacity[11:15])[0]
    assert 0x00F59D32 + 5 + full_cleanup_rel == 0x00501F66

    assert bytes.fromhex("6A02") not in queue_helper + commit_guard + capacity
    assert bytes.fromhex("6A05") not in queue_helper + commit_guard + capacity
    assert bytes.fromhex("6A23") not in queue_helper + commit_guard + capacity
    assert FULL_CASTLE_REQUEUE_RETRAINING_CASTLE_TARGET_CAVE != RETRAINING_CASTLE_TARGET_CAVE
    assert FULL_CASTLE_REQUEUE_RETRAINING_DIRECT_TARGET_CAVE != RETRAINING_DIRECT_TARGET_CAVE


def test_foreign_army_requeue_preserves_exact_removed_queue_position() -> None:
    image_base = 0x00400000
    hook_offset, hook_original, hook_hex = RETRAINING_DRAG_PATCHES[21]
    cave_offset, cave_original, cave_hex = RETRAINING_DRAG_PATCHES[22]
    state_offset, state_original, state_final = RETRAINING_DRAG_PATCHES[23]
    hook = bytes.fromhex(hook_hex)
    cave = bytes.fromhex(cave_hex)
    cave_base = 0x00F59B00

    assert hook_offset == 0x0012AFF2
    assert hook_original == "8B55008B4504"
    assert len(hook) == 6
    assert hook[0] == 0xE8 and hook[-1] == 0x90
    hook_rel = struct.unpack("<i", hook[1:5])[0]
    assert image_base + hook_offset + 5 + hook_rel == cave_base

    assert cave_offset == 0x006F8B00
    assert cave_original == "00" * 0x9A
    assert len(cave) == 0x9A
    capture = cave[:0x12]
    restore = cave[0x12:]
    assert capture == bytes.fromhex("8B55008B45048915F8AFF500A3FCAFF500C3")
    assert capture[:6] == bytes.fromhex(hook_original)

    # Runtime state lives in the verified zero tail of the writable final
    # .data section, never in the RX code cave and never at the known-live
    # 0x00F5A000 legacy marker address.
    assert state_offset == 0x006F9FF8
    assert state_original == state_final == "00" * 8
    assert bytes.fromhex("F8AFF500") in capture
    assert bytes.fromhex("FCAFF500") in capture
    assert bytes.fromhex("929BF500") not in cave
    assert bytes.fromhex("969BF500") not in cave
    assert bytes.fromhex("00A0F500") not in cave

    # The helper duplicates the exact five existing args, invokes the native
    # transaction once, and retains its EAX result and EFLAGS. Because the
    # native return value is not the list node, it finds the unique restored
    # unit id through one circular-list pass before moving only that node.
    assert restore.startswith(bytes.fromhex("FF742414" * 5))
    queue_call = restore.index(b"\xE8")
    queue_rel = struct.unpack("<i", restore[queue_call + 1 : queue_call + 5])[0]
    assert cave_base + 0x12 + queue_call + 5 + queue_rel == 0x0052B870
    assert restore.count(bytes.fromhex("E8")) == 1
    assert restore[queue_call + 5 : queue_call + 7] == bytes.fromhex("9C50")
    assert bytes.fromhex("8B54240C8B52286639510C74088B0939C175F4") in restore
    assert bytes.fromhex("8950048902A1F8AFF5008B15FCAFF5008901895104894804890A") in restore
    assert restore.endswith(bytes.fromhex("31C0A3F8AFF500A3FCAFF500589DC21400"))

    # Active foreign/full rejection reaches event 7 and then this helper. The
    # generic non-retraining fallback remains the untouched native insertion.
    direct = bytes.fromhex(TARGET_TAXONOMY_V8_RETRAINING_DRAG_PATCHES[20][2])
    queue_helper = direct[0x253:0x294]
    generic_rel = struct.unpack("<i", queue_helper[0x37:0x3B])[0]
    assert 0x00F59FC9 + 5 + generic_rel == 0x00F59CF6
    terminal_rel = struct.unpack("<i", queue_helper[0x3C:0x40])[0]
    assert 0x00F59D40 + 0x293 + terminal_rel == 0x00F59C45
    event7_helper = direct[0xB6:0xC9]
    position_rel = struct.unpack("<i", event7_helper[-4:])[0]
    assert 0x00F59E09 + position_rel == cave_base + 0x12


def test_mismatched_foreign_army_guard_byte_fails_without_mutation(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    for offset, _original, final in RETRAINING_DRAG_PATCHES:
        write_bytes(blob, offset, final)
    guard_offset = RETRAINING_DRAG_PATCHES[20][0] + 0x294
    blob[guard_offset + 0x10] ^= 0x01
    exe.write_bytes(blob)
    mismatched = exe.read_bytes()

    result = run_patcher("--apply", "retraining-drag", target=game)

    assert result.returncode != 0
    assert any(word in (result.stdout + result.stderr).lower() for word in ("partial", "unsupported"))
    assert exe.read_bytes() == mismatched
    assert not (game / SHARED_BACKUP).exists()


def test_mismatched_queue_position_or_shared_policy_site_fails_without_mutation(
    tmp_path: Path,
) -> None:
    for case_name, patch_index, relative_offset in (
        ("hook", 21, 1),
        ("cave", 22, 0x54),
        ("runtime-data", 23, 4),
        ("hover-hook", 24, 7),
        ("shared-policy-cave", 25, 0xA4),
        ("data1-section-flags", 26, 3),
    ):
        case_root = tmp_path / case_name
        case_root.mkdir()
        game = make_clean_game(case_root)
        exe = game / "ShogunM.exe"
        blob = bytearray(exe.read_bytes())
        for offset, _original, final in RETRAINING_DRAG_PATCHES:
            write_bytes(blob, offset, final)
        blob[RETRAINING_DRAG_PATCHES[patch_index][0] + relative_offset] ^= 0x01
        exe.write_bytes(blob)
        mismatched = exe.read_bytes()

        result = run_patcher("--apply", "retraining-drag", target=game)

        assert result.returncode != 0
        assert any(
            word in (result.stdout + result.stderr).lower()
            for word in ("partial", "unsupported")
        )
        assert exe.read_bytes() == mismatched
        assert not (game / SHARED_BACKUP).exists()


def test_retraining_success_state_is_patch_owned_and_external_data_byte_is_restored() -> None:
    cave = bytes.fromhex(RETRAINING_DRAG_EXTENDED_CAVE)
    province_cave = bytes.fromhex(RETRAINING_DRAG_PROVINCE_CAVE)
    external_marker_address = bytes.fromhex("00A0F500")

    assert external_marker_address not in cave
    assert external_marker_address not in province_cave
    assert bytes.fromhex("C605") not in cave
    assert bytes.fromhex("C605") not in province_cave
    assert RETRAINING_DRAG_PATCHES[16] == (0x006F9000, "00", "00")
    assert AUDIO_FULL_RETRAINING_DRAG_PATCHES[16] == (0x006F9000, "00", "52")
    assert REPEAT_RC_RETRAINING_DRAG_PATCHES[16] == (0x006F9000, "00", "52")


def test_executable_patch_ranges_and_code_caves_do_not_overlap() -> None:
    ranges: list[tuple[int, int]] = []
    for offset, original, patched in ALL_PATCHES:
        original_size = len(bytes.fromhex(original))
        patched_size = len(bytes.fromhex(patched))
        assert original_size == patched_size
        candidate = (offset, offset + original_size)
        for existing in ranges:
            assert candidate[1] <= existing[0] or candidate[0] >= existing[1], (candidate, existing)
        ranges.append(candidate)


def test_advisor_random_cave_mixes_time_stamp_counter_with_existing_rng_state() -> None:
    assert ADVISOR_RANDOM_CAVE.startswith("52510F31")
    assert "3201" in ADVISOR_RANDOM_CAVE
    assert "326101" in ADVISOR_RANDOM_CAVE
    assert "FE01" in ADVISOR_RANDOM_CAVE
    assert "304101" in ADVISOR_RANDOM_CAVE
    assert ADVISOR_RANDOM_CAVE.endswith("90" * 35)


def test_odawara_routed_soldier_destination_cave_covers_full_wall_collision_corridor() -> None:
    cave = ODAWARA_ROUTED_SOLDIER_DESTINATION_CAVE

    assert "803D00C0D20001" in cave
    assert "81FA00280000" in cave
    assert "817B1000580000" not in cave
    assert "817B1400080000" in cave
    assert "817B1400980000" in cave
    assert "BA00280000" in cave
    assert "8B0DF8987200" in cave
    assert "A1F8987200" in cave
    assert "8B15F4987200" in cave
    assert "8B1520BFD200" in ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE
    assert "A124BFD200" in ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE
    assert "803D00C0D20001" in ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE
    assert "A1F8987200" in ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE
    assert "8B15F4987200" in ODAWARA_GLOBAL_ROUTED_DESTINATION_CAVE


def test_odawara_map_name_guard_limits_route_rewrite_to_odawara() -> None:
    assert ODAWARA_PATCHES[0] == (0x000B3656, "BB01000000", "E965782600")
    assert ODAWARA_PATCHES[1][0] == 0x0031AEC0
    assert "813E6F646177" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "817E0461726120" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "817E0828746F79" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "817E0C6F746F6D" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "66817E106929" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "C60500C0D20001" in ODAWARA_MAP_NAME_GUARD_CAVE
    assert "C60500C0D20000" in ODAWARA_MAP_NAME_GUARD_CAVE


def test_odawara_open_side_exit_choice_matches_normal_nearest_edge_routing() -> None:
    def choose_exit(current_x: int, current_z: int, map_x_max: int = 0xA000, map_z_max: int = 0xA000) -> tuple[int, int]:
        target_x = max(current_x, 0x2800)
        target_z = 0
        best_distance = current_z

        north_distance = map_z_max - current_z
        if north_distance < best_distance:
            best_distance = north_distance
            target_x = max(current_x, 0x2800)
            target_z = map_z_max

        east_distance = map_x_max - current_x
        if east_distance < best_distance:
            target_x = map_x_max
            target_z = current_z

        return target_x, target_z

    assert choose_exit(0x3000, 0x0C00) == (0x3000, 0)
    assert choose_exit(0x2100, 0x0C00) == (0x2800, 0)
    assert choose_exit(0x3000, 0x9400) == (0x3000, 0xA000)
    assert choose_exit(0x9800, 0x5000) == (0xA000, 0x5000)


def test_odawara_patch_does_not_ship_unpublished_cleanup_paths() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "shogun_fix_patcher.c").read_text(encoding="utf-8")

    for marker in (
        "OdawaraFailedRoutedTargetHookCleanup",
        "OdawaraNarrowRouteCorridorHookCleanup",
        "OdawaraEastEdgeRouteHookCleanup",
        "OdawaraNearestRouteHookCleanup",
        "GROUP_ODAWARA_NEAREST_ROUTE_CLEANUP",
    ):
        assert marker not in source


def test_partial_odawara_exe_patch_fails_without_repairing_or_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    blob = bytearray(exe.read_bytes())
    write_bytes(blob, ODAWARA_PATCHES[0][0], ODAWARA_PATCHES[0][2])
    exe.write_bytes(blob)
    partial_bytes = exe.read_bytes()

    result = run_patcher("--apply", "odawara", target=game)

    assert result.returncode != 0
    assert "partial" in (result.stdout + result.stderr).lower()
    assert exe.read_bytes() == partial_bytes
    assert_odawara_map_unchanged(game)
    assert_no_odawara_map_backup(game)
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


def test_odawara_fix_preserves_existing_map_state_without_repairing_or_backups(tmp_path: Path) -> None:
    game = make_clean_game(tmp_path)
    exe = game / "ShogunM.exe"
    odawara_map = game / ODAWARA_MAP
    partial = ORIGINAL_ODAWARA_MAP.replace(b"cwallsec\n", b"surround\n", 1)
    odawara_map.write_bytes(partial)
    original_exe = exe.read_bytes()

    result = run_patcher("--apply", "odawara", target=game)

    assert result.returncode == 0, result.stdout + result.stderr
    assert_group_state(exe, ODAWARA_PATCHES, patched=True)
    assert odawara_map.read_bytes() == partial
    assert not (game / f"{ODAWARA_MAP}{SIDE_CAR_BACKUP}").exists()
    assert_no_odawara_bdf_backup(game)
    assert_only_shared_exe_backup(game, original_exe)


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
    assert "retraining-drag=clean" in clean.stdout
    assert "unit=clean" in clean.stdout
    assert "ammo=clean" in clean.stdout
    assert "kawanakajima=clean" in clean.stdout
    assert "odawara=clean" in clean.stdout
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert patched.returncode == 0, patched.stdout + patched.stderr
    assert "historical=patched" in patched.stdout
    assert "retraining-drag=clean" in patched.stdout
    assert "unit=clean" in patched.stdout
    assert "ammo=clean" in patched.stdout
    assert "kawanakajima=clean" in patched.stdout
    assert "odawara=clean" in patched.stdout
