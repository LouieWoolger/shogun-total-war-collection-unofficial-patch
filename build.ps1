param(
    [switch]$SkipInstaller,
    [switch]$RegenerateTemplateImages,
    [switch]$SkipTests,
    [switch]$Sign,
    [string]$CertificateThumbprint,
    [string]$TimestampUrl = 'http://timestamp.digicert.com',
    [string]$SignToolPath
)

$ErrorActionPreference = 'Stop'

$installerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $installerRoot
$bundledGcc = Join-Path $workspaceRoot '_tools\w64devkit\bin\gcc.exe'
$bundledMakensis = Join-Path $workspaceRoot '_tools\nsis-3.11\makensis.exe'
$src = Join-Path $installerRoot 'src\shogun_fix_patcher.c'
$resourceScript = Join-Path $installerRoot 'src\shogun_fix_patcher.rc'
$buildDir = Join-Path $installerRoot 'build'
$distDir = Join-Path $installerRoot 'dist'
$patcher = Join-Path $buildDir 'shogun-fix-patcher.exe'
$installerOutput = Join-Path $distDir 'Unofficial Shogun Total War Collection Patch.exe'
$resourceObject = Join-Path $buildDir 'shogun_fix_patcher_res.o'
$assetsDir = Join-Path $installerRoot 'assets'

New-Item -ItemType Directory -Force -Path $buildDir, $distDir | Out-Null

function Resolve-BuildTool {
    param(
        [string]$Name,
        [string]$BundledPath,
        [string]$InstallHint
    )

    if (Test-Path $BundledPath) {
        return (Resolve-Path $BundledPath).Path
    }

    $fromPath = Get-Command $Name -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    throw "Missing $Name. $InstallHint"
}

