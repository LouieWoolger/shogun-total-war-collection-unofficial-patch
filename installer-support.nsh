; Shared installer/uninstaller diagnostics and native process runner.
!macro SHOGUN_DIAGNOSTICS PREFIX
Function ${PREFIX}WriteDiagnostic
    ${If} $LogHandle != ""
        ClearErrors
        FileWriteUTF16LE $LogHandle "$LogLine$\r$\n"
        ${If} ${Errors}
            StrCpy $DiagnosticWriteFailed "1"
        ${EndIf}
        ; Use named variables; RunHelper keeps its process handle in $5.
        System::Call 'kernel32::FlushFileBuffers(p $LogHandle) i.s ?e'
        Pop $LogFlushNativeError
        Pop $LogFlushResult
        ${If} $LogFlushResult == 0
            StrCpy $DiagnosticWriteFailed "1"
            StrCpy $DiagnosticNativeError "$LogFlushNativeError"
        ${EndIf}
    ${EndIf}
FunctionEnd

Function ${PREFIX}LogPhase
    StrCpy $LogLine "phase=$InstallPhase"
    Call ${PREFIX}WriteDiagnostic
FunctionEnd

Function ${PREFIX}TryLogDirectory
    StrCpy $LogHandle ""
    ClearErrors
    CreateDirectory "$LogBase"
    GetTempFileName $LogDirectory "$LogBase"
    ${If} ${Errors}
        Return
    ${EndIf}
    ; GetTempFileName reserves a unique name. Only remove the file we just made.
    Delete "$LogDirectory"
    CreateDirectory "$LogDirectory"
    StrCpy $InstallerLog "$LogDirectory\installer.log"
    StrCpy $HelperLog "$LogDirectory\helper.log"
    StrCpy $ConsoleLog "$LogDirectory\helper-console.log"
    ClearErrors
    FileOpen $LogHandle "$InstallerLog" w
    ${If} ${Errors}
        StrCpy $LogHandle ""
        Return
    ${EndIf}
    FileWriteUTF16LE /BOM $LogHandle "Unofficial Shogun Patch $OperationName diagnostics$\r$\n"
    ${If} ${Errors}
        FileClose $LogHandle
        StrCpy $LogHandle ""
    ${EndIf}
FunctionEnd

Function ${PREFIX}InitializeDiagnostics
    ${GetParameters} $CommandOptions
    StrCpy $LogBase ""
    ${GetOptions} $CommandOptions "/LOGDIR=" $LogBase
    StrCpy $RequestedLogBase "$LogBase"
    ${If} $LogBase != ""
        Call ${PREFIX}TryLogDirectory
    ${EndIf}
    ${If} $LogHandle == ""
        StrCpy $LogBase "$LOCALAPPDATA\Unofficial Shogun Patch\Logs"
        Call ${PREFIX}TryLogDirectory
    ${EndIf}
    ${If} $LogHandle == ""
        StrCpy $LogBase "$TEMP\Unofficial Shogun Patch Logs"
        Call ${PREFIX}TryLogDirectory
    ${EndIf}
    ${If} $LogHandle == ""
        StrCpy $LogBase "$EXEDIR\Unofficial Shogun Patch Logs"
        Call ${PREFIX}TryLogDirectory
    ${EndIf}
    ${If} $LogHandle == ""
        MessageBox MB_ICONSTOP|MB_OK "No writable diagnostic location is available. The game was not changed. Run this installer with /LOGDIR= followed by a writable folder." /SD IDOK
        SetErrorLevel 2
        Quit
    ${EndIf}
    StrCpy $LogLine "version=${APP_VERSION}"
    Call ${PREFIX}WriteDiagnostic
    StrCpy $LogLine "installer=$EXEPATH"
    Call ${PREFIX}WriteDiagnostic
    StrCpy $LogLine "helper_log=$HelperLog"
    Call ${PREFIX}WriteDiagnostic
    StrCpy $LogLine "helper_console_log=$ConsoleLog"
    Call ${PREFIX}WriteDiagnostic
    StrCpy $LogLine "requested_log_directory=$RequestedLogBase"
    Call ${PREFIX}WriteDiagnostic
    System::Call 'kernel32::GetCurrentProcessId() i.r0'
    StrCpy $LogLine "installer_pid=$0"
    Call ${PREFIX}WriteDiagnostic
FunctionEnd

