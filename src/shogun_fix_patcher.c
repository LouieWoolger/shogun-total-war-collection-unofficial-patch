#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0501
#endif

#include <windows.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#define EXPECTED_EXE_SIZE 7319552LL
#define EXE_NAME L"ShogunM.exe"
#define MAX_PATH_CHARS 32768
#define SHARED_BACKUP_SUFFIX L".unofficial-patch.bak"

typedef struct {
    const char *name;
    DWORD offset;
    const char *original_hex;
    const char *patched_hex;
} PatchSpec;

typedef struct {
    const wchar_t *cli_name;
    const char *report_name;
    const wchar_t *backup_suffix;
    const PatchSpec *patches;
    size_t patch_count;
} PatchGroup;

typedef enum {
    GROUP_CLEAN,
    GROUP_PATCHED,
    GROUP_PARTIAL,
    GROUP_UNSUPPORTED
} GroupState;

typedef struct {
    bool historical;
    bool throne;
    bool unit;
    bool harvest;
} Selection;

static const PatchSpec AUDIO_PATCHES[] = {
    {"AudioEosCheckEntry", 0x001B7CCB, "8B4E6085C974", "E9102F160090"},
    {"AudioDurationScalingGate", 0x001B80D2, "8A451884C07532", "E9492B16009090"},
    {"AudioPostEofDelayGate", 0x001B7916, "8A451884C07407B801000000EB05", "E91C331600909090909090909090"},
    {"AudioStreamTimingCodeCave", 0x0031ABE0,
     "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
     "8B4E6085C975348B4E5485C974238D44241050518B01FF502085C07C148B5424108B7C24148B46408B764429C219F77C05E9E4D0E9FFE9EAD0E9FFE9B2D0E9FF837D6000740C8A451884C07505E9A7D4E9FFE9D4D4E9FF837D600074078A451884C0740AB801000000E9DBCCE9FFB888130000E9D1CCE9FF"},
    {"AudioScriptCleanupGate", 0x00198FA5, "A9FF0000007505E82FF8FFFF", "E9AE1C180090909090909090"},
    {"AudioCleanupGuardCodeCave", 0x0031AC58,
     "0000000000000000000000000000000000000000000000000000000000000000",
     "A9FF00000075148B0D8079C90085C974058039007505E86DDBE7FFE939E3E7FF"},
};

static const PatchSpec UNIT_PATCHES[] = {
    {"RecruitCostSizeScalar", 0x001364BC, "A16004C700", "B83C000000"},
    {"SupportCostSumTail", 0x00135792, "8BC683C4045E5FC38BF690909090", "E937541E00909090909090909090"},
    {"SupportCostCodeCave", 0x0031ABCE, "000000000000000000000000000000000000", "8BC66BC03C99F73D6004C70083C4045E5FC3"},
    {"TrainingTimeInitLoopCompare", 0x0015C550, "83F864", "83F87F"},
    {"TrainingTimeInitLoopSpecialCompare", 0x0015C57E, "83F864", "83F87F"},
    {"TrainingTimeInitUnrolledCompare", 0x0017CAEE, "83F864", "83F87F"},
    {"TrainingTimeDoublePassACompare", 0x001BFA08, "83FA64", "83FA7F"},
    {"TrainingTimeDoublePassBCompare", 0x002E3213, "83F864", "83F87F"},
};

static const PatchSpec HARVEST_PATCHES[] = {
    {"HarvestReportUseMp3Suffix", 0x00149D7F, "6032F100", "8033F100"},
    {"HarvestReportVoiceHook", 0x00149D88,
     "33C9898C2480020000898C2484020000C78424880200000E000000B80D0000008984248C02000089842490020000",
     "E9F30E1D009090909090909090909090909090909090909090909090909090909090909090909090909090909090"},
    {"HarvestReportCodeCave", 0x0031AC80,
     "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
     "33C9898C2480020000898C2484020000C78424880200000E000000B80D0000008984248C020000898424900200009090909090909090909C608B0D1C88C20085C974116A01E8E6D2E2FFC7051C88C200000000006A68E8C415FEFF83C40485C0742689C631D2885601895604895608C6460C018D9424640200005289F1E8AED5E9FF89351C88C200619D31C9E9A5F0E2FF"},
};

