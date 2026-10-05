/* File replacements are prepared on the same volume, verified, then committed.
   A flushed journal records each replacement intent before the target changes. */
#define TX_COUNT 13
#define TX_MAGIC 0x53475054u
#define TX_VERSION 2u
typedef struct {
    DWORD selected, existed, changed, started;
    char before[65], after[65];
} TxEntry;
typedef struct {
    DWORD magic, version, complete;
    TxEntry entries[TX_COUNT];
    char checksum[65];
} TxJournal;
typedef struct {
    wchar_t game[MAX_PATH_CHARS], root[MAX_PATH_CHARS], stage[MAX_PATH_CHARS];
    HANDLE journal_file;
    TxJournal journal;
} InstallTransaction;

static InstallTransaction *patch_completed_transaction;
/* A lifecycle caller can pin parents in its outer stage without changing the
   historical standalone helper contract. */
static bool (*transaction_parent_guard)(const wchar_t *, bool);
static void (*transaction_release_directory)(const wchar_t *);

static const wchar_t *TX_FILES[TX_COUNT] = {
    EXE_NAME, KAWANAKAJIMA_BDF_RELATIVE_PATH, DGVOODOO_CONF_RELATIVE_PATH,
    L"DDraw.dll", L"D3DImm.dll", L"D3D9.dll",
    L"ShogunM.exe.unofficial-patch.bak",
    KAWANAKAJIMA_BDF_RELATIVE_PATH L".unofficial-patch.bak",
    L"dgVoodoo.conf.unofficial-patch.bak", L"DDraw.dll.unofficial-patch.bak",
    L"D3DImm.dll.unofficial-patch.bak", L"D3D9.dll.unofficial-patch.bak",
    L"ShogunM.exe.unofficial-patch.pre-repair.bak"
};

static bool tx_path(const wchar_t *root, const wchar_t *relative, wchar_t *out)
{
    if (wcslen(root) + wcslen(relative) + 2 >= MAX_PATH_CHARS) {
        fprintf(stderr, "error=transaction_path_too_long\n");
        return false;
    }
    wcscpy(out, root);
    return append_path(out, MAX_PATH_CHARS, L"\\") && append_path(out, MAX_PATH_CHARS, relative);
}

static bool tx_no_reparse(const wchar_t *path)
{
    wchar_t copy[MAX_PATH_CHARS];
    if (wcslen(path) >= MAX_PATH_CHARS) return false;
    wcscpy(copy, path);
    for (;;) {
        DWORD attrs = GetFileAttributesW(copy);
        if (attrs != INVALID_FILE_ATTRIBUTES && (attrs & FILE_ATTRIBUTE_REPARSE_POINT)) {
            fwprintf(stderr, L"error=transaction_reparse_path path=%ls\n", copy);
            return false;
        }
        wchar_t *slash = wcsrchr(copy, L'\\');
        if (!slash || slash <= copy + 2) break;
        *slash = 0;
    }
    return true;
}

static bool tx_regular(const wchar_t *path, bool *exists)
{
    if (transaction_parent_guard && !transaction_parent_guard(path, false)) return false;
    if (!tx_no_reparse(path)) return false;
    DWORD attrs = GetFileAttributesW(path);
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        DWORD error = GetLastError();
        if (error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND) {
            *exists = false;
            return true;
        }
        print_last_error(L"transaction_stat_failed", path);
        return false;
    }
    if (attrs & FILE_ATTRIBUTE_DIRECTORY) {
        fwprintf(stderr, L"error=transaction_not_regular path=%ls\n", path);
        return false;
    }
    *exists = true;
    return true;
}

