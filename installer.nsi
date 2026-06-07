Unicode true
XPStyle on

!define SOURCE_DIR "${__FILEDIR__}"
!define APP_NAME "Unofficial Shogun: Total War Collection Patch Setup"
!define APP_SHORT_NAME "Unofficial Shogun: Total War Collection Patch"
!define APP_VERSION "1.1.0"

Name "${APP_SHORT_NAME}"
Caption "${APP_NAME}"
OutFile "${SOURCE_DIR}\dist\Unofficial Shogun Total War Collection Patch.exe"
RequestExecutionLevel user
InstallDir "$EXEDIR"
SetCompressor /SOLID lzma
ShowInstDetails show
BrandingText " "

VIProductVersion "1.1.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "Louie Woolger"
VIAddVersionKey "FileDescription" "${APP_NAME}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright 2026 Louie Woolger"

!include MUI2.nsh
!include LogicLib.nsh
!include nsDialogs.nsh
!include StrFunc.nsh
!include WinMessages.nsh
!include WinVer.nsh
!include x64.nsh
${Using:StrFunc} StrStr
${Using:StrFunc} StrRep
${Using:StrFunc} StrLoc

!macro CHECK_PREVIEW_HOVER HANDLE KEY
    System::Call "*(i 0, i 0, i 0, i 0) p.r2"
    System::Call "user32::GetWindowRect(p${HANDLE}, p r2)i.r3"
    ${If} $3 <> 0
        System::Call "*$2(i.r3, i.r4, i.r5, i.r6)"
        ${If} $0 >= $3
        ${AndIf} $0 <= $5
        ${AndIf} $1 >= $4
        ${AndIf} $1 <= $6
            System::Free $2
            StrCpy $R0 "${KEY}"
            Call SetPreview
            Return
        ${EndIf}
    ${EndIf}
    System::Free $2
!macroend

!macro CHECK_FINISH_BADGE_HOVER HANDLE KEY
    System::Call "*(i 0, i 0, i 0, i 0) p.r2"
    System::Call "user32::GetWindowRect(p${HANDLE}, p r2)i.r3"
    ${If} $3 <> 0
        System::Call "*$2(i.r3, i.r4, i.r5, i.r6)"
        ${If} $0 >= $3
        ${AndIf} $0 <= $5
        ${AndIf} $1 >= $4
        ${AndIf} $1 <= $6
            StrCpy $R0 "${KEY}"
        ${EndIf}
    ${EndIf}
    System::Free $2
!macroend

!macro ABORT_INSTALL
    SetErrorLevel 2
    IfSilent 0 +2
    Quit
    Abort
!macroend

!define MUI_ABORTWARNING
!define MUI_ICON "${SOURCE_DIR}\assets\shogun.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${SOURCE_DIR}\assets\welcome-finish.bmp"
!define MUI_FONT "Tahoma"
!define MUI_ABORTWARNING_TEXT "Are you sure you want to quit the Unofficial Shogun: Total War Collection Patch Setup?"
!define MUI_WELCOMEPAGE_TITLE "Install Unofficial Shogun Total War Collection Patch"
!define MUI_WELCOMEPAGE_TEXT "This installer patches your existing Shogun: Total War Collection folder."
!define MUI_FINISHPAGE_TITLE "Installation complete"
!define MUI_FINISHPAGE_TEXT "Selected options were applied to your game. Have fun!"

!define MUI_PAGE_CUSTOMFUNCTION_SHOW WelcomePageShow
!insertmacro MUI_PAGE_WELCOME
!ifdef MUI_PAGE_CUSTOMFUNCTION_SHOW
!undef MUI_PAGE_CUSTOMFUNCTION_SHOW
!endif
Page custom FixesPageCreate FixesPageLeave
!insertmacro MUI_PAGE_INSTFILES
!define MUI_PAGE_CUSTOMFUNCTION_SHOW FinishPageShow
!define MUI_PAGE_CUSTOMFUNCTION_DESTROYED FinishPageDestroyed
!insertmacro MUI_PAGE_FINISH
!ifdef MUI_PAGE_CUSTOMFUNCTION_SHOW
!undef MUI_PAGE_CUSTOMFUNCTION_SHOW
!endif
!ifdef MUI_PAGE_CUSTOMFUNCTION_DESTROYED
!undef MUI_PAGE_CUSTOMFUNCTION_DESTROYED
!endif
!insertmacro MUI_LANGUAGE "English"

Var Dialog
Var TargetText
Var BrowseButton
Var KofiButton
Var DiscordButton
Var KofiBadgeImage
Var DiscordBadgeImage
Var FinishBadgeHoverState
Var HistoricalCheck
Var KawanakajimaCheck
Var OdawaraCheck
Var ThroneCheck
Var UnitCheck
Var DgVoodooCheck
Var HarvestCheck
Var AmmoCheck
Var PreviewBitmap
Var PreviewImage
Var PreviewTitle
Var PreviewText
Var PreviewWarningText
Var PatchPageFont
Var PatchPageTitleFont
Var PatchPageBodyFont
Var SelectedFlags
Var PatcherFlags
Var InstallDgVoodoo
Var DgVoodooSupported
Var BackupsGenerated
Var PatcherOutput
Var CurrentPreviewKey
Var FixesPageVisited
Var SavedTargetDir
Var SavedDgVoodooState
Var SavedHistoricalState
Var SavedKawanakajimaState
Var SavedOdawaraState
Var SavedThroneState
Var SavedUnitState
Var SavedHarvestState
Var SavedAmmoState
Var DgVoodooRollbackFailed