static const PatchSpec HISTORICAL_PATCHES[] = {
    {"TimedReinforcementPositionCall", 0x000AD6E3, "E87863F7FF", "E8D8C3AA00"},
    {"AdfCoordinateStub", 0x006F8AC0,
     "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
     "8B5424048B816C80000089028B81708000008942048B41103B81247800007E068B81247800008942088A812078000088420C8B8138780000894210C20400"},
};

static const PatchGroup GROUP_AUDIO = {
    L"throne", "throne", SHARED_BACKUP_SUFFIX, AUDIO_PATCHES, sizeof(AUDIO_PATCHES) / sizeof(AUDIO_PATCHES[0])
};

static const PatchGroup GROUP_UNIT = {
    L"unit", "unit", SHARED_BACKUP_SUFFIX, UNIT_PATCHES, sizeof(UNIT_PATCHES) / sizeof(UNIT_PATCHES[0])
};

static const PatchGroup GROUP_HARVEST = {
    L"harvest", "harvest", SHARED_BACKUP_SUFFIX, HARVEST_PATCHES, sizeof(HARVEST_PATCHES) / sizeof(HARVEST_PATCHES[0])
};

static const PatchGroup GROUP_HISTORICAL = {
    L"historical", "historical", SHARED_BACKUP_SUFFIX, HISTORICAL_PATCHES, sizeof(HISTORICAL_PATCHES) / sizeof(HISTORICAL_PATCHES[0])
};

static int hex_value(char c)
{
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

static size_t hex_to_bytes(const char *hex, unsigned char **out)
{
    size_t len = strlen(hex);
    if (len % 2 != 0) {
        *out = NULL;
        return 0;
    }
    size_t bytes_len = len / 2;
    unsigned char *bytes = (unsigned char *)malloc(bytes_len ? bytes_len : 1);
    if (!bytes) {
        *out = NULL;
        return 0;
    }
    for (size_t i = 0; i < bytes_len; ++i) {
        int hi = hex_value(hex[i * 2]);
        int lo = hex_value(hex[i * 2 + 1]);
        if (hi < 0 || lo < 0) {
            free(bytes);
            *out = NULL;
            return 0;
        }
        bytes[i] = (unsigned char)((hi << 4) | lo);
    }
    *out = bytes;
    return bytes_len;
}

static bool same_bytes(const unsigned char *a, const unsigned char *b, size_t len)
{
    return len == 0 || memcmp(a, b, len) == 0;
}

static const char *state_name(GroupState state)
{
    switch (state) {
    case GROUP_CLEAN:
        return "clean";
    case GROUP_PATCHED:
        return "patched";
    case GROUP_PARTIAL:
        return "partial";
    case GROUP_UNSUPPORTED:
        return "unsupported";
    default:
        return "unknown";
    }
}

static void print_last_error(const wchar_t *prefix, const wchar_t *path)
{
    DWORD err = GetLastError();
    fwprintf(stderr, L"error=%ls path=%ls win32=%lu\n", prefix, path ? path : L"", (unsigned long)err);
}

static bool append_path(wchar_t *buffer, size_t capacity, const wchar_t *suffix)
{
    size_t current = wcslen(buffer);
    size_t extra = wcslen(suffix);
    if (current + extra + 1 >= capacity) {
        return false;
    }
    wcscat(buffer, suffix);
    return true;
}

static bool resolve_exe_path(const wchar_t *target, wchar_t *out, DWORD out_count)
{
    wchar_t full[MAX_PATH_CHARS];
    DWORD full_len = GetFullPathNameW(target, MAX_PATH_CHARS, full, NULL);
    if (full_len == 0 || full_len >= MAX_PATH_CHARS) {
        print_last_error(L"could_not_resolve_target", target);
        return false;
    }

    DWORD attrs = GetFileAttributesW(full);
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        print_last_error(L"target_not_found", full);
        return false;
    }

    if (attrs & FILE_ATTRIBUTE_DIRECTORY) {
        size_t len = wcslen(full);
        if (len > 0 && full[len - 1] != L'\\' && full[len - 1] != L'/') {
            if (!append_path(full, MAX_PATH_CHARS, L"\\")) {
                fwprintf(stderr, L"error=path_too_long path=%ls\n", full);
                return false;
            }
        }
        if (!append_path(full, MAX_PATH_CHARS, EXE_NAME)) {
            fwprintf(stderr, L"error=path_too_long path=%ls\n", full);
            return false;
        }
        attrs = GetFileAttributesW(full);
        if (attrs == INVALID_FILE_ATTRIBUTES || (attrs & FILE_ATTRIBUTE_DIRECTORY)) {
            fwprintf(stderr, L"error=shogunm_not_found path=%ls\n", full);
            return false;
        }
    }

    const wchar_t *name = wcsrchr(full, L'\\');
    name = name ? name + 1 : full;
    if (_wcsicmp(name, EXE_NAME) != 0) {
        fwprintf(stderr, L"error=target_must_be_shogunm path=%ls\n", full);
        return false;
    }

    if (wcslen(full) + 1 > out_count) {
        fwprintf(stderr, L"error=path_too_long path=%ls\n", full);
        return false;
    }
    wcscpy(out, full);
    return true;
}

