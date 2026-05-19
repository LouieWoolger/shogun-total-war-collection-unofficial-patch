from __future__ import annotations

from pathlib import Path
import struct


SCRIPT = Path(__file__).resolve().parents[1] / "installer.nsi"
ASSETS = Path(__file__).resolve().parents[1] / "assets"
VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "dgvoodoo2"


def script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def bmp_pixel(path: Path, x: int, y: int) -> tuple[int, int, int]:
    data = path.read_bytes()
    width, height = struct.unpack_from("<ii", data, 18)
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    row_stride = ((width * bits_per_pixel + 31) // 32) * 4
    row = height - 1 - y if height > 0 else y
    index = pixel_offset + row * row_stride + x * 3
    blue, green, red = data[index : index + 3]
    return red, green, blue


def assert_rgb_close(actual: tuple[int, int, int], expected: tuple[int, int, int], tolerance: int = 8) -> None:
    assert all(abs(a - e) <= tolerance for a, e in zip(actual, expected)), (actual, expected)


def test_installer_branding_and_output_name() -> None:
    text = script_text()

    assert '!define APP_NAME "Unofficial Shogun: Total War Collection Patch Setup"' in text
    assert 'OutFile "${SOURCE_DIR}\\dist\\Unofficial Shogun Total War Collection Patch.exe"' in text
    assert '!define MUI_ICON "${SOURCE_DIR}\\assets\\shogun.ico"' in text
    assert '!define MUI_WELCOMEFINISHPAGE_BITMAP "${SOURCE_DIR}\\assets\\welcome-finish.bmp"' in text
    assert 'Icon "${SOURCE_DIR}\\assets\\shogun.ico"' not in text
    assert (ASSETS / "shogun.ico").is_file()
    assert (ASSETS / "welcome-finish.bmp").is_file()
    assert (
        '!define MUI_ABORTWARNING_TEXT "Are you sure you want to quit the '
        'Unofficial Shogun: Total War Collection Patch Setup?"'
    ) in text
    assert '!define MUI_WELCOMEPAGE_TITLE "Install Unofficial Shogun Total War Collection Patch"' in text
    assert "This installer patches your existing Shogun: Total War Collection folder." in text
    assert "Recommended options are selected by default." in text
    assert "Recommended fixes are selected by default." not in text
    assert "Shogun: Total War Fixes" not in text
    assert "ShogunTotalWarFixesSetup.exe" not in text


def test_finish_page_copy_reflects_backup_state() -> None:
    text = script_text()

    assert '!define MUI_FINISHPAGE_TITLE "Installation complete"' in text
    assert '!define MUI_FINISHPAGE_TEXT "Selected options were applied to your game. Have fun!"' in text
    assert "Fixes applied" not in text
    assert "Selected fixes were applied to ShogunM.exe" not in text
    assert "Var BackupsGenerated" in text
    assert 'StrCpy $BackupsGenerated "0"' in text
    assert "!define MUI_PAGE_CUSTOMFUNCTION_SHOW FinishPageShow" in text
    assert 'Function FinishPageShow' in text
    assert 'Backup files were generated in your game folder.' in text
    assert '${NSD_SetText} $mui.FinishPage.Text "Selected options were applied to your game. Backup files were generated in your game folder. Have fun!"' in text
    assert '${NSD_SetText} $mui.FinishPage.Text "Selected options were applied to your game. Have fun!"' in text


def test_finish_page_has_optional_support_and_community_buttons() -> None:
    text = script_text()
    finish_page = text.split("Function FinishPageShow", 1)[1].split("FunctionEnd", 1)[0]

    assert "Var KofiButton" in text
    assert "Var DiscordButton" in text
    assert "Var KofiBadgeImage" in text
    assert "Var DiscordBadgeImage" in text
    assert "Var FinishBadgeHoverState" in text
    assert 'File /oname=$PLUGINSDIR\\kofi-badge.bmp "${SOURCE_DIR}\\assets\\kofi-badge.bmp"' in text
    assert 'File /oname=$PLUGINSDIR\\discord-badge.bmp "${SOURCE_DIR}\\assets\\discord-badge.bmp"' in text
    assert 'File /oname=$PLUGINSDIR\\kofi-badge-hover.bmp "${SOURCE_DIR}\\assets\\kofi-badge-hover.bmp"' in text
    assert 'File /oname=$PLUGINSDIR\\discord-badge-hover.bmp "${SOURCE_DIR}\\assets\\discord-badge-hover.bmp"' in text
    assert "user32::SetWindowPos(p$mui.FinishPage.Text,p0,i180,i100,i293,i64,i0x14)" in finish_page
    assert "Optional support and community links:" not in finish_page
    assert '${NSD_CreateBitmap} 120u 169u 92u 17u ""' in finish_page
    assert '${NSD_SetImage} $DiscordButton "$PLUGINSDIR\\discord-badge.bmp" $DiscordBadgeImage' in finish_page
    assert '${NSD_CreateBitmap} 223u 169u 92u 17u ""' in finish_page
    assert '${NSD_SetImage} $KofiButton "$PLUGINSDIR\\kofi-badge.bmp" $KofiBadgeImage' in finish_page
    assert "${NSD_CreateTimer} FinishBadgeHoverTimer 60" in finish_page
    assert '"Buy me a coffee"' not in finish_page
    assert '"Join Discord"' not in finish_page
    assert "${NSD_OnClick} $KofiButton OpenKofiPage" in finish_page
    assert "${NSD_OnClick} $DiscordButton OpenDiscordInvite" in finish_page
    assert "Function FinishBadgeHoverTimer" in text
    assert "Function FinishBadgeFromCursor" in text
    assert "Function SetFinishBadgeHover" in text
    assert '${NSD_SetImage} $DiscordButton "$PLUGINSDIR\\discord-badge-hover.bmp" $DiscordBadgeImage' in text
    assert '${NSD_SetImage} $KofiButton "$PLUGINSDIR\\kofi-badge-hover.bmp" $KofiBadgeImage' in text
    assert "LoadCursor" not in text
    assert "SetCursor" not in text
    assert "Function FinishPageDestroyed" in text
    assert "${NSD_KillTimer} FinishBadgeHoverTimer" in text
    assert "${NSD_FreeImage} $KofiBadgeImage" in text
    assert "${NSD_FreeImage} $DiscordBadgeImage" in text
    assert 'Function OpenKofiPage' in text
    assert 'ExecShell "open" "https://ko-fi.com/louiewoolger"' in text
    assert 'Function OpenDiscordInvite' in text
    assert 'ExecShell "open" "https://discord.gg/zKbDADqWRC"' in text
    assert text.count("https://ko-fi.com/louiewoolger") == 1
    assert text.count("https://discord.gg/zKbDADqWRC") == 1


def test_finish_badge_bitmaps_match_readme_badge_style() -> None:
    assert (ASSETS / "discord-social-icon.png").is_file()
    assert (ASSETS / "kofi-social-icon.png").is_file()

    for name in ("discord-badge.bmp", "kofi-badge.bmp", "discord-badge-hover.bmp", "kofi-badge-hover.bmp"):
        assert (ASSETS / name).is_file()
        data = (ASSETS / name).read_bytes()
        width, height = struct.unpack_from("<ii", data, 18)
        bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
        assert width == 138
        assert abs(height) == 28
        assert bits_per_pixel == 24

    discord = ASSETS / "discord-badge.bmp"
    kofi = ASSETS / "kofi-badge.bmp"
    assert bmp_pixel(discord, 4, 14) == (85, 87, 93)
    assert bmp_pixel(discord, 92, 14) == (88, 101, 242)
    assert_rgb_close(bmp_pixel(discord, 14, 12), (88, 101, 242))
    assert bmp_pixel(discord, 12, 14) == (85, 87, 93)
    assert bmp_pixel(discord, 20, 14) == (85, 87, 93)
    assert bmp_pixel(kofi, 4, 14) == (85, 87, 93)
    assert bmp_pixel(kofi, 82, 14) == (255, 95, 95)
    assert_rgb_close(bmp_pixel(kofi, 22, 14), (255, 255, 255))
    assert_rgb_close(bmp_pixel(kofi, 16, 15), (255, 90, 22))
    assert bmp_pixel(kofi, 29, 14) == (85, 87, 93)
    assert bmp_pixel(ASSETS / "discord-badge-hover.bmp", 92, 14) == (122, 136, 255)
    assert bmp_pixel(ASSETS / "kofi-badge-hover.bmp", 82, 14) == (255, 135, 135)
    assert bmp_pixel(ASSETS / "discord-badge-hover.bmp", 1, 0) == (153, 153, 153)
    assert bmp_pixel(ASSETS / "kofi-badge-hover.bmp", 1, 0) == (153, 153, 153)
    assert bmp_pixel(discord, 4, 27) == (85, 87, 93)
    assert bmp_pixel(discord, 92, 27) == (88, 101, 242)
    assert bmp_pixel(kofi, 4, 27) == (85, 87, 93)
    assert bmp_pixel(kofi, 82, 27) == (255, 95, 95)


def test_installer_marks_backups_generated_only_when_new_backups_are_created() -> None:
    text = script_text()

    assert '!include StrFunc.nsh' in text
    assert '${Using:StrFunc} StrStr' in text
    assert 'nsExec::ExecToStack \'\"$PLUGINSDIR\\shogun-fix-patcher.exe\" --target "$INSTDIR" --apply "$PatcherFlags"\'' in text
    assert 'Pop $PatcherOutput' in text
    assert '${StrStr} $1 "$PatcherOutput" "backup_created="' in text
    assert 'StrCpy $BackupsGenerated "1"' in text
    dgvoodoo_backup_macro = text.split("!macro BACKUP_DGVOODOO_FILE NAME", 1)[1].split("!macroend", 1)[0]
    assert 'nsExec::ExecToStack \'"$SYSDIR\\cmd.exe" /C fc /B "$INSTDIR\\${NAME}" "$PLUGINSDIR\\dgvoodoo\\${NAME}" >NUL\'' in dgvoodoo_backup_macro
    assert "${If} $0 != 0" in dgvoodoo_backup_macro
    assert "ClearErrors" in dgvoodoo_backup_macro
    assert 'CopyFiles /SILENT "$INSTDIR\\${NAME}" "$INSTDIR\\${NAME}.unofficial-patch.bak"' in dgvoodoo_backup_macro
    assert 'MessageBox MB_ICONSTOP|MB_OK "The existing ${NAME} file could not be backed up.' in dgvoodoo_backup_macro
    assert '/SD IDOK' in dgvoodoo_backup_macro
    assert "Abort" in dgvoodoo_backup_macro
    assert 'StrCpy $BackupsGenerated "1"' in dgvoodoo_backup_macro
    assert ".unofficial-patch-dgvoodoo-installed" not in text


def test_dgvoodoo_reinstall_refuses_to_overwrite_modified_files_when_backup_exists() -> None:
    text = script_text()
    protect_macro = text.split("!macro PROTECT_EXISTING_DGVOODOO_FILE NAME", 1)[1].split("!macroend", 1)[0]
    install_function = text.split("Function InstallDgVoodooFiles", 1)[1].split("FunctionEnd", 1)[0]

    assert 'nsExec::ExecToStack \'"$SYSDIR\\cmd.exe" /C fc /B "$INSTDIR\\${NAME}" "$PLUGINSDIR\\dgvoodoo\\${NAME}" >NUL\'' in protect_macro
    assert "Skipped dgVoodoo2 overwrite" in protect_macro
    assert "differs from the bundled dgVoodoo2 file" in protect_macro
    assert "Abort" in protect_macro
    assert install_function.index('File /oname=D3D9.dll "${SOURCE_DIR}\\vendor\\dgvoodoo2\\D3D9.dll"') < install_function.index('!insertmacro PROTECT_EXISTING_DGVOODOO_FILE "D3D9.dll"')
    assert install_function.index('!insertmacro PROTECT_EXISTING_DGVOODOO_FILE "D3D9.dll"') < install_function.index('!insertmacro BACKUP_DGVOODOO_FILE "D3D9.dll"')
    assert install_function.index('!insertmacro BACKUP_DGVOODOO_FILE "D3D9.dll"') < install_function.index('!insertmacro INSTALL_DGVOODOO_FILE "D3D9.dll"')


def test_dgvoodoo_copy_failure_rolls_back_changed_wrapper_files() -> None:
    text = script_text()
    rollback_macro = text.split("!macro ROLLBACK_DGVOODOO_FILE NAME", 1)[1].split("!macroend", 1)[0]
    rollback_function = text.split("Function RollbackDgVoodooFiles", 1)[1].split("FunctionEnd", 1)[0]
    prepare_function = text.split("Function PrepareDgVoodooRollback", 1)[1].split("FunctionEnd", 1)[0]
    install_macro = text.split("!macro INSTALL_DGVOODOO_FILE NAME", 1)[1].split("!macroend", 1)[0]
    install_function = text.split("Function InstallDgVoodooFiles", 1)[1].split("FunctionEnd", 1)[0]

    for name in ("DDraw.dll", "D3DImm.dll", "D3D9.dll", "dgVoodoo.conf"):
        assert f'!insertmacro PREPARE_DGVOODOO_ROLLBACK_FILE "{name}"' in prepare_function
        assert f'!insertmacro ROLLBACK_DGVOODOO_FILE "{name}"' in rollback_function
        assert f'!insertmacro INSTALL_DGVOODOO_FILE "{name}"' in install_function

    assert "Var DgVoodooRollbackFailed" in text
    assert 'CopyFiles /SILENT "$INSTDIR\\${NAME}" "$PLUGINSDIR\\dgrollback\\${NAME}"' in text
    assert 'CopyFiles /SILENT "$PLUGINSDIR\\dgrollback\\${NAME}" "$INSTDIR\\${NAME}"' in rollback_macro
    assert 'StrCpy $DgVoodooRollbackFailed "1"' in rollback_macro
    assert "Call PrepareDgVoodooRollback" in install_function
    assert install_function.index('Call PrepareDgVoodooRollback') < install_function.index('!insertmacro BACKUP_DGVOODOO_FILE "D3D9.dll"')
    assert 'CopyFiles /SILENT "$PLUGINSDIR\\dgvoodoo\\${NAME}" "$INSTDIR\\${NAME}"' in install_macro
    assert "Call RollbackDgVoodooFiles" in install_macro
    assert "The installer restored any wrapper files it changed." in install_macro
    assert "could not be restored automatically" in install_macro
    assert "Abort" in install_macro


def test_install_preflights_game_folder_write_access_before_any_payload_writes() -> None:
    text = script_text()
    section = text.split('Section "Apply selected fixes"', 1)[1].split("SectionEnd", 1)[0]

    assert "Function VerifyTargetFolderWritable" in text
    assert 'FileOpen $0 "$INSTDIR\\.unofficial-patch-write-test.tmp" w' in text
    assert 'Delete "$INSTDIR\\.unofficial-patch-write-test.tmp"' in text
    assert '${IfNot} ${FileExists} "$INSTDIR\\ShogunM.exe"' in section
    assert section.index('${IfNot} ${FileExists} "$INSTDIR\\ShogunM.exe"') < section.index("Call VerifyTargetFolderWritable")
    assert section.index("Call VerifyTargetFolderWritable") < section.index('File /oname=shogun-fix-patcher.exe')


def test_patches_page_copy_and_requested_descriptions() -> None:
    text = script_text()

    assert '!insertmacro MUI_HEADER_TEXT "Select patches" "Recommended options are selected by default. Hover over an option for more information."' in text
    assert '"Game folder"' in text
    assert "Game folder containing ShogunM.exe" not in text
    assert '"Historical campaign fix"' in text
    assert "Historical campaign reinforcement fix" not in text
    assert "Fixes a bug that causes the game to crash in certain battles when reinforcements arrive." in text
    assert "Fixes a bug that causes audio in the throne room to cut out." in text
    assert '"Recruitment, upkeep && training fix"' in text
    assert (
        "Fixes a bug where setting battle unit size to 120 will double recruitment cost, "
        "upkeep cost, and training time for every unit."
    ) in text
    assert "Restores the original voice clips that play at the annual harvest report." in text
    assert "Requires throne room audio fix to be installed." in text
    assert "SetCtlColors $PreviewWarningText FF0000 F0F0F0" in text
    assert '"Terrain movement fix"' in text
    assert '"dgVoodoo2 terrain movement fix"' not in text
    assert (
        "Installs dgVoodoo2 to fix terrain-click unit movement and "
        "drag-formation issues on modern systems."
    ) in text
    assert "Installs dgVoodoo2 v2.87.2" not in text
    assert "Not available on Windows XP." in text


def test_default_path_and_hover_preview_are_configured() -> None:
    text = script_text()

    assert 'StrCpy $INSTDIR "$PROGRAMFILES32\\Total War Shogun 1 Gold"' in text
    assert '${FileExists} "$INSTDIR\\ShogunM.exe"' in text
    assert "${NSD_CreateTimer} PreviewHoverTimer" in text
    assert "${NSD_KillTimer} PreviewHoverTimer" in text
    assert "Call PreviewFromCursor" in text


def test_game_path_detection_checks_steam_app_registry_and_library_folders() -> None:
    text = script_text()
    detect = text.split("Function DetectGamePath", 1)[1].split("FunctionEnd", 1)[0]
    fixes_create = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]
    section = text.split('Section "Apply selected fixes"', 1)[1].split("SectionEnd", 1)[0]

    assert 'Steam App 345240' in text
    assert 'ReadRegStr $0 HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App 345240" "InstallLocation"' in text
    assert 'ReadRegStr $0 HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App 345240" "InstallLocation"' in text
    assert 'SetRegView 64' in detect
    assert 'Call TryRegistryGamePath' in detect
    assert 'Call TrySteamRoot' in detect
    assert 'steamapps\\libraryfolders.vdf' in text
    assert 'Total War Shogun 1 Gold' in text
    assert "Call DetectGamePath" in fixes_create
    assert "Call DetectGamePath" in section