Function .onInit
    InitPluginsDir
    File /oname=$PLUGINSDIR\historical.bmp "${SOURCE_DIR}\assets\historical.bmp"
    File /oname=$PLUGINSDIR\throne.bmp "${SOURCE_DIR}\assets\throne.bmp"
    File /oname=$PLUGINSDIR\unit.bmp "${SOURCE_DIR}\assets\unit.bmp"
    File /oname=$PLUGINSDIR\ammo.bmp "${SOURCE_DIR}\assets\ammo.bmp"
    File /oname=$PLUGINSDIR\kawanakajima.bmp "${SOURCE_DIR}\assets\kawanakajima.bmp"
    File /oname=$PLUGINSDIR\odawara.bmp "${SOURCE_DIR}\assets\odawara.bmp"
    File /oname=$PLUGINSDIR\dgvoodoo.bmp "${SOURCE_DIR}\assets\dgvoodoo.bmp"
    File /oname=$PLUGINSDIR\harvest.bmp "${SOURCE_DIR}\assets\harvest.bmp"
    File /oname=$PLUGINSDIR\discord-badge.bmp "${SOURCE_DIR}\assets\discord-badge.bmp"
    File /oname=$PLUGINSDIR\kofi-badge.bmp "${SOURCE_DIR}\assets\kofi-badge.bmp"
    File /oname=$PLUGINSDIR\discord-badge-hover.bmp "${SOURCE_DIR}\assets\discord-badge-hover.bmp"
    File /oname=$PLUGINSDIR\kofi-badge-hover.bmp "${SOURCE_DIR}\assets\kofi-badge-hover.bmp"

    StrCpy $SelectedFlags "historical,throne,ammo,kawanakajima,odawara"
    StrCpy $PatcherFlags "historical,throne,ammo,kawanakajima,odawara"
    StrCpy $InstallDgVoodoo "0"
    StrCpy $DgVoodooSupported "0"
    StrCpy $BackupsGenerated "0"
    StrCpy $FixesPageVisited "0"
    StrCpy $SavedTargetDir ""
    StrCpy $SavedDgVoodooState ${BST_UNCHECKED}
    StrCpy $SavedHistoricalState ${BST_CHECKED}
    StrCpy $SavedKawanakajimaState ${BST_CHECKED}
    StrCpy $SavedOdawaraState ${BST_CHECKED}
    StrCpy $SavedThroneState ${BST_CHECKED}
    StrCpy $SavedUnitState ${BST_UNCHECKED}
    StrCpy $SavedHarvestState ${BST_UNCHECKED}
    StrCpy $SavedAmmoState ${BST_CHECKED}
    ${If} ${AtLeastWinVista}
        StrCpy $DgVoodooSupported "1"
        StrCpy $SelectedFlags "dgvoodoo,historical,throne,ammo,kawanakajima,odawara"
        StrCpy $InstallDgVoodoo "1"
        StrCpy $SavedDgVoodooState ${BST_CHECKED}
    ${EndIf}
FunctionEnd

Function DetectGamePath
    ${If} ${FileExists} "$INSTDIR\ShogunM.exe"
        Return
    ${EndIf}

    ${If} ${FileExists} "$EXEDIR\ShogunM.exe"
        StrCpy $INSTDIR "$EXEDIR"
        Return
    ${EndIf}

    ${If} ${RunningX64}
        SetRegView 64
        ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 345240" "InstallLocation"
        Call TryRegistryGamePath
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 345240" "InstallLocation"
        Call TryRegistryGamePath
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\1874325037_is1" "InstallLocation"
        Call TryRegistryGamePath
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\1874325037_is1" "InstallLocation"
        Call TryRegistryGamePath
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        SetRegView 32
    ${EndIf}

    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 345240" "InstallLocation"
    Call TryRegistryGamePath
    ${If} $9 == "1"
        Return
    ${EndIf}
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 345240" "InstallLocation"
    Call TryRegistryGamePath
    ${If} $9 == "1"
        Return
    ${EndIf}
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\1874325037_is1" "InstallLocation"
    Call TryRegistryGamePath
    ${If} $9 == "1"
        Return
    ${EndIf}
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\1874325037_is1" "InstallLocation"
    Call TryRegistryGamePath
    ${If} $9 == "1"
        Return
    ${EndIf}

    ReadRegStr $0 HKCU "Software\Valve\Steam" "SteamPath"
    Call TrySteamRoot
    ${If} $9 == "1"
        Return
    ${EndIf}

    ReadRegStr $0 HKLM "Software\Valve\Steam" "InstallPath"
    Call TrySteamRoot
    ${If} $9 == "1"
        Return
    ${EndIf}

    ${If} ${RunningX64}
        SetRegView 64
        ReadRegStr $0 HKCU "Software\Valve\Steam" "SteamPath"
        Call TrySteamRoot
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        ReadRegStr $0 HKLM "Software\Valve\Steam" "InstallPath"
        Call TrySteamRoot
        ${If} $9 == "1"
            SetRegView 32
            Return
        ${EndIf}
        SetRegView 32
    ${EndIf}

    ${If} ${FileExists} "$PROGRAMFILES\GOG Games\SHOGUN Total War Gold\ShogunM.exe"
        StrCpy $INSTDIR "$PROGRAMFILES\GOG Games\SHOGUN Total War Gold"
        Return
    ${EndIf}

    ${If} ${FileExists} "$PROGRAMFILES\Total War Shogun 1 Gold\ShogunM.exe"
        StrCpy $INSTDIR "$PROGRAMFILES\Total War Shogun 1 Gold"
        Return
    ${EndIf}

    ${If} ${RunningX64}
        ${If} ${FileExists} "$PROGRAMFILES32\Steam\steamapps\common\Total War Shogun 1 Gold\ShogunM.exe"
            StrCpy $INSTDIR "$PROGRAMFILES32\Steam\steamapps\common\Total War Shogun 1 Gold"
            Return
        ${EndIf}
        ${If} ${FileExists} "$PROGRAMFILES32\GOG Games\SHOGUN Total War Gold\ShogunM.exe"
            StrCpy $INSTDIR "$PROGRAMFILES32\GOG Games\SHOGUN Total War Gold"
            Return
        ${EndIf}
    ${EndIf}

    StrCpy $INSTDIR "$PROGRAMFILES32\Total War Shogun 1 Gold"
FunctionEnd

Function TryRegistryGamePath
    StrCpy $9 "0"
    ${If} $0 == ""
        Return
    ${EndIf}

    ${StrRep} $0 "$0" "/" "\"
    ${If} ${FileExists} "$0\ShogunM.exe"
        StrCpy $INSTDIR "$0"
        StrCpy $9 "1"
    ${EndIf}