static bool check_file_size(const wchar_t *exe_path)
{
    HANDLE file = CreateFileW(exe_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        print_last_error(L"open_failed", exe_path);
        return false;
    }

    LARGE_INTEGER size;
    BOOL ok = GetFileSizeEx(file, &size);
    CloseHandle(file);
    if (!ok) {
        print_last_error(L"size_failed", exe_path);
        return false;
    }
    if (size.QuadPart != EXPECTED_EXE_SIZE) {
        fwprintf(stderr, L"error=unexpected_exe_size path=%ls size=%lld expected=%lld\n",
                 exe_path, (long long)size.QuadPart, (long long)EXPECTED_EXE_SIZE);
        return false;
    }
    return true;
}

static bool read_at(const wchar_t *path, DWORD offset, unsigned char *buffer, size_t len)
{
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        print_last_error(L"open_failed", path);
        return false;
    }

    LARGE_INTEGER pos;
    pos.QuadPart = offset;
    if (!SetFilePointerEx(file, pos, NULL, FILE_BEGIN)) {
        print_last_error(L"seek_failed", path);
        CloseHandle(file);
        return false;
    }

    DWORD read = 0;
    BOOL ok = ReadFile(file, buffer, (DWORD)len, &read, NULL);
    CloseHandle(file);
    if (!ok || read != len) {
        print_last_error(L"read_failed", path);
        return false;
    }
    return true;
}

static bool write_at(const wchar_t *path, DWORD offset, const unsigned char *buffer, size_t len)
{
    HANDLE file = CreateFileW(path, GENERIC_READ | GENERIC_WRITE,
                              FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        print_last_error(L"open_write_failed", path);
        return false;
    }

    LARGE_INTEGER pos;
    pos.QuadPart = offset;
    if (!SetFilePointerEx(file, pos, NULL, FILE_BEGIN)) {
        print_last_error(L"seek_failed", path);
        CloseHandle(file);
        return false;
    }

    DWORD written = 0;
    BOOL ok = WriteFile(file, buffer, (DWORD)len, &written, NULL);
    if (ok) {
        ok = FlushFileBuffers(file);
    }
    CloseHandle(file);
    if (!ok || written != len) {
        print_last_error(L"write_failed", path);
        return false;
    }
    return true;
}

