<#
.SYNOPSIS
Collect a small, read-only Shogun launch support bundle. Never launches the game.
.EXAMPLE
.\Collect-LaunchDiagnostics.ps1 -GameDirectory 'D:\SteamLibrary\steamapps\common\Total War Shogun 1 Gold' -OutputDirectory "$env:USERPROFILE\Desktop\Shogun-launch-report"
.EXAMPLE
.\Collect-LaunchDiagnostics.ps1 -GameDirectory 'D:\Games\Shogun' -OutputDirectory 'D:\Reports\Shogun-launch' -LogDirectory 'D:\Reports\Patch-logs'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GameDirectory,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string[]]$LogDirectory = @(),
    [string[]]$InstallerLogPath = @(),
    [string]$InstallerPath,
    [ValidateRange(4096, 1048576)][int]$MaxLogBytes = 65536
)

$ErrorActionPreference = 'Stop'

function Get-AbsolutePath([string]$Path) {
    if (-not [IO.Path]::IsPathRooted($Path)) { throw "Use an absolute path: $Path" }
    return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
}

function Test-Within([string]$Path, [string]$Root) {
    return $Path.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($Root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparse([string]$Path) {
    $current = $Path
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse paths are not supported: $current" }
        }
        $parent = Split-Path -Parent $current
        if ($parent -eq $current) { break }
        $current = $parent
    }
}

$gameRoot = Get-AbsolutePath $GameDirectory
$outputRoot = Get-AbsolutePath $OutputDirectory
if (-not (Test-Path -LiteralPath $gameRoot -PathType Container)) { throw "Game directory does not exist: $gameRoot" }
Assert-NoReparse $gameRoot
Assert-NoReparse $outputRoot
if (Test-Within $outputRoot $gameRoot) { throw 'OutputDirectory must be outside the game directory.' }
if (Test-Within $outputRoot 'F:\AI_Projects\Tools') { throw 'OutputDirectory must be outside the Tools installation.' }
if (Test-Path -LiteralPath $outputRoot) { throw 'OutputDirectory already exists; choose a new directory to avoid overwriting reports.' }
if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'ShogunM.exe') -PathType Leaf)) { throw 'GameDirectory must contain ShogunM.exe.' }

$warnings = New-Object 'System.Collections.Generic.List[string]'
$files = New-Object 'System.Collections.Generic.List[object]'
$logs = New-Object 'System.Collections.Generic.List[object]'
$compatibility = New-Object 'System.Collections.Generic.List[object]'
$null = New-Item -ItemType Directory -Path $outputRoot

function Get-FileIdentity([string]$Path) {
    $result = [ordered]@{ Path = $Path; Exists = (Test-Path -LiteralPath $Path -PathType Leaf) }
    if (-not $result.Exists) { return [pscustomobject]$result }
    try {
        Assert-NoReparse $Path
        $item = Get-Item -LiteralPath $Path -Force
        $result.Length = $item.Length
        $result.LastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
        $result.SHA256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        $result.FileVersion = $item.VersionInfo.FileVersion
        $result.ProductVersion = $item.VersionInfo.ProductVersion
        $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            $reader = New-Object IO.BinaryReader($stream)
            if ($stream.Length -ge 64 -and $reader.ReadUInt16() -eq 0x5a4d) {
                $stream.Position = 0x3c
                $offset = $reader.ReadUInt32()
                if ($offset -le ($stream.Length - 26)) {
                    $stream.Position = $offset
                    if ($reader.ReadUInt32() -eq 0x4550) {
                        $machine = $reader.ReadUInt16()
                        $result.PEMachine = ('0x{0:X4}' -f $machine)
                        $result.Architecture = switch ($machine) { 0x14c { 'x86' } 0x8664 { 'x64' } 0xaa64 { 'ARM64' } default { 'unknown' } }
                        $stream.Position = $offset + 24
                        $magic = $reader.ReadUInt16()
                        $result.PEFormat = switch ($magic) { 0x10b { 'PE32' } 0x20b { 'PE32+' } default { 'unknown' } }
                    }
                }
            }
        } finally { $stream.Dispose() }
    } catch { $result.CollectionError = $_.Exception.Message }
    return [pscustomobject]$result
}

foreach ($name in @('shogun.exe', 'ShogunM.exe', 'ShogunM.exe.unofficial-patch.bak', 'DDraw.dll', 'D3DImm.dll', 'D3D9.dll', 'dgVoodoo.conf', 'shogun-fix-patcher.exe')) {
    $files.Add((Get-FileIdentity (Join-Path $gameRoot $name)))
}
if ($InstallerPath) { $files.Add((Get-FileIdentity (Get-AbsolutePath $InstallerPath))) }