function Resolve-SignTool {
    if ($SignToolPath) {
        if (!(Test-Path $SignToolPath)) {
            throw "SignToolPath does not exist: $SignToolPath"
        }
        return (Resolve-Path $SignToolPath).Path
    }

    $fromPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    $kitRoots = @()
    if (${env:ProgramFiles(x86)}) {
        $kitRoots += (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin')
    }
    if ($env:ProgramFiles) {
        $kitRoots += (Join-Path $env:ProgramFiles 'Windows Kits\10\bin')
    }

    foreach ($root in $kitRoots) {
        if (!(Test-Path $root)) {
            continue
        }
        $candidate = Get-ChildItem -Path $root -Directory |
            Sort-Object Name -Descending |
            ForEach-Object {
                $x64 = Join-Path $_.FullName 'x64\signtool.exe'
                $x86 = Join-Path $_.FullName 'x86\signtool.exe'
                if (Test-Path $x64) { $x64 }
                elseif (Test-Path $x86) { $x86 }
            } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }

    throw "signtool.exe was not found. Install the Windows SDK or pass -SignToolPath."
}

function Invoke-CodeSigning {
    param(
        [string]$Path,
        [string]$Description
    )

    if (!$Sign) {
        return
    }
    if (!$CertificateThumbprint) {
        throw "Pass -CertificateThumbprint when using -Sign."
    }
    if (!(Test-Path $Path)) {
        throw "Cannot sign missing file: $Path"
    }

    $signTool = Resolve-SignTool
    & $signTool sign /fd SHA256 /td SHA256 /tr $TimestampUrl /sha1 $CertificateThumbprint /d $Description $Path
    if ($LASTEXITCODE -ne 0) {
        throw "Code signing failed for $Path with exit code $LASTEXITCODE"
    }

    & $signTool verify /pa /v $Path
    if ($LASTEXITCODE -ne 0) {
        throw "Signature verification failed for $Path with exit code $LASTEXITCODE"
    }
}

function Write-ReleaseHashes {
    param(
        [string[]]$Paths,
        [string]$OutputPath
    )

    $lines = foreach ($path in $Paths) {
        if (!(Test-Path $path)) {
            throw "Cannot hash missing file: $path"
        }

        $hash = Get-FileHash -Algorithm SHA256 -Path $path
        "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), (Split-Path -Leaf $path)
    }

    Set-Content -Path $OutputPath -Value $lines -Encoding ASCII
}

$gcc = Resolve-BuildTool -Name 'gcc.exe' -BundledPath $bundledGcc -InstallHint 'Install w64devkit or place it at ..\_tools\w64devkit.'
$makensis = Resolve-BuildTool -Name 'makensis.exe' -BundledPath $bundledMakensis -InstallHint 'Install NSIS 3.11+ or place it at ..\_tools\nsis-3.11.'
$w64Bin = Split-Path -Parent $gcc
$windres = Join-Path $w64Bin 'windres.exe'
if (!(Test-Path $windres)) {
    $windresCmd = Get-Command windres.exe -ErrorAction SilentlyContinue
    if (!$windresCmd) {
        throw 'Missing windres.exe. Install w64devkit or another MinGW-w64 toolchain with windres on PATH.'
    }
    $windres = $windresCmd.Source
}

$env:PATH = "$w64Bin;$env:PATH"

$targetTriple = & $gcc -dumpmachine
if ($LASTEXITCODE -ne 0 -or $targetTriple.Trim() -ne 'i686-w64-mingw32') {
    throw "Expected i686-w64-mingw32 GCC, got '$targetTriple'"
}

Push-Location (Join-Path $installerRoot 'src')
try {
    & $windres $resourceScript $resourceObject
    if ($LASTEXITCODE -ne 0) {
        throw "Resource compile failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

& $gcc -std=c99 -Wall -Wextra -Werror -Os -D_WIN32_WINNT=0x0501 -municode -s '-Wl,--major-subsystem-version,5,--minor-subsystem-version,1' -o $patcher $src $resourceObject
if ($LASTEXITCODE -ne 0) {
    throw "Patcher compile failed with exit code $LASTEXITCODE"
}

function Assert-PeI386Subsystem51 {
    param([string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 256) {
        throw "PE file is too small: $Path"
    }

    $peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    $optionalHeader = $peOffset + 24
    $majorSubsystem = [BitConverter]::ToUInt16($bytes, $optionalHeader + 48)
    $minorSubsystem = [BitConverter]::ToUInt16($bytes, $optionalHeader + 50)

    if ($machine -ne 0x014C) {
        throw ("Expected PE Machine 0x014C (i386), got 0x{0:X4}" -f $machine)
    }
    if ($majorSubsystem -ne 5 -or $minorSubsystem -ne 1) {
        throw "Expected PE subsystem version 5.1, got $majorSubsystem.$minorSubsystem"
    }
}

Assert-PeI386Subsystem51 -Path $patcher
Invoke-CodeSigning -Path $patcher -Description 'Unofficial Shogun Total War Collection Patch Helper'

if ($SkipInstaller) {
    return
}

function New-PreviewBitmap {
    param(
        [string]$Path,
        [string]$Title,
        [string]$Subtitle,
        [int]$BackR,
        [int]$BackG,
        [int]$BackB,
        [int]$AccentR,
        [int]$AccentG,
        [int]$AccentB
    )

    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 480, 270
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb($BackR, $BackG, $BackB))

    $accent = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb($AccentR, $AccentG, $AccentB))
    $light = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(245, 244, 238))
    $muted = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(220, 216, 205))
    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(245, 244, 238)), 2
    $titleFont = New-Object System.Drawing.Font 'Segoe UI', 13, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Point)
    $subtitleFont = New-Object System.Drawing.Font 'Segoe UI', 8, ([System.Drawing.FontStyle]::Regular), ([System.Drawing.GraphicsUnit]::Point)

    $graphics.FillRectangle($accent, 0, 0, 24, 270)
    $graphics.DrawRectangle($pen, 52, 44, 126, 126)
    $graphics.DrawLine($pen, 82, 122, 112, 152)
    $graphics.DrawLine($pen, 112, 152, 158, 76)
    $graphics.DrawString($Title, $titleFont, $light, 210, 66)
    $graphics.DrawString($Subtitle, $subtitleFont, $muted, 212, 112)
    $graphics.DrawLine($pen, 210, 184, 430, 184)

    $graphics.Dispose()
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Bmp)
    $bmp.Dispose()
}

function New-TintedIconBitmap {
    param(
        [string]$Path,
        [System.Drawing.Color]$Color
    )

    $sourceImage = [System.Drawing.Image]::FromFile($Path)
    $source = New-Object System.Drawing.Bitmap $sourceImage
    $sourceImage.Dispose()
    $tinted = New-Object System.Drawing.Bitmap $source.Width, $source.Height, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)

    try {
        for ($y = 0; $y -lt $source.Height; $y++) {
            for ($x = 0; $x -lt $source.Width; $x++) {
                $pixel = $source.GetPixel($x, $y)
                if ($pixel.A -gt 0) {
                    $tinted.SetPixel($x, $y, ([System.Drawing.Color]::FromArgb($pixel.A, $Color.R, $Color.G, $Color.B)))
                }
            }
        }
    }
    finally {
        $source.Dispose()
    }

    return $tinted
}