static bool check_write_access(const wchar_t *path)
{
    HANDLE file = CreateFileW(path, GENERIC_READ | GENERIC_WRITE,
                              FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        print_last_error(L"open_write_failed", path);
        return false;
    }
    CloseHandle(file);
    return true;
}

static bool inspect_group(const wchar_t *exe_path, const PatchGroup *group, GroupState *state_out)
{
    size_t clean = 0;
    size_t patched = 0;

    for (size_t i = 0; i < group->patch_count; ++i) {
        const PatchSpec *spec = &group->patches[i];
        unsigned char *original = NULL;
        unsigned char *patched_bytes = NULL;
        size_t original_len = hex_to_bytes(spec->original_hex, &original);
        size_t patched_len = hex_to_bytes(spec->patched_hex, &patched_bytes);
        if (!original || !patched_bytes || original_len != patched_len) {
            fprintf(stderr, "error=invalid_manifest patch=%s\n", spec->name);
            free(original);
            free(patched_bytes);
            return false;
        }

        unsigned char *current = (unsigned char *)malloc(original_len);
        if (!current) {
            fprintf(stderr, "error=out_of_memory\n");
            free(original);
            free(patched_bytes);
            return false;
        }
        bool read_ok = read_at(exe_path, spec->offset, current, original_len);
        if (!read_ok) {
            free(original);
            free(patched_bytes);
            free(current);
            return false;
        }

        if (same_bytes(current, original, original_len)) {
            clean++;
        } else if (same_bytes(current, patched_bytes, patched_len)) {
            patched++;
        } else {
            fprintf(stderr, "error=unsupported group=%s patch=%s offset=0x%08lX\n",
                    group->report_name, spec->name, (unsigned long)spec->offset);
            free(original);
            free(patched_bytes);
            free(current);
            *state_out = GROUP_UNSUPPORTED;
            return true;
        }

        free(original);
        free(patched_bytes);
        free(current);
    }

    if (clean == group->patch_count) {
        *state_out = GROUP_CLEAN;
    } else if (patched == group->patch_count) {
        *state_out = GROUP_PATCHED;
    } else {
        *state_out = GROUP_PARTIAL;
    }
    return true;
}

static bool make_backup_path(const wchar_t *exe_path, const wchar_t *suffix, wchar_t *backup_path, size_t capacity)
{
    size_t exe_len = wcslen(exe_path);
    size_t suffix_len = wcslen(suffix);
    if (exe_len + suffix_len + 1 >= capacity) {
        return false;
    }
    wcscpy(backup_path, exe_path);
    wcscat(backup_path, suffix);
    return true;
}

static bool ensure_backup_from_source(const wchar_t *source_path, const wchar_t *exe_path, const wchar_t *suffix)
{
    wchar_t backup[MAX_PATH_CHARS];
    if (!make_backup_path(exe_path, suffix, backup, MAX_PATH_CHARS)) {
        fwprintf(stderr, L"error=backup_path_too_long path=%ls\n", exe_path);
        return false;
    }
    DWORD attrs = GetFileAttributesW(backup);
    if (attrs != INVALID_FILE_ATTRIBUTES) {
        fwprintf(stdout, L"backup_preserved=%ls\n", backup);
        return true;
    }
    if (!CopyFileW(source_path, backup, TRUE)) {
        print_last_error(L"backup_failed", backup);
        return false;
    }
    fwprintf(stdout, L"backup_created=%ls\n", backup);
    return true;
}

static bool ensure_backup(const wchar_t *exe_path, const wchar_t *suffix)
{
    return ensure_backup_from_source(exe_path, exe_path, suffix);
}

static bool group_needs_writes(const wchar_t *exe_path, const PatchGroup *group, bool *needs_writes)
{
    GroupState state;
    if (!inspect_group(exe_path, group, &state)) {
        return false;
    }
    if (state == GROUP_UNSUPPORTED || state == GROUP_PARTIAL) {
        fprintf(stderr, "error=%s_state group=%s\n", state_name(state), group->report_name);
        return false;
    }
    *needs_writes = state != GROUP_PATCHED;
    return true;
}