def test_game_path_detection_checks_gog_uninstall_registry() -> None:
    text = script_text()

    assert '1874325037_is1' in text
    assert 'ReadRegStr $0 HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\1874325037_is1" "InstallLocation"' in text
    assert 'ReadRegStr $0 HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\1874325037_is1" "InstallLocation"' in text


def test_silent_mode_skips_the_custom_dialog_page() -> None:
    text = script_text()
    fixes_create = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]
    section = text.split('Section "Apply selected fixes"', 1)[1].split("SectionEnd", 1)[0]
    silent_override = text.split("Function ValidateSilentTargetOverride", 1)[1].split("FunctionEnd", 1)[0]

    assert "IfSilent" in fixes_create
    assert "Abort" in fixes_create.split("IfSilent", 1)[1]
    assert "Function ValidateSilentTargetOverride" in text
    assert "IfSilent validate done" in silent_override
    assert '${IfNot} ${FileExists} "$INSTDIR\\ShogunM.exe"' in silent_override
    assert '$INSTDIR != "$EXEDIR"' not in silent_override
    assert "silent install target folder" in silent_override
    assert "pass the game folder with /D=" in silent_override
    assert section.index("Call ValidateSilentTargetOverride") < section.index("Call DetectGamePath")
    assert 'MessageBox MB_ICONSTOP|MB_OK "ShogunM.exe was not found.' in section
    assert 'MessageBox MB_ICONSTOP|MB_OK "The selected fixes could not be applied.' in section
    assert '/SD IDOK' in section


