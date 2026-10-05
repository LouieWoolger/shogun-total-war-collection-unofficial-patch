/* Durable per-installation removal. All destinations are compiled allowlist
   entries, never paths supplied by an on-disk receipt. XP-compatible Win32. */
#ifndef SHOGUN_LIFECYCLE_H
#define SHOGUN_LIFECYCLE_H

#define LC_VERSION 1u
#define LC_MAGIC 0x5347554eu
#define LC_TX_MAGIC 0x53474c54u
#define LC_FILES 13
#define LC_TARGETS 28
#define LC_STATE_INDEX 26
#define LC_UNINSTALL_INDEX 27
#define LC_STATE_DIR L".unofficial-shogun-patch"
#define LC_TX_DIR L".unofficial-shogun-patch-lifecycle"
#define LC_UNINSTALLER L"Uninstall Unofficial Shogun Patch.exe"
#define LC_REG_COUNT 11
#define LC_REG_BYTES (MAX_PATH_CHARS * 2 + 256)

typedef struct {
    DWORD managed, existed, ambiguous;
    char original[65], installed[65];
} LcFile;

typedef struct {
    DWORD magic, version, phase, volume, id_high, id_low;
    char path_hash[65];
    LcFile file[LC_FILES];
    char uninstaller[65], checksum[65];
} LcState;

typedef struct {
    DWORD exists, type, size;
    unsigned char bytes[LC_REG_BYTES];
} LcRegValue;

typedef struct {
    DWORD existed;
    LcRegValue value[LC_REG_COUNT];
} LcRegistry;

typedef struct {
    DWORD before_exists, after_exists, changed, started;
    char before[65], after[65];
} LcChange;

typedef struct {
    DWORD magic, version, complete, install, registry_started;
    DWORD volume, id_high, id_low;
    char path_hash[65];
    LcChange file[LC_TARGETS];
    LcRegistry registry;
    char checksum[65];
} LcJournal;

typedef struct {
    wchar_t game[MAX_PATH_CHARS], display[MAX_PATH_CHARS], root[MAX_PATH_CHARS];
    wchar_t stage[MAX_PATH_CHARS], key[160];
    HANDLE lock, journal_handle, pins[128];
    wchar_t *pin_paths[128];
    size_t pin_count;
    DWORD volume, id_high, id_low;
    char path_hash[65];
    bool state_exists;
    bool transaction_owned;
    bool preflight_bound;
    DWORD preflight_exists[LC_FILES];
    char preflight_hash[LC_FILES][65];
    LcState state;
    LcJournal journal;
} Lifecycle;

static const wchar_t *LC_REG_NAMES[LC_REG_COUNT] = {
    L"DisplayName", L"DisplayVersion", L"Publisher", L"InstallLocation",
    L"UninstallString", L"QuietUninstallString", L"DisplayIcon", L"URLInfoAbout",
    L"NoModify", L"NoRepair", L"EstimatedSize"
};

static bool lc_relative(int index, wchar_t *out)
{
    if (index < 0 || index >= LC_TARGETS) return false;
    if (index < LC_FILES) wcscpy(out, TX_FILES[index]);
    else if (index < LC_STATE_INDEX) swprintf(out, 128, LC_STATE_DIR L"\\original\\%d", index - LC_FILES);
    else wcscpy(out, index == LC_STATE_INDEX ? LC_STATE_DIR L"\\state.bin" : LC_UNINSTALLER);
    return true;
}

static bool lc_path(const wchar_t *root, int index, wchar_t *out)
{
    wchar_t relative[256];
    return lc_relative(index, relative) && tx_path(root, relative, out);
}

static bool lc_regular(const wchar_t *path, bool *exists)
{
    if (!tx_regular(path, exists)) return false;
    if (!*exists) return true;
    HANDLE file = CreateFileW(path, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              NULL, OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    BY_HANDLE_FILE_INFORMATION info;
    bool ok = file != INVALID_HANDLE_VALUE && GetFileInformationByHandle(file, &info) &&
        info.nNumberOfLinks == 1 && !(info.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT));
    if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    if (!ok) fwprintf(stderr, L"error=lifecycle_unsafe_file path=%ls\n", path);
    return ok;
}

static bool lc_hash(const wchar_t *path, bool *exists, char hash[65])
{
    *exists = false;
    hash[0] = 0;
    return lc_regular(path, exists) && (!*exists || file_sha256(path, hash));
}

