# CHC Geomatics Office 2 - Developer Guide

## 1. Scope
Current maintained runtime components:
- usb_guard.py -> builds CHC Geomatics Office 2.exe
- keygen.py -> builds LicenseTool.exe

Deprecated helper binaries are not required for deployment.

## 2. Runtime Design
Main executable responsibilities:
- Validate license from USB .lic file.
- Generate expected key from USB volume serial fingerprint.
- Show activation UI (Tkinter) when license missing/invalid.
- Prepare DLL storage in %APPDATA%\CHCNAV\CHC Geomatics Office 2\DLL_Storage.
- Apply cracked DLL before launching target software.
- Monitor app/USB state and attempt restore to original DLL on shutdown/unplug.

Guardian mode:
- Spawned as detached child using same executable with --guardian.
- Watches process lifecycle and optional USB presence.
- Attempts forced restore as fallback even if main process is interrupted.

## 3. Key Paths
- USB license: <USB_ROOT>\.lic
- AppData mirror license: %APPDATA%\CHCNAV\CHC Geomatics Office 2\license.dat
- Original DLL backup: %APPDATA%\CHCNAV\CHC Geomatics Office 2\DLL_Storage\original.dll
- Cracked DLL backup: %APPDATA%\CHCNAV\CHC Geomatics Office 2\DLL_Storage\cracked.dll
- Target DLL: %APPDATA%\CHCNAV\CHC Geomatics Office 2\CHC.CGO.Common.dll

## 4. Build Commands
From project root:

```powershell
python -m py_compile usb_guard.py keygen.py
python -m PyInstaller --clean --noconfirm "CHC Geomatics Office 2.spec"
python -m PyInstaller --clean --noconfirm "KeyGen.spec"
```

Outputs:
- dist\CHC Geomatics Office 2.exe
- dist\LicenseTool.exe

## 5. Spec Notes
CHC Geomatics Office 2.spec:
- entry script: usb_guard.py
- bundles source_crack.dll and source_original.dll
- console=False (windowed runtime)

KeyGen.spec:
- entry script: keygen.py
- output binary: LicenseTool.exe
- upx=False to reduce false-positive risk
- console can remain true for admin tool

## 6. Activation Logic Contract
- Expected code seed = SHA256("USB-<volume_serial>-150925")[:16].upper()
- Activation key format = CHC-XXXX-XXXX-XXXX (derived from first 12 chars of seed)
- License is valid only when USB .lic key matches generated expected key

## 7. Regression Checklist
Before release, test at least:
1. First activation flow (copy code, enter key, confirm).
2. Re-open with valid license (no activation prompt).
3. Run on another PC with same USB (should work).
4. Copy files to different USB (should require activation).
5. Unplug USB while app is running (app closes, restore path runs).
6. Re-open after unplug stress test multiple times.

## 8. Troubleshooting Guidance
If restore intermittently fails:
- Add runtime logging in AppData guard.log for:
  - USB unplug detection timestamp
  - App kill result
  - Restore retry count and final outcome
- Verify no external process keeps target DLL locked.
- Verify Guardian process is started with expected args.

## 9. Release Checklist
1. Rebuild both executables.
2. Smoke test on clean machine profile.
3. Archive only required deliverables.
4. Update USER_GUIDE.md if behavior changes.