FunctionEnd

Function TrySteamRoot
    StrCpy $9 "0"
    ${If} $0 == ""
        Return
    ${EndIf}

    ${StrRep} $0 "$0" "/" "\"
    StrCpy $1 "$0\steamapps\common\Total War Shogun 1 Gold"
    ${If} ${FileExists} "$1\ShogunM.exe"
        StrCpy $INSTDIR "$1"
        StrCpy $9 "1"
        Return
    ${EndIf}

    StrCpy $1 "$0\steamapps\libraryfolders.vdf"
    ${IfNot} ${FileExists} "$1"
        Return
    ${EndIf}

    ClearErrors
    FileOpen $2 "$1" r
    ${If} ${Errors}
        Return
    ${EndIf}

    ${Do}
        ClearErrors
        FileRead $2 $3
        ${If} ${Errors}
            ${ExitDo}
        ${EndIf}
        StrCpy $4 "$3"
        Call TrySteamLibraryFolderLine
        ${If} $9 == "1"
            FileClose $2
            Return
        ${EndIf}
    ${Loop}

    FileClose $2
FunctionEnd

Function TrySteamLibraryFolderLine
    StrCpy $9 "0"
    ${StrStr} $5 "$4" "$\"path$\""
    ${If} $5 == ""
        Return
    ${EndIf}

    StrCpy $5 "$5" "" 6
    ${StrStr} $5 "$5" "$\""
    ${If} $5 == ""
        Return
    ${EndIf}

    StrCpy $5 "$5" "" 1
    ${StrLoc} $6 "$5" "$\"" ">"
    ${If} $6 == ""
        Return
    ${EndIf}

    StrCpy $5 "$5" $6
    ${StrRep} $5 "$5" "\\" "\"
    StrCpy $5 "$5\steamapps\common\Total War Shogun 1 Gold"
    ${If} ${FileExists} "$5\ShogunM.exe"
        StrCpy $INSTDIR "$5"
        StrCpy $9 "1"
    ${EndIf}
FunctionEnd

Function RestoreDefaultWizard
    LockWindow on

    System::Call 'user32::SetWindowPos(p$HWNDPARENT,p0,i0,i0,i503,i390,i0x16)'

    GetDlgItem $0 $HWNDPARENT 1034
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i0,i498,i57,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1036
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i57,i508,i2,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1037
    System::Call 'user32::SetWindowPos(p$0,p0,i15,i8,i420,i16,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1038
    System::Call 'user32::SetWindowPos(p$0,p0,i23,i26,i413,i26,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1039
    System::Call 'user32::SetWindowPos(p$0,p0,i453,i13,i32,i32,i0x14)'

    GetDlgItem $0 $HWNDPARENT 1028
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i305,i483,i13,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1256
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i305,i483,i13,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1035
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i313,i480,i2,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1045
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i313,i508,i2,i0x14)'

    GetDlgItem $0 $HWNDPARENT 3
    System::Call 'user32::SetWindowPos(p$0,p0,i252,i326,i75,i23,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1
    System::Call 'user32::SetWindowPos(p$0,p0,i327,i326,i75,i23,i0x14)'
    GetDlgItem $0 $HWNDPARENT 2
    System::Call 'user32::SetWindowPos(p$0,p0,i413,i326,i75,i23,i0x14)'

    LockWindow off
FunctionEnd

Function WelcomePageShow
    Call RestoreDefaultWizard
FunctionEnd

Function FinishPageShow
    ${If} $BackupsGenerated == "1"
        ${NSD_SetText} $mui.FinishPage.Text "Selected options were applied to your game. Backup files were generated in your game folder. Have fun!"
    ${Else}
        ${NSD_SetText} $mui.FinishPage.Text "Selected options were applied to your game. Have fun!"
    ${EndIf}
    System::Call 'user32::SetWindowPos(p$mui.FinishPage.Text,p0,i180,i100,i293,i64,i0x14)'

    StrCpy $FinishBadgeHoverState ""

    ${NSD_CreateBitmap} 120u 169u 92u 17u ""
    Pop $DiscordButton
    ${NSD_SetImage} $DiscordButton "$PLUGINSDIR\discord-badge.bmp" $DiscordBadgeImage
    ${NSD_OnClick} $DiscordButton OpenDiscordInvite

    ${NSD_CreateBitmap} 223u 169u 92u 17u ""
    Pop $KofiButton
    ${NSD_SetImage} $KofiButton "$PLUGINSDIR\kofi-badge.bmp" $KofiBadgeImage
    ${NSD_OnClick} $KofiButton OpenKofiPage
    ${NSD_CreateTimer} FinishBadgeHoverTimer 60
FunctionEnd

Function FinishPageDestroyed
    ${NSD_KillTimer} FinishBadgeHoverTimer
    ${If} $KofiBadgeImage != ""
        ${NSD_FreeImage} $KofiBadgeImage
        StrCpy $KofiBadgeImage ""
    ${EndIf}
    ${If} $DiscordBadgeImage != ""
        ${NSD_FreeImage} $DiscordBadgeImage
        StrCpy $DiscordBadgeImage ""
    ${EndIf}
FunctionEnd

Function FinishBadgeHoverTimer
    Call FinishBadgeFromCursor
FunctionEnd

Function FinishBadgeFromCursor
    System::Call "*(i 0, i 0) p.r8"
    System::Call "user32::GetCursorPos(p r8)i.r9"
    ${If} $9 == 0
        System::Free $8
        Return
    ${EndIf}
    System::Call "*$8(i.r0, i.r1)"
    System::Free $8

    StrCpy $R0 ""
    !insertmacro CHECK_FINISH_BADGE_HOVER $DiscordButton "discord"
    !insertmacro CHECK_FINISH_BADGE_HOVER $KofiButton "kofi"
    Call SetFinishBadgeHover
FunctionEnd

