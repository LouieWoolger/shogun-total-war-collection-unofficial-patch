#ifndef SHOGUN_PATCH_IDENTITY_H
#define SHOGUN_PATCH_IDENTITY_H

/* SHA-256 and identity checks use no cryptographic DLL or post-XP API.
   The algorithm below is an original implementation of SHA-256 (FIPS 180-4).
   Include after PatchSpec, patch groups, hex_to_bytes, read_at, write_at,
   and inspect_group_internal. Define PATCH_IDENTITY_SHA_ONLY for vector tests. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef struct {
    uint32_t h[8];
    uint64_t bytes;
    unsigned char block[64];
    size_t used;
} PiSha256;

static uint32_t pi_rotr(uint32_t v, unsigned n)
{
    return (v >> n) | (v << (32U - n));
}

static void pi_sha256_block(PiSha256 *ctx, const unsigned char block[64])
{
    static const uint32_t k[64] = {
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,
        0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,
        0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,
        0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,
        0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,
        0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,
        0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,
        0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,
        0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U
    };
    uint32_t w[64], a,b,c,d,e,f,g,h;
    size_t i;
    for (i=0; i<16; ++i) {
        size_t p=i*4;
        w[i]=((uint32_t)block[p]<<24)|((uint32_t)block[p+1]<<16)|
             ((uint32_t)block[p+2]<<8)|block[p+3];
    }
    for (i=16; i<64; ++i) {
        uint32_t s0=pi_rotr(w[i-15],7)^pi_rotr(w[i-15],18)^(w[i-15]>>3);
        uint32_t s1=pi_rotr(w[i-2],17)^pi_rotr(w[i-2],19)^(w[i-2]>>10);
        w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    a=ctx->h[0];b=ctx->h[1];c=ctx->h[2];d=ctx->h[3];
    e=ctx->h[4];f=ctx->h[5];g=ctx->h[6];h=ctx->h[7];
    for (i=0; i<64; ++i) {
        uint32_t s1=pi_rotr(e,6)^pi_rotr(e,11)^pi_rotr(e,25);
        uint32_t t1=h+s1+((e&f)^((~e)&g))+k[i]+w[i];
        uint32_t s0=pi_rotr(a,2)^pi_rotr(a,13)^pi_rotr(a,22);
        uint32_t t2=s0+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    ctx->h[0]+=a;ctx->h[1]+=b;ctx->h[2]+=c;ctx->h[3]+=d;
    ctx->h[4]+=e;ctx->h[5]+=f;ctx->h[6]+=g;ctx->h[7]+=h;
}

static void pi_sha256_init(PiSha256 *ctx)
{
    static const uint32_t initial[8]={0x6a09e667U,0xbb67ae85U,0x3c6ef372U,
        0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
    memcpy(ctx->h,initial,sizeof(initial));ctx->bytes=0;ctx->used=0;
}

static void pi_sha256_update(PiSha256 *ctx, const unsigned char *bytes, size_t len)
{
    ctx->bytes+=(uint64_t)len;
    while (len) {
        size_t take=64-ctx->used;
        if (take>len) take=len;
        memcpy(ctx->block+ctx->used,bytes,take);
        ctx->used+=take;bytes+=take;len-=take;
        if (ctx->used==64) { pi_sha256_block(ctx,ctx->block);ctx->used=0; }
    }
}

static void pi_sha256_final(PiSha256 *ctx, char output[65])
{
    static const char hex[]="0123456789abcdef";
    uint64_t bits=ctx->bytes*8U;
    size_t i;
    ctx->block[ctx->used++]=0x80;
    if (ctx->used>56) {
        memset(ctx->block+ctx->used,0,64-ctx->used);
        pi_sha256_block(ctx,ctx->block);ctx->used=0;
    }
    memset(ctx->block+ctx->used,0,56-ctx->used);
    for (i=0; i<8; ++i) ctx->block[63-i]=(unsigned char)(bits>>(i*8));
    pi_sha256_block(ctx,ctx->block);
    for (i=0; i<32; ++i) {
        unsigned char v=(unsigned char)(ctx->h[i/4]>>(24-(i%4)*8));
        output[i*2]=hex[v>>4];output[i*2+1]=hex[v&15];
    }
    output[64]='\0';
}

#ifndef PATCH_IDENTITY_SHA_ONLY

static bool file_sha256(const wchar_t *path, char output[65])
{
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,
                            FILE_ATTRIBUTE_NORMAL|FILE_FLAG_SEQUENTIAL_SCAN,NULL);
    unsigned char buffer[32768];DWORD got;PiSha256 ctx;bool ok=true;
    output[0]='\0';
    if (file==INVALID_HANDLE_VALUE) return false;
    pi_sha256_init(&ctx);
    for (;;) {
        if (!ReadFile(file,buffer,sizeof(buffer),&got,NULL)) { ok=false;break; }
        if (!got) break;
        pi_sha256_update(&ctx,buffer,got);
    }
    if (!CloseHandle(file)) ok=false;
    if (ok) pi_sha256_final(&ctx,output);
    return ok;
}

/* Keep the read handle open until all classifiers have finished. This stops
   cooperating Windows file users replacing or writing the input mid-check. */