static bool lc_pin(Lifecycle *lc, const wchar_t *directory)
{
    DWORD attrs = GetFileAttributesW(directory);
    if (attrs == INVALID_FILE_ATTRIBUTES) return GetLastError() == ERROR_FILE_NOT_FOUND || GetLastError() == ERROR_PATH_NOT_FOUND;
    if (!(attrs & FILE_ATTRIBUTE_DIRECTORY) || (attrs & FILE_ATTRIBUTE_REPARSE_POINT)) return false;
    HANDLE handle = CreateFileW(directory, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    BY_HANDLE_FILE_INFORMATION info;
    if (handle == INVALID_HANDLE_VALUE || !GetFileInformationByHandle(handle, &info) ||
        !(info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) {
        if (handle != INVALID_HANDLE_VALUE) CloseHandle(handle);
        return false;
    }
    for (size_t i = 0; i < lc->pin_count; ++i) if (lc->pins[i] != INVALID_HANDLE_VALUE) {
        BY_HANDLE_FILE_INFORMATION prior;
        if (GetFileInformationByHandle(lc->pins[i], &prior) && prior.dwVolumeSerialNumber == info.dwVolumeSerialNumber &&
            prior.nFileIndexHigh == info.nFileIndexHigh && prior.nFileIndexLow == info.nFileIndexLow) {
            CloseHandle(handle); return true;
        }
    }
    for (size_t i = 0; i < lc->pin_count; ++i) if (lc->pins[i] == INVALID_HANDLE_VALUE) {
        lc->pin_paths[i] = _wcsdup(directory);
        if (!lc->pin_paths[i]) { CloseHandle(handle); return false; }
        lc->pins[i] = handle; return true;
    }
    if (lc->pin_count == 128) { CloseHandle(handle); return false; }
    lc->pin_paths[lc->pin_count] = _wcsdup(directory);
    if (!lc->pin_paths[lc->pin_count]) { CloseHandle(handle); return false; }
    lc->pins[lc->pin_count++] = handle;
    return true;
}

static bool lc_pin_parents(Lifecycle *lc, const wchar_t *path)
{
    wchar_t copy[MAX_PATH_CHARS];
    wcscpy(copy, path);
    /* Local absolute extended paths only; network/device namespaces are not
       accepted as installation identities. */
    for (wchar_t *p = copy + 7; *p; ++p) if (*p == L'\\') {
        *p = 0;
        bool ok = lc_pin(lc, copy);
        *p = L'\\';
        if (!ok) return false;
    }
    return true;
}

static bool lc_guard_parents(Lifecycle *lc, const wchar_t *path, bool create)
{
    wchar_t copy[MAX_PATH_CHARS];
    DWORD n = GetFullPathNameW(path, MAX_PATH_CHARS, copy, NULL);
    if (!n || n >= MAX_PATH_CHARS) return false;
    wchar_t extended[MAX_PATH_CHARS];
    if (wcsncmp(copy, L"\\\\?\\", 4) != 0) {
        if (wcslen(copy) + 5 >= MAX_PATH_CHARS || copy[1] != L':') return false;
        wcscpy(extended, L"\\\\?\\"); wcscat(extended, copy); wcscpy(copy, extended);
    }
    if (copy[5] != L':' || copy[6] != L'\\') return false;
    for (wchar_t *p = copy + 7; *p; ++p) if (*p == L'\\') {
        *p = 0;
        if (create && !CreateDirectoryW(copy, NULL) && GetLastError() != ERROR_ALREADY_EXISTS) { *p = L'\\'; return false; }
        bool ok = lc_pin(lc, copy); *p = L'\\';
        if (!ok) { fprintf(stderr, "error=lifecycle_unsafe_parent\n"); return false; }
    }
    return true;
}

static bool lc_copy(Lifecycle *lc, const wchar_t *source, const wchar_t *destination)
{
    return lc_guard_parents(lc, source, false) && lc_guard_parents(lc, destination, true) && tx_flush_copy(source, destination);
}

static void lc_close(Lifecycle *lc)
{
    if (lc->journal_handle != INVALID_HANDLE_VALUE) CloseHandle(lc->journal_handle);
    for (size_t i = 0; i < lc->pin_count; ++i) {
        if (lc->pins[i] != INVALID_HANDLE_VALUE) CloseHandle(lc->pins[i]);
        free(lc->pin_paths[i]);
    }
    if (lc->lock != INVALID_HANDLE_VALUE) CloseHandle(lc->lock);
    free(lc);
}

static bool lc_initialize(Lifecycle *lc, const wchar_t *target)
{
    lc->lock = lc->journal_handle = INVALID_HANDLE_VALUE;
    wchar_t full[MAX_PATH_CHARS];
    DWORD n = GetFullPathNameW(target, MAX_PATH_CHARS, full, NULL);
    if (!n || n >= MAX_PATH_CHARS) return false;
    if (wcsncmp(full, L"\\\\?\\", 4) == 0) memmove(full, full + 4, (wcslen(full + 4) + 1) * sizeof(wchar_t));
    if (wcslen(full) < 3 || full[1] != L':' || full[2] != L'\\' || wcschr(full + 2, L':')) {
        fprintf(stderr, "error=lifecycle_requires_local_absolute_directory\n"); return false;
    }
    wchar_t *name = wcsrchr(full, L'\\');
    if (name && _wcsicmp(name + 1, EXE_NAME) == 0) *name = 0;
    while (wcslen(full) > 3 && full[wcslen(full) - 1] == L'\\') full[wcslen(full) - 1] = 0;
    n = GetLongPathNameW(full, lc->display, MAX_PATH_CHARS);
    if (!n || n >= MAX_PATH_CHARS || n + 5 >= MAX_PATH_CHARS) return false;
    CharUpperBuffW(lc->display, 1);
    wcscpy(lc->game, L"\\\\?\\"); wcscat(lc->game, lc->display);
    if (!tx_no_reparse(lc->game) || !lc_pin_parents(lc, lc->game) || !lc_pin(lc, lc->game)) return false;
    BY_HANDLE_FILE_INFORMATION info;
    if (!GetFileInformationByHandle(lc->pins[lc->pin_count - 1], &info)) return false;
    lc->volume = info.dwVolumeSerialNumber; lc->id_high = info.nFileIndexHigh; lc->id_low = info.nFileIndexLow;
    wchar_t lower[MAX_PATH_CHARS]; wcscpy(lower, lc->display); CharLowerBuffW(lower, (DWORD)wcslen(lower));
    PiSha256 sha; char hash[65]; pi_sha256_init(&sha);
    pi_sha256_update(&sha, (unsigned char *)lower, wcslen(lower) * sizeof(wchar_t)); pi_sha256_final(&sha, hash);
    strcpy(lc->path_hash, hash);
    swprintf(lc->key, 160, L"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\UnofficialShogunPatch-%hs", hash);
    wchar_t lock_path[MAX_PATH_CHARS];
    if (!tx_path(lc->game, L".unofficial-shogun-patch.lock", lock_path)) return false;
    bool exists = false;
    if (!lc_regular(lock_path, &exists)) return false;
    lc->lock = CreateFileW(lock_path, GENERIC_READ | GENERIC_WRITE | DELETE, 0, NULL, CREATE_NEW,
        FILE_ATTRIBUTE_HIDDEN | FILE_FLAG_DELETE_ON_CLOSE | FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    if (lc->lock == INVALID_HANDLE_VALUE) { print_last_error(L"lifecycle_busy_or_denied", lock_path); return false; }
    if (!GetFileInformationByHandle(lc->lock, &info) || info.nNumberOfLinks != 1 ||
        (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) return false;
    for (int i = 0; i < LC_TARGETS; ++i) {
        wchar_t path[MAX_PATH_CHARS];
        if (!lc_path(lc->game, i, path) || !lc_regular(path, &exists)) return false;
        /* The BDF and durable-state directories are pinned against junction
           replacement. Repeated parents need not consume additional handles. */
        if ((i == 1 || i == LC_STATE_INDEX || i == LC_FILES) && !lc_pin_parents(lc, path)) return false;
    }
    return tx_path(lc->game, LC_TX_DIR, lc->root) && tx_path(lc->root, L"stage", lc->stage);
}

static void lc_checksum(void *object, size_t size, char out[65])
{
    PiSha256 sha; pi_sha256_init(&sha); pi_sha256_update(&sha, object, size); pi_sha256_final(&sha, out);
}

static bool lc_read_blob(const wchar_t *path, void *buffer, DWORD size)
{
    bool exists = false;
    if (!lc_regular(path, &exists) || !exists) return false;
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    LARGE_INTEGER length; DWORD got = 0;
    bool ok = file != INVALID_HANDLE_VALUE && GetFileSizeEx(file, &length) && length.QuadPart == size &&
        ReadFile(file, buffer, size, &got, NULL) && got == size;
    if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    return ok;
}

static bool lc_write_blob(Lifecycle *lc, const wchar_t *path, const void *buffer, DWORD size)
{
    if (!lc_guard_parents(lc, path, true) || !tx_no_reparse(path)) return false;
    HANDLE file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    DWORD written = 0;
    bool ok = file != INVALID_HANDLE_VALUE && WriteFile(file, buffer, size, &written, NULL) &&
        written == size && FlushFileBuffers(file);
    if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    if (!ok) print_last_error(L"lifecycle_write_failed", path);
    return ok;
}

static bool lc_state_load(Lifecycle *lc)
{
    wchar_t path[MAX_PATH_CHARS]; bool exists = false;
    if (!lc_path(lc->game, LC_STATE_INDEX, path) || !lc_regular(path, &exists)) return false;
    lc->state_exists = exists;
    if (!exists) {
        /* A directory without a receipt is not proof that its contents belong
           to this patch. Refuse it rather than adopting or clearing it. */
        wchar_t directory[MAX_PATH_CHARS];
        if (!tx_path(lc->game, LC_STATE_DIR, directory)) return false;
        if (GetFileAttributesW(directory) != INVALID_FILE_ATTRIBUTES) {
            fwprintf(stderr, L"error=lifecycle_receipt_missing retained=%ls\n", directory); return false;
        }
        memset(&lc->state, 0, sizeof(lc->state));
        lc->state.magic = LC_MAGIC; lc->state.version = LC_VERSION; lc->state.phase = 1;
        lc->state.volume = lc->volume; lc->state.id_high = lc->id_high; lc->state.id_low = lc->id_low;
        strcpy(lc->state.path_hash, lc->path_hash);
        return true;
    }
    if (!lc_read_blob(path, &lc->state, sizeof(lc->state))) goto bad;
    char checksum[65]; lc_checksum(&lc->state, offsetof(LcState, checksum), checksum);
    if (lc->state.magic != LC_MAGIC || lc->state.version != LC_VERSION || !tx_hash_valid(lc->state.checksum) ||
        (lc->state.phase != 1 && lc->state.phase != 2) || strcmp(checksum, lc->state.checksum) != 0 ||
        lc->state.volume != lc->volume || lc->state.id_high != lc->id_high || lc->state.id_low != lc->id_low ||
        !tx_hash_valid(lc->state.path_hash) || strcmp(lc->state.path_hash, lc->path_hash) != 0 ||
        !tx_hash_valid(lc->state.uninstaller)) goto bad;
    for (int i = 0; i < LC_FILES; ++i) {
        LcFile *f = &lc->state.file[i];
        if (f->managed > 1 || f->existed > 1 || f->ambiguous > 1 ||
            (i < 2 && f->managed && !f->existed) ||
            (f->ambiguous && (i < 2 || i > 5 || f->existed)) ||
            (f->managed && !tx_hash_valid(f->installed)) ||
            (f->managed && f->existed && !tx_hash_valid(f->original))) goto bad;
        if (f->managed && f->existed && lc->state.phase == 1) {
            char hash[65];
            if (!lc_path(lc->game, i + LC_FILES, path) || !lc_hash(path, &exists, hash) ||
                !exists || strcmp(hash, f->original) != 0) {
                fwprintf(stderr, L"error=lifecycle_baseline_invalid file=%d path=%ls\n", i, path); return false;
            }
        }
    }
    return true;
bad:
    fprintf(stderr, "error=lifecycle_receipt_invalid_or_wrong_directory action=if_folder_was_moved_return_it_to_its_registered_location\n"); return false;
}

static bool lc_registry_snapshot(Lifecycle *lc, LcRegistry *snapshot)
{
    memset(snapshot, 0, sizeof(*snapshot));
    HKEY key;
    LONG error = RegOpenKeyExW(HKEY_CURRENT_USER, lc->key, 0, KEY_QUERY_VALUE | KEY_WOW64_32KEY, &key);
    if (error == ERROR_FILE_NOT_FOUND) return true;
    if (error != ERROR_SUCCESS) { fprintf(stderr, "error=lifecycle_registry_read win32=%ld\n", error); return false; }
    snapshot->existed = 1;
    bool ok = true;
    for (int i = 0; i < LC_REG_COUNT; ++i) {
        LcRegValue *value = &snapshot->value[i]; value->size = LC_REG_BYTES;
        error = RegQueryValueExW(key, LC_REG_NAMES[i], NULL, &value->type, value->bytes, &value->size);
        if (error == ERROR_FILE_NOT_FOUND) { value->size = 0; continue; }
        if (error != ERROR_SUCCESS) { ok = false; break; }
        value->exists = 1;
    }
    RegCloseKey(key); return ok;
}

static bool lc_registry_expected(Lifecycle *lc, int index, LcRegValue *value)
{
    memset(value, 0, sizeof(*value)); value->exists = 1;
    if (index >= 8) {
        DWORD number = index == 10 ? 16384 : 1;
        value->type = REG_DWORD; value->size = sizeof(number); memcpy(value->bytes, &number, sizeof(number)); return true;
    }
    wchar_t *text = (wchar_t *)value->bytes;
    size_t capacity = LC_REG_BYTES / sizeof(wchar_t);
    int n = 0;
    switch (index) {
    case 0: n = swprintf(text, capacity, L"Unofficial Shogun Patch (%ls)", lc->display); break;
    case 1: n = swprintf(text, capacity, L"1.3.3"); break;
    case 2: n = swprintf(text, capacity, L"Louie Woolger"); break;
    case 3: n = swprintf(text, capacity, L"%ls", lc->display); break;
    case 4: n = swprintf(text, capacity, L"\"%ls\\%ls\"", lc->display, LC_UNINSTALLER); break;
    case 5: n = swprintf(text, capacity, L"\"%ls\\%ls\" /S", lc->display, LC_UNINSTALLER); break;
    case 6: n = swprintf(text, capacity, L"%ls\\%ls", lc->display, LC_UNINSTALLER); break;
    case 7: n = swprintf(text, capacity, L"https://github.com/LouieWoolger/shogun-total-war-collection-unofficial-patch"); break;
    }
    if (n < 0 || (size_t)n + 1 > capacity) return false;
    value->type = REG_SZ; value->size = (DWORD)((n + 1) * sizeof(wchar_t)); return true;
}

static bool lc_reg_value_equal(const LcRegValue *a, const LcRegValue *b)
{
    return a->exists == b->exists && (!a->exists ||
        (a->type == b->type && a->size == b->size && memcmp(a->bytes, b->bytes, a->size) == 0));
}

static bool lc_reg_path_equal(const LcRegValue *a, const LcRegValue *b)
{
    if (!a->exists || !b->exists || a->type != REG_SZ || b->type != REG_SZ ||
        a->size != b->size || a->size < sizeof(wchar_t) || a->size % sizeof(wchar_t) ||
        ((const wchar_t *)a->bytes)[a->size / sizeof(wchar_t) - 1] != 0) return false;
    return _wcsicmp((const wchar_t *)a->bytes, (const wchar_t *)b->bytes) == 0;
}

static bool lc_registry_owned(Lifecycle *lc, const LcRegistry *snapshot)
{
    if (!snapshot->existed) return true;
    LcRegValue *expected = calloc(1, sizeof(*expected));
    if (!expected) return false;
    bool ok = lc_registry_expected(lc, 3, expected) && lc_reg_path_equal(&snapshot->value[3], expected) &&
        lc_registry_expected(lc, 4, expected) && lc_reg_path_equal(&snapshot->value[4], expected);
    free(expected);
    if (!ok) fprintf(stderr, "error=lifecycle_registry_identity_conflict\n");
    return ok;
}

static bool lc_registry_write(Lifecycle *lc, const LcRegistry *restore)
{
    HKEY key; DWORD disposition;
    LONG error = RegCreateKeyExW(HKEY_CURRENT_USER, lc->key, 0, NULL, REG_OPTION_NON_VOLATILE,
        KEY_SET_VALUE | KEY_QUERY_VALUE | KEY_WOW64_32KEY, NULL, &key, &disposition);
    if (error != ERROR_SUCCESS) { fprintf(stderr, "error=lifecycle_registry_write win32=%ld\n", error); return false; }
    LcRegValue *expected = calloc(1, sizeof(*expected)); bool ok = expected != NULL;
    for (int i = 0; i < LC_REG_COUNT && ok; ++i) {
        const LcRegValue *value = restore ? &restore->value[i] : expected;
        if (!restore && !lc_registry_expected(lc, i, expected)) { ok = false; break; }
        error = value->exists ? RegSetValueExW(key, LC_REG_NAMES[i], 0, value->type, value->bytes, value->size)
                              : RegDeleteValueW(key, LC_REG_NAMES[i]);
        ok = error == ERROR_SUCCESS || (!value->exists && error == ERROR_FILE_NOT_FOUND);
    }
    if (ok) ok = RegFlushKey(key) == ERROR_SUCCESS;
    free(expected); RegCloseKey(key);
    if (ok && restore && !restore->existed) {
        error = RegDeleteKeyW(HKEY_CURRENT_USER, lc->key);
        ok = error == ERROR_SUCCESS || error == ERROR_FILE_NOT_FOUND;
    }
    if (!ok) fprintf(stderr, "error=lifecycle_registry_write win32=%ld\n", error);
    return ok;
}

static bool lc_registry_delete(Lifecycle *lc)
{
    LcRegistry *snapshot = calloc(1, sizeof(*snapshot));
    if (!snapshot) return false;
    bool ok = lc_registry_snapshot(lc, snapshot) && lc_registry_owned(lc, snapshot);
    if (ok && snapshot->existed) {
        LONG error = RegDeleteKeyW(HKEY_CURRENT_USER, lc->key);
        ok = error == ERROR_SUCCESS || error == ERROR_FILE_NOT_FOUND;
        if (!ok) fprintf(stderr, "error=lifecycle_registry_delete win32=%ld\n", error);
    }
    free(snapshot); return ok;
}

static bool lc_save_journal(Lifecycle *lc)
{
    lc_checksum(&lc->journal, offsetof(LcJournal, checksum), lc->journal.checksum);
    LARGE_INTEGER zero; zero.QuadPart = 0; DWORD written = 0;
    bool ok = lc->journal_handle != INVALID_HANDLE_VALUE &&
        SetFilePointerEx(lc->journal_handle, zero, NULL, FILE_BEGIN) &&
        WriteFile(lc->journal_handle, &lc->journal, sizeof(lc->journal), &written, NULL) &&
        written == sizeof(lc->journal) && FlushFileBuffers(lc->journal_handle);
    if (!ok) print_last_error(L"lifecycle_journal_write", lc->root);
    return ok;
}

static bool lc_journal_valid(Lifecycle *lc)
{
    LcJournal *j = &lc->journal; char hash[65];
    lc_checksum(j, offsetof(LcJournal, checksum), hash);
    if (j->magic != LC_TX_MAGIC || j->version != LC_VERSION || j->complete > 1 || j->install > 1 ||
        j->registry_started > 1 || j->volume != lc->volume || j->id_high != lc->id_high || j->id_low != lc->id_low ||
        !tx_hash_valid(j->path_hash) || strcmp(j->path_hash, lc->path_hash) != 0 ||
        !tx_hash_valid(j->checksum) || strcmp(hash, j->checksum) != 0 || j->registry.existed > 1) return false;
    for (int i = 0; i < LC_TARGETS; ++i) {
        LcChange *f = &j->file[i];
        if (f->before_exists > 1 || f->after_exists > 1 || f->changed > 1 || f->started > 1 ||
            (f->started && !f->changed) || (f->before_exists && !tx_hash_valid(f->before)) ||
            (f->after_exists && !tx_hash_valid(f->after))) return false;
    }
    for (int i = 0; i < LC_REG_COUNT; ++i) {
        LcRegValue *v = &j->registry.value[i];
        if (v->exists > 1 || v->size > LC_REG_BYTES) return false;
    }
    return true;
}

static bool lc_matches(const wchar_t *path, DWORD wanted_exists, const char *wanted_hash)
{
    bool exists = false; char hash[65];
    return lc_hash(path, &exists, hash) && exists == (wanted_exists != 0) &&
        (!exists || strcmp(hash, wanted_hash) == 0);
}

static bool lc_copy_replace(Lifecycle *lc, const wchar_t *source, const wchar_t *destination, const wchar_t *scratch)
{
    bool exists = false;
    char hash[65];
    if (!lc_guard_parents(lc, source, false) || !lc_guard_parents(lc, destination, true) ||
        !lc_guard_parents(lc, scratch, true) || !lc_regular(source, &exists) || !exists ||
        !file_sha256(source, hash) || !lc_regular(scratch, &exists)) return false;
    if (exists ? !lc_matches(scratch, 1, hash) : !lc_copy(lc, source, scratch)) return false;
    if (!lc_regular(destination, &exists)) return false;
    bool ok = exists ? ReplaceFileW(destination, scratch, NULL, 0, NULL, NULL) != FALSE
                     : MoveFileExW(scratch, destination, MOVEFILE_WRITE_THROUGH) != FALSE;
    if (!ok) print_last_error(L"lifecycle_replace_failed", destination);
    return ok;
}

static bool lc_registry_can_rollback(Lifecycle *lc)
{
    LcRegistry *current = calloc(1, sizeof(*current));
    LcRegValue *expected = calloc(1, sizeof(*expected));
    if (!current || !expected) { free(current); free(expected); return false; }
    bool ok = lc_registry_snapshot(lc, current);
    for (int i = 0; i < LC_REG_COUNT && ok; ++i) {
        ok = lc_registry_expected(lc, i, expected) &&
            (lc_reg_value_equal(&current->value[i], &lc->journal.registry.value[i]) ||
             lc_reg_value_equal(&current->value[i], expected));
    }
    free(current); free(expected);
    if (!ok) fprintf(stderr, "error=lifecycle_registry_recovery_conflict\n");
    return ok;
}

static bool lc_rollback(Lifecycle *lc)
{
    fprintf(stderr, "phase=lifecycle_rollback\n");
    /* Validate the entire live set before changing any byte during recovery. */
    for (int i = 0; i < LC_TARGETS; ++i) {
        LcChange *f = &lc->journal.file[i]; if (!f->started) continue;
        wchar_t path[MAX_PATH_CHARS];
        if (!lc_path(lc->game, i, path) ||
            (!lc_matches(path, f->before_exists, f->before) && !lc_matches(path, f->after_exists, f->after))) {
            fwprintf(stderr, L"error=lifecycle_recovery_conflict path=%ls retained=%ls\n", path, lc->root); return false;
        }
    }
    if (lc->journal.registry_started && (!lc_registry_can_rollback(lc) ||
        !lc_registry_write(lc, &lc->journal.registry))) return false;
    lc->journal.registry_started = 0;
    if (!lc_save_journal(lc)) return false;
    for (int i = LC_TARGETS - 1; i >= 0; --i) {
        LcChange *f = &lc->journal.file[i]; if (!f->started) continue;
        wchar_t path[MAX_PATH_CHARS], backup[MAX_PATH_CHARS], scratch[MAX_PATH_CHARS], relative[48];
        if (!lc_path(lc->game, i, path)) return false;
        if (!lc_matches(path, f->before_exists, f->before)) {
            swprintf(relative, 48, L"rollback\\%d", i);
            if (!tx_path(lc->root, relative, backup)) return false;
            swprintf(relative, 48, L"restore-%d", i);
            if (!tx_path(lc->root, relative, scratch)) return false;
            if (f->before_exists) {
                if (!lc_matches(backup, 1, f->before) || !lc_copy_replace(lc, backup, path, scratch)) return false;
            } else if (!DeleteFileW(path)) { print_last_error(L"lifecycle_rollback_delete", path); return false; }
        }
        if (!lc_matches(path, f->before_exists, f->before)) return false;
        f->started = 0;
        if (!lc_save_journal(lc)) return false;
    }
    fprintf(stderr, "lifecycle_rollback=complete\n"); return true;
}

static void lc_release_directory_pin(Lifecycle *lc, const wchar_t *path);
static void lc_remove_empty_state_directories(Lifecycle *lc);

static void lc_release_subtree(Lifecycle *lc, const wchar_t *root)
{
    size_t length = wcslen(root);
    for (size_t i = 0; i < lc->pin_count; ++i) {
        if (lc->pins[i] == INVALID_HANDLE_VALUE || !lc->pin_paths[i]) continue;
        const wchar_t *path = lc->pin_paths[i];
        if (!_wcsnicmp(path, root, length) && (path[length] == 0 || path[length] == L'\\')) {
            CloseHandle(lc->pins[i]); lc->pins[i] = INVALID_HANDLE_VALUE;
            free(lc->pin_paths[i]); lc->pin_paths[i] = NULL;
        }
    }
}

static bool lc_directory_only_journal(const wchar_t *root, bool *empty)
{
    wchar_t pattern[MAX_PATH_CHARS];
    if (!tx_path(root, L"*", pattern)) return false;
    WIN32_FIND_DATAW item;
    HANDLE search = FindFirstFileW(pattern, &item);
    if (search == INVALID_HANDLE_VALUE) return false;
    bool only_journal = true; *empty = true;
    do {
        if (!wcscmp(item.cFileName, L".") || !wcscmp(item.cFileName, L"..")) continue;
        *empty = false;
        if (wcscmp(item.cFileName, L"journal.bin") != 0) only_journal = false;
    } while (FindNextFileW(search, &item));
    FindClose(search); return only_journal;
}

static bool lc_remove_owned_file(Lifecycle *lc, const wchar_t *path)
{
    bool exists = false;
    if (!lc_guard_parents(lc, path, false) || !lc_regular(path, &exists)) return false;
    return !exists || DeleteFileW(path) != FALSE;
}

static void lc_prune_parents(Lifecycle *lc, const wchar_t *path, const wchar_t *boundary)
{
    wchar_t parent[MAX_PATH_CHARS]; wcscpy(parent, path);
    wchar_t *slash;
    while ((slash = wcsrchr(parent, L'\\')) != NULL) {
        *slash = 0;
        if (wcslen(parent) <= wcslen(boundary)) break;
        if (!tx_no_reparse(parent)) break;
        lc_release_directory_pin(lc, parent);
        if (!RemoveDirectoryW(parent)) break;
    }
}

static bool lc_cleanup_transaction(Lifecycle *lc)
{
    if (lc->journal_handle != INVALID_HANDLE_VALUE) {
        CloseHandle(lc->journal_handle); lc->journal_handle = INVALID_HANDLE_VALUE;
    }
    /* Delete only compiled task-owned names. Unknown inserted files survive in
       a plainly named diagnostic archive; recursive deletion is never used. */
    bool ok = true; wchar_t path[MAX_PATH_CHARS], relative[64];
    for (int i = 0; i < LC_TARGETS; ++i) {
        if (!lc_path(lc->stage, i, path) || !lc_remove_owned_file(lc, path)) ok = false;
        else lc_prune_parents(lc, path, lc->stage);
        swprintf(relative, 64, L"rollback\\%d", i);
        if (!tx_path(lc->root, relative, path) || !lc_remove_owned_file(lc, path)) ok = false;
        swprintf(relative, 64, L"restore-%d", i);
        if (!tx_path(lc->root, relative, path) || !lc_remove_owned_file(lc, path)) ok = false;
    }
    for (int i = 0; i < 6; ++i) {
        swprintf(relative, 64, L"candidate-%d", i);
        if (!tx_path(lc->root, relative, path) || !lc_remove_owned_file(lc, path)) ok = false;
    }
    if (!ok) { fwprintf(stderr, L"warning=lifecycle_transaction_retained path=%ls\n", lc->root); return false; }
    lc_release_directory_pin(lc, lc->stage); RemoveDirectoryW(lc->stage);
    if (tx_path(lc->root, L"rollback", path)) { lc_release_directory_pin(lc, path); RemoveDirectoryW(path); }
    bool empty = false;
    if (lc_directory_only_journal(lc->root, &empty)) {
        if (!tx_path(lc->root, L"journal.bin", path) || !lc_remove_owned_file(lc, path)) return false;
        lc_release_directory_pin(lc, lc->root);
        if (RemoveDirectoryW(lc->root)) { lc->transaction_owned = false; return true; }
        /* An empty directory can be safely removed on retry even if a crash
           occurs after the final journal deletion and before RemoveDirectory. */
        fwprintf(stderr, L"warning=lifecycle_empty_transaction_cleanup_pending path=%ls\n", lc->root);
        return false;
    }
    lc_release_subtree(lc, lc->root);
    swprintf(relative, 64, L"Unofficial Shogun Patch recovery transaction %08lx-%lu", (unsigned long)GetTickCount(), (unsigned long)GetCurrentProcessId());
    if (!tx_path(lc->game, relative, path) || !tx_no_reparse(lc->root) ||
        !MoveFileExW(lc->root, path, MOVEFILE_WRITE_THROUGH)) {
        fwprintf(stderr, L"warning=lifecycle_transaction_retained path=%ls\n", lc->root); return false;
    }
    fwprintf(stdout, L"warning=unrecognized_transaction_files_preserved recovery_archive=%ls\n", path);
    lc->transaction_owned = false; return true;
}

static bool lc_recover(Lifecycle *lc)
{
    DWORD attrs = GetFileAttributesW(lc->root);
    if (attrs == INVALID_FILE_ATTRIBUTES) return GetLastError() == ERROR_FILE_NOT_FOUND || GetLastError() == ERROR_PATH_NOT_FOUND;
    wchar_t path[MAX_PATH_CHARS]; bool exists = false;
    bool empty = false;
    if ((attrs & FILE_ATTRIBUTE_DIRECTORY) && !(attrs & FILE_ATTRIBUTE_REPARSE_POINT) &&
        lc_directory_only_journal(lc->root, &empty) && empty) return RemoveDirectoryW(lc->root) != FALSE;
    if (!(attrs & FILE_ATTRIBUTE_DIRECTORY) || !tx_no_reparse(lc->root) || !lc_pin(lc, lc->root) ||
        !tx_path(lc->root, L"journal.bin", path) || !lc_regular(path, &exists) || !exists ||
        !lc_read_blob(path, &lc->journal, sizeof(lc->journal)) || !lc_journal_valid(lc)) {
        fprintf(stderr, "error=lifecycle_recovery_journal_invalid\n"); return false;
    }
    lc->journal_handle = CreateFileW(path, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (lc->journal_handle == INVALID_HANDLE_VALUE) return false;
    lc->transaction_owned = true;
    fprintf(stdout, "phase=lifecycle_recover\n");
    bool rolled_back_new_state = !lc->journal.complete && !lc->journal.file[LC_STATE_INDEX].before_exists;
    if (!lc->journal.complete) {
        if (!lc_rollback(lc)) return false;
    } else {
        for (int i = 0; i < LC_TARGETS; ++i) if (lc->journal.file[i].changed) {
            LcChange *f = &lc->journal.file[i];
            if (!lc_path(lc->game, i, path) || !lc_matches(path, f->after_exists, f->after)) {
                fprintf(stderr, "error=lifecycle_completed_target_changed file=%d\n", i); return false;
            }
        }
    }
    bool cleaned = lc_cleanup_transaction(lc);
    if (cleaned && rolled_back_new_state) lc_remove_empty_state_directories(lc);
    return cleaned;
}

static bool lc_begin(Lifecycle *lc, bool install)
{
    if (!CreateDirectoryW(lc->root, NULL)) return false;
    lc->transaction_owned = true;
    if (!lc_pin(lc, lc->root)) return false;
    memset(&lc->journal, 0, sizeof(lc->journal));
    lc->journal.magic = LC_TX_MAGIC; lc->journal.version = LC_VERSION; lc->journal.install = install;
    lc->journal.volume = lc->volume; lc->journal.id_high = lc->id_high; lc->journal.id_low = lc->id_low;
    strcpy(lc->journal.path_hash, lc->path_hash);
    wchar_t path[MAX_PATH_CHARS];
    if (!tx_path(lc->root, L"journal.bin", path)) return false;
    lc->journal_handle = CreateFileW(path, GENERIC_READ | GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (lc->journal_handle == INVALID_HANDLE_VALUE || !lc_registry_snapshot(lc, &lc->journal.registry) ||
        !lc_registry_owned(lc, &lc->journal.registry) || !lc_save_journal(lc) ||
        !CreateDirectoryW(lc->stage, NULL) || !lc_pin(lc, lc->stage)) return false;
    for (int i = 0; i < LC_TARGETS; ++i) {
        LcChange *f = &lc->journal.file[i];
        wchar_t live[MAX_PATH_CHARS], stage[MAX_PATH_CHARS], backup[MAX_PATH_CHARS], relative[48];
        bool exists = false;
        if (!lc_path(lc->game, i, live) || !lc_path(lc->stage, i, stage) || !lc_hash(live, &exists, f->before)) return false;
        f->before_exists = exists;
        if (lc->preflight_bound && i < LC_FILES && lc->state.file[i].managed &&
            (f->before_exists != lc->preflight_exists[i] || (exists && strcmp(f->before, lc->preflight_hash[i]) != 0))) {
            fwprintf(stderr, L"error=lifecycle_changed_after_conflict_check path=%ls\n", live); return false;
        }
        if (!exists) continue;
        swprintf(relative, 48, L"rollback\\%d", i);
        if (!tx_path(lc->root, relative, backup) || !lc_copy(lc, live, backup) ||
            !lc_copy(lc, live, stage) || !lc_matches(backup, 1, f->before) || !lc_matches(stage, 1, f->before)) return false;
    }
    return lc_save_journal(lc);
}

static bool lc_stage_state(Lifecycle *lc)
{
    wchar_t path[MAX_PATH_CHARS]; bool exists = false;
    lc_checksum(&lc->state, offsetof(LcState, checksum), lc->state.checksum);
    if (!lc_path(lc->stage, LC_STATE_INDEX, path) || !lc_regular(path, &exists)) return false;
    if (exists && !DeleteFileW(path)) return false;
    return lc_write_blob(lc, path, &lc->state, sizeof(lc->state));
}

static bool lc_commit(Lifecycle *lc)
{
    if (patch_log_failed) return false;
    for (int i = 0; i < LC_TARGETS; ++i) {
        LcChange *f = &lc->journal.file[i]; wchar_t stage[MAX_PATH_CHARS], live[MAX_PATH_CHARS]; bool exists = false;
        if (!lc_path(lc->stage, i, stage) || !lc_path(lc->game, i, live) || !lc_hash(stage, &exists, f->after)) return false;
        f->after_exists = exists;
        f->changed = f->before_exists != f->after_exists || (exists && strcmp(f->before, f->after) != 0);
        if (!f->changed) continue;
        if (!lc_matches(live, f->before_exists, f->before) || (f->before_exists && !check_write_access(live))) return false;
    }
    if (!lc_save_journal(lc)) return false;
    fprintf(stdout, "phase=lifecycle_commit\n");
    /* Establish durable originals, receipt and removal executable before any
       gameplay byte. Rollback retains the previous working removal path. */
    for (int n = 0; n < LC_TARGETS; ++n) {
        int i = n < 15 ? n + 13 : n - 15;
        LcChange *f = &lc->journal.file[i]; if (!f->changed) continue;
        wchar_t live[MAX_PATH_CHARS], stage[MAX_PATH_CHARS];
        if (!lc_path(lc->game, i, live) || !lc_path(lc->stage, i, stage) ||
            !lc_guard_parents(lc, live, true) || !lc_guard_parents(lc, stage, false) ||
            !lc_matches(live, f->before_exists, f->before)) return false;
        f->started = 1;
        if (!lc_save_journal(lc)) return false;
        bool ok;
        if (!f->after_exists) ok = DeleteFileW(live) != FALSE;
        else ok = f->before_exists ? ReplaceFileW(live, stage, NULL, 0, NULL, NULL) != FALSE
                                   : MoveFileExW(stage, live, MOVEFILE_WRITE_THROUGH) != FALSE;
        if (!ok || !lc_matches(live, f->after_exists, f->after)) {
            print_last_error(L"lifecycle_commit_failed", live); return false;
        }
        fprintf(stdout, "lifecycle_committed_file=%d\n", i);
        if (patch_log_failed) return false;
    }
    if (lc->journal.install) {
        lc->journal.registry_started = 1;
        if (!lc_save_journal(lc) || !lc_registry_write(lc, NULL)) return false;
    }
    lc->journal.complete = 1;
    if (!lc_save_journal(lc)) { lc->journal.complete = 0; return false; }
    return true;
}

static bool lc_reverse_exe(const wchar_t *path, bool *changed)
{
    const PatchGroup *groups[] = {&GROUP_AUDIO, &GROUP_UNIT, &GROUP_HARVEST, &GROUP_HISTORICAL,
        &GROUP_AMMO, &GROUP_ODAWARA, &GROUP_ADVISOR, &GROUP_RETRAINING_DRAG, &GROUP_SHUTDOWN};
    enum { GROUP_COUNT = sizeof(groups) / sizeof(groups[0]) };
    GroupState states[GROUP_COUNT]; *changed = false;
    if (!check_file_size(path)) return false;
    for (int g = 0; g < GROUP_COUNT; ++g) {
        if (!inspect_group_internal(path, groups[g], &states[g], true)) return false;
        if (states[g] == GROUP_UNSUPPORTED || (states[g] == GROUP_PARTIAL &&
            (groups[g] != &GROUP_RETRAINING_DRAG || !current_retraining_fragments(path) || !canonical_clean_identity(path)))) {
            fprintf(stderr, "error=lifecycle_unrecognized_executable group=%s\n", groups[g]->report_name); return false;
        }
    }
    /* Exact supported manifests establish these bytes; no file from a reference
       game, network service or development machine participates. */
    for (int g = 0; g < GROUP_COUNT; ++g) {
        if (states[g] == GROUP_CLEAN) continue;
        *changed = true;
        for (size_t i = 0; i < groups[g]->patch_count; ++i) {
            const PatchSpec *spec = &groups[g]->patches[i]; unsigned char *original = NULL;
            size_t n = hex_to_bytes(spec->original_hex, &original);
            bool ok = n && write_at(path, spec->offset, original, n);
            free(original); if (!ok) return false;
        }
    }
    for (int g = 0; g < GROUP_COUNT; ++g) if (!inspect_group_internal(path, groups[g], &states[g], true) || states[g] != GROUP_CLEAN) return false;
    return true;
}

static bool lc_reverse_bdf(const wchar_t *path, bool *changed)
{
    char *text = NULL; size_t size = 0; *changed = false;
    if (!read_entire_file(path, &text, &size)) return false;
    bool ok = true;
    for (size_t i = 0; i < sizeof(KAWANAKAJIMA_BDF_PATCHES) / sizeof(KAWANAKAJIMA_BDF_PATCHES[0]); ++i) {
        const TextPatchSpec *p = &KAWANAKAJIMA_BDF_PATCHES[i];
        size_t original = count_text_occurrences(text, p->original_text), patched = count_text_occurrences(text, p->patched_text);
        if (original + patched != 1) { ok = false; break; }
    }
    for (size_t i = 0; ok && i < sizeof(KAWANAKAJIMA_BDF_PATCHES) / sizeof(KAWANAKAJIMA_BDF_PATCHES[0]); ++i) {
        const TextPatchSpec *p = &KAWANAKAJIMA_BDF_PATCHES[i];
        if (strstr(text, p->patched_text)) {
            ok = replace_once(&text, &size, p->patched_text, p->original_text); *changed = true;
        }
    }
    if (ok && *changed) ok = write_entire_file(path, text, size);
    free(text); return ok;
}

static bool lc_backup_compatible(Lifecycle *lc, int index, const wchar_t *original, bool *compatible)
{
    *compatible = false;
    wchar_t backup[MAX_PATH_CHARS], candidate[MAX_PATH_CHARS], relative[48]; bool exists = false;
    if (!lc_path(lc->game, index + 6, backup) || !lc_regular(backup, &exists)) return false;
    if (!exists) return true;
    swprintf(relative, 48, L"candidate-%d", index);
    if (!tx_path(lc->root, relative, candidate) || !lc_copy(lc, backup, candidate)) return false;
    bool changed = false, valid = true; char baseline[65], hash[65];
    if (index == 0) valid = lc_reverse_exe(candidate, &changed);
    else if (index == 1) valid = lc_reverse_bdf(candidate, &changed);
    if (valid) valid = file_sha256(original, baseline) && file_sha256(candidate, hash);
    if (valid) *compatible = strcmp(baseline, hash) == 0;
    if (!DeleteFileW(candidate)) return false;
    if (!*compatible) fwprintf(stdout, L"warning=legacy_backup_retained path=%ls reason=incompatible_or_not_original\n", backup);
    return true;
}

static bool lc_config_backup_valid(const wchar_t *path, const char *current_hash, bool bundled)
{
    char *text = NULL; size_t size = 0;
    if (!read_entire_file(path, &text, &size)) return false;
    bool a = false, b = false, changed = false;
    bool ok = inspect_dgvoodoo_config_line(text, size, DGVOODOO_DEFAULT_PREFIX, DGVOODOO_DEFAULT_FIXED, &a) &&
        inspect_dgvoodoo_config_line(text, size, DGVOODOO_EXTRA_PREFIX, DGVOODOO_EXTRA_FIXED, &b);
    if (ok && !bundled) {
        ok = rewrite_dgvoodoo_config_line(&text, &size, DGVOODOO_DEFAULT_PREFIX, DGVOODOO_DEFAULT_FIXED, &changed) &&
            rewrite_dgvoodoo_config_line(&text, &size, DGVOODOO_EXTRA_PREFIX, DGVOODOO_EXTRA_FIXED, &changed);
        if (ok) { char hash[65]; lc_checksum(text, size, hash); ok = strcmp(hash, current_hash) == 0; }
    }
    free(text); return ok;
}

static bool lc_dll_rva(const IMAGE_NT_HEADERS32 *nt, const IMAGE_SECTION_HEADER *sections,
                       DWORD rva, DWORD length, ULONGLONG file_size, DWORD *offset)
{
    if (rva < nt->OptionalHeader.SizeOfHeaders && (ULONGLONG)rva + length <= nt->OptionalHeader.SizeOfHeaders &&
        (ULONGLONG)rva + length <= file_size) { *offset = rva; return true; }
    for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i) {
        const IMAGE_SECTION_HEADER *s = &sections[i];
        if (rva >= s->VirtualAddress && (ULONGLONG)rva - s->VirtualAddress + length <= s->SizeOfRawData &&
            (ULONGLONG)s->PointerToRawData + rva - s->VirtualAddress + length <= file_size) {
            *offset = s->PointerToRawData + rva - s->VirtualAddress; return true;
        }
    }
    return false;
}

static bool lc_legacy_dll_valid(const wchar_t *path, int index)
{
    bool exists = false;
    if (!lc_regular(path, &exists) || !exists) return false;
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER size; IMAGE_DOS_HEADER dos; IMAGE_NT_HEADERS32 nt; DWORD got = 0;
    IMAGE_SECTION_HEADER sections[96];
    bool ok = GetFileSizeEx(file, &size) && size.QuadPart >= (LONGLONG)sizeof(dos) &&
        size.QuadPart <= 512 * 1024 * 1024 && ReadFile(file, &dos, sizeof(dos), &got, NULL) && got == sizeof(dos) &&
        dos.e_magic == IMAGE_DOS_SIGNATURE && dos.e_lfanew >= (LONG)sizeof(dos) &&
        (LONGLONG)dos.e_lfanew + sizeof(nt) <= size.QuadPart;
    LARGE_INTEGER position; position.QuadPart = dos.e_lfanew;
    if (ok) ok = SetFilePointerEx(file, position, NULL, FILE_BEGIN) && ReadFile(file, &nt, sizeof(nt), &got, NULL) &&
        got == sizeof(nt) && nt.Signature == IMAGE_NT_SIGNATURE && nt.FileHeader.Machine == IMAGE_FILE_MACHINE_I386 &&
        (nt.FileHeader.Characteristics & IMAGE_FILE_DLL) && nt.FileHeader.NumberOfSections > 0 &&
        nt.FileHeader.NumberOfSections <= 96 && nt.FileHeader.SizeOfOptionalHeader >= sizeof(IMAGE_OPTIONAL_HEADER32) &&
        nt.OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR32_MAGIC && nt.OptionalHeader.SizeOfImage > 0 &&
        nt.OptionalHeader.SizeOfHeaders > 0 && nt.OptionalHeader.SizeOfHeaders <= size.QuadPart;
    if (ok) {
        position.QuadPart = (LONGLONG)dos.e_lfanew + sizeof(DWORD) + sizeof(IMAGE_FILE_HEADER) + nt.FileHeader.SizeOfOptionalHeader;
        ok = position.QuadPart + nt.FileHeader.NumberOfSections * sizeof(IMAGE_SECTION_HEADER) <= size.QuadPart &&
            SetFilePointerEx(file, position, NULL, FILE_BEGIN);
        for (unsigned i = 0; ok && i < nt.FileHeader.NumberOfSections; ++i) {
            IMAGE_SECTION_HEADER *section = &sections[i];
            ok = ReadFile(file, section, sizeof(*section), &got, NULL) && got == sizeof(*section) &&
                (ULONGLONG)section->PointerToRawData + section->SizeOfRawData <= (ULONGLONG)size.QuadPart &&
                (ULONGLONG)section->VirtualAddress + section->Misc.VirtualSize <= nt.OptionalHeader.SizeOfImage;
        }
    }
    if (ok) {
        IMAGE_EXPORT_DIRECTORY exports; DWORD offset, names, ordinals, functions;
        IMAGE_DATA_DIRECTORY dir = nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
        ok = nt.OptionalHeader.NumberOfRvaAndSizes > IMAGE_DIRECTORY_ENTRY_EXPORT && dir.Size >= sizeof(exports) &&
            lc_dll_rva(&nt, sections, dir.VirtualAddress, sizeof(exports), size.QuadPart, &offset) &&
            read_at(path, offset, (unsigned char *)&exports, sizeof(exports)) && exports.NumberOfNames > 0 &&
            exports.NumberOfNames <= 4096 && exports.NumberOfFunctions > 0 && exports.NumberOfFunctions <= 65536 &&
            lc_dll_rva(&nt, sections, exports.AddressOfNames, exports.NumberOfNames * sizeof(DWORD), size.QuadPart, &names) &&
            lc_dll_rva(&nt, sections, exports.AddressOfNameOrdinals, exports.NumberOfNames * sizeof(WORD), size.QuadPart, &ordinals) &&
            lc_dll_rva(&nt, sections, exports.AddressOfFunctions, exports.NumberOfFunctions * sizeof(DWORD), size.QuadPart, &functions);
        const char *first = index == 3 ? "DirectDrawCreate" : index == 4 ? "GetD3DInterface" : "Direct3DCreate9";
        const char *second = index == 3 ? "DirectDrawCreateEx" : index == 4 ? "GetD3DVersion" : NULL;
        bool found_first = false, found_second = second == NULL;
        for (DWORD i = 0; ok && i < exports.NumberOfNames; ++i) {
            DWORD rva, function; WORD ordinal;
            ok = read_at(path, names + i * sizeof(DWORD), (unsigned char *)&rva, sizeof(rva)) &&
                lc_dll_rva(&nt, sections, rva, 1, size.QuadPart, &offset) &&
                read_at(path, ordinals + i * sizeof(WORD), (unsigned char *)&ordinal, sizeof(ordinal)) &&
                ordinal < exports.NumberOfFunctions &&
                read_at(path, functions + ordinal * sizeof(DWORD), (unsigned char *)&function, sizeof(function)) &&
                function > 0 && function < nt.OptionalHeader.SizeOfImage;
            char name[80]; size_t n = 0;
            while (ok && n + 1 < sizeof(name)) {
                ok = (ULONGLONG)offset + n < (ULONGLONG)size.QuadPart &&
                    read_at(path, offset + (DWORD)n, (unsigned char *)&name[n], 1);
                if (!ok || name[n++] == 0) break;
            }
            if (!ok) break;
            if (!n || name[n - 1] != 0) continue;
            if (!strcmp(name, first)) found_first = true;
            if (second && !strcmp(name, second)) found_second = true;
        }
        ok = ok && found_first && found_second;
    }
    CloseHandle(file); return ok;
}

static bool lc_prepare_baselines(Lifecycle *lc)
{
    bool legacy = false;
    bool consumed[6] = {false};
    for (int i = 0; i < LC_FILES; ++i) {
        LcFile *f = &lc->state.file[i];
        wchar_t live[MAX_PATH_CHARS], original[MAX_PATH_CHARS];
        if (!lc_path(lc->game, i, live) || !lc_path(lc->stage, i + LC_FILES, original)) return false;
        if (f->managed) {
            if (!lc_matches(live, 1, f->installed)) {
                fwprintf(stderr, L"error=lifecycle_installed_file_changed path=%ls action=uninstall_with_recovery_or_restore_file\n", live); return false;
            }
            continue;
        }
        bool exists = lc->journal.file[i].before_exists != 0;
        f->existed = exists;
        if (!exists) continue;
        if (!lc_copy(lc, live, original)) return false;
        bool changed = false;
        if (i == 0) {
            if (!lc_reverse_exe(original, &changed)) return false;
        } else if (i == 1) {
            /* An unrelated custom BDF is left alone if no supported edit is
               recognized. Selecting this component still uses its old guard. */
            if (!lc_reverse_bdf(original, &changed)) changed = false;
        }
        if (!file_sha256(original, f->original)) return false;
        if (changed) { legacy = true; f->managed = 1; }
        if (!lc->state_exists && i < 2 && changed && !lc_backup_compatible(lc, i, original, &consumed[i])) return false;
    }
    if (!lc->state_exists) for (int i = 2; i <= 5; ++i) {
        if (!lc->journal.file[i].before_exists) continue;
        LcFile *f = &lc->state.file[i];
        bool bundled = dgvoodoo_known_payload_hash(i, lc->journal.file[i].before);
        if (!legacy && !bundled) continue;
        bool resolution_fixed = false;
        wchar_t live[MAX_PATH_CHARS], original[MAX_PATH_CHARS], backup[MAX_PATH_CHARS];
        if (!lc_path(lc->game, i, live) || !lc_path(lc->stage, i + LC_FILES, original) ||
            !lc_path(lc->game, i + 6, backup)) return false;
        if (i == 2) {
            GroupState state; bool exists = false; wchar_t ignored[MAX_PATH_CHARS], exe[MAX_PATH_CHARS];
            if (!lc_path(lc->game, 0, exe) || !inspect_dgvoodoo_resolution_fix(exe, &state, ignored, MAX_PATH_CHARS, &exists)) return false;
            resolution_fixed = exists && state == GROUP_PATCHED;
        }
        if (!bundled && !resolution_fixed) continue;
        bool exists = false; char hash[65];
        if (!lc_hash(backup, &exists, hash)) return false;
        bool valid_backup = exists;
        /* No known bundle, including an older one in the wrong slot, is an original. */
        for (int known = 2; valid_backup && known <= 5; ++known)
            if (dgvoodoo_known_payload_hash(known, hash)) valid_backup = false;
        if (valid_backup && i == 2) valid_backup = lc_config_backup_valid(backup, lc->journal.file[i].before, bundled);
        if (valid_backup && i != 2) valid_backup = lc_legacy_dll_valid(backup, i);
        if (!DeleteFileW(original)) return false;
        f->managed = 1;
        if (valid_backup) {
            if (!lc_copy(lc, backup, original) || !file_sha256(original, f->original)) return false;
            f->existed = 1; consumed[i] = true;
            fprintf(stdout, "legacy_baseline=validated_backup file=%d\n", i);
        } else {
            f->existed = 0; f->ambiguous = 1; f->original[0] = 0;
            fwprintf(stdout, L"warning=legacy_wrapper_origin_unknown path=%ls uninstall_requires_archive_choice=1\n", live);
        }
    }
    for (int i = 0; i < 6; ++i) if (consumed[i]) {
        LcFile *f = &lc->state.file[i + 6];
        f->managed = 1; f->existed = 0; f->original[0] = 0;
        wchar_t original[MAX_PATH_CHARS];
        if (!lc_path(lc->stage, i + 6 + LC_FILES, original) || !DeleteFileW(original)) return false;
        fprintf(stdout, "legacy_backup=adopted file=%d\n", i + 6);
    }
    return true;
}

static Lifecycle *lc_inner_context;
static bool lc_inner_guard(const wchar_t *path, bool create)
{
    return lc_guard_parents(lc_inner_context, path, create);
}
static void lc_inner_release(const wchar_t *path)
{
    lc_release_directory_pin(lc_inner_context, path);
}

static bool lc_stage_apply(Lifecycle *lc, const Selection *selection, const wchar_t *payload)
{
    /* Durable originals supersede size-only sidecars. Keep every pre-existing
       sidecar byte-for-byte, but do not let a corrupt legacy sidecar prevent
       exact-manifest reconstruction in the disposable stage. */
    for (int i = 6; i <= 11; ++i) {
        wchar_t stage[MAX_PATH_CHARS]; bool exists = false;
        if (!lc_path(lc->stage, i, stage) || !lc_regular(stage, &exists)) return false;
        if (exists && !DeleteFileW(stage)) return false;
    }
    wchar_t exe[MAX_PATH_CHARS];
    if (!lc_path(lc->stage, 0, exe)) return false;
    lc_inner_context = lc;
    transaction_parent_guard = lc_inner_guard; transaction_release_directory = lc_inner_release;
    bool ok = apply_transaction(exe, selection, payload);
    tx_finish_diagnostics();
    transaction_parent_guard = NULL; transaction_release_directory = NULL; lc_inner_context = NULL;
    if (!ok || patch_log_failed) return false;
    for (int i = 6; i <= 11; ++i) if (lc->journal.file[i].before_exists) {
        wchar_t stage[MAX_PATH_CHARS], backup[MAX_PATH_CHARS], relative[48]; bool exists = false;
        if (!lc_path(lc->stage, i, stage) || !lc_regular(stage, &exists)) return false;
        if (exists && !DeleteFileW(stage)) return false;
        swprintf(relative, 48, L"rollback\\%d", i);
        if (!tx_path(lc->root, relative, backup) || !lc_copy(lc, backup, stage)) return false;
    }
    return true;
}

static bool lc_finish_install_stage(Lifecycle *lc, const wchar_t *uninstaller)
{
    for (int i = 0; i < LC_FILES; ++i) {
        wchar_t stage[MAX_PATH_CHARS], original[MAX_PATH_CHARS]; bool exists = false; char hash[65];
        LcFile *f = &lc->state.file[i];
        if (!lc_path(lc->stage, i, stage) || !lc_path(lc->stage, i + LC_FILES, original) || !lc_hash(stage, &exists, hash)) return false;
        if (exists && (!lc->journal.file[i].before_exists || strcmp(hash, lc->journal.file[i].before) != 0)) f->managed = 1;
        if (f->managed) {
            if (!exists) { fprintf(stderr, "error=lifecycle_staged_managed_file_missing file=%d\n", i); return false; }
            strcpy(f->installed, hash);
            if (f->existed && !file_sha256(original, f->original)) return false;
        } else {
            bool original_exists = false;
            if (!lc_regular(original, &original_exists)) return false;
            if (original_exists && !DeleteFileW(original)) return false;
        }
    }
    bool exists = false; char hash[65]; wchar_t stage[MAX_PATH_CHARS];
    if (!lc_hash(uninstaller, &exists, hash) || !exists || !lc_path(lc->stage, LC_UNINSTALL_INDEX, stage)) return false;
    if (lc->journal.file[LC_UNINSTALL_INDEX].before_exists) {
        if (!lc->state_exists || strcmp(lc->journal.file[LC_UNINSTALL_INDEX].before, lc->state.uninstaller) != 0) {
            fprintf(stderr, "error=lifecycle_uninstaller_name_in_use\n"); return false;
        }
        if (!DeleteFileW(stage)) return false;
    }
    if (!lc_copy(lc, uninstaller, stage) || !lc_matches(stage, 1, hash)) return false;
    strcpy(lc->state.uninstaller, hash); lc->state.phase = 1;
    return lc_stage_state(lc);
}

static void lc_release_directory_pin(Lifecycle *lc, const wchar_t *path)
{
    HANDLE handle = CreateFileW(path, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    BY_HANDLE_FILE_INFORMATION wanted, got;
    if (handle == INVALID_HANDLE_VALUE) return;
    bool identified = GetFileInformationByHandle(handle, &wanted) != FALSE; CloseHandle(handle);
    if (!identified) return;
    for (size_t i = 0; i < lc->pin_count; ++i) {
        if (lc->pins[i] == INVALID_HANDLE_VALUE) continue;
        if (GetFileInformationByHandle(lc->pins[i], &got) && got.dwVolumeSerialNumber == wanted.dwVolumeSerialNumber &&
            got.nFileIndexHigh == wanted.nFileIndexHigh && got.nFileIndexLow == wanted.nFileIndexLow) {
            CloseHandle(lc->pins[i]); lc->pins[i] = INVALID_HANDLE_VALUE;
            free(lc->pin_paths[i]); lc->pin_paths[i] = NULL;
        }
    }
}

static void lc_remove_empty_state_directories(Lifecycle *lc)
{
    wchar_t path[MAX_PATH_CHARS];
    if (tx_path(lc->game, LC_STATE_DIR L"\\original", path) && tx_no_reparse(path)) {
        lc_release_directory_pin(lc, path); RemoveDirectoryW(path);
    }
    if (tx_path(lc->game, LC_STATE_DIR, path) && tx_no_reparse(path)) {
        lc_release_directory_pin(lc, path); RemoveDirectoryW(path);
    }
}

static bool lc_archive(Lifecycle *lc, const bool conflicts[LC_FILES])
{
    SYSTEMTIME time; GetSystemTime(&time);
    wchar_t name[128], archive[MAX_PATH_CHARS], path[MAX_PATH_CHARS];
    swprintf(name, 128, L"Unofficial Shogun Patch recovery %04u%02u%02u-%02u%02u%02u-%lu",
        time.wYear, time.wMonth, time.wDay, time.wHour, time.wMinute, time.wSecond, (unsigned long)GetCurrentProcessId());
    if (!tx_path(lc->game, name, archive) || !CreateDirectoryW(archive, NULL) || !lc_pin(lc, archive)) return false;
    static const char note[] =
        "Unofficial Shogun Patch removal recovery archive\r\n"
        "These files were preserved after your explicit archive-and-remove choice.\r\n"
        "They were changed since installation or their legacy origin was unknown.\r\n"
        "The original game folder has been restored where an established baseline exists.\r\n"
        "Keep this folder if you need your modified files or old graphics wrapper.\r\n"
        "This archive is not an installed patch and can be copied elsewhere.\r\n\r\n"
        "file-0 = ShogunM.exe\r\n"
        "file-1 = Battle\\batinit\\Historical Battles\\4th Kawanakajima\\4th Kawanakajima.bdf\r\n"
        "file-2 = dgVoodoo.conf\r\nfile-3 = DDraw.dll\r\nfile-4 = D3DImm.dll\r\nfile-5 = D3D9.dll\r\n"
        "file-6 through file-11 = the matching .unofficial-patch.bak sidecars\r\n"
        "file-12 = ShogunM.exe.unofficial-patch.pre-repair.bak\r\n";
    if (!tx_path(archive, L"README.txt", path) || !lc_write_blob(lc, path, note, sizeof(note) - 1)) return false;
    for (int i = 0; i < LC_FILES; ++i) if (conflicts[i]) {
        wchar_t source[MAX_PATH_CHARS]; bool exists = false; char hash[65];
        if (!lc_path(lc->game, i, source) || !lc_hash(source, &exists, hash)) return false;
        if (!exists) continue;
        swprintf(name, 128, L"file-%d", i);
        if (!tx_path(archive, name, path) || !lc_copy(lc, source, path) || !lc_matches(path, 1, hash)) return false;
        fwprintf(stdout, L"archived_file=%ls sha256=%hs\n", path, hash);
    }
    fwprintf(stdout, L"recovery_archive=%ls\n", archive); return true;
}

static int lc_uninstall_conflicts(Lifecycle *lc, bool archive, bool keep_legacy_wrappers)
{
    bool conflicts[LC_FILES] = {false}, any = false;
    unsigned ambiguous_count = 0, changed_count = 0, retained_count = 0;
    for (int i = 0; i < LC_FILES; ++i) {
        LcFile *f = &lc->state.file[i]; if (!f->managed) continue;
        wchar_t path[MAX_PATH_CHARS]; bool exists = false; char hash[65];
        if (!lc_path(lc->game, i, path) || !lc_hash(path, &exists, hash)) return 2;
        lc->preflight_exists[i] = exists; strcpy(lc->preflight_hash[i], hash);
        if (f->ambiguous && keep_legacy_wrappers) {
            /* Explicitly keeping an uncertain legacy wrapper is not a general
               override for executable, data or known-owned file conflicts. */
            f->managed = 0; f->ambiguous = 0; ++retained_count;
            fwprintf(stdout, L"retained_wrapper=%ls reason=explicit_keep_choice\n", path);
            continue;
        }
        bool restored = exists == (f->existed != 0) && (!exists || strcmp(hash, f->original) == 0);
        conflicts[i] = f->ambiguous || (!restored && (!exists || strcmp(hash, f->installed) != 0));
        if (conflicts[i]) {
            any = true;
            if (f->ambiguous) ++ambiguous_count; else ++changed_count;
            fwprintf(stdout, L"conflict=%ls reason=%hs\n", path, f->ambiguous ? "legacy_origin_unknown" : "changed_or_missing_since_installation");
        }
    }
    lc->preflight_bound = true;
    fprintf(stdout, "ambiguous_wrappers=%u changed_files=%u\n", ambiguous_count, changed_count);
    if (ambiguous_count) fprintf(stdout, "conflict=legacy_wrapper_ownership\n");
    if (retained_count) fprintf(stdout, "warning=legacy_wrappers_retained count=%u reason=explicit_keep_choice\n", retained_count);
    if (!any) return 0;
    if (!archive) {
        fprintf(stderr, "error=uninstall_conflicts action=archive_conflicts_and_remove result=4\n"); return 4;
    }
    return lc_archive(lc, conflicts) ? 0 : 2;
}

static bool lc_finish_removed(Lifecycle *lc)
{
    for (int i = 0; i < LC_FILES; ++i) if (lc->state.file[i].managed) {
        wchar_t path[MAX_PATH_CHARS]; LcFile *f = &lc->state.file[i];
        if (!lc_path(lc->game, i, path) || !lc_matches(path, f->existed, f->original)) {
            fwprintf(stderr, L"error=uninstall_restoration_verification path=%ls\n", path); return false;
        }
    }
    if (!lc_registry_delete(lc)) return false;
    wchar_t path[MAX_PATH_CHARS]; bool exists = false; char hash[65];
    if (!lc_path(lc->game, LC_UNINSTALL_INDEX, path) || !lc_hash(path, &exists, hash)) return false;
    if (exists && (strcmp(hash, lc->state.uninstaller) != 0 || !DeleteFileW(path))) {
        /* A denied self-cleanup must still leave both user entry points. */
        bool restored_entry = lc_registry_write(lc, NULL);
        fwprintf(stderr, L"error=uninstaller_cleanup_failed retained=%ls registration_restored=%d\n", path, restored_entry ? 1 : 0);
        return false;
    }
    bool cleaned = true;
    for (int i = 0; i < LC_FILES; ++i) {
        if (!lc_path(lc->game, i + LC_FILES, path) || !lc_hash(path, &exists, hash)) { cleaned = false; continue; }
        if (!exists) continue;
        LcFile *f = &lc->state.file[i];
        if (!f->managed || !f->existed || strcmp(hash, f->original) != 0 || !DeleteFileW(path)) cleaned = false;
    }
    if (cleaned && lc_path(lc->game, LC_STATE_INDEX, path)) {
        lc_checksum(&lc->state, sizeof(lc->state), hash);
        if (!lc_matches(path, 1, hash) || !DeleteFileW(path)) cleaned = false;
    }
    lc_remove_empty_state_directories(lc);
    if (!tx_path(lc->game, LC_STATE_DIR, path) || GetFileAttributesW(path) != INVALID_FILE_ATTRIBUTES) cleaned = false;
    if (!cleaned) fwprintf(stdout, L"warning=completed_removal_diagnostics_retained path=%ls\\%ls\n", lc->game, LC_STATE_DIR);
    fprintf(stdout, "uninstall_restoration=verified registration=removed uninstaller=removed\n");
    return true;
}

static bool lc_stage_uninstall(Lifecycle *lc)
{
    for (int i = 0; i < LC_FILES; ++i) if (lc->state.file[i].managed) {
        wchar_t stage[MAX_PATH_CHARS], original[MAX_PATH_CHARS]; bool exists = false;
        LcFile *f = &lc->state.file[i];
        if (!lc_path(lc->stage, i, stage) || !lc_regular(stage, &exists)) return false;
        if (exists && !DeleteFileW(stage)) return false;
        if (f->existed) {
            if (!lc_path(lc->game, i + LC_FILES, original) || !lc_matches(original, 1, f->original) ||
                !lc_copy(lc, original, stage) || !lc_matches(stage, 1, f->original)) return false;
        }
    }
    lc->state.phase = 2;
    return lc_stage_state(lc);
}

static bool lc_legacy_relative_allowed(const wchar_t *relative, bool directory)
{
    if (directory && (!_wcsicmp(relative, L"stage") || !_wcsicmp(relative, L"rollback"))) return true;
    if (!directory && !_wcsicmp(relative, L"journal.bin")) return true;
    for (int i = 0; i < TX_COUNT; ++i) {
        wchar_t allowed[300];
        swprintf(allowed, 300, L"stage\\%ls", TX_FILES[i]);
        if (!directory && !_wcsicmp(relative, allowed)) return true;
        size_t length = wcslen(relative);
        if (directory && !_wcsnicmp(relative, allowed, length) && allowed[length] == L'\\') return true;
        swprintf(allowed, 300, L"rollback\\%d", i);
        if (!directory && !_wcsicmp(relative, allowed)) return true;
    }
    return false;
}

static bool lc_legacy_tree_known(Lifecycle *lc, const wchar_t *root, const wchar_t *relative)
{
    wchar_t directory[MAX_PATH_CHARS], pattern[MAX_PATH_CHARS];
    if (*relative) { if (!tx_path(root, relative, directory)) return false; }
    else wcscpy(directory, root);
    if (!lc_pin(lc, directory) || !tx_path(directory, L"*", pattern)) return false;
    WIN32_FIND_DATAW item; HANDLE search = FindFirstFileW(pattern, &item);
    if (search == INVALID_HANDLE_VALUE) return false;
    bool ok = true;
    do {
        if (!wcscmp(item.cFileName, L".") || !wcscmp(item.cFileName, L"..")) continue;
        wchar_t child_relative[MAX_PATH_CHARS], child[MAX_PATH_CHARS];
        if (*relative) ok = tx_path(relative, item.cFileName, child_relative);
        else wcscpy(child_relative, item.cFileName);
        bool is_directory = (item.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
        if (!ok || (item.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) ||
            !lc_legacy_relative_allowed(child_relative, is_directory) || !tx_path(root, child_relative, child)) {
            fwprintf(stderr, L"error=legacy_transaction_unrecognized_files retained=%ls action=preserve_this_folder_and_review_recovery_log\n", root);
            ok = false; break;
        }
        if (is_directory) ok = lc_legacy_tree_known(lc, root, child_relative);
        else { bool exists = false; ok = lc_regular(child, &exists) && exists; }
    } while (ok && FindNextFileW(search, &item));
    FindClose(search); return ok;
}

static bool lc_recover_legacy_transaction(Lifecycle *lc)
{
    wchar_t root[MAX_PATH_CHARS], exe[MAX_PATH_CHARS];
    if (!tx_path(lc->game, L".unofficial-patch-transaction", root)) return false;
    if (GetFileAttributesW(root) == INVALID_FILE_ATTRIBUTES) return true;
    if (!lc_legacy_tree_known(lc, root, L"")) return false;
    InstallTransaction *tx = calloc(1, sizeof(*tx)); if (!tx) return false;
    tx->journal_file = INVALID_HANDLE_VALUE;
    lc_inner_context = lc;
    transaction_parent_guard = lc_inner_guard; transaction_release_directory = lc_inner_release;
    bool ok = lc_path(lc->game, 0, exe) && tx_begin(tx, exe);
    if (ok) ok = tx_cleanup(tx);
    transaction_parent_guard = NULL; transaction_release_directory = NULL; lc_inner_context = NULL;
    if (tx->journal_file != INVALID_HANDLE_VALUE) CloseHandle(tx->journal_file);
    free(tx); return ok;
}

static int lifecycle_install(const wchar_t *target, const Selection *selection, const wchar_t *payload, const wchar_t *uninstaller)
{
    Lifecycle *lc = calloc(1, sizeof(*lc)); if (!lc) return 2;
    bool ok = lc_initialize(lc, target);
    wchar_t actual_exe[MAX_PATH_CHARS]; char hash[65];
    if (ok && lc_path(lc->game, 0, actual_exe)) {
        fwprintf(stdout, L"target=%ls\n", actual_exe);
        if (file_sha256(actual_exe, hash)) fprintf(stdout, "before_sha256=%s\n", hash);
    }
    ok = ok && lc_recover(lc) && lc_recover_legacy_transaction(lc) && lc_state_load(lc);
    if (ok && lc->state_exists && lc->state.phase == 2) {
        ok = lc_finish_removed(lc) && lc_state_load(lc);
    }
    bool begun = false, preparing = false;
    if (ok) { preparing = true; begun = lc_begin(lc, true); ok = begun; }
    if (ok) ok = lc_prepare_baselines(lc) && lc_stage_apply(lc, selection, payload) &&
        lc_finish_install_stage(lc, uninstaller) && lc_commit(lc);
    if (!ok && begun) {
        bool rolled_back = lc_rollback(lc);
        if (rolled_back) {
            lc_cleanup_transaction(lc);
            if (!lc->state_exists) lc_remove_empty_state_directories(lc);
        } else fwprintf(stderr, L"error=lifecycle_recovery_needed retained=%ls\n", lc->root);
    } else if (!ok && preparing && lc->transaction_owned) {
        /* Begin/snapshot failure has not changed any live file or registry.
           Remove our incomplete first journal so the old removal path works. */
        lc_cleanup_transaction(lc);
    } else if (ok) {
        if (lc_path(lc->game, 0, actual_exe) && file_sha256(actual_exe, hash)) fprintf(stdout, "after_sha256=%s\n", hash);
        fprintf(stdout, "phase=complete result=0\n");
        fprintf(stdout, "phase=lifecycle_complete operation=install result=0\n");
        fwprintf(stdout, L"registry_key=HKCU32\\%ls\nuninstaller=%ls\\%ls\n", lc->key, lc->display, LC_UNINSTALLER);
        if (!patch_log_failed) lc_cleanup_transaction(lc);
    }
    if (!ok) fprintf(stdout, "phase=failed result=2\n");
    int result = patch_log_failed ? 3 : ok ? 0 : 2;
    lc_close(lc); return result;
}

static int lifecycle_uninstall(const wchar_t *target, bool archive, bool keep_legacy_wrappers)
{
    Lifecycle *lc = calloc(1, sizeof(*lc)); if (!lc) return 2;
    bool ok = lc_initialize(lc, target) && lc_recover(lc) && lc_state_load(lc);
    int result = 2;
    if (ok && !lc->state_exists) { fprintf(stderr, "error=uninstall_state_missing action=run_current_installer_to_adopt\n"); ok = false; }
    if (ok && lc->state.phase == 2) {
        ok = lc_finish_removed(lc);
    } else if (ok) {
        result = lc_uninstall_conflicts(lc, archive, keep_legacy_wrappers);
        if (result) { lc_close(lc); return patch_log_failed ? 3 : result; }
        bool begun = lc_begin(lc, false);
        ok = begun && lc_stage_uninstall(lc) && lc_commit(lc);
        if (!ok && begun) {
            if (lc_rollback(lc)) lc_cleanup_transaction(lc);
            else fwprintf(stderr, L"error=lifecycle_recovery_needed retained=%ls\n", lc->root);
        } else if (!ok && lc->transaction_owned) {
            lc_cleanup_transaction(lc);
        } else if (ok) {
            /* A completed game transaction is a durable removed-state marker.
               Keep the original executable and registration on finalization
               failure so either entry point can retry the remaining cleanup. */
            if (!lc_cleanup_transaction(lc)) ok = false;
            if (ok && !patch_log_failed) ok = lc_finish_removed(lc);
        }
    }
    if (ok) fprintf(stdout, "phase=lifecycle_complete operation=uninstall result=0\n");
    result = patch_log_failed ? 3 : ok ? 0 : 2;
    lc_close(lc); return result;
}

#endif