Function SetFinishBadgeHover
    ${If} $FinishBadgeHoverState == $R0
        Return
    ${EndIf}

    StrCpy $FinishBadgeHoverState "$R0"

    ${If} $DiscordBadgeImage != ""
        ${NSD_FreeImage} $DiscordBadgeImage
        StrCpy $DiscordBadgeImage ""
    ${EndIf}
    ${If} $R0 == "discord"
        ${NSD_SetImage} $DiscordButton "$PLUGINSDIR\discord-badge-hover.bmp" $DiscordBadgeImage
    ${Else}
        ${NSD_SetImage} $DiscordButton "$PLUGINSDIR\discord-badge.bmp" $DiscordBadgeImage
    ${EndIf}

    ${If} $KofiBadgeImage != ""
        ${NSD_FreeImage} $KofiBadgeImage
        StrCpy $KofiBadgeImage ""
    ${EndIf}
    ${If} $R0 == "kofi"
        ${NSD_SetImage} $KofiButton "$PLUGINSDIR\kofi-badge-hover.bmp" $KofiBadgeImage
    ${Else}
        ${NSD_SetImage} $KofiButton "$PLUGINSDIR\kofi-badge.bmp" $KofiBadgeImage
    ${EndIf}

FunctionEnd

Function OpenKofiPage
    Pop $0
    ExecShell "open" "https://ko-fi.com/louiewoolger"
FunctionEnd

Function OpenDiscordInvite
    Pop $0
    ExecShell "open" "https://discord.gg/zKbDADqWRC"
FunctionEnd

Function ResizePatchWizard
    LockWindow on

    System::Call 'user32::SetWindowPos(p$HWNDPARENT,p0,i0,i0,i900,i660,i0x16)'
    System::Call 'user32::SetWindowPos(p$Dialog,p0,i0,i0,i848,i500,i0x16)'

    GetDlgItem $0 $HWNDPARENT 1034
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i0,i894,i57,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1036
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i57,i894,i2,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1037
    System::Call 'user32::SetWindowPos(p$0,p0,i15,i8,i790,i16,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1038
    System::Call 'user32::SetWindowPos(p$0,p0,i23,i26,i790,i26,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1039
    System::Call 'user32::SetWindowPos(p$0,p0,i844,i13,i32,i32,i0x14)'

    GetDlgItem $0 $HWNDPARENT 1028
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i572,i870,i13,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1256
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i572,i870,i13,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1035
    System::Call 'user32::SetWindowPos(p$0,p0,i8,i585,i870,i2,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1045
    System::Call 'user32::SetWindowPos(p$0,p0,i0,i585,i894,i2,i0x14)'

    GetDlgItem $0 $HWNDPARENT 3
    System::Call 'user32::SetWindowPos(p$0,p0,i628,i593,i75,i23,i0x14)'
    GetDlgItem $0 $HWNDPARENT 1
    System::Call 'user32::SetWindowPos(p$0,p0,i708,i593,i75,i23,i0x14)'
    GetDlgItem $0 $HWNDPARENT 2
    System::Call 'user32::SetWindowPos(p$0,p0,i794,i593,i75,i23,i0x14)'

    LockWindow off
FunctionEnd

Function FixesPageCreate
    IfSilent fixesPageSilent fixesPageInteractive
fixesPageSilent:
    Return