static bool apply_group_without_backup(const wchar_t *exe_path, const PatchGroup *group)
{
    GroupState state;
    if (!inspect_group(exe_path, group, &state)) {
        return false;
    }
    if (state == GROUP_UNSUPPORTED || state == GROUP_PARTIAL) {
        fprintf(stderr, "error=%s_state group=%s\n", state_name(state), group->report_name);
        return false;
    }
    if (state == GROUP_PATCHED) {
        printf("already_patched=%s\n", group->report_name);
        return true;
    }

    for (size_t i = 0; i < group->patch_count; ++i) {
        const PatchSpec *spec = &group->patches[i];
        unsigned char *original = NULL;
        unsigned char *patched_bytes = NULL;
        size_t len = hex_to_bytes(spec->original_hex, &original);
        size_t patched_len = hex_to_bytes(spec->patched_hex, &patched_bytes);
        if (!original || !patched_bytes || len != patched_len) {
            fprintf(stderr, "error=invalid_manifest patch=%s\n", spec->name);
            free(original);
            free(patched_bytes);
            return false;
        }

        unsigned char *current = (unsigned char *)malloc(len);
        if (!current) {
            fprintf(stderr, "error=out_of_memory\n");
            free(original);
            free(patched_bytes);
            return false;
        }
        if (!read_at(exe_path, spec->offset, current, len)) {
            free(original);
            free(patched_bytes);
            free(current);
            return false;
        }

        if (same_bytes(current, patched_bytes, len)) {
            free(original);
            free(patched_bytes);
            free(current);
            continue;
        }
        if (!same_bytes(current, original, len)) {
            fprintf(stderr, "error=unsupported group=%s patch=%s offset=0x%08lX\n",
                    group->report_name, spec->name, (unsigned long)spec->offset);
            free(original);
            free(patched_bytes);
            free(current);
            return false;
        }
        if (!write_at(exe_path, spec->offset, patched_bytes, len)) {
            free(original);
            free(patched_bytes);
            free(current);
            return false;
        }
        printf("patched group=%s patch=%s offset=0x%08lX\n",
               group->report_name, spec->name, (unsigned long)spec->offset);

        free(original);
        free(patched_bytes);
        free(current);
    }
    return true;
}

static bool apply_group(const wchar_t *exe_path, const PatchGroup *group)
{
    GroupState state;
    if (!inspect_group(exe_path, group, &state)) {
        return false;
    }
    if (state == GROUP_UNSUPPORTED || state == GROUP_PARTIAL) {
        fprintf(stderr, "error=%s_state group=%s\n", state_name(state), group->report_name);
        return false;
    }
    if (state == GROUP_PATCHED) {
        printf("already_patched=%s\n", group->report_name);
        return true;
    }
    if (!ensure_backup(exe_path, group->backup_suffix)) {
        return false;
    }
    return apply_group_without_backup(exe_path, group);
}

static bool verify_all(const wchar_t *exe_path)
{
    const PatchGroup *groups[] = {&GROUP_HISTORICAL, &GROUP_AUDIO, &GROUP_UNIT, &GROUP_HARVEST};
    for (size_t i = 0; i < sizeof(groups) / sizeof(groups[0]); ++i) {
        GroupState state;
        if (!inspect_group(exe_path, groups[i], &state)) {
            return false;
        }
        printf("%s=%s\n", groups[i]->report_name, state_name(state));
        if (state == GROUP_UNSUPPORTED || state == GROUP_PARTIAL) {
            return false;
        }
    }
    return true;
}