function Save-LogTail([string]$Path, [string]$Label, [string]$EncodingHint = 'UTF8') {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    try {
        Assert-NoReparse $Path
        $item = Get-Item -LiteralPath $Path -Force
        $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            $length = $stream.Length
            $first = New-Object byte[] 2
            $null = $stream.Read($first, 0, [Math]::Min(2, $length))
            $unicode = ($EncodingHint -eq 'UTF16LE') -or ($first[0] -eq 0xff -and $first[1] -eq 0xfe)
            $start = [Math]::Max(0L, $length - $MaxLogBytes)
            if ($unicode -and ($start % 2) -ne 0) { $start++ }
            $stream.Position = $start
            $bytes = New-Object byte[] ([int]($length - $start))
            $read = 0
            while ($read -lt $bytes.Length) {
                $count = $stream.Read($bytes, $read, $bytes.Length - $read)
                if ($count -eq 0) { break }
                $read += $count
            }
        } finally { $stream.Dispose() }
        $encoding = if ($unicode) { [Text.Encoding]::Unicode } else { [Text.Encoding]::UTF8 }
        $text = $encoding.GetString($bytes, 0, $read).TrimStart([char]0xfeff)
        $destination = $Label + '.tail.txt'
        [IO.File]::WriteAllText((Join-Path $outputRoot $destination), $text, (New-Object Text.UTF8Encoding($false)))
        $logs.Add([pscustomobject]@{ Source = $Path; Output = $destination; SourceBytes = $length; CapturedBytes = $read; StartOffset = $start; Truncated = ($start -gt 0); LastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o'); DecodedAs = $encoding.WebName })
    } catch { $warnings.Add("Could not collect $Path : $($_.Exception.Message)") }
}

Save-LogTail (Join-Path $gameRoot 'proteus.txt') 'proteus'
$config = Join-Path $gameRoot 'dgVoodoo.conf'
if (Test-Path -LiteralPath $config -PathType Leaf) { Save-LogTail $config 'dgVoodoo-config' }

$roots = @($LogDirectory)
if ($env:LOCALAPPDATA) { $roots += (Join-Path $env:LOCALAPPDATA 'Unofficial Shogun Patch\Logs') }
if ($env:TEMP) { $roots += (Join-Path $env:TEMP 'Unofficial Shogun Patch Logs') }
if ($InstallerPath) { $roots += (Join-Path (Split-Path -Parent (Get-AbsolutePath $InstallerPath)) 'Unofficial Shogun Patch Logs') }
$logNumber = 0
foreach ($root in ($roots | Select-Object -Unique)) {
    try {
        $root = Get-AbsolutePath $root
        Assert-NoReparse $root
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        # The explicit directory can be a session folder or the parent holding sessions.
        $sessions = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Directory -Force | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0 } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 3)
        foreach ($session in $sessions) {
            foreach ($name in @('installer.log', 'helper.log', 'helper-console.log')) {
                $logNumber++
                $hint = if ($name -eq 'installer.log') { 'UTF16LE' } else { 'UTF8' }
                Save-LogTail (Join-Path $session.FullName $name) ('patch-log-{0}-{1}' -f $logNumber, $name) $hint
            }
        }
    } catch { $warnings.Add("Could not inspect log directory $root : $($_.Exception.Message)") }
}
foreach ($path in $InstallerLogPath) { $logNumber++; Save-LogTail (Get-AbsolutePath $path) ('explicit-log-{0}' -f $logNumber) }

$targets = @((Join-Path $gameRoot 'shogun.exe'), (Join-Path $gameRoot 'ShogunM.exe'))
foreach ($hive in @([Microsoft.Win32.RegistryHive]::CurrentUser, [Microsoft.Win32.RegistryHive]::LocalMachine)) {
    foreach ($view in @([Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64)) {
        $base = $null; $key = $null
        try {
            $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, $view)
            $key = $base.OpenSubKey('Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers', $false)
            if ($key) {
                foreach ($target in $targets) {
                    $value = $key.GetValue($target, $null)
                    if ($null -ne $value) { $compatibility.Add([pscustomobject]@{ Hive = $hive.ToString(); View = $view.ToString(); Target = $target; Flags = $value }) }
                }
            }
        } catch { $warnings.Add("Compatibility flags unavailable for $hive/$view : $($_.Exception.Message)") }
        finally { if ($key) { $key.Dispose() }; if ($base) { $base.Dispose() } }
    }
}

$os = $null; $gpu = @()
try { $os = Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture } catch { $warnings.Add("OS information unavailable: $($_.Exception.Message)") }
try { $gpu = @(Get-CimInstance -ClassName Win32_VideoController | Select-Object Name, AdapterCompatibility, DriverVersion, DriverDate, VideoProcessor) } catch { $warnings.Add("GPU information unavailable: $($_.Exception.Message)") }
$report = [ordered]@{
    CollectedAtUtc = [DateTime]::UtcNow.ToString('o')
    GameDirectory = $gameRoot
    CollectionMode = 'Read-only sources; no launch, configuration changes, process dump, or event-log collection'
    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    OS = $os; GPU = $gpu; Files = $files.ToArray(); Logs = $logs.ToArray(); CompatibilityFlags = $compatibility.ToArray(); Warnings = $warnings.ToArray()
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outputRoot 'launch-diagnostics.json') -Encoding UTF8
@'
This bundle does not reproduce a launch or identify the cause by itself.
Add the patch installer version/download URL, selected options, and what happens
when launching through Steam, shogun.exe, and ShogunM.exe. State whether a window
appears and whether proteus.txt gets a new session. If available, include the exact
installer error and the log folder shown by the installer. Text files are bounded
tails; truncation and source paths are recorded in launch-diagnostics.json.
Review the files before sharing: game/log paths may contain your Windows username.
'@ | Set-Content -LiteralPath (Join-Path $outputRoot 'README.txt') -Encoding UTF8
Write-Output "Launch diagnostic bundle: $outputRoot"