fixesPageInteractive:
    ${If} $FixesPageVisited == "0"
        Call DetectGamePath
        StrCpy $SavedTargetDir "$INSTDIR"
        StrCpy $FixesPageVisited "1"
    ${ElseIf} $SavedTargetDir != ""
        StrCpy $INSTDIR "$SavedTargetDir"
    ${EndIf}
    !insertmacro MUI_HEADER_TEXT "Select patches" "Recommended options are selected by default. Hover over an option for more information."

    nsDialogs::Create 1018
    Pop $Dialog
    Call ResizePatchWizard
    ${NSD_OnBack} PatchPageBack
    CreateFont $PatchPageFont "Tahoma" "10" "400"
    CreateFont $PatchPageTitleFont "Tahoma" "12" "700"
    CreateFont $PatchPageBodyFont "Tahoma" "10" "400"

    ${NSD_CreateLabel} 0 0 100% 18 "Game folder"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $PatchPageFont 1
    ${NSD_CreateText} 0 24 688 26 "$INSTDIR"
    Pop $TargetText
    SendMessage $TargetText ${WM_SETFONT} $PatchPageFont 1
    ${NSD_CreateButton} 700 23 110 28 "Browse..."
    Pop $BrowseButton
    SendMessage $BrowseButton ${WM_SETFONT} $PatchPageFont 1
    ${NSD_OnClick} $BrowseButton BrowseTarget

    ${NSD_CreateGroupBox} 0 62 320 264 "Recommended"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $PatchPageFont 1

    ${NSD_CreateCheckbox} 12 94 295 24 "Terrain Movement Fix"
    Pop $DgVoodooCheck
    SendMessage $DgVoodooCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $DgVoodooSupported == "1"
        ${If} $SavedDgVoodooState == ${BST_CHECKED}
            ${NSD_Check} $DgVoodooCheck
        ${Else}
            ${NSD_Uncheck} $DgVoodooCheck
        ${EndIf}
    ${Else}
        EnableWindow $DgVoodooCheck 0
        ${NSD_Uncheck} $DgVoodooCheck
    ${EndIf}
    ${NSD_OnClick} $DgVoodooCheck PreviewDgVoodoo

    ${NSD_CreateCheckbox} 12 128 290 24 "Historical Campaigns Crash Fix"
    Pop $HistoricalCheck
    SendMessage $HistoricalCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedHistoricalState == ${BST_CHECKED}
        ${NSD_Check} $HistoricalCheck
    ${Else}
        ${NSD_Uncheck} $HistoricalCheck
    ${EndIf}
    ${NSD_OnClick} $HistoricalCheck PreviewHistorical

    ${NSD_CreateCheckbox} 12 162 290 24 "Voice Audio Fix"
    Pop $ThroneCheck
    SendMessage $ThroneCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedThroneState == ${BST_CHECKED}
        ${NSD_Check} $ThroneCheck
    ${Else}
        ${NSD_Uncheck} $ThroneCheck
    ${EndIf}
    ${NSD_OnClick} $ThroneCheck PreviewThrone

    ${NSD_CreateCheckbox} 12 196 295 24 "Limited Ammo Setting Fix"
    Pop $AmmoCheck
    SendMessage $AmmoCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedAmmoState == ${BST_CHECKED}
        ${NSD_Check} $AmmoCheck
    ${Else}
        ${NSD_Uncheck} $AmmoCheck
    ${EndIf}
    ${NSD_OnClick} $AmmoCheck PreviewAmmo

    ${NSD_CreateCheckbox} 12 230 295 24 "Kawanakajima AI Behaviour Fix"
    Pop $KawanakajimaCheck
    SendMessage $KawanakajimaCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedKawanakajimaState == ${BST_CHECKED}
        ${NSD_Check} $KawanakajimaCheck
    ${Else}
        ${NSD_Uncheck} $KawanakajimaCheck
    ${EndIf}
    ${NSD_OnClick} $KawanakajimaCheck PreviewKawanakajima

    ${NSD_CreateCheckbox} 12 264 295 24 "Odawara Rout Pathing Fix"
    Pop $OdawaraCheck
    SendMessage $OdawaraCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedOdawaraState == ${BST_CHECKED}
        ${NSD_Check} $OdawaraCheck
    ${Else}
        ${NSD_Uncheck} $OdawaraCheck
    ${EndIf}
    ${NSD_OnClick} $OdawaraCheck PreviewOdawara

    ${NSD_CreateGroupBox} 0 360 320 106 "Optional"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $PatchPageFont 1

    ${NSD_CreateCheckbox} 12 392 295 24 "120-Man Unit Balance Fix"
    Pop $UnitCheck
    SendMessage $UnitCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedUnitState == ${BST_CHECKED}
        ${NSD_Check} $UnitCheck
    ${Else}
        ${NSD_Uncheck} $UnitCheck
    ${EndIf}
    ${NSD_OnClick} $UnitCheck PreviewUnit

    ${NSD_CreateCheckbox} 12 426 295 24 "Annual Harvest Report Audio Restoration"
    Pop $HarvestCheck
    SendMessage $HarvestCheck ${WM_SETFONT} $PatchPageFont 1
    ${If} $SavedHarvestState == ${BST_CHECKED}
        ${NSD_Check} $HarvestCheck
    ${Else}
        ${NSD_Uncheck} $HarvestCheck
    ${EndIf}
    ${NSD_OnClick} $HarvestCheck PreviewHarvest

    ${NSD_CreateGroupBox} 340 62 506 430 "Preview"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $PatchPageFont 1
    ${NSD_CreateBitmap} 352 92 480 270 ""
    Pop $PreviewBitmap
    ${NSD_CreateLabel} 352 374 480 28 ""
    Pop $PreviewTitle
    SendMessage $PreviewTitle ${WM_SETFONT} $PatchPageTitleFont 1
    ${NSD_CreateLabel} 352 410 480 56 ""
    Pop $PreviewText
    SendMessage $PreviewText ${WM_SETFONT} $PatchPageBodyFont 1
    ${NSD_CreateLabel} 352 474 480 24 ""
    Pop $PreviewWarningText
    SendMessage $PreviewWarningText ${WM_SETFONT} $PatchPageBodyFont 1
    SetCtlColors $PreviewWarningText FF0000 F0F0F0
    ShowWindow $PreviewWarningText ${SW_HIDE}

    StrCpy $CurrentPreviewKey ""
    ${If} $DgVoodooSupported == "1"
        StrCpy $R0 "dgvoodoo"
    ${Else}
        StrCpy $R0 "historical"
    ${EndIf}
    Call SetPreview
    ${NSD_CreateTimer} PreviewHoverTimer 120

    nsDialogs::Show
    ${NSD_KillTimer} PreviewHoverTimer

    ${If} $PreviewImage != ""
        System::Call "gdi32::DeleteObject(p$PreviewImage)"
    ${EndIf}
    System::Call "gdi32::DeleteObject(p$PatchPageFont)"
    System::Call "gdi32::DeleteObject(p$PatchPageTitleFont)"
    System::Call "gdi32::DeleteObject(p$PatchPageBodyFont)"
FunctionEnd

Function SaveFixesPageState
    ${NSD_GetText} $TargetText $SavedTargetDir
    StrCpy $INSTDIR "$SavedTargetDir"
    ${NSD_GetState} $DgVoodooCheck $SavedDgVoodooState
    ${NSD_GetState} $HistoricalCheck $SavedHistoricalState
    ${NSD_GetState} $KawanakajimaCheck $SavedKawanakajimaState
    ${NSD_GetState} $OdawaraCheck $SavedOdawaraState
    ${NSD_GetState} $ThroneCheck $SavedThroneState
    ${NSD_GetState} $UnitCheck $SavedUnitState
    ${NSD_GetState} $AmmoCheck $SavedAmmoState
    ${NSD_GetState} $HarvestCheck $SavedHarvestState
FunctionEnd

Function PatchPageBack
    Call SaveFixesPageState
    Call RestoreDefaultWizard
FunctionEnd

Function BrowseTarget
    Pop $0
    nsDialogs::SelectFolderDialog "Select the Shogun: Total War game folder" "$INSTDIR"
    Pop $1
    ${If} $1 != "error"
        StrCpy $INSTDIR "$1"
        ${NSD_SetText} $TargetText "$INSTDIR"
    ${EndIf}
FunctionEnd

Function PreviewHistorical
    Pop $0
    StrCpy $R0 "historical"
    Call SetPreview
FunctionEnd

Function PreviewKawanakajima
    Pop $0
    StrCpy $R0 "kawanakajima"
    Call SetPreview
FunctionEnd

Function PreviewOdawara
    Pop $0
    StrCpy $R0 "odawara"
    Call SetPreview
FunctionEnd

Function PreviewThrone
    Pop $0
    ${NSD_GetState} $HarvestCheck $1
    ${NSD_GetState} $ThroneCheck $2
    ${If} $1 == ${BST_CHECKED}
    ${AndIf} $2 != ${BST_CHECKED}
        ${NSD_Uncheck} $HarvestCheck
    ${EndIf}
    StrCpy $R0 "throne"
    Call SetPreview
FunctionEnd