def test_patch_page_preserves_selection_state_across_back_next_navigation() -> None:
    text = script_text()
    on_init = text.split("Function .onInit", 1)[1].split("FunctionEnd", 1)[0]
    fixes_create = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]
    save_state = text.split("Function SaveFixesPageState", 1)[1].split("FunctionEnd", 1)[0]
    back_function = text.split("Function PatchPageBack", 1)[1].split("FunctionEnd", 1)[0]

    for var_name in (
        "FixesPageVisited",
        "SavedTargetDir",
        "SavedDgVoodooState",
        "SavedHistoricalState",
        "SavedThroneState",
        "SavedUnitState",
        "SavedHarvestState",
    ):
        assert f"Var {var_name}" in text

    assert 'StrCpy $FixesPageVisited "0"' in on_init
    assert 'StrCpy $SavedHistoricalState ${BST_CHECKED}' in on_init
    assert 'StrCpy $SavedHarvestState ${BST_UNCHECKED}' in on_init
    assert '${If} $FixesPageVisited == "0"' in fixes_create
    assert 'StrCpy $SavedTargetDir "$INSTDIR"' in fixes_create
    assert '${ElseIf} $SavedTargetDir != ""' in fixes_create
    assert '${If} $SavedHarvestState == ${BST_CHECKED}' in fixes_create
    assert '${NSD_GetState} $HarvestCheck $SavedHarvestState' in save_state
    assert '${NSD_GetText} $TargetText $SavedTargetDir' in save_state
    assert "Call SaveFixesPageState" in back_function
    assert "Call RestoreDefaultWizard" in back_function


