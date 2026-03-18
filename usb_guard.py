import sys
import os
import subprocess
import time
import threading
import shutil
import hashlib
import json
import signal
import atexit
import tempfile
import ctypes

# USB root is still used for presence monitoring.
USB_ROOT = os.path.dirname(sys.executable)

APPDATA_DIR = os.path.join(
    os.environ.get("APPDATA", ""), r"CHCNAV\CHC Geomatics Office 2"
)
USB_LICENSE_FILE = os.path.join(USB_ROOT, ".lic")
APPDATA_LICENSE_FILE = os.path.join(APPDATA_DIR, "license.dat")
DLL_STORAGE_DIR = os.path.join(APPDATA_DIR, "DLL_Storage")
CRACKED_DLL = os.path.join(DLL_STORAGE_DIR, "cracked.dll")
ORIGINAL_DLL = os.path.join(DLL_STORAGE_DIR, "original.dll")
TARGET_DLL = os.path.join(APPDATA_DIR, "CHC.CGO.Common.dll")
EXE_PATH = os.path.join(
    os.environ.get("APPDATA", ""),
    r"CHCNAV\CHC Geomatics Office 2\CHC Geomatics Office 2.exe",
)

software_pid = [None]
software_proc = [None]
monitoring = [True]
shutdown_guard = threading.Lock()


def cleanup():
    monitoring[0] = False
    restore()


def signal_handler(signum, frame):
    cleanup()
    sys.exit(0)


def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_usb_drive_root():
    drive = os.path.splitdrive(os.path.abspath(USB_ROOT))[0]
    if not drive:
        return ""
    return drive + "\\"


def get_usb_fingerprint():
    root = get_usb_drive_root()
    if not root:
        return ""

    try:
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))
        if drive_type != 2:
            return ""

        serial = ctypes.c_ulong(0)
        max_component = ctypes.c_ulong(0)
        fs_flags = ctypes.c_ulong(0)
        volume_name = ctypes.create_unicode_buffer(261)
        fs_name = ctypes.create_unicode_buffer(261)

        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root),
            volume_name,
            260,
            ctypes.byref(serial),
            ctypes.byref(max_component),
            ctypes.byref(fs_flags),
            fs_name,
            260,
        )
        if not ok:
            return ""

        return f"{serial.value:08X}"
    except Exception:
        return ""


def get_password():
    usb_fingerprint = get_usb_fingerprint()
    if not usb_fingerprint:
        return ""
    return hashlib.sha256(f"USB-{usb_fingerprint}-150925".encode()).hexdigest()[:16].upper()