Function PreviewUnit
    Pop $0
    StrCpy $R0 "unit"
    Call SetPreview
FunctionEnd

Function PreviewDgVoodoo
    Pop $0
    StrCpy $R0 "dgvoodoo"
    Call SetPreview
FunctionEnd

Function PreviewAmmo
    Pop $0
    StrCpy $R0 "ammo"
    Call SetPreview
FunctionEnd

Function PreviewHarvest
    Pop $0
    ${NSD_GetState} $HarvestCheck $1
    ${If} $1 == ${BST_CHECKED}
        ${NSD_Check} $ThroneCheck
    ${EndIf}
    StrCpy $R0 "harvest"
    Call SetPreview
FunctionEnd

Function PreviewHoverTimer
    Call PreviewFromCursor
FunctionEnd

Function PreviewFromCursor
    System::Call "*(i 0, i 0) p.r8"
    System::Call "user32::GetCursorPos(p r8)i.r9"
    ${If} $9 == 0
        System::Free $8
        Return
    ${EndIf}
    System::Call "*$8(i.r0, i.r1)"
    System::Free $8

    System::Call "user32::WindowFromPoint(ir0, ir1)p.r7"
    ${If} $7 == 0
        Return
    ${EndIf}
    ${If} $7 != $HWNDPARENT
        System::Call "user32::IsChild(p$HWNDPARENT, pr7)i.r9"
        ${If} $9 == 0
            Return
        ${EndIf}
    ${EndIf}

    !insertmacro CHECK_PREVIEW_HOVER $DgVoodooCheck "dgvoodoo"
    !insertmacro CHECK_PREVIEW_HOVER $HistoricalCheck "historical"
    !insertmacro CHECK_PREVIEW_HOVER $KawanakajimaCheck "kawanakajima"
    !insertmacro CHECK_PREVIEW_HOVER $OdawaraCheck "odawara"
    !insertmacro CHECK_PREVIEW_HOVER $ThroneCheck "throne"
    !insertmacro CHECK_PREVIEW_HOVER $UnitCheck "unit"
    !insertmacro CHECK_PREVIEW_HOVER $AmmoCheck "ammo"
    !insertmacro CHECK_PREVIEW_HOVER $HarvestCheck "harvest"
FunctionEnd

Function SetPreview
    ${If} $CurrentPreviewKey == $R0
        Return
    ${EndIf}
    StrCpy $CurrentPreviewKey "$R0"

    ${If} $PreviewImage != ""
        System::Call "gdi32::DeleteObject(p$PreviewImage)"
        StrCpy $PreviewImage ""
    ${EndIf}

    ${If} $R0 == "historical"
        ${NSD_SetText} $PreviewTitle "Historical Campaigns Crash Fix"
        ${NSD_SetText} $PreviewText "Fixes crashes in certain historical campaign battles when timed reinforcements arrive."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\historical.bmp"
    ${ElseIf} $R0 == "kawanakajima"
        ${NSD_SetText} $PreviewTitle "Kawanakajima AI Behaviour Fix"
        ${NSD_SetText} $PreviewText "Fixes the Uesugi AI in the 4th Kawanakajima historical battle so its army no longer remains passive."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\kawanakajima.bmp"
    ${ElseIf} $R0 == "odawara"
        ${NSD_SetText} $PreviewTitle "Odawara Rout Pathing Fix"
        ${NSD_SetText} $PreviewText "Fixes routed Hojo units in the Odawara historical campaign battle so they retreat toward the nearest map edge instead of being sent into the wall and becoming stuck."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\odawara.bmp"
    ${ElseIf} $R0 == "throne"
        ${NSD_SetText} $PreviewTitle "Voice Audio Fix"
        ${NSD_SetText} $PreviewText "Fixes voice clips cutting out across the game, including throne room dialogue, and other spoken lines."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\throne.bmp"
    ${ElseIf} $R0 == "unit"
        ${NSD_SetText} $PreviewTitle "120-Man Unit Balance Fix"
        ${NSD_SetText} $PreviewText "Rebalances 120-man unit sizes so recruitment cost, upkeep cost, and training time remain consistent with the 60-man unit size setting."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\unit.bmp"
    ${ElseIf} $R0 == "ammo"
        ${NSD_SetText} $PreviewTitle "Limited Ammo Setting Fix"
        ${NSD_SetText} $PreviewText "Ensures the Limited Ammo setting works correctly in campaign and historical battles when disabled."
        ${NSD_SetText} $PreviewWarningText ""
        ShowWindow $PreviewWarningText ${SW_HIDE}
        StrCpy $1 "$PLUGINSDIR\ammo.bmp"
    ${ElseIf} $R0 == "dgvoodoo"
        ${NSD_SetText} $PreviewTitle "Terrain Movement Fix"
        ${NSD_SetText} $PreviewText "Installs dgVoodoo2 to fix click-to-move and drag-formation issues on modern Windows systems."
        ${NSD_SetText} $PreviewWarningText "Windows XP is not supported."
        ShowWindow $PreviewWarningText ${SW_SHOW}
        StrCpy $1 "$PLUGINSDIR\dgvoodoo.bmp"
    ${Else}
        ${NSD_SetText} $PreviewTitle "Annual Harvest Report Audio Restoration"
        ${NSD_SetText} $PreviewText "Restores the original voice clips heard during the annual harvest report."
        ${NSD_SetText} $PreviewWarningText "Requires voice audio fix to be installed."
        ShowWindow $PreviewWarningText ${SW_SHOW}
        StrCpy $1 "$PLUGINSDIR\harvest.bmp"
    ${EndIf}

    ${NSD_SetImage} $PreviewBitmap "$1" $PreviewImage
FunctionEnd

Function AddSelectedFlag
    ${If} $SelectedFlags == ""
        StrCpy $SelectedFlags "$R0"
    ${Else}
        StrCpy $SelectedFlags "$SelectedFlags,$R0"
    ${EndIf}
FunctionEnd

Function AddPatcherFlag
    ${If} $PatcherFlags == ""
        StrCpy $PatcherFlags "$R0"
    ${Else}
        StrCpy $PatcherFlags "$PatcherFlags,$R0"
    ${EndIf}
