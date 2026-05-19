# Unofficial Shogun: Total War Collection Patch
[![Downloads](https://img.shields.io/github/downloads/LouieWoolger/shogun-total-war-collection-patch/total?style=for-the-badge)](https://github.com/LouieWoolger/shogun-total-war-collection-patch/releases)
[![Release](https://img.shields.io/github/v/release/LouieWoolger/shogun-total-war-collection-patch?style=for-the-badge)](https://github.com/LouieWoolger/shogun-total-war-collection-patch/releases/latest)
[![Discord](https://img.shields.io/discord/1505490825889579018?style=for-the-badge&logo=discord&label=Discord&color=5865F2)](https://discord.gg/zKbDADqWRC)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5F5F?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/louiewoolger)

An installer for Shogun: Total War Collection on GOG and Steam. It patches your existing game folder and lets you choose the fixes you want.

The installer looks for `ShogunM.exe`, makes a backup when it needs to change a file, and applies the selected options to your own install.

## Included Fixes

Recommended:

- Terrain movement fix - installs dgVoodoo2 to fix terrain-click unit movement and drag-formation issues on modern Windows. Not available on Windows XP.
- Historical campaign fix - fixes a crash that can happen in certain battles when reinforcements arrive.
- Throne room audio fix - fixes throne-room speech cutting out before the line has finished.
- Recruitment, upkeep & training fix - stops 120-man battle unit size from doubling recruitment cost, upkeep cost, and training time for every unit.

Optional:

- Harvest report audio restoration - restores the original voice clips that play at the annual harvest report. Requires the throne room audio fix.

## Requirements

- Windows XP through Windows 11
- Shogun: Total War Collection from GOG or Steam
- A game folder containing `ShogunM.exe`

The terrain movement fix is for modern Windows and is not available on Windows XP.

## Usage

Download the latest installer from the [Releases](https://github.com/LouieWoolger/shogun-total-war-collection-patch/releases/latest) page.

Run:

```text
Unofficial Shogun Total War Collection Patch.exe
```

The installer will try to find your Steam or GOG install automatically. If it picks the wrong folder, browse to the folder that contains `ShogunM.exe`.

Recommended options are selected by default. The harvest report audio restoration is optional because it restores removed audio rather than fixing a crash or major gameplay bug.

## Backups

When the installer changes a file, it creates a `.unofficial-patch.bak` backup beside that file. Existing backups are preserved.

To restore manually, close the game, delete or rename the patched file, then rename the matching `.unofficial-patch.bak` file back to its original filename.

## Notes

This repository is the combined installer version of these fixes:

- [Throne room audio fix](https://github.com/LouieWoolger/shogun-total-war-throne-room-audio-fix)
- [Recruitment, upkeep & training fix](https://github.com/LouieWoolger/shogun-total-war-unit-cost-training-upkeep-fix)
- [Harvest report voice fix](https://github.com/LouieWoolger/shogun-total-war-harvest-report-voice-fix)
- [Historical campaign reinforcement fix](https://github.com/LouieWoolger/shogun-total-war-historical-campaign-reinforcement-fix)

The installer also includes dgVoodoo2 for the terrain movement option.

## Building from Source

Build requirements:

- Python 3.9 or newer
- NSIS 3.11 or newer
- w64devkit, or another MinGW-w64 toolchain that provides `i686-w64-mingw32` GCC and `windres.exe`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The installer is written to `dist\Unofficial Shogun Total War Collection Patch.exe`.