static bool preflight_selected(const wchar_t *exe_path, const Selection *selection)
{
    const PatchGroup *groups[] = {
        selection->historical ? &GROUP_HISTORICAL : NULL,
        selection->unit ? &GROUP_UNIT : NULL,
        (selection->throne || selection->harvest) ? &GROUP_AUDIO : NULL,
        selection->harvest ? &GROUP_HARVEST : NULL,
    };

    for (size_t i = 0; i < sizeof(groups) / sizeof(groups[0]); ++i) {
        if (!groups[i]) {
            continue;
        }
        GroupState state;
        if (!inspect_group(exe_path, groups[i], &state)) {
            return false;
        }
        if (state == GROUP_UNSUPPORTED || state == GROUP_PARTIAL) {
            fprintf(stderr, "error=%s_state group=%s\n", state_name(state), groups[i]->report_name);
            return false;
        }
    }
    return true;
}

static bool prepare_selected_backups(const wchar_t *exe_path, const Selection *selection)
{
    bool needs_historical = false;
    bool needs_unit = false;
    bool needs_audio = false;
    bool needs_harvest = false;

    if (selection->historical && !group_needs_writes(exe_path, &GROUP_HISTORICAL, &needs_historical)) {
        return false;
    }
    if (selection->unit && !group_needs_writes(exe_path, &GROUP_UNIT, &needs_unit)) {
        return false;
    }
    if ((selection->throne || selection->harvest) && !group_needs_writes(exe_path, &GROUP_AUDIO, &needs_audio)) {
        return false;
    }
    if (selection->harvest && !group_needs_writes(exe_path, &GROUP_HARVEST, &needs_harvest)) {
        return false;
    }

    if (needs_historical && !ensure_backup_from_source(exe_path, exe_path, GROUP_HISTORICAL.backup_suffix)) {
        return false;
    }
    if (needs_unit && !ensure_backup_from_source(exe_path, exe_path, GROUP_UNIT.backup_suffix)) {
        return false;
    }
    if (selection->throne && needs_audio &&
        !ensure_backup_from_source(exe_path, exe_path, GROUP_AUDIO.backup_suffix)) {
        return false;
    }
    if (selection->harvest && (needs_audio || needs_harvest) &&
        !ensure_backup_from_source(exe_path, exe_path, GROUP_HARVEST.backup_suffix)) {
        return false;
    }
    return true;
}

static bool selected_needs_writes(const wchar_t *exe_path, const Selection *selection, bool *needs_writes)
{
    bool needs_historical = false;
    bool needs_unit = false;
    bool needs_audio = false;
    bool needs_harvest = false;

    if (selection->historical && !group_needs_writes(exe_path, &GROUP_HISTORICAL, &needs_historical)) {
        return false;
    }
    if (selection->unit && !group_needs_writes(exe_path, &GROUP_UNIT, &needs_unit)) {
        return false;
    }
    if ((selection->throne || selection->harvest) && !group_needs_writes(exe_path, &GROUP_AUDIO, &needs_audio)) {
        return false;
    }
    if (selection->harvest && !group_needs_writes(exe_path, &GROUP_HARVEST, &needs_harvest)) {
        return false;
    }

    *needs_writes = needs_historical || needs_unit || needs_audio || needs_harvest;
    return true;
}

static bool apply_selected(const wchar_t *exe_path, const Selection *selection)
{
    if (!preflight_selected(exe_path, selection)) {
        return false;
    }
    bool needs_writes = false;
    if (!selected_needs_writes(exe_path, selection, &needs_writes)) {
        return false;
    }
    if (needs_writes && !check_write_access(exe_path)) {
        return false;
    }
    if (!prepare_selected_backups(exe_path, selection)) {
        return false;
    }
    if (selection->historical && !apply_group(exe_path, &GROUP_HISTORICAL)) {
        return false;
    }
    if (selection->unit && !apply_group(exe_path, &GROUP_UNIT)) {
        return false;
    }
    if (selection->throne && !apply_group(exe_path, &GROUP_AUDIO)) {
        return false;
    }
    if (selection->harvest) {
        if (!selection->throne) {
            bool audio_needs_writes = false;
            bool harvest_needs_writes = false;
            if (!group_needs_writes(exe_path, &GROUP_AUDIO, &audio_needs_writes) ||
                !group_needs_writes(exe_path, &GROUP_HARVEST, &harvest_needs_writes)) {
                return false;
            }
            if ((audio_needs_writes || harvest_needs_writes) &&
                !ensure_backup(exe_path, GROUP_HARVEST.backup_suffix)) {
                return false;
            }
            if (!apply_group_without_backup(exe_path, &GROUP_AUDIO)) {
                return false;
            }
        }
        if (!apply_group(exe_path, &GROUP_HARVEST)) {
            return false;
        }
    }
    return verify_all(exe_path);
}