static HANDLE pi_load_exe(const wchar_t *path, unsigned char **bytes)
{
    LARGE_INTEGER size;DWORD got;
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,
                            FILE_ATTRIBUTE_NORMAL|FILE_FLAG_SEQUENTIAL_SCAN,NULL);
    *bytes=NULL;
    if (file==INVALID_HANDLE_VALUE) return INVALID_HANDLE_VALUE;
    if (!GetFileSizeEx(file,&size) || size.QuadPart!=EXPECTED_EXE_SIZE) {
        CloseHandle(file);return INVALID_HANDLE_VALUE;
    }
    *bytes=(unsigned char *)malloc((size_t)EXPECTED_EXE_SIZE);
    if (!*bytes || !ReadFile(file,*bytes,(DWORD)EXPECTED_EXE_SIZE,&got,NULL) ||
        got!=(DWORD)EXPECTED_EXE_SIZE) {
        free(*bytes);*bytes=NULL;CloseHandle(file);return INVALID_HANDLE_VALUE;
    }
    return file;
}

static bool pi_check_group_bytes(const unsigned char *bytes, const PatchGroup *group)
{
    size_t i;
    for (i=0; i<group->patch_count; ++i) {
        const PatchSpec *spec=&group->patches[i];
        unsigned char *original=NULL,*patched=NULL;
        size_t n=hex_to_bytes(spec->original_hex,&original);
        size_t p=hex_to_bytes(spec->patched_hex,&patched);
        bool ok=n && n==p && spec->offset<=(DWORD)EXPECTED_EXE_SIZE &&
            n<=(size_t)EXPECTED_EXE_SIZE-spec->offset &&
            (!memcmp(bytes+spec->offset,original,n) ||
             !memcmp(bytes+spec->offset,patched,n));
        free(original);free(patched);
        if (!ok) return false;
    }
    return true;
}

static bool current_retraining_fragments(const wchar_t *exe_path)
{
    unsigned char *bytes;HANDLE file=pi_load_exe(exe_path,&bytes);bool ok;
    if (file==INVALID_HANDLE_VALUE) return false;
    ok=pi_check_group_bytes(bytes,&GROUP_RETRAINING_DRAG);
    free(bytes);if (!CloseHandle(file)) ok=false;
    return ok;
}

static bool canonical_clean_identity(const wchar_t *exe_path)
{
    static const char clean_hash[]=
        "4445dcb123d595a9b68fd18a20b98a9f9332f9651474976636cb9ec54f3d16af";
    const PatchGroup *groups[]={&GROUP_AUDIO,&GROUP_UNIT,&GROUP_HARVEST,
        &GROUP_HISTORICAL,&GROUP_AMMO,&GROUP_ODAWARA,&GROUP_ADVISOR,
        &GROUP_RETRAINING_DRAG,&GROUP_SHUTDOWN};
    unsigned char *bytes;HANDLE file=pi_load_exe(exe_path,&bytes);
    bool ok=true;size_t g,i;char hash[65];PiSha256 ctx;
    if (file==INVALID_HANDLE_VALUE) return false;
    for (g=0; ok && g<sizeof(groups)/sizeof(groups[0]); ++g) {
        const PatchGroup *group=groups[g];
        if (!pi_check_group_bytes(bytes,group)) {
            GroupState state=GROUP_UNSUPPORTED;
            /* Older retraining revisions are admitted only as complete exact
               manifests by the existing classifier; arbitrary mixtures fail. */
            if (group!=&GROUP_RETRAINING_DRAG ||
                !inspect_group_internal(exe_path,group,&state,true) ||
                state==GROUP_PARTIAL || state==GROUP_UNSUPPORTED) {
                ok=false;break;
            }
        }
        for (i=0; ok && i<group->patch_count; ++i) {
            const PatchSpec *spec=&group->patches[i];unsigned char *original=NULL;
            size_t n=hex_to_bytes(spec->original_hex,&original);
            if (!n || spec->offset>(DWORD)EXPECTED_EXE_SIZE ||
                n>(size_t)EXPECTED_EXE_SIZE-spec->offset) ok=false;
            else memcpy(bytes+spec->offset,original,n);
            free(original);
        }
    }
    if (ok) {
        pi_sha256_init(&ctx);pi_sha256_update(&ctx,bytes,(size_t)EXPECTED_EXE_SIZE);
        pi_sha256_final(&ctx,hash);ok=!strcmp(hash,clean_hash);
    }
    free(bytes);if (!CloseHandle(file)) ok=false;
    return ok;
}

/* The caller supplies a disposable transaction-stage copy. Validate everything
   before the first write. Never invoke this on an installed executable. */
static bool reset_current_retraining_fragments(const wchar_t *stage_exe)
{
    size_t i;
    if (!canonical_clean_identity(stage_exe) ||
        !current_retraining_fragments(stage_exe)) return false;
    for (i=0; i<GROUP_RETRAINING_DRAG.patch_count; ++i) {
        const PatchSpec *spec=&GROUP_RETRAINING_DRAG.patches[i];
        unsigned char *original=NULL;size_t n=hex_to_bytes(spec->original_hex,&original);
        bool ok=n && write_at(stage_exe,spec->offset,original,n);
        free(original);if (!ok) return false;
    }
    return true;
}
#endif /* PATCH_IDENTITY_SHA_ONLY */
#endif /* SHOGUN_PATCH_IDENTITY_H */
