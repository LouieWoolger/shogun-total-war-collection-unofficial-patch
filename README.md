# Unofficial Shogun: Total War Collection Patch
[![Downloads](https://img.shields.io/github/downloads/LouieWoolger/shogun-total-war-collection-unofficial-patch/total?style=for-the-badge)](https://github.com/LouieWoolger/shogun-total-war-collection-unofficial-patch/releases)
[![Release](https://img.shields.io/github/v/release/LouieWoolger/shogun-total-war-collection-unofficial-patch?style=for-the-badge)](https://github.com/LouieWoolger/shogun-total-war-collection-unofficial-patch/releases/latest)
[![Discord](https://img.shields.io/discord/1505490825889579018?style=for-the-badge&logo=discord&label=Discord&color=5865F2)](https://discord.gg/zKbDADqWRC)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5F5F?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/louiewoolger)

An installer for Shogun: Total War Collection on GOG and Steam. It patches your existing game folder and lets you choose the fixes you want.

The installer looks for `ShogunM.exe`, makes a backup when it needs to change a file, and applies the selected options to your own install.

## Included Fixes

Recommended:

- Terrain Movement Fix - installs dgVoodoo2 to fix click-to-move and drag-formation issues on modern Windows systems. Windows XP is not supported.
- Historical Campaigns Crash Fix - fixes crashes in certain historical campaign battles when timed reinforcements arrive.
- Voice Audio Fix - fixes voice clips cutting out across the game, including throne room dialogue, and other spoken lines.
- Limited Ammo Fix - fixes a bug where ammunition remains limited in campaign and historical battles even when the limited ammo setting is disabled.

Optional:

- 120-Man Unit Balance Fix - rebalances 120-man unit sizes so recruitment cost, upkeep cost, and training time remain consistent with the 60-man unit size setting.
- Annual Harvest Report Audio Restoration - restores the original voice clips heard during the annual harvest report. Requires the voice audio fix.

## Requirements

- Windows XP through Windows 11
- Shogun: Total War Collection from GOG or Steam
- A game folder containing `ShogunM.exe`

The Terrain Movement Fix is for modern Windows systems. Windows XP is not supported.

## Usage

Download the latest installer from the [Releases](https://github.com/LouieWoolger/shogun-total-war-collection-unofficial-patch/releases/latest) page.

Run:

```text
Unofficial Shogun Total War Collection Patch.exe
```

The installer will try to find your Steam or GOG install automatically. If it picks the wrong folder, browse to the folder that contains `ShogunM.exe`.

Recommended options are selected by default. 120-Man Unit Balance Fix and Annual Harvest Report Audio Restoration are optional.

## Backups

When the installer changes a file, it creates a `.unofficial-patch.bak` backup beside that file. Existing backups are preserved.

To restore manually, close the game, delete or rename the patched file, then rename the matching `.unofficial-patch.bak` file back to its original filename.

## Notes

This repository is the combined installer version of these fixes:

- [Voice Audio Fix](https://github.com/LouieWoolger/shogun-total-war-throne-room-audio-fix)
- [120-Man Unit Balance Fix](https://github.com/LouieWoolger/shogun-total-war-unit-cost-training-upkeep-fix)
- [Annual Harvest Report Audio Restoration](https://github.com/LouieWoolger/shogun-total-war-harvest-report-voice-fix)
- [Historical Campaigns Crash Fix](https://github.com/LouieWoolger/shogun-total-war-historical-campaign-reinforcement-fix)

The installer also includes the Limited Ammo Fix and dgVoodoo2 for the Terrain Movement Fix.

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