function New-FinishBadgeBitmap {
    param(
        [string]$Path,
        [ValidateSet('Discord', 'Kofi')]
        [string]$Kind,
        [switch]$Hover
    )

    Add-Type -AssemblyName System.Drawing
    $width = 138
    $height = 28
    $leftWidth = 78
    $rightWidth = $width - $leftWidth
    $dark = [System.Drawing.Color]::FromArgb(85, 87, 93)
    $discord = [System.Drawing.Color]::FromArgb(88, 101, 242)
    $kofi = [System.Drawing.Color]::FromArgb(255, 95, 95)
    if ($Hover) {
        $dark = [System.Drawing.Color]::FromArgb(60, 62, 68)
        $discord = [System.Drawing.Color]::FromArgb(122, 136, 255)
        $kofi = [System.Drawing.Color]::FromArgb(255, 135, 135)
    }
    $white = [System.Drawing.Color]::FromArgb(255, 255, 255)
    $hoverBorder = [System.Drawing.Color]::FromArgb(245, 244, 238)

    if ($Kind -eq 'Discord') {
        $accentColor = $discord
        $leftText = 'DISCORD'
        $rightText = 'JOIN'
    }
    else {
        $accentColor = $kofi
        $leftText = 'KO-FI'
        $rightText = 'SUPPORT'
    }

    $bmp = New-Object System.Drawing.Bitmap $width, $height, ([System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $darkBrush = New-Object System.Drawing.SolidBrush $dark
    $accentBrush = New-Object System.Drawing.SolidBrush $accentColor
    $whiteBrush = New-Object System.Drawing.SolidBrush $white
    $hoverBorderPen = New-Object System.Drawing.Pen $hoverBorder, 1
    $labelFont = New-Object System.Drawing.Font 'Segoe UI', 7, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Point)
    $valueFont = New-Object System.Drawing.Font 'Segoe UI', 7, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Point)
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center

    try {
        $graphics.FillRectangle($darkBrush, 0, 0, $leftWidth, $height)
        $graphics.FillRectangle($accentBrush, $leftWidth, 0, $rightWidth, $height)
        if ($Hover) {
            $graphics.DrawRectangle($hoverBorderPen, 0, 0, $width - 1, $height - 1)
        }

        if ($Kind -eq 'Discord') {
            $discordIconPath = Join-Path $assetsDir 'discord-social-icon.png'
            if (!(Test-Path $discordIconPath)) {
                throw "Missing Discord badge source icon at $discordIconPath"
            }
            $discordIcon = New-TintedIconBitmap -Path $discordIconPath -Color $accentColor
            try {
                $graphics.DrawImage($discordIcon, (New-Object System.Drawing.Rectangle 5, 6, 22, 17))
            }
            finally {
                $discordIcon.Dispose()
            }
        }
        else {
            $kofiIconPath = Join-Path $assetsDir 'kofi-social-icon.png'
            if (!(Test-Path $kofiIconPath)) {
                throw "Missing Ko-fi badge source icon at $kofiIconPath"
            }
            $kofiIcon = [System.Drawing.Image]::FromFile($kofiIconPath)
            try {
                $graphics.DrawImage($kofiIcon, (New-Object System.Drawing.Rectangle 5, 5, 24, 19))
            }
            finally {
                $kofiIcon.Dispose()
            }
        }

        $graphics.DrawString($leftText, $labelFont, $whiteBrush, (New-Object System.Drawing.RectangleF 28, 0, ($leftWidth - 30), $height), $format)
        $graphics.DrawString($rightText, $valueFont, $whiteBrush, (New-Object System.Drawing.RectangleF $leftWidth, 0, $rightWidth, $height), $format)
        $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Bmp)
    }
    finally {
        $format.Dispose()
        $valueFont.Dispose()
        $labelFont.Dispose()
        $whiteBrush.Dispose()
        $hoverBorderPen.Dispose()
        $accentBrush.Dispose()
        $darkBrush.Dispose()
        $graphics.Dispose()
        $bmp.Dispose()
    }
}