; Native diagnostics are UTF-8, regardless of the user's Windows ANSI codepage.
; FileRead would corrupt non-ASCII paths. Read raw bytes up to a whole line,
; then use the XP-compatible decoder. Oversized lines remain intact on disk.
Function ${PREFIX}ReadHelperLine
    StrCpy $PatcherOutput ""
    StrCpy $Utf8Size 0
    StrCpy $Utf8End 0
    StrCpy $Utf8Overflow 0
    System::Alloc 4096
    Pop $Utf8Buffer
    ${If} $Utf8Buffer == 0
        SetErrors
        Return
    ${EndIf}
    StrCpy $Utf8Pointer $Utf8Buffer
    ${Do}
        ClearErrors
        FileReadByte $2 $3
        ${If} ${Errors}
            StrCpy $Utf8End 1
            ${ExitDo}
        ${EndIf}
        ${If} $3 == 10
            ${ExitDo}
        ${EndIf}
        ${If} $3 != 13
            ${If} $Utf8Size < 4095
                System::Call '*$Utf8Pointer(&i1 r3)'
                IntOp $Utf8Pointer $Utf8Pointer + 1
                IntOp $Utf8Size $Utf8Size + 1
            ${Else}
                StrCpy $Utf8Overflow 1
            ${EndIf}
        ${EndIf}
    ${Loop}
    System::Call '*$Utf8Pointer(&i1 0)'
    ${If} $Utf8Overflow == 0
        System::Call 'kernel32::MultiByteToWideChar(i 65001,i 0,p$Utf8Buffer,i -1,w.r0,i ${NSIS_MAX_STRLEN}) i.r1'
        ${If} $1 != 0
            StrCpy $PatcherOutput $0
        ${Else}
            StrCpy $PatcherOutput "[Diagnostic line too long for this window; see the complete helper log.]"
        ${EndIf}
    ${Else}
        StrCpy $PatcherOutput "[Diagnostic line too long for this window; see the complete helper log.]"
    ${EndIf}
    System::Free $Utf8Buffer
    ${If} $Utf8Size == 0
    ${AndIf} $Utf8End == 1
        SetErrors
    ${Else}
        ClearErrors
    ${EndIf}
FunctionEnd

Function ${PREFIX}ShowHelperDetails
    ClearErrors
    FileOpen $2 "$HelperLog" r
    ${If} ${Errors}
        DetailPrint "Helper did not create its log; displaying captured console output."
        ClearErrors
        FileOpen $2 "$ConsoleLog" r
        ${If} ${Errors}
            Return
        ${EndIf}
    ${EndIf}
    ${Do}
        ClearErrors
        Call ${PREFIX}ReadHelperLine
        ${If} ${Errors}
            ${ExitDo}
        ${EndIf}
        DetailPrint "$PatcherOutput"
        !if "${PREFIX}" == "un."
            ${UnStrStr} $1 "$PatcherOutput" "backup_created="
        !else
            ${StrStr} $1 "$PatcherOutput" "backup_created="
        !endif
        ${If} $1 != ""
            StrCpy $BackupsGenerated "1"
        ${EndIf}
    ${Loop}
    FileClose $2
FunctionEnd

Function ${PREFIX}RunHelper
    ; NSIS is x86: STARTUPINFOW is 68 bytes and PROCESS_INFORMATION is 16.
    ; Capture CreateProcess's own native error at the API boundary. ExecWait's
    ; generic error flag cannot reliably retain it for a later GetLastError.
    StrCpy $ChildStatus "not-started"
    StrCpy $0 '"$PLUGINSDIR\shogun-fix-patcher.exe" $HelperArguments'
    ; Inherit only our deliberately inheritable console/NUL handles. This
    ; captures errors before the helper can open its own diagnostic stream.
    System::Call '*(i 12,p 0,i 1) p.r1'
    System::Call 'kernel32::CreateFileW(w "$ConsoleLog",i 0x40000000,i 1,p r1,i 2,i 0x80,p 0) p.s ?e'
    Pop $4
    Pop $ConsoleHandle
    ${If} $ConsoleHandle == -1
        System::Free $1
        StrCpy $InstallError "error=console_log_open_failed native_error=$4"
        Return
    ${EndIf}
    System::Call 'kernel32::CreateFileW(w "NUL",i 0x80000000,i 3,p r1,i 3,i 0x80,p 0) p.s ?e'
    Pop $4
    Pop $NullInputHandle
    System::Free $1
    ${If} $NullInputHandle == -1
        System::Call 'kernel32::CloseHandle(p $ConsoleHandle)'
        StrCpy $InstallError "error=child_input_open_failed native_error=$4"
        Return
    ${EndIf}
    ; dwFlags=STARTF_USESTDHANDLES; the last three fields are stdin/out/err.
    System::Call '*(i 68,p 0,p 0,p 0,i 0,i 0,i 0,i 0,i 0,i 0,i 0,i 0x100,i 0,p 0,p $NullInputHandle,p $ConsoleHandle,p $ConsoleHandle) p.r1'
    System::Call '*(p 0,p 0,i 0,i 0) p.r2'
    System::Call 'kernel32::CreateProcessW(w "$PLUGINSDIR\shogun-fix-patcher.exe",w r0,p 0,p 0,i 1,i 0x08000000,p 0,w "$PLUGINSDIR",p r1,p r2) i.r3 ?e'
    Pop $4
    System::Call 'kernel32::CloseHandle(p $NullInputHandle)'
    ${If} $3 == 0
        System::Call 'kernel32::CloseHandle(p $ConsoleHandle)'
        System::Free $1
        System::Free $2
        StrCpy $InstallError "error=helper_start_failed native_error=$4"
        Return
    ${EndIf}
    System::Call '*$2(p.r5,p.r6,i.r7,i.r8)'
    System::Free $1
    System::Free $2
    System::Call 'kernel32::CloseHandle(p r6)'
    StrCpy $LogLine "child_pid=$7"
    Call ${PREFIX}WriteDiagnostic
    ${Do}
        System::Call 'kernel32::WaitForSingleObject(p r5,i 100) i.r3'
        ${If} $3 == 0
            ${ExitDo}
        ${EndIf}
        ${If} $3 != 258
            StrCpy $InstallError "error=helper_wait_failed wait_status=$3"
            ; Keep handle open until process completes; do not pretend a
            ; running transaction failed or delete its extracted executable.
            System::Call 'kernel32::WaitForSingleObject(p r5,i -1)'
            ${ExitDo}
        ${EndIf}
        Sleep 10
    ${Loop}
    System::Call 'kernel32::GetExitCodeProcess(p r5,*i.r0) i.r3 ?e'
    Pop $4
    System::Call 'kernel32::CloseHandle(p r5)'
    System::Call 'kernel32::FlushFileBuffers(p $ConsoleHandle) i.s ?e'
    Pop $ConsoleFlushError
    Pop $ConsoleFlushResult
    System::Call 'kernel32::CloseHandle(p $ConsoleHandle)'
    ${If} $3 == 0
        StrCpy $InstallError "error=helper_exit_status_failed native_error=$4"
        Return
    ${EndIf}
    StrCpy $ChildStatus "$0"
    ${If} $ConsoleFlushResult == 0
        StrCpy $InstallError "error=console_log_flush_failed native_error=$ConsoleFlushError child_exit=$ChildStatus"
    ${EndIf}
