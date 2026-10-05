#ifndef SHOGUN_DGVOODOO_PAYLOAD_H
#define SHOGUN_DGVOODOO_PAYLOAD_H

/* Lifecycle slots: config=2, DDraw=3, D3DImm=4, D3D9=5.
   Only column 0 is a valid installation payload. Older bundled bytes remain
   recognizable during migration, but never prove ownership or an original. */
static const char *const DGVOODOO_HASHES[4][2] = {
    { /* Configured Shogun config: current 2.87.5, previous 2.87.2. */
        "9d7c51e11438522b259a5742bc266187643209d93573d0da0cae2382b5a84dfc",
        "1c2e43ab4296c12cecdaa6d52ba1e95a24cc07f5296717f64e45e5f11dc20cc8"
    },
    {
        "612a24408a090a3c6f3886557fa18034ee742e94ad0a40ebdf854d2816176c2e",
        "81325e9b5c71f544b9a28ae4c375af38e12535e8ac57c8f33b5456a342ae1465"
    },
    {
        "93c534f2d17419ea78f15551f7e0aac78b3c503733a840914fa063708a5afe8e",
        "fbe72ef46ae87dc80f5aeb3d8fc12f97f9d9b2274c4887c70ba65651458d5bf2"
    },
    {
        "6a0ca214784be04b7c8b547105aa9d79acf4dc26c0b6f8702b437ddca54058b2",
        "e36f5c8140eb6d1dc8f35e60ab231c07dfa2eb667f9cc0a909ac2d419de078c6"
    }
};

static const char *dgvoodoo_current_hash(int file_index)
{
    return file_index >= 2 && file_index <= 5 ? DGVOODOO_HASHES[file_index - 2][0] : "";
}

static bool dgvoodoo_known_payload_hash(int file_index, const char *sha256)
{
    if (file_index < 2 || file_index > 5) return false;
    for (size_t i = 0; i < sizeof(DGVOODOO_HASHES[0]) / sizeof(DGVOODOO_HASHES[0][0]); ++i)
        if (strcmp(sha256, DGVOODOO_HASHES[file_index - 2][i]) == 0) return true;
    return false;
}

#endif
