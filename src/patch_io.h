/* All helper diagnostics use UTF-8, including redirected installer output. */
#include <stdarg.h>
#include <io.h>
#include <fcntl.h>
#include <errno.h>

static FILE *patch_log_file;
static bool patch_log_failed;
static const char *patch_game_outcome = "none";

static void patch_log_failure(void)
{
    if (patch_log_failed) return;
    DWORD native_error = GetLastError();
    int crt_error = errno;
    patch_log_failed = true;
    /* This fallback deliberately bypasses the failed persistent stream. */
    char message[160];
    int length = snprintf(message, sizeof(message),
        "error=diagnostic_write_failed win32=%lu errno=%d\n",
        (unsigned long)native_error, crt_error);
    if (length > 0) fwrite(message, 1, (size_t)length, stderr);
    fflush(stderr);
}

static int patch_emit(FILE *stream, const char *text, size_t length)
{
    size_t written = fwrite(text, 1, length, stream);
    fflush(stream);
    if (patch_log_file && !patch_log_failed) {
        if (fwrite(text, 1, length, patch_log_file) != length ||
            fflush(patch_log_file) != 0 ||
            !FlushFileBuffers((HANDLE)_get_osfhandle(_fileno(patch_log_file)))) patch_log_failure();
    }
    return written == length ? (int)length : -1;
}

static int patch_fprintf(FILE *stream, const char *format, ...)
{
    va_list args, measure;
    va_start(args, format);
    va_copy(measure, args);
    int length = vsnprintf(NULL, 0, format, measure);
    va_end(measure);
    char *text = length >= 0 ? malloc((size_t)length + 1) : NULL;
    int result = -1;
    if (text) {
        vsnprintf(text, (size_t)length + 1, format, args);
        result = patch_emit(stream, text, (size_t)length);
        free(text);
    }
    va_end(args);
    return result;
}

static int patch_fwprintf(FILE *stream, const wchar_t *format, ...)
{
    va_list args, measure;
    va_start(args, format);
    va_copy(measure, args);
    int length = _vscwprintf(format, measure);
    va_end(measure);
    wchar_t *wide = length >= 0 ? malloc(((size_t)length + 1) * sizeof(wchar_t)) : NULL;
    int result = -1;
    if (wide) {
        _vsnwprintf(wide, (size_t)length + 1, format, args);
        int bytes = WideCharToMultiByte(CP_UTF8, 0, wide, length, NULL, 0, NULL, NULL);
        char *text = bytes > 0 ? malloc((size_t)bytes) : NULL;
        if (text) {
            WideCharToMultiByte(CP_UTF8, 0, wide, length, text, bytes, NULL, NULL);
            result = patch_emit(stream, text, (size_t)bytes);
            free(text);
        }
        free(wide);
    }
    va_end(args);
    return result;
}

#define fprintf patch_fprintf
#define printf(...) patch_fprintf(stdout, __VA_ARGS__)
#define fwprintf patch_fwprintf