FunctionEnd

Function FixesPageLeave
    Call SaveFixesPageState

    ${IfNot} ${FileExists} "$INSTDIR\ShogunM.exe"
        MessageBox MB_ICONEXCLAMATION|MB_OK "Select the game folder that contains ShogunM.exe." /SD IDOK
        Abort
    ${EndIf}

    ${NSD_GetState} $HarvestCheck $0
    ${If} $0 == ${BST_CHECKED}
        ${NSD_Check} $ThroneCheck
        StrCpy $SavedThroneState ${BST_CHECKED}
    ${EndIf}

    StrCpy $SelectedFlags ""
    StrCpy $PatcherFlags ""
    StrCpy $InstallDgVoodoo "0"

    ${NSD_GetState} $DgVoodooCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "dgvoodoo"
        Call AddSelectedFlag
        StrCpy $InstallDgVoodoo "1"
    ${EndIf}

    ${NSD_GetState} $HistoricalCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "historical"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $ThroneCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "throne"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $UnitCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "unit"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $AmmoCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "ammo"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $KawanakajimaCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "kawanakajima"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $OdawaraCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "odawara"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${NSD_GetState} $HarvestCheck $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $R0 "harvest"
        Call AddSelectedFlag
        Call AddPatcherFlag
    ${EndIf}

    ${If} $SelectedFlags == ""
        MessageBox MB_ICONEXCLAMATION|MB_OK "Select at least one fix to install." /SD IDOK
        Abort
    ${EndIf}

    Call RestoreDefaultWizard
FunctionEnd

!macro BACKUP_DGVOODOO_FILE NAME
    ${If} ${FileExists} "$INSTDIR\${NAME}"
    ${AndIfNot} ${FileExists} "$INSTDIR\${NAME}.unofficial-patch.bak"
        nsExec::ExecToStack '"$SYSDIR\cmd.exe" /C fc /B "$INSTDIR\${NAME}" "$PLUGINSDIR\dgvoodoo\${NAME}" >NUL'
        Pop $0
        Pop $1
        ${If} $0 != 0
            ClearErrors
            CopyFiles /SILENT "$INSTDIR\${NAME}" "$INSTDIR\${NAME}.unofficial-patch.bak"
            ${If} ${Errors}
                MessageBox MB_ICONSTOP|MB_OK "The existing ${NAME} file could not be backed up. No dgVoodoo2 files were overwritten. Check that the game folder is writable and rerun this installer." /SD IDOK
                !insertmacro ABORT_INSTALL
            ${Else}
                StrCpy $BackupsGenerated "1"
            ${EndIf}
        ${EndIf}
    ${EndIf}
!macroend

!macro PROTECT_EXISTING_DGVOODOO_FILE NAME
    ${If} ${FileExists} "$INSTDIR\${NAME}"
    ${AndIf} ${FileExists} "$INSTDIR\${NAME}.unofficial-patch.bak"
        ClearErrors
        nsExec::ExecToStack '"$SYSDIR\cmd.exe" /C fc /B "$INSTDIR\${NAME}" "$PLUGINSDIR\dgvoodoo\${NAME}" >NUL'
        Pop $0
        Pop $1
        ${If} $0 != 0
            DetailPrint "Skipped dgVoodoo2 overwrite: existing ${NAME} differs from the bundled file and a backup already exists."
            MessageBox MB_ICONSTOP|MB_OK "The existing ${NAME} file differs from the bundled dgVoodoo2 file, and ${NAME}.unofficial-patch.bak already exists. To avoid overwriting your current file, the terrain movement fix was not installed. Move or rename the current file or backup, then run the installer again." /SD IDOK
            !insertmacro ABORT_INSTALL
        ${EndIf}
    ${EndIf}
!macroend

!macro ROLLBACK_DGVOODOO_FILE NAME
    ${If} ${FileExists} "$PLUGINSDIR\dgrollback\${NAME}"
        DetailPrint "Restoring ${NAME} to its pre-install state after dgVoodoo2 install failure"
        ClearErrors
        CopyFiles /SILENT "$PLUGINSDIR\dgrollback\${NAME}" "$INSTDIR\${NAME}"
        ${If} ${Errors}
            StrCpy $DgVoodooRollbackFailed "1"
        ${EndIf}
    ${Else}
        DetailPrint "Removing ${NAME} after dgVoodoo2 install failure"
        ClearErrors
        Delete "$INSTDIR\${NAME}"
        ${If} ${FileExists} "$INSTDIR\${NAME}"
            StrCpy $DgVoodooRollbackFailed "1"
        ${EndIf}
    ${EndIf}
!macroend

Function RollbackDgVoodooFiles
    StrCpy $DgVoodooRollbackFailed "0"
    !insertmacro ROLLBACK_DGVOODOO_FILE "DDraw.dll"
    !insertmacro ROLLBACK_DGVOODOO_FILE "D3DImm.dll"
    !insertmacro ROLLBACK_DGVOODOO_FILE "D3D9.dll"
    !insertmacro ROLLBACK_DGVOODOO_FILE "dgVoodoo.conf"
FunctionEnd

!macro PREPARE_DGVOODOO_ROLLBACK_FILE NAME
    ${If} ${FileExists} "$INSTDIR\${NAME}"
        ClearErrors
        CopyFiles /SILENT "$INSTDIR\${NAME}" "$PLUGINSDIR\dgrollback\${NAME}"
        ${If} ${Errors}
            MessageBox MB_ICONSTOP|MB_OK "The existing ${NAME} file could not be prepared for rollback. No dgVoodoo2 files were overwritten. Check that the game folder is readable and rerun this installer." /SD IDOK
            !insertmacro ABORT_INSTALL
        ${EndIf}
    ${EndIf}
!macroend

Function PrepareDgVoodooRollback
    RMDir /r "$PLUGINSDIR\dgrollback"
    CreateDirectory "$PLUGINSDIR\dgrollback"
    !insertmacro PREPARE_DGVOODOO_ROLLBACK_FILE "DDraw.dll"
    !insertmacro PREPARE_DGVOODOO_ROLLBACK_FILE "D3DImm.dll"
    !insertmacro PREPARE_DGVOODOO_ROLLBACK_FILE "D3D9.dll"
    !insertmacro PREPARE_DGVOODOO_ROLLBACK_FILE "dgVoodoo.conf"