def test_patch_page_uses_expanded_layout_for_readable_previews() -> None:
    text = script_text()

    assert "Call ResizePatchWizard" in text
    assert "user32::SetWindowPos" in text
    assert "${NSD_CreateGroupBox} 340 62 506 430 \"Preview\"" in text
    assert "${NSD_CreateBitmap} 352 92 480 270" in text
    assert "${NSD_CreateLabel} 352 374 480 28" in text
    assert "${NSD_CreateLabel} 352 410 480 56" in text
    assert "${NSD_CreateLabel} 352 474 480 24" in text


def test_patch_page_uses_larger_scannable_fonts() -> None:
    text = script_text()
    fixes_create = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]

    assert 'CreateFont $PatchPageFont "$(^Font)" "10" "400"' in fixes_create
    assert 'CreateFont $PatchPageTitleFont "$(^Font)" "12" "700"' in fixes_create
    assert 'CreateFont $PatchPageBodyFont "$(^Font)" "10" "400"' in fixes_create
    assert "SendMessage $DgVoodooCheck ${WM_SETFONT} $PatchPageFont 1" in fixes_create
    assert "SendMessage $HarvestCheck ${WM_SETFONT} $PatchPageFont 1" in fixes_create
    assert "SendMessage $PreviewTitle ${WM_SETFONT} $PatchPageTitleFont 1" in fixes_create
    assert "SendMessage $PreviewText ${WM_SETFONT} $PatchPageBodyFont 1" in fixes_create
    assert "SendMessage $PreviewWarningText ${WM_SETFONT} $PatchPageBodyFont 1" in fixes_create
    for y in (94, 128, 162, 196, 316):
        assert f' {y} ' in fixes_create
    assert '${NSD_CreateCheckbox} 12 196 295 24 "Recruitment, upkeep && training fix"' in fixes_create
    assert '${NSD_CreateCheckbox} 12 316 295 24 "Harvest report audio restoration"' in fixes_create