def hide_console_window():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def gen_key(pw):
    return f"CHC-{pw[:4]}-{pw[4:8]}-{pw[8:12]}"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def read_key_from_file(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return (data.get("key") or data.get("master_key") or "").strip().upper()
    except Exception:
        return ""


def check_lic(expected_key):
    # Security gate: license must exist and match on USB, not just AppData.
    usb_key = read_key_from_file(USB_LICENSE_FILE)
    if usb_key != expected_key:
        return False

    # Keep AppData copy synchronized for diagnostics/compatibility.
    appdata_key = read_key_from_file(APPDATA_LICENSE_FILE)
    if appdata_key != expected_key:
        save_lic(expected_key)
    return True


def save_lic(key):
    ensure_dir(APPDATA_DIR)
    payload = {"key": key, "time": time.time()}

    def atomic_write_json(dest_file):
        fd, tmp_path = tempfile.mkstemp(
            prefix="lic_", suffix=".tmp", dir=os.path.dirname(dest_file)
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(payload, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, dest_file)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # USB file is mandatory.
    atomic_write_json(USB_LICENSE_FILE)
    # AppData file is a mirrored backup.
    atomic_write_json(APPDATA_LICENSE_FILE)


def setup_dlls():
    ensure_dir(DLL_STORAGE_DIR)

    bundle = get_bundle_dir()
    cracked_src = os.path.join(bundle, "source_crack.dll")
    original_src = os.path.join(bundle, "source_original.dll")

    if os.path.exists(cracked_src) and not os.path.exists(CRACKED_DLL):
        shutil.copy2(cracked_src, CRACKED_DLL)
    if os.path.exists(original_src) and not os.path.exists(ORIGINAL_DLL):
        shutil.copy2(original_src, ORIGINAL_DLL)


def apply_dll():
    if os.path.exists(CRACKED_DLL):
        dest_dir = os.path.dirname(TARGET_DLL)
        ensure_dir(dest_dir)
        shutil.copy2(CRACKED_DLL, TARGET_DLL)


def kill_app():
    try:
        r = subprocess.run(["tasklist"], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if "CHC Geomatics Office 2.exe" in line:
                p = line.split()[1]
                subprocess.run(["taskkill", "/F", "/PID", p], capture_output=True)
    except:
        pass


def get_target_pids():
    pids = []
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq CHC Geomatics Office 2.exe"],
            capture_output=True,
            text=True,
        )
        for line in r.stdout.split("\n"):
            if "CHC Geomatics Office 2.exe" not in line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                pids.append(int(parts[1]))
    except Exception:
        pass
    return pids


def wait_until_app_stopped(timeout_sec=120):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not get_target_pids():
            return True
        time.sleep(0.25)
    return False


def restore():
    if os.path.exists(ORIGINAL_DLL):
        dest_dir = os.path.dirname(TARGET_DLL)
        ensure_dir(dest_dir)
        for _ in range(40):
            try:
                shutil.copy2(ORIGINAL_DLL, TARGET_DLL)
                return True
            except Exception:
                time.sleep(0.25)
        return False
    return True


def restore_with_wait(timeout_sec=120):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if restore():
            return True
        time.sleep(0.25)
    return False


def launch():
    if not os.path.exists(EXE_PATH):
        return None
    try:
        p = subprocess.Popen(
            [EXE_PATH],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return p
    except Exception:
        try:
            os.startfile(EXE_PATH)
            time.sleep(1.5)
            r = subprocess.run(["tasklist"], capture_output=True, text=True)
            for line in r.stdout.split("\n"):
                if "CHC Geomatics Office 2.exe" in line:
                    return int(line.split()[1])
        except Exception:
            pass
        return None


def ps_quote(value):
    return value.replace("'", "''")


def start_restore_watchdog(app_pid=None, watch_usb=False):
    if not os.path.exists(ORIGINAL_DLL):
        return

    pid_target = int(app_pid) if app_pid else 0
    watch_usb_ps = "$true" if watch_usb else "$false"

    wait_clause = (
        f"$pidTarget={pid_target};"
        f"$watchUsb={watch_usb_ps};"
        f"$usbRoot='{ps_quote(USB_ROOT)}';"
        "$deadline=(Get-Date).AddHours(12);"
        "while ((Get-Date) -lt $deadline) {"
        "  $alive=Get-Process -Name 'CHC Geomatics Office 2' -ErrorAction SilentlyContinue;"
        "  if (-not $alive) { break };"
        "  if ($watchUsb -and -not (Test-Path -LiteralPath $usbRoot)) {"
        "    Stop-Process -Name 'CHC Geomatics Office 2' -Force -ErrorAction SilentlyContinue;"
        "    Start-Sleep -Milliseconds 300;"
        "    continue"
        "  };"
        "  if ($pidTarget -gt 0) {"
        "    $tracked=$alive | Where-Object { $_.Id -eq $pidTarget };"
        "    if (-not $tracked) { $pidTarget = 0 };"
        "  };"
        "  Start-Sleep -Milliseconds 250"
        "};"
    )

    # Detached rescue survives launcher termination and restores original DLL promptly.
    script = (
        wait_clause
        + f"$original='{ps_quote(ORIGINAL_DLL)}';"
        + f"$target='{ps_quote(TARGET_DLL)}';"
        + "$destDir=[System.IO.Path]::GetDirectoryName($target);"
        + "if (-not [string]::IsNullOrWhiteSpace($destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null };"
        + "for ($i=0; $i -lt 1200; $i++) {"
        + "  try { Copy-Item -LiteralPath $original -Destination $target -Force -ErrorAction Stop; break }"
        + "  catch { Start-Sleep -Milliseconds 250 }"
        + "}"
    )

    creation_flags = 0
    for flag_name in ["DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"]:
        creation_flags |= int(getattr(subprocess, flag_name, 0))

    try:
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-Command",
                script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=True,
        )
    except Exception:
        pass


def safe_exit(reason, kill_running=False):
    with shutdown_guard:
        if not monitoring[0]:
            return
        monitoring[0] = False
    if kill_running:
        # Fire independent rescue before killing app in case launcher is terminated abruptly.
        start_restore_watchdog(watch_usb=False)
        kill_app()
        wait_until_app_stopped(timeout_sec=120)

    # Do a synchronous, long retry restore before final exit.
    restore_with_wait(timeout_sec=120)
    os._exit(0)


def monitor():
    while monitoring[0]:
        time.sleep(0.5)
        # USB removed
        if not os.path.exists(USB_ROOT):
            safe_exit("usb_removed", kill_running=True)

        # App closed: consider both tracked PID and real process name.
        pids = get_target_pids()
        tracked = software_pid[0]
        proc = software_proc[0]

        if tracked is None and proc is None:
            if not pids:
                safe_exit("app_closed", kill_running=False)
            continue

        if proc is not None and proc.poll() is None:
            continue

        if tracked in pids:
            continue

        if pids:
            software_pid[0] = pids[0]
            continue

        safe_exit("app_closed", kill_running=False)


def main():
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    pw = get_password()
    if not pw:
        print("Cannot detect USB identity. Run from a removable USB drive.")
        time.sleep(2)
        sys.exit(1)

    expected_key = gen_key(pw)

    already_licensed = check_lic(expected_key)

    if not already_licensed:
        print("=" * 45)
        print("ACTIVATION")
        print("=" * 45)
        print(f"\nCode: {pw}")
        print("\nSend to admin for key.")
        print("\nKey: ", end="")

        try:
            key = input().strip().upper()
        except:
            sys.exit(1)

        if key != expected_key:
            print("\nWrong key!")
            time.sleep(2)
            sys.exit(1)

        save_lic(expected_key)
        print("\nOK!")
        time.sleep(1)
    else:
        hide_console_window()

    hide_console_window()

    setup_dlls()

    # Self-heal stale state from previous crash/unplug before applying patched DLL.
    restore()
    apply_dll()

    pid = launch()
    if not pid and pid != 0:
        sys.exit(1)

    software_proc[0] = pid if hasattr(pid, "poll") else None
    software_pid[0] = pid.pid if hasattr(pid, "pid") else pid
    start_restore_watchdog(software_pid[0], watch_usb=True)

    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
