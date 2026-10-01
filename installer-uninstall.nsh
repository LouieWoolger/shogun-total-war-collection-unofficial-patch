; NSIS self-copies to TEMP before un.onInit. $INSTDIR remains the original
; game directory, independent of cwd. The helper validates its durable binding.
; Never delete game files or registration here: the native lifecycle owns them.

Function un.Fail
    StrCpy $LogLine "result=failure child_exit=$ChildStatus $InstallError"
    Call un.WriteDiagnostic
    DetailPrint "$InstallError"
    ${If} $RemovalRestored == "1"
        DetailPrint "Restoration completed, but the final diagnostic log could not be saved."
        MessageBox MB_ICONEXCLAMATION|MB_OK "Removal from this folder completed:$\r$\n$INSTDIR$\r$\n$\r$\nThe final diagnostic log could not be saved. Any logs that were saved are here:$\r$\n$LogDirectory" /SD IDOK
        SetErrorLevel 3
        IfSilent 0 +2
        Quit
        Abort
    ${EndIf}
    DetailPrint "Removal was not completed. Keep the uninstaller and recovery files for retry."
    DetailPrint "Diagnostics: $LogDirectory"
    MessageBox MB_ICONSTOP|MB_OK "The patch could not be completely removed from:$\r$\n$INSTDIR$\r$\n$\r$\n$InstallError$\r$\n$\r$\nClose the game and retry. If access is denied, use an account with write access to this folder. If restoration state is damaged, keep the files and include these logs when requesting help.$\r$\n$\r$\nDiagnostics:$\r$\n$LogDirectory" /SD IDOK
    ${If} $ChildStatus == "3"
        SetErrorLevel 3
    ${ElseIf} $ChildStatus == "4"
        SetErrorLevel 4
    ${Else}
        SetErrorLevel 2
    ${EndIf}
    IfSilent 0 +2
    Quit
    Abort
FunctionEnd

Function un.onInit
    StrCpy $OperationName "removal"
    StrCpy $ChildStatus "not-started"
    StrCpy $RemovalRestored "0"
    Call un.InitializeDiagnostics
    StrCpy $LogLine "operation=uninstall target=$INSTDIR"
    Call un.WriteDiagnostic
    ; Preserve changed/uncertain files automatically before removing them from
    ; active use. The native helper still validates originals and archive writes.
    ; /ARCHIVECHANGES remains accepted for older automation; it is now the default.
    StrCpy $ArchiveArgument "--archive-conflicts"
    StrCpy $LogLine "removal_policy=archive_conflicts"
    Call un.WriteDiagnostic
    StrCpy $KeepArgument ""
    StrCpy $RetainedWrappers "0"
    ClearErrors
    ${GetOptions} $CommandOptions "/KEEPLEGACYWRAPPERS" $0
    ${IfNot} ${Errors}
        StrCpy $KeepArgument "--keep-legacy-wrappers"
    ${EndIf}
    StrCpy $InstallPhase "extraction-helper"
    Call un.LogPhase
    ClearErrors
    InitPluginsDir
    SetOutPath "$PLUGINSDIR"
    File /oname=shogun-fix-patcher.exe "${PATCHER_FILE}"
    File /oname=LICENSE.txt "${SOURCE_DIR}\LICENSE"
    File /oname=MinGW-w64-runtime.txt "${SOURCE_DIR}\licenses\MinGW-w64-runtime.txt"
    ${If} ${Errors}
        StrCpy $InstallError "error=helper_extraction_failed"
        Call un.Fail
    ${EndIf}
    ${If} $DiagnosticWriteFailed == "1"
        StrCpy $InstallError "error=diagnostic_write_failed native_error=$DiagnosticNativeError"
        Call un.Fail
    ${EndIf}
FunctionEnd

Function un.ReadRemovalResult
    StrCpy $RetainedWrappers "0"
    ClearErrors
    FileOpen $2 "$HelperLog" r
    IfErrors choices_done
choices_read:
    ClearErrors
    Call un.ReadHelperLine
    IfErrors choices_close
    ${UnStrStr} $1 $PatcherOutput "warning=legacy_wrappers_retained"
    ${If} $1 != ""
        StrCpy $RetainedWrappers "1"
    ${EndIf}
    Goto choices_read
choices_close:
    FileClose $2
choices_done:
FunctionEnd

Section "Uninstall"
    DetailPrint "Remove the unofficial patch from: $INSTDIR"
    DetailPrint "Your game, saves and unrelated content are kept."
    DetailPrint "Diagnostics: $LogDirectory"
    StrCpy $InstallPhase "uninstall-helper"
    Call un.LogPhase
    StrCpy $HelperArguments '--target "$INSTDIR" --uninstall --log "$HelperLog" $ArchiveArgument $KeepArgument'
    StrCpy $InstallError ""
    Call un.RunHelper
    StrCpy $LogLine "child_exit=$ChildStatus"
    Call un.WriteDiagnostic
    Call un.ShowHelperDetails
    Call un.ReadRemovalResult
    ${If} $InstallError != ""
        Call un.Fail
    ${EndIf}
    ${If} $ChildStatus != "0"
        StrCpy $InstallError "error=removal_incomplete child_exit=$ChildStatus; see Details for the affected files"
        Call un.Fail
    ${EndIf}
    ${IfNot} ${FileExists} "$HelperLog"
        StrCpy $InstallError "error=helper_log_missing"
        Call un.Fail
    ${EndIf}
    StrCpy $RemovalRestored "1"
    StrCpy $InstallPhase "complete"
    Call un.LogPhase
    StrCpy $LogLine "result=success operation=uninstall"
    Call un.WriteDiagnostic
    ${If} $DiagnosticWriteFailed == "1"
        StrCpy $ChildStatus "3"
        StrCpy $InstallError "error=diagnostic_write_failed after_restoration=1"
        Call un.Fail
    ${EndIf}
    ${If} $RetainedWrappers == "1"
        DetailPrint "Known patch changes removed. At your request, uncertain graphics wrappers remain active."
    ${Else}
        DetailPrint "Unofficial patch removed. Your game is kept."
    ${EndIf}
    SetErrorLevel 0
SectionEnd

Function un.FinishPageShow
    ${If} $RetainedWrappers == "1"
        ${NSD_SetText} $mui.FinishPage.Title "Known patch changes removed"
        ${NSD_SetText} $mui.FinishPage.Text "Known patch changes have been removed from:$\r$\n$INSTDIR$\r$\n$\r$\nGraphics wrappers were kept as requested. Your game and personal files have been kept."
    ${EndIf}
FunctionEnd

Function un.LogUserAbort
    StrCpy $LogLine "user_cancelled=1"
    Call un.WriteDiagnostic
    SetErrorLevel 1
FunctionEnd

Function un.onGUIEnd
    ${If} $LogHandle != ""
        StrCpy $LogLine "uninstaller_closed=1"
        Call un.WriteDiagnostic
        FileClose $LogHandle
        StrCpy $LogHandle ""
    ${EndIf}
FunctionEnd