FunctionEnd
!macroend

!insertmacro SHOGUN_DIAGNOSTICS ""
!insertmacro SHOGUN_DIAGNOSTICS "un."

; Durable diagnostics are initialized before extracting any helper or UI asset.
; The helper owns one transaction for executable, data, backups and wrappers.
; Keep logs outside the game folder so a rejected/unwritable target is diagnosable.





Function ParseSilentSelections
    IfSilent 0 done
    StrCpy $0 ""
    ${GetOptions} $CommandOptions "/FIXES=" $0
    ${If} $0 == ""
        Goto done
    ${EndIf}
    StrCpy $SelectedFlags "$0"
    StrCpy $PatcherFlags "$0"
    StrCpy $InstallDgVoodoo "0"
    ${If} $0 == "recommended"
        StrCpy $PatcherFlags "historical,retraining-drag,throne,ammo,kawanakajima,odawara"
        ${If} $DgVoodooSupported == "1"
            StrCpy $InstallDgVoodoo "1"
            StrCpy $PatcherFlags "dgvoodoo-resolution,$PatcherFlags"
        ${EndIf}
    ${ElseIf} $0 == "all"
        StrCpy $PatcherFlags "historical,retraining-drag,throne,unit,harvest,ammo,kawanakajima,odawara,advisor"
        ${If} $DgVoodooSupported == "1"
            StrCpy $InstallDgVoodoo "1"
            StrCpy $PatcherFlags "dgvoodoo-resolution,$PatcherFlags"
        ${EndIf}
    ${Else}
        ; Token-bounded match avoids accepting a prefix or substring as Terrain.
        ${StrStr} $1 ",$0," ",dgvoodoo,"
        ${If} $1 != ""
            ${If} $DgVoodooSupported != "1"
                StrCpy $InstallPhase "options"
                StrCpy $InstallError "error=terrain_requires_vista_or_later"
                !insertmacro ABORT_INSTALL
            ${EndIf}
            StrCpy $InstallDgVoodoo "1"
            ${StrRep} $PatcherFlags ",$0," ",dgvoodoo," ",dgvoodoo-resolution,"
        ${EndIf}
    ${EndIf}
done:
FunctionEnd

Function ReportInstallFailure
    Call LogPhase
    StrCpy $LogLine "$InstallError"
    Call WriteDiagnostic
    DetailPrint "$InstallError"
    DetailPrint "Diagnostic folder: $LogDirectory"
    MessageBox MB_ICONSTOP|MB_OK "Installation could not complete during $InstallPhase.$\r$\n$InstallError$\r$\n$\r$\nDiagnostics are saved here:$\r$\n$LogDirectory$\r$\n$\r$\nSend the .log files in that folder when reporting this error. If the helper reports recovery is required, keep its transaction folder until recovery completes." /SD IDOK
FunctionEnd

Function RequireDiagnostics
    ${If} $DiagnosticWriteFailed == "1"
        StrCpy $InstallError "error=diagnostic_write_failed native_error=$DiagnosticNativeError"
        !insertmacro ABORT_INSTALL
    ${EndIf}
FunctionEnd

Function .onGUIEnd
    ${If} $LogHandle != ""
        StrCpy $LogLine "installer_closed=1"
        Call WriteDiagnostic
        FileClose $LogHandle
        StrCpy $LogHandle ""
    ${EndIf}
FunctionEnd

Function LogUserAbort
    StrCpy $LogLine "user_cancelled=1"
    Call WriteDiagnostic
FunctionEnd