def test_dgvoodoo2_option_is_recommended_and_installs_vendor_files() -> None:
    text = script_text()

    assert "Var DgVoodooCheck" in text
    assert "Var DgVoodooSupported" in text
    assert "${AtLeastWinVista}" in text
    assert 'StrCpy $InstallDgVoodoo "1"' in text
    assert 'StrCpy $InstallDgVoodoo "0"' in text
    assert '${NSD_CreateCheckbox} 12 94 295 24 "Terrain movement fix"' in text
    assert "${NSD_Check} $DgVoodooCheck" in text
    assert "EnableWindow $DgVoodooCheck 0" in text
    assert '${NSD_OnClick} $DgVoodooCheck PreviewDgVoodoo' in text
    assert '!insertmacro BACKUP_DGVOODOO_FILE "D3D9.dll"' in text
    assert 'File /oname=DDraw.dll "${SOURCE_DIR}\\vendor\\dgvoodoo2\\DDraw.dll"' in text
    assert 'File /oname=D3DImm.dll "${SOURCE_DIR}\\vendor\\dgvoodoo2\\D3DImm.dll"' in text
    assert 'File /oname=D3D9.dll "${SOURCE_DIR}\\vendor\\dgvoodoo2\\D3D9.dll"' in text
    assert 'File /oname=dgVoodoo.conf "${SOURCE_DIR}\\vendor\\dgvoodoo2\\dgVoodoo.conf"' in text