static bool tx_log_safe(const wchar_t *log_path, const wchar_t *target)
{
    wchar_t log_full[MAX_PATH_CHARS], game[MAX_PATH_CHARS];
    DWORD length = GetFullPathNameW(log_path, MAX_PATH_CHARS, log_full, NULL);
    if (!length || length >= MAX_PATH_CHARS || !tx_no_reparse(log_full)) return false;
    if (!target) return true;
    length = GetFullPathNameW(target, MAX_PATH_CHARS, game, NULL);
    if (!length || length >= MAX_PATH_CHARS) return false;
    wchar_t *paths[] = {log_full, game};
    for (int i = 0; i < 2; ++i) {
        wchar_t *path = paths[i];
        if (wcsncmp(path, L"\\\\?\\UNC\\", 8) == 0) {
            memmove(path + 2, path + 8, (wcslen(path + 8) + 1) * sizeof(wchar_t));
            path[0] = path[1] = L'\\';
        } else if (wcsncmp(path, L"\\\\?\\", 4) == 0) {
            memmove(path, path + 4, (wcslen(path + 4) + 1) * sizeof(wchar_t));
        }
    }
    wchar_t *name = wcsrchr(game, L'\\');
    if (name && _wcsicmp(name + 1, EXE_NAME) == 0) *name = 0;
    while (wcslen(game) > 3 && game[wcslen(game) - 1] == L'\\') game[wcslen(game) - 1] = 0;
    size_t game_length = wcslen(game);
    if (_wcsnicmp(log_full, game, game_length) == 0 &&
        (log_full[game_length] == 0 || log_full[game_length] == L'\\')) return false;
    /* Directory IDs also cover 8.3 aliases for a not-yet-created log file. */
    HANDLE game_handle = CreateFileW(game, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                    NULL, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, NULL);
    BY_HANDLE_FILE_INFORMATION game_info;
    if (game_handle != INVALID_HANDLE_VALUE) {
        bool identified = GetFileInformationByHandle(game_handle, &game_info) != FALSE;
        CloseHandle(game_handle);
        if (!identified) return false;
        wchar_t parent[MAX_PATH_CHARS];
        wcscpy(parent, log_full);
        wchar_t *separator;
        while ((separator = wcsrchr(parent, L'\\')) != NULL && separator > parent + 2) {
            *separator = 0;
            HANDLE directory = CreateFileW(parent, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                          NULL, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, NULL);
            if (directory != INVALID_HANDLE_VALUE) {
                BY_HANDLE_FILE_INFORMATION info;
                bool inside = GetFileInformationByHandle(directory, &info) &&
                    info.dwVolumeSerialNumber == game_info.dwVolumeSerialNumber &&
                    info.nFileIndexHigh == game_info.nFileIndexHigh && info.nFileIndexLow == game_info.nFileIndexLow;
                CloseHandle(directory);
                if (inside) return false;
            }
        }
    }
    HANDLE log_handle = CreateFileW(log_full, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                   NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    BY_HANDLE_FILE_INFORMATION log_info;
    bool log_exists = log_handle != INVALID_HANDLE_VALUE;
    if (log_exists && (!GetFileInformationByHandle(log_handle, &log_info) || log_info.nNumberOfLinks != 1)) {
        CloseHandle(log_handle);
        return false;
    }
    bool safe = true;
    for (int i = 0; i < TX_COUNT && safe; ++i) {
        wchar_t protected_path[MAX_PATH_CHARS];
        if (!tx_path(game, TX_FILES[i], protected_path)) { safe = false; break; }
        if (_wcsicmp(log_full, protected_path) == 0) { safe = false; break; }
        if (log_exists) {
            HANDLE file = CreateFileW(protected_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                     NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
            if (file != INVALID_HANDLE_VALUE) {
                BY_HANDLE_FILE_INFORMATION info;
                if (GetFileInformationByHandle(file, &info) && info.dwVolumeSerialNumber == log_info.dwVolumeSerialNumber &&
                    info.nFileIndexHigh == log_info.nFileIndexHigh && info.nFileIndexLow == log_info.nFileIndexLow) safe = false;
                CloseHandle(file);
            }
        }
    }
    wchar_t transaction_root[MAX_PATH_CHARS];
    if (tx_path(game, L".unofficial-patch-transaction", transaction_root)) {
        size_t n = wcslen(transaction_root);
        if (_wcsnicmp(log_full, transaction_root, n) == 0 && (log_full[n] == 0 || log_full[n] == L'\\')) safe = false;
    } else safe = false;
    if (log_exists) CloseHandle(log_handle);
    return safe;
}

static bool tx_parents(const wchar_t *path)
{
    wchar_t copy[MAX_PATH_CHARS];
    wcscpy(copy, path);
    wchar_t *start = copy + 3;
    if (wcsncmp(copy, L"\\\\?\\UNC\\", 8) == 0) {
        start = wcschr(copy + 8, L'\\');
        if (start) start = wcschr(start + 1, L'\\');
        if (!start) return false;
        ++start;
    } else if (wcsncmp(copy, L"\\\\?\\", 4) == 0) start = copy + 7;
    for (wchar_t *p = start; *p; ++p) {
        if (*p == L'\\') {
            *p = 0;
            BOOL created = CreateDirectoryW(copy, NULL);
            DWORD error = GetLastError();
            *p = L'\\';
            if (!created && error != ERROR_ALREADY_EXISTS) return false;
        }
    }
    return true;
}

static bool tx_flush_copy(const wchar_t *source, const wchar_t *destination)
{
    if (transaction_parent_guard && (!transaction_parent_guard(source, false) ||
        !transaction_parent_guard(destination, true))) return false;
    if (!tx_parents(destination) || !CopyFileW(source, destination, TRUE)) {
        print_last_error(L"transaction_copy_failed", destination);
        return false;
    }
    /* Clearing attributes affects only the task-owned snapshot/stage. */
    SetFileAttributesW(destination, FILE_ATTRIBUTE_NORMAL);
    HANDLE file = CreateFileW(destination, GENERIC_WRITE, FILE_SHARE_READ,
                              NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return false;
    BOOL ok = FlushFileBuffers(file);
    CloseHandle(file);
    return ok != FALSE;
}

static bool tx_save(InstallTransaction *tx)
{
    LARGE_INTEGER zero;
    zero.QuadPart = 0;
    DWORD written = 0;
    PiSha256 checksum;
    pi_sha256_init(&checksum);
    pi_sha256_update(&checksum, (const unsigned char *)&tx->journal, offsetof(TxJournal, checksum));
    pi_sha256_final(&checksum, tx->journal.checksum);
    if (!SetFilePointerEx(tx->journal_file, zero, NULL, FILE_BEGIN) ||
        !WriteFile(tx->journal_file, &tx->journal, sizeof(tx->journal), &written, NULL) ||
        written != sizeof(tx->journal) || !FlushFileBuffers(tx->journal_file)) {
        print_last_error(L"transaction_journal_failed", tx->root);
        return false;
    }
    return true;
}

static bool tx_hash_valid(const char hash[65])
{
    if (hash[64] != 0) return false;
    for (int i = 0; i < 64; ++i) {
        if (!((hash[i] >= '0' && hash[i] <= '9') || (hash[i] >= 'a' && hash[i] <= 'f'))) return false;
    }
    return true;
}

static bool tx_journal_valid(const TxJournal *journal)
{
    if (journal->magic != TX_MAGIC || journal->version != TX_VERSION || journal->complete > 2 ||
        !tx_hash_valid(journal->checksum)) return false;
    PiSha256 checksum;
    char hash[65];
    pi_sha256_init(&checksum);
    pi_sha256_update(&checksum, (const unsigned char *)journal, offsetof(TxJournal, checksum));
    pi_sha256_final(&checksum, hash);
    if (strcmp(hash, journal->checksum) != 0) return false;
    for (int i = 0; i < TX_COUNT; ++i) {
        const TxEntry *entry = &journal->entries[i];
        if (entry->selected > 1 || entry->existed > 1 || entry->changed > 1 || entry->started > 1 ||
            entry->before[64] != 0 || entry->after[64] != 0 ||
            (entry->started && (!entry->selected || !entry->changed)) ||
            (entry->changed && (!entry->selected || !tx_hash_valid(entry->after))) ||
            (entry->changed && entry->existed && !tx_hash_valid(entry->before))) return false;
    }
    return true;
}

static bool tx_completed_targets_valid(InstallTransaction *tx)
{
    for (int i = 0; i < TX_COUNT; ++i) {
        const TxEntry *entry = &tx->journal.entries[i];
        if (!entry->changed) continue;
        wchar_t live[MAX_PATH_CHARS];
        bool exists;
        char hash[65];
        if (!tx_path(tx->game, TX_FILES[i], live) || !tx_regular(live, &exists) || !exists ||
            !file_sha256(live, hash) || strcmp(hash, entry->after) != 0) {
            fwprintf(stderr, L"error=completed_transaction_target_mismatch retained=%ls\n", tx->root);
            return false;
        }
    }
    return true;
}

static bool tx_remove_tree(const wchar_t *path)
{
    if (!tx_no_reparse(path)) return false;
    wchar_t pattern[MAX_PATH_CHARS];
    if (!tx_path(path, L"*", pattern)) return false;
    WIN32_FIND_DATAW data;
    HANDLE search = FindFirstFileW(pattern, &data);
    if (search == INVALID_HANDLE_VALUE) {
        if (transaction_release_directory) transaction_release_directory(path);
        return RemoveDirectoryW(path) != FALSE;
    }
    bool ok = true;
    do {
        if (wcscmp(data.cFileName, L".") == 0 || wcscmp(data.cFileName, L"..") == 0) continue;
        wchar_t child[MAX_PATH_CHARS];
        if (!tx_path(path, data.cFileName, child) || (data.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) {
            ok = false;
            break;
        }
        if (data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            if (!tx_remove_tree(child)) ok = false;
        } else if (!DeleteFileW(child)) ok = false;
    } while (FindNextFileW(search, &data));
    FindClose(search);
    if (transaction_release_directory) transaction_release_directory(path);
    return ok && RemoveDirectoryW(path) != FALSE;
}

static bool tx_cleanup(InstallTransaction *tx)
{
    if (tx->journal_file != INVALID_HANDLE_VALUE) {
        CloseHandle(tx->journal_file);
        tx->journal_file = INVALID_HANDLE_VALUE;
    }
    return tx_remove_tree(tx->root);
}

static bool tx_rollback(InstallTransaction *tx)
{
    fprintf(stderr, "phase=rollback\n");
    /* A failed final journal flush must never leave a terminal-success state
       while restoration is underway. Persist rollback intent first. */
    tx->journal.complete = 2;
    if (!tx_save(tx)) return false;
    bool had_intent = false;
    for (int i = 0; i < TX_COUNT; ++i) if (tx->journal.entries[i].started) had_intent = true;
    /* Validate every changed target before restoring any, so an unrelated
       post-crash edit is preserved and receives an explicit recovery error. */
    for (int i = 0; i < TX_COUNT; ++i) {
        TxEntry *entry = &tx->journal.entries[i];
        if (!entry->started) continue;
        wchar_t live[MAX_PATH_CHARS];
        bool exists;
        if (!tx_path(tx->game, TX_FILES[i], live) || !tx_regular(live, &exists)) return false;
        char hash[65];
        if (exists && (!file_sha256(live, hash) ||
            (strcmp(hash, entry->before) != 0 && strcmp(hash, entry->after) != 0))) {
            fwprintf(stderr, L"error=transaction_recovery_target_changed path=%ls journal=%ls\n", live, tx->root);
            return false;
        }
        if (!exists && entry->existed) {
            fwprintf(stderr, L"error=transaction_recovery_target_missing path=%ls\n", live);
            return false;
        }
    }
    for (int i = TX_COUNT - 1; i >= 0; --i) {
        TxEntry *entry = &tx->journal.entries[i];
        if (!entry->started) continue;
        wchar_t live[MAX_PATH_CHARS], rollback[MAX_PATH_CHARS], index[32];
        swprintf(index, 32, L"rollback\\%d", i);
        if (!tx_path(tx->game, TX_FILES[i], live) || !tx_path(tx->root, index, rollback)) return false;
        bool exists;
        if (!tx_regular(live, &exists)) return false;
        if (entry->existed) {
            char hash[65];
            /* A crash after restoration but before journaling may have
               consumed this snapshot already.  Its exact original hash is
               sufficient to finish the remaining recovery safely. */
            if (exists && file_sha256(live, hash) && strcmp(hash, entry->before) == 0) {
                entry->started = 0;
                if (!tx_save(tx)) return false;
                continue;
            }
            if (!file_sha256(rollback, hash) || strcmp(hash, entry->before) != 0 ||
                !(exists ? ReplaceFileW(live, rollback, NULL, 0, NULL, NULL)
                          : MoveFileExW(rollback, live, MOVEFILE_WRITE_THROUGH))) {
                print_last_error(L"transaction_restore_failed", live);
                return false;
            }
        } else if (exists && !DeleteFileW(live)) {
            print_last_error(L"transaction_remove_failed", live);
            return false;
        }
        entry->started = 0;
        if (!tx_save(tx)) return false;
    }
    fprintf(stderr, "rollback=complete\n");
    if (had_intent) patch_game_outcome = "rolled_back";
    return true;
}

static bool tx_begin(InstallTransaction *tx, const wchar_t *exe_path)
{
    tx->journal_file = INVALID_HANDLE_VALUE;
    wcscpy(tx->game, exe_path);
    wchar_t *slash = wcsrchr(tx->game, L'\\');
    if (!slash) return false;
    *slash = 0;
    if (!tx_no_reparse(tx->game) || !tx_path(tx->game, L".unofficial-patch-transaction", tx->root) ||
        !tx_path(tx->root, L"stage", tx->stage)) return false;
    wchar_t journal_path[MAX_PATH_CHARS];
    if (!tx_path(tx->root, L"journal.bin", journal_path)) return false;
    if (!CreateDirectoryW(tx->root, NULL)) {
        if (GetLastError() != ERROR_ALREADY_EXISTS || !tx_no_reparse(tx->root)) return false;
        bool journal_exists;
        if (!tx_regular(journal_path, &journal_exists) || !journal_exists) return false;
        tx->journal_file = CreateFileW(journal_path, GENERIC_READ | GENERIC_WRITE, 0,
                                      NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        DWORD read = 0;
        LARGE_INTEGER size;
        if (tx->journal_file == INVALID_HANDLE_VALUE ||
            !ReadFile(tx->journal_file, &tx->journal, sizeof(tx->journal), &read, NULL) ||
            read != sizeof(tx->journal) || !GetFileSizeEx(tx->journal_file, &size) ||
            size.QuadPart != sizeof(tx->journal) || !tx_journal_valid(&tx->journal)) {
            fwprintf(stderr, L"error=unfinished_transaction_unreadable journal=%ls\n", journal_path);
            return false;
        }
        fwprintf(stderr, L"phase=recover journal=%ls\n", journal_path);
        if (tx->journal.complete == 1) {
            if (!tx_completed_targets_valid(tx)) return false;
        } else if (!tx_rollback(tx)) return false;
        if (!tx_cleanup(tx) || !CreateDirectoryW(tx->root, NULL)) return false;
    }
    memset(&tx->journal, 0, sizeof(tx->journal));
    tx->journal.magic = TX_MAGIC;
    tx->journal.version = TX_VERSION;
    if (transaction_parent_guard && !transaction_parent_guard(journal_path, false)) return false;
    tx->journal_file = CreateFileW(journal_path, GENERIC_READ | GENERIC_WRITE, 0,
                                  NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (tx->journal_file == INVALID_HANDLE_VALUE || !tx_save(tx)) return false;
    return CreateDirectoryW(tx->stage, NULL) != FALSE;
}

static bool tx_snapshot(InstallTransaction *tx, int index)
{
    TxEntry *entry = &tx->journal.entries[index];
    wchar_t live[MAX_PATH_CHARS], staged[MAX_PATH_CHARS], rollback[MAX_PATH_CHARS], number[32];
    bool exists;
    if (!tx_path(tx->game, TX_FILES[index], live) || !tx_path(tx->stage, TX_FILES[index], staged) ||
        !tx_regular(live, &exists)) return false;
    entry->existed = exists;
    if (!exists) return true;
    if (index >= 6 && index <= 11) {
        WIN32_FILE_ATTRIBUTE_DATA info;
        if (!GetFileAttributesExW(live, GetFileExInfoStandard, &info) ||
            (info.nFileSizeHigh == 0 && info.nFileSizeLow == 0) ||
            (index == 6 && (info.nFileSizeHigh != 0 || info.nFileSizeLow != EXPECTED_EXE_SIZE))) {
            fwprintf(stderr, L"error=invalid_backup path=%ls reason=unexpected_size\n", live);
            return false;
        }
    }
    if (!file_sha256(live, entry->before)) return false;
    swprintf(number, 32, L"rollback\\%d", index);
    if (!tx_path(tx->root, number, rollback) || !tx_flush_copy(live, rollback) ||
        !tx_flush_copy(live, staged)) return false;
    char hash[65];
    if (!file_sha256(rollback, hash) || strcmp(hash, entry->before) != 0 ||
        !file_sha256(staged, hash) || strcmp(hash, entry->before) != 0) {
        fwprintf(stderr, L"error=transaction_snapshot_changed path=%ls\n", live);
        return false;
    }
    return true;
}

static bool tx_payload(InstallTransaction *tx, const wchar_t *payload)
{
    static const int indexes[] = {3, 4, 5, 2};
    /* Validate the complete bundled payload before staging any wrapper. */
    for (int j = 0; j < 4; ++j) {
        wchar_t source[MAX_PATH_CHARS];
        bool exists;
        char hash[65];
        if (!tx_path(payload, TX_FILES[indexes[j]], source) || !tx_regular(source, &exists) || !exists ||
            !file_sha256(source, hash) || strcmp(hash, dgvoodoo_current_hash(indexes[j])) != 0) {
            fwprintf(stderr, L"error=invalid_payload file=%ls\n", TX_FILES[indexes[j]]);
            return false;
        }
    }
    for (int j = 0; j < 4; ++j) {
        int i = indexes[j];
        wchar_t source[MAX_PATH_CHARS], staged[MAX_PATH_CHARS];
        if (!tx_path(payload, TX_FILES[i], source) || !tx_path(tx->stage, TX_FILES[i], staged)) return false;
        if (tx->journal.entries[i].existed && strcmp(tx->journal.entries[i].before, dgvoodoo_current_hash(i)) != 0 &&
            !ensure_backup(staged, SHARED_BACKUP_SUFFIX)) return false;
        if (file_exists(staged) && !DeleteFileW(staged)) return false;
        if (!tx_flush_copy(source, staged)) return false;
    }
    return true;
}

static bool tx_commit(InstallTransaction *tx)
{
    fprintf(stdout, "phase=commit\n");
    if (patch_log_failed) return false;
    for (int i = 0; i < TX_COUNT; ++i) {
        TxEntry *entry = &tx->journal.entries[i];
        if (!entry->selected) continue;
        wchar_t staged[MAX_PATH_CHARS], live[MAX_PATH_CHARS];
        bool exists;
        if (!tx_path(tx->stage, TX_FILES[i], staged) || !tx_path(tx->game, TX_FILES[i], live) ||
            !tx_regular(staged, &exists)) return false;
        if (!exists) continue;
        if (!file_sha256(staged, entry->after)) return false;
        entry->changed = !entry->existed || strcmp(entry->before, entry->after) != 0;
        if (!entry->changed) continue;
        char current[65];
        if (!tx_regular(live, &exists) || exists != (entry->existed != 0) ||
            (exists && (!file_sha256(live, current) || strcmp(current, entry->before) != 0))) {
            fwprintf(stderr, L"error=transaction_target_changed path=%ls\n", live);
            return false;
        }
        if (exists && !check_write_access(live)) return false;
    }
    if (!tx_save(tx)) return false;
    /* Commit backup sidecars before target content: every changed executable
       always has its recoverable backup on disk before its first replacement. */
    for (int n = 0; n < TX_COUNT; ++n) {
        int i = n < 7 ? n + 6 : n - 7;
        TxEntry *entry = &tx->journal.entries[i];
        if (!entry->changed) continue;
        wchar_t staged[MAX_PATH_CHARS], live[MAX_PATH_CHARS];
        if (!tx_path(tx->stage, TX_FILES[i], staged) || !tx_path(tx->game, TX_FILES[i], live)) return false;
        bool exists;
        char current[65];
        if (!tx_regular(live, &exists) || exists != (entry->existed != 0) ||
            (exists && (!file_sha256(live, current) || strcmp(current, entry->before) != 0))) {
            fwprintf(stderr, L"error=transaction_target_changed path=%ls\n", live);
            return false;
        }
        entry->started = 1;
        if (!tx_save(tx)) return false;
        if (!(entry->existed ? ReplaceFileW(live, staged, NULL, 0, NULL, NULL)
                            : MoveFileExW(staged, live, MOVEFILE_WRITE_THROUGH))) {
            print_last_error(L"transaction_commit_failed", live);
            return false;
        }
        fprintf(stdout, "transaction_committed_file=%d\n", i);
        patch_game_outcome = "pending";
    }
    tx->journal.complete = 1;
    bool ok = tx_save(tx);
    if (ok && strcmp(patch_game_outcome, "pending") == 0) patch_game_outcome = "committed";
    return ok;
}

static bool apply_transaction(const wchar_t *exe_path, const Selection *selection, const wchar_t *payload)
{
    if (patch_log_failed) return false;
    InstallTransaction *tx = calloc(1, sizeof(*tx));
    if (!tx) return false;
    bool begun = tx_begin(tx, exe_path);
    if (!begun) {
        fwprintf(stderr, L"error=transaction_begin_failed path=%ls\n", tx->root);
        if (tx->journal_file != INVALID_HANDLE_VALUE) CloseHandle(tx->journal_file);
        free(tx);
        return false;
    }
    fprintf(stdout, "phase=stage\n");
    tx->journal.entries[0].selected = 1;
    tx->journal.entries[1].selected = selection->kawanakajima;
    tx->journal.entries[2].selected = selection->dgvoodoo_resolution || payload != NULL;
    tx->journal.entries[6].selected = selection->shutdown || selection->historical || selection->retraining_drag || selection->throne ||
        selection->unit || selection->harvest || selection->ammo || selection->advisor || selection->odawara;
    tx->journal.entries[7].selected = selection->kawanakajima;
    tx->journal.entries[8].selected = selection->dgvoodoo_resolution || payload != NULL;
    for (int i = 3; i < 6; ++i) {
        tx->journal.entries[i].selected = payload != NULL;
        tx->journal.entries[i + 6].selected = payload != NULL;
    }
    bool ok = !patch_log_failed;
    for (int i = 0; i < TX_COUNT && ok; ++i) {
        if (tx->journal.entries[i].selected) ok = tx_snapshot(tx, i);
    }
    wchar_t staged_exe[MAX_PATH_CHARS];
    ok = ok && tx_path(tx->stage, EXE_NAME, staged_exe);
    if (ok && selection->retraining_drag) {
        GroupState state;
        ok = inspect_group(staged_exe, &GROUP_RETRAINING_DRAG, &state);
        if (ok && state == GROUP_PARTIAL) {
            if (!current_retraining_fragments(staged_exe) || !canonical_clean_identity(staged_exe)) {
                fprintf(stderr, "error=partial_state group=retraining-drag reason=unrecognized_executable\n");
                ok = false;
            } else {
                tx->journal.entries[12].selected = 1;
                ok = tx_snapshot(tx, 12);
                wchar_t repair_backup[MAX_PATH_CHARS];
                char current[65], existing[65];
                if (ok) ok = tx_path(tx->stage, TX_FILES[12], repair_backup) && file_sha256(staged_exe, current);
                if (ok && file_exists(repair_backup)) {
                    ok = file_sha256(repair_backup, existing) && strcmp(existing, current) == 0;
                    if (!ok) fprintf(stderr, "error=pre_repair_backup_conflict\n");
                } else if (ok) {
                    ok = tx_flush_copy(staged_exe, repair_backup);
                    if (ok) fwprintf(stdout, L"pre_repair_backup_created=%ls\n", repair_backup);
                }
                if (ok) ok = ensure_backup(staged_exe, SHARED_BACKUP_SUFFIX) &&
                             reset_current_retraining_fragments(staged_exe);
                if (ok) fprintf(stdout, "repair=recognized_current_fragments identity=canonical_clean\n");
            }
        }
    }
    if (ok && payload) ok = tx_payload(tx, payload);
    if (ok) ok = apply_selected(staged_exe, selection);
    if (patch_log_failed) ok = false;
    if (ok) ok = tx_commit(tx);
    if (!ok && !tx_rollback(tx)) {
        patch_game_outcome = "recovery_needed";
        fwprintf(stderr, L"error=transaction_rollback_incomplete retained=%ls\n", tx->root);
        CloseHandle(tx->journal_file);
        free(tx);
        return false;
    }
    if (ok) {
        /* Retain the completed journal through the caller's final diagnostic
           flush.  A diagnostic failure must not discard recovery evidence. */
        patch_completed_transaction = tx;
        return true;
    }
    if (!tx_cleanup(tx)) fwprintf(stderr, L"warning=transaction_cleanup_pending path=%ls\n", tx->root);
    free(tx);
    return ok;
}

static void tx_finish_diagnostics(void)
{
    InstallTransaction *tx = patch_completed_transaction;
    if (!tx) return;
    if (patch_log_failed) {
        fwprintf(stderr, L"error=diagnostic_write_failed game_changes=%hs retained=%ls\n", patch_game_outcome, tx->root);
        CloseHandle(tx->journal_file);
    } else if (!tx_cleanup(tx)) {
        fwprintf(stderr, L"warning=transaction_cleanup_pending path=%ls\n", tx->root);
    }
    free(tx);
    patch_completed_transaction = NULL;
}