FunctionEnd

!macro INSTALL_DGVOODOO_FILE NAME
    ClearErrors
    CopyFiles /SILENT "$PLUGINSDIR\dgvoodoo\${NAME}" "$INSTDIR\${NAME}"
    ${If} ${Errors}
        DetailPrint "Failed to install ${NAME}; rolling back dgVoodoo2 files"
        Call RollbackDgVoodooFiles
        ${If} $DgVoodooRollbackFailed == "1"
            MessageBox MB_ICONSTOP|MB_OK "dgVoodoo2 files could not be installed, and one or more wrapper files could not be restored automatically. Check the installer details log and your backup files in the game folder." /SD IDOK
        ${Else}
            MessageBox MB_ICONSTOP|MB_OK "dgVoodoo2 files could not be installed. The installer restored any wrapper files it changed. If the game is installed under Program Files, close the game and rerun this installer as administrator." /SD IDOK
        ${EndIf}
        !insertmacro ABORT_INSTALL
    ${EndIf}
!macroend

Function VerifyTargetFolderWritable
    ClearErrors
    FileOpen $0 "$INSTDIR\.unofficial-patch-write-test.tmp" w
    ${If} ${Errors}
        MessageBox MB_ICONSTOP|MB_OK "The selected game folder is not writable. If the game is installed under Program Files, close the game and rerun this installer as administrator." /SD IDOK
        !insertmacro ABORT_INSTALL
    ${EndIf}
    FileClose $0
    Delete "$INSTDIR\.unofficial-patch-write-test.tmp"
FunctionEnd

Function ValidateSilentTargetOverride
    IfSilent validate done
validate:
    ${IfNot} ${FileExists} "$INSTDIR\ShogunM.exe"
        MessageBox MB_ICONSTOP|MB_OK "ShogunM.exe was not found in the silent install target folder. Run the installer from your Shogun: Total War Collection game folder or pass the game folder with /D=." /SD IDOK
        !insertmacro ABORT_INSTALL
    ${EndIf}
done:
FunctionEnd

Function InstallDgVoodooFiles
    DetailPrint "Installing dgVoodoo2 v2.87.2 wrapper files"
    SetOutPath "$PLUGINSDIR\dgvoodoo"
    ClearErrors
    File /oname=DDraw.dll "${SOURCE_DIR}\vendor\dgvoodoo2\DDraw.dll"
    File /oname=D3DImm.dll "${SOURCE_DIR}\vendor\dgvoodoo2\D3DImm.dll"
    File /oname=D3D9.dll "${SOURCE_DIR}\vendor\dgvoodoo2\D3D9.dll"
    File /oname=dgVoodoo.conf "${SOURCE_DIR}\vendor\dgvoodoo2\dgVoodoo.conf"
    ${If} ${Errors}
        MessageBox MB_ICONSTOP|MB_OK "dgVoodoo2 files could not be prepared for installation." /SD IDOK
        !insertmacro ABORT_INSTALL
    ${EndIf}

    !insertmacro PROTECT_EXISTING_DGVOODOO_FILE "DDraw.dll"
    !insertmacro PROTECT_EXISTING_DGVOODOO_FILE "D3DImm.dll"
    !insertmacro PROTECT_EXISTING_DGVOODOO_FILE "D3D9.dll"
    !insertmacro PROTECT_EXISTING_DGVOODOO_FILE "dgVoodoo.conf"
    Call PrepareDgVoodooRollback
    !insertmacro BACKUP_DGVOODOO_FILE "DDraw.dll"
    !insertmacro BACKUP_DGVOODOO_FILE "D3DImm.dll"
    !insertmacro BACKUP_DGVOODOO_FILE "D3D9.dll"
    !insertmacro BACKUP_DGVOODOO_FILE "dgVoodoo.conf"

    SetOutPath "$INSTDIR"
    !insertmacro INSTALL_DGVOODOO_FILE "DDraw.dll"
    !insertmacro INSTALL_DGVOODOO_FILE "D3DImm.dll"
    !insertmacro INSTALL_DGVOODOO_FILE "D3D9.dll"
    !insertmacro INSTALL_DGVOODOO_FILE "dgVoodoo.conf"
FunctionEnd

Section "Apply selected fixes"
    Call ValidateSilentTargetOverride
    ${IfNot} ${FileExists} "$INSTDIR\ShogunM.exe"
        MessageBox MB_ICONSTOP|MB_OK "ShogunM.exe was not found. Select your Shogun: Total War Collection game folder and run the installer again." /SD IDOK
        !insertmacro ABORT_INSTALL
    ${EndIf}
    Call VerifyTargetFolderWritable
    SetOutPath "$PLUGINSDIR"
    File /oname=shogun-fix-patcher.exe "${SOURCE_DIR}\build\shogun-fix-patcher.exe"

    DetailPrint "Target folder: $INSTDIR"
    DetailPrint "Selected fixes: $SelectedFlags"
    ${If} $PatcherFlags != ""
        DetailPrint "Helper fixes: $PatcherFlags"
        nsExec::ExecToStack '"$PLUGINSDIR\shogun-fix-patcher.exe" --target "$INSTDIR" --apply "$PatcherFlags"'
        Pop $0
        Pop $PatcherOutput
        DetailPrint "$PatcherOutput"
        ${If} $0 != 0
            MessageBox MB_ICONSTOP|MB_OK "The selected fixes could not be applied. Check the installer details log for the exact error. If the game is installed under Program Files, close the game and rerun this installer as administrator." /SD IDOK
            !insertmacro ABORT_INSTALL
        ${EndIf}
        ${StrStr} $1 "$PatcherOutput" "backup_created="
        ${If} $1 != ""
            StrCpy $BackupsGenerated "1"
        ${EndIf}
    ${EndIf}

    ${If} $InstallDgVoodoo == "1"
        Call InstallDgVoodooFiles
    ${EndIf}
SectionEnd