def test_xp_initial_preview_uses_first_supported_recommended_option() -> None:
    text = script_text()
    fixes_create = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]

    assert '${If} $DgVoodooSupported == "1"' in fixes_create
    assert 'StrCpy $R0 "dgvoodoo"' in fixes_create
    assert '${Else}' in fixes_create
    assert 'StrCpy $R0 "historical"' in fixes_create
    assert fixes_create.index('${If} $DgVoodooSupported == "1"', fixes_create.index('StrCpy $CurrentPreviewKey ""')) < fixes_create.index('Call SetPreview')


def test_dgvoodoo2_vendor_payload_and_config_are_present() -> None:
    assert (VENDOR / "DDraw.dll").is_file()
    assert (VENDOR / "D3DImm.dll").is_file()
    assert (VENDOR / "D3D9.dll").is_file()
    config = (VENDOR / "dgVoodoo.conf").read_text(encoding="utf-8")
    version = (VENDOR / "VERSION.txt").read_text(encoding="utf-8")

    assert "Version                              = 0x287" in config
    assert "OutputAPI                            = d3d11_fl10_1" in config
    assert "ScalingMode                          = stretched_ar" in config
    assert "Resampling                           = lanczos-3" in config
    assert "FastVideoMemoryAccess               = true" in config
    assert "MS/x86/D3D9.dll" in version


