#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%  ; Ensures consistent starting directory

; ===== CONFIGURATION =====
AppName := "CHC Geomatics Office 2"
ExeName := "CHCGeomaticsOffice2.exe"
ExePath := "C:\Program Files\CHCNAV\CHC Geomatics Office 2\" ExeName
AppDataDir := A_AppData "\CHCNAV\CHC Geomatics Office 2"
TargetDll := AppDataDir "\CHC.CGO.Common.dll"
; =========================

; Record launcher's drive letter at startup (e.g., "Z:")
LauncherDrive := SubStr(A_ScriptDir, 1, 2)

; Create AppData directory if it doesn't exist
if (!FileExist(AppDataDir))
    FileCreateDir, %AppDataDir%

; Extract and copy the modified DLL to AppData (overwrite if exists)
FileInstall, source_crack.dll, %TargetDll%, 1

; Launch the target application
if (!FileExist(ExePath)) {
    MsgBox, 16, Error, Cannot find %ExeName% at %ExePath%
    ExitApp
}
Run, %ExePath%,, Hide, OutPid
if (OutPid = "") {
    MsgBox, 16, Error, Failed to launch %ExeName%
    ExitApp
}

; Set up USB removal monitoring
OnMessage(0x219, "DeviceChange")  ; WM_DEVICECHANGE
OnExit, Cleanup  ; Ensure cleanup on exit (normal termination)

return  ; End of auto-execute section

DeviceChange(wParam, lParam) {
    global AppDataDir, TargetDll, OutPid, LauncherDrive
    if (wParam = 0x8004) {  ; DBT_DEVICEREMOVECOMPLETE
        ; Extract unitmask from lParam (DWORD at offset 4)
        unitmask := NumGet(lParam+0, 4, "UInt")
        ; Calculate drive number for launcher drive (A:=0, B:=1, ...)
        DriveNum := Asc(LauncherDrive) - 65
        ; Check if this drive was removed
        if (unitmask & (1 << DriveNum)) {
            ; IMMEDIATELY terminate the target application
            ProcessClose, %OutPid%
            ; Restore the original DLL from embedded resource
            if (!FileExist(AppDataDir))
                FileCreateDir, %AppDataDir%
            FileInstall, source_original.dll, %TargetDll%, 1
            ; Show brief notification
            TrayTip, USB Guard, USB removed - %AppName% stopped safely., 1500
            ; Exit the launcher script
            ExitApp
        }
    }
}

Cleanup() {
    global AppDataDir, TargetDll, OutPid
    ; Ensure original DLL is in place when launcher exits (safety net)
    if (!FileExist(AppDataDir))
        FileCreateDir, %AppDataDir%
    FileInstall, source_original.dll, %TargetDll%, 1
    ; Terminate target app if still running (shouldn't be if USB removal triggered, but safe)
    if (ProcessExist(OutPid))
        ProcessClose, %OutPid%
}