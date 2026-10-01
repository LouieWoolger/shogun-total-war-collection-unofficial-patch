Section "Apply selected fixes"
    StrCpy $InstallPhase "target-validation"
    Call LogPhase
    StrCpy $LogLine "target=$INSTDIR"
    Call WriteDiagnostic
    StrCpy $LogLine "selected=$SelectedFlags"
    Call WriteDiagnostic
    StrCpy $LogLine "helper_options=$PatcherFlags"
    Call WriteDiagnostic
    ${IfNot} ${FileExists} "$INSTDIR\ShogunM.exe"
        StrCpy $InstallError "error=target_missing (ShogunM.exe was not found)"
        !insertmacro ABORT_INSTALL
    ${EndIf}

    StrCpy $InstallPhase "extraction-helper"
    Call LogPhase
    ClearErrors
    SetOutPath "$PLUGINSDIR"
    File /oname=shogun-fix-patcher.exe "${PATCHER_FILE}"
    ${If} ${Errors}
        StrCpy $InstallError "error=helper_extraction_failed"
        !insertmacro ABORT_INSTALL
    ${EndIf}
    ; Generate before any game mutation. The native lifecycle commits this
    ; together with restoration state, game files and Windows registration.
    ClearErrors
    WriteUninstaller "$PLUGINSDIR\${UNINSTALL_NAME}"
    ${If} ${Errors}
        StrCpy $InstallError "error=uninstaller_generation_failed"
        !insertmacro ABORT_INSTALL
    ${EndIf}
    StrCpy $PayloadArgument ""
    ${If} $InstallDgVoodoo == "1"
        StrCpy $InstallPhase "extraction-payload"
        Call LogPhase
        ClearErrors
        SetOutPath "$PLUGINSDIR\dgvoodoo"
        File /oname=DDraw.dll "${SOURCE_DIR}\vendor\dgvoodoo2\DDraw.dll"
        File /oname=D3DImm.dll "${SOURCE_DIR}\vendor\dgvoodoo2\D3DImm.dll"
        File /oname=D3D9.dll "${SOURCE_DIR}\vendor\dgvoodoo2\D3D9.dll"
        File /oname=dgVoodoo.conf "${SOURCE_DIR}\vendor\dgvoodoo2\dgVoodoo.conf"
        ${If} ${Errors}
            StrCpy $InstallError "error=payload_extraction_failed"
            !insertmacro ABORT_INSTALL
        ${EndIf}
        StrCpy $PayloadArgument '--payload "$PLUGINSDIR\dgvoodoo"'
    ${EndIf}

    StrCpy $InstallPhase "helper"
    Call LogPhase
    Call RequireDiagnostics
    DetailPrint "Target folder: $INSTDIR"
    DetailPrint "Selected fixes: $SelectedFlags"
    DetailPrint "Diagnostics: $LogDirectory"
    StrCpy $ChildStatus "not-started"
    ; No shell and no fixed-size stdout buffer. The helper writes its complete
    ; output directly to a persistent UTF-8 file, including preflight/rollback.
    StrCpy $InstallError ""
    StrCpy $HelperArguments '--target "$INSTDIR" --apply "$PatcherFlags" --log "$HelperLog" $PayloadArgument --uninstaller "$PLUGINSDIR\${UNINSTALL_NAME}"'
    Call RunHelper
    ${If} $InstallError != ""
        !insertmacro ABORT_INSTALL
    ${EndIf}
    StrCpy $LogLine "child_exit=$ChildStatus"
    Call WriteDiagnostic
    Call ShowHelperDetails
    ${If} $ChildStatus != 0
        StrCpy $InstallError "error=helper_failed child_exit=$ChildStatus"
        !insertmacro ABORT_INSTALL
    ${EndIf}
    ${IfNot} ${FileExists} "$HelperLog"
        StrCpy $InstallError "error=helper_log_missing"
        !insertmacro ABORT_INSTALL
    ${EndIf}
    StrCpy $InstallPhase "complete"
    Call LogPhase
    StrCpy $LogLine "result=success"
    Call WriteDiagnostic
    Call RequireDiagnostics
    DetailPrint "Installation complete. Diagnostics: $LogDirectory"
    SetErrorLevel 0
SectionEnd