def test_harvest_preview_dependency_updates_both_checkboxes() -> None:
    text = script_text()

    harvest_function = text.split("Function PreviewHarvest", 1)[1].split("FunctionEnd", 1)[0]
    throne_function = text.split("Function PreviewThrone", 1)[1].split("FunctionEnd", 1)[0]

    assert "${NSD_Check} $ThroneCheck" in harvest_function
    assert "${NSD_GetState} $HarvestCheck" in throne_function
    assert "${NSD_Uncheck} $HarvestCheck" in throne_function


def test_warning_label_is_hidden_for_non_harvest_previews() -> None:
    text = script_text()

    assert 'StrCpy $CurrentPreviewKey ""' in text
    for key in ("historical", "throne", "unit"):
        branch_start = f'$R0 == "{key}"'
        assert branch_start in text
    assert text.count("ShowWindow $PreviewWarningText ${SW_HIDE}") >= 4
    assert "ShowWindow $PreviewWarningText ${SW_SHOW}" in text
    assert "Not available on Windows XP." in text


def test_recommended_checkbox_order_matches_requested_priority() -> None:
    text = script_text()

    terrain = '${NSD_CreateCheckbox} 12 94 295 24 "Terrain movement fix"'
    historical = '${NSD_CreateCheckbox} 12 128 290 24 "Historical campaign fix"'
    throne = '${NSD_CreateCheckbox} 12 162 290 24 "Throne room audio fix"'
    unit = '${NSD_CreateCheckbox} 12 196 295 24 "Recruitment, upkeep && training fix"'
    assert terrain in text
    assert historical in text
    assert throne in text
    assert unit in text
    assert text.index(terrain) < text.index(historical) < text.index(throne) < text.index(unit)
    create_body = text.split("Function FixesPageCreate", 1)[1].split("FunctionEnd", 1)[0]
    assert 'StrCpy $R0 "dgvoodoo"' in create_body