static void print_usage(void)
{
    fputs("usage: shogun-fix-patcher.exe --target <folder-or-ShogunM.exe> --verify\n", stderr);
    fputs("       shogun-fix-patcher.exe --target <folder-or-ShogunM.exe> --apply <historical,throne,unit,harvest|recommended|all>\n", stderr);
}

static bool parse_apply_list(const wchar_t *value, Selection *selection)
{
    wchar_t *copy = _wcsdup(value);
    if (!copy) {
        return false;
    }
    wchar_t *context = NULL;
    wchar_t *token = wcstok(copy, L",", &context);
    while (token) {
        while (*token == L' ' || *token == L'\t') {
            token++;
        }
        if (_wcsicmp(token, L"recommended") == 0) {
            selection->historical = true;
            selection->throne = true;
            selection->unit = true;
        } else if (_wcsicmp(token, L"all") == 0) {
            selection->historical = true;
            selection->throne = true;
            selection->unit = true;
            selection->harvest = true;
        } else if (_wcsicmp(token, L"historical") == 0) {
            selection->historical = true;
        } else if (_wcsicmp(token, L"throne") == 0 || _wcsicmp(token, L"audio") == 0) {
            selection->throne = true;
        } else if (_wcsicmp(token, L"unit") == 0 || _wcsicmp(token, L"economics") == 0) {
            selection->unit = true;
        } else if (_wcsicmp(token, L"harvest") == 0) {
            selection->harvest = true;
        } else if (*token != L'\0') {
            fwprintf(stderr, L"error=unknown_fix name=%ls\n", token);
            free(copy);
            return false;
        }
        token = wcstok(NULL, L",", &context);
    }
    free(copy);
    return selection->historical || selection->throne || selection->unit || selection->harvest;
}

int wmain(int argc, wchar_t **argv)
{
    const wchar_t *target = NULL;
    const wchar_t *apply_value = NULL;
    bool verify = false;

    for (int i = 1; i < argc; ++i) {
        if (_wcsicmp(argv[i], L"--target") == 0 && i + 1 < argc) {
            target = argv[++i];
        } else if (_wcsicmp(argv[i], L"--apply") == 0 && i + 1 < argc) {
            apply_value = argv[++i];
        } else if (_wcsicmp(argv[i], L"--verify") == 0) {
            verify = true;
        } else {
            fwprintf(stderr, L"error=unknown_argument arg=%ls\n", argv[i]);
            print_usage();
            return 1;
        }
    }

    if (!target || (verify && apply_value) || (!verify && !apply_value)) {
        print_usage();
        return 1;
    }

    wchar_t exe_path[MAX_PATH_CHARS];
    if (!resolve_exe_path(target, exe_path, MAX_PATH_CHARS)) {
        return 2;
    }
    fwprintf(stdout, L"target=%ls\n", exe_path);

    if (!check_file_size(exe_path)) {
        return 2;
    }

    if (verify) {
        return verify_all(exe_path) ? 0 : 2;
    }

    Selection selection = {0};
    if (!parse_apply_list(apply_value, &selection)) {
        print_usage();
        return 1;
    }

    return apply_selected(exe_path, &selection) ? 0 : 2;
}