function New-WelcomeFinishBitmap {
    param([string]$Path)

    Add-Type -AssemblyName System.Drawing
    $iconPath = Join-Path $assetsDir 'shogun.ico'
    $bmp = New-Object System.Drawing.Bitmap 164, 314, ([System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $rect = New-Object System.Drawing.Rectangle 0, 0, 164, 314
    $background = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, ([System.Drawing.Color]::FromArgb(76, 12, 18)), ([System.Drawing.Color]::FromArgb(28, 31, 28)), ([System.Drawing.Drawing2D.LinearGradientMode]::Vertical)
    $darkBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(21, 22, 21))
    $logoBackingBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)

    try {
        $graphics.FillRectangle($background, $rect)
        $graphics.FillPolygon($darkBrush, [System.Drawing.Point[]]@(
            (New-Object System.Drawing.Point -20, 236),
            (New-Object System.Drawing.Point 180, 180),
            (New-Object System.Drawing.Point 184, 238),
            (New-Object System.Drawing.Point -10, 292)
        ))

        $graphics.FillEllipse($logoBackingBrush, (New-Object System.Drawing.Rectangle 48, 44, 68, 68))
        $icon = New-Object System.Drawing.Icon $iconPath, 48, 48
        $graphics.DrawIcon($icon, (New-Object System.Drawing.Rectangle 58, 54, 48, 48))
        $icon.Dispose()

        $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Bmp)
    }
    finally {
        $logoBackingBrush.Dispose()
        $darkBrush.Dispose()
        $background.Dispose()
        $graphics.Dispose()
        $bmp.Dispose()
    }
}

New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
$welcomeFinishBitmap = Join-Path $assetsDir 'welcome-finish.bmp'
$discordBadgeBitmap = Join-Path $assetsDir 'discord-badge.bmp'
$kofiBadgeBitmap = Join-Path $assetsDir 'kofi-badge.bmp'
$discordBadgeHoverBitmap = Join-Path $assetsDir 'discord-badge-hover.bmp'
$kofiBadgeHoverBitmap = Join-Path $assetsDir 'kofi-badge-hover.bmp'
$templateImages = @(
    @{ Path = Join-Path $assetsDir 'historical.bmp'; Title = 'Reinforcements'; Subtitle = 'Historical campaign arrival fix'; BackR = 60; BackG = 72; BackB = 66; AccentR = 164; AccentG = 42; AccentB = 38 },
    @{ Path = Join-Path $assetsDir 'throne.bmp'; Title = 'Throne Audio'; Subtitle = 'Speech plays to completion'; BackR = 68; BackG = 61; BackB = 76; AccentR = 190; AccentG = 141; AccentB = 57 },
    @{ Path = Join-Path $assetsDir 'unit.bmp'; Title = 'Unit Economy'; Subtitle = 'Cost, training, upkeep fix'; BackR = 48; BackG = 78; BackB = 84; AccentR = 196; AccentG = 90; AccentB = 54 },
    @{ Path = Join-Path $assetsDir 'harvest.bmp'; Title = 'Harvest Voice'; Subtitle = 'Annual report audio restored'; BackR = 80; BackG = 69; BackB = 48; AccentR = 116; AccentG = 143; AccentB = 69 },
    @{ Path = Join-Path $assetsDir 'dgvoodoo.bmp'; Title = 'Terrain movement'; Subtitle = 'dgVoodoo2 wrapper fix'; BackR = 87; BackG = 111; BackB = 86; AccentR = 83; AccentG = 139; AccentB = 151 }
)

foreach ($image in $templateImages) {
    if ($RegenerateTemplateImages -or !(Test-Path $image.Path)) {
        New-PreviewBitmap @image
    }
}

if ($RegenerateTemplateImages -or !(Test-Path $welcomeFinishBitmap)) {
    New-WelcomeFinishBitmap -Path $welcomeFinishBitmap
}

if ($RegenerateTemplateImages -or !(Test-Path $discordBadgeBitmap)) {
    New-FinishBadgeBitmap -Path $discordBadgeBitmap -Kind Discord
}

if ($RegenerateTemplateImages -or !(Test-Path $kofiBadgeBitmap)) {
    New-FinishBadgeBitmap -Path $kofiBadgeBitmap -Kind Kofi
}

if ($RegenerateTemplateImages -or !(Test-Path $discordBadgeHoverBitmap)) {
    New-FinishBadgeBitmap -Path $discordBadgeHoverBitmap -Kind Discord -Hover
}

if ($RegenerateTemplateImages -or !(Test-Path $kofiBadgeHoverBitmap)) {
    New-FinishBadgeBitmap -Path $kofiBadgeHoverBitmap -Kind Kofi -Hover
}

if (!$SkipTests) {
    & python -B -m pytest (Join-Path $installerRoot 'tests') -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) {
        throw "Patcher tests failed with exit code $LASTEXITCODE"
    }
}

if (!(Test-Path $makensis)) {
    throw "Missing makensis at $makensis"
}

& $makensis (Join-Path $installerRoot 'installer.nsi')
if ($LASTEXITCODE -ne 0) {
    throw "NSIS compile failed with exit code $LASTEXITCODE"
}

Invoke-CodeSigning -Path $installerOutput -Description 'Unofficial Shogun Total War Collection Patch Setup'
Write-ReleaseHashes -Paths @($installerOutput) -OutputPath (Join-Path $distDir 'SHA256SUMS.txt')