def test_welcome_page_restores_standard_wizard_after_back_navigation() -> None:
    text = script_text()

    assert "!define MUI_PAGE_CUSTOMFUNCTION_SHOW WelcomePageShow" in text
    assert "!undef MUI_PAGE_CUSTOMFUNCTION_SHOW" in text
    assert "Function RestoreDefaultWizard" in text
    assert "Call RestoreDefaultWizard" in text
    assert "${NSD_OnBack} PatchPageBack" in text


def test_preview_bitmaps_are_large_enough_for_expanded_preview_area() -> None:
    for name in ("historical.bmp", "throne.bmp", "unit.bmp", "harvest.bmp", "dgvoodoo.bmp"):
        data = (ASSETS / name).read_bytes()
        width, height = struct.unpack_from("<ii", data, 18)
        assert width == 480
        assert abs(height) == 270

    terrain_bottom = bmp_pixel(ASSETS / "dgvoodoo.bmp", 240, 269)
    assert terrain_bottom[1] > 45
    assert terrain_bottom[0] > 35
    assert terrain_bottom[2] < 60


def test_welcome_finish_bitmap_uses_modern_ui_recommended_dimensions() -> None:
    data = (ASSETS / "welcome-finish.bmp").read_bytes()
    width, height = struct.unpack_from("<ii", data, 18)
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]

    assert width == 164
    assert abs(height) == 314
    assert bits_per_pixel == 24


def test_welcome_finish_bitmap_has_no_divider_lines_or_red_logo_ring() -> None:
    bitmap = ASSETS / "welcome-finish.bmp"
    removed_line_colors = {
        (214, 176, 96),
        (199, 52, 54),
    }

    for y in (136, 143, 262, 269):
        for x in (32, 50, 82, 100):
            assert bmp_pixel(bitmap, x, y) not in removed_line_colors

    for point in ((42, 78), (48, 58), (48, 98), (116, 78)):
        assert bmp_pixel(bitmap, *point) != (191, 46, 49)


def test_welcome_finish_bitmap_has_no_top_red_band_or_diagonal_line_motif() -> None:
    bitmap = ASSETS / "welcome-finish.bmp"
    removed_top_band = (126, 18, 29)

    for x, y in ((20, 50), (80, 30), (130, 20)):
        assert bmp_pixel(bitmap, x, y) != removed_top_band

    for y, xs in (
        (180, (23, 44, 65, 86, 107, 128, 149)),
        (200, (28, 49, 70, 91, 112, 133, 154)),
        (220, (32, 53, 74, 95, 116, 137, 158)),
        (240, (37, 58, 79, 100, 121, 142, 163)),
    ):
        for x in xs:
            red, green, blue = bmp_pixel(bitmap, x, y)
            assert not (red > 150 and green > 110 and blue < 120)


def test_welcome_finish_bitmap_restores_centered_logo_with_connected_white_backing() -> None:
    text = (Path(__file__).resolve().parents[1] / "build.ps1").read_text(encoding="utf-8")
    bitmap = ASSETS / "welcome-finish.bmp"

    welcome_bitmap_function = text.split("function New-WelcomeFinishBitmap", 1)[1].split("New-Item -ItemType Directory", 1)[0]
    assert "DrawIcon" in welcome_bitmap_function
    assert "New-Object System.Drawing.Icon" in welcome_bitmap_function
    assert "New-Object System.Drawing.Rectangle 58, 54, 48, 48" in welcome_bitmap_function
    assert "FillEllipse" in welcome_bitmap_function
    assert "DrawEllipse" not in welcome_bitmap_function
    assert "New-Object System.Drawing.Rectangle 48, 44, 68, 68" in welcome_bitmap_function
    assert "New-Object System.Drawing.Rectangle 104, 54, 48, 48" not in text
    assert bmp_pixel(bitmap, 50, 78) == (255, 255, 255)
    assert bmp_pixel(bitmap, 56, 78) == (255, 255, 255)
    assert bmp_pixel(bitmap, 82, 46) == (255, 255, 255)
    assert bmp_pixel(bitmap, 82, 52) == (255, 255, 255)
    assert bmp_pixel(bitmap, 82, 78) == (255, 0, 0)
    assert bmp_pixel(bitmap, 80, 78) == (255, 255, 255)
