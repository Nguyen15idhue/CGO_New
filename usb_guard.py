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
import tkinter as tk
from tkinter import messagebox

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
GUARD_LOG = os.path.join(APPDATA_DIR, "guard.log")
EXE_PATH = os.path.join(
    os.environ.get("APPDATA", ""),
    r"CHCNAV\CHC Geomatics Office 2\CHC Geomatics Office 2.exe",
)

software_pid = [None]
software_proc = [None]
monitoring = [True]
shutdown_guard = threading.Lock()
internal_pids = {os.getpid()}


def log_event(msg):
    try:
        ensure_dir(APPDATA_DIR)
        with open(GUARD_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


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


def show_info(title, text):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(title, text, parent=root)
    root.destroy()


def show_error(title, text):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showerror(title, text, parent=root)
    root.destroy()


def ask_activation_key(code):
    result = {"key": ""}

    root = tk.Tk()
    root.title("License Activation")
    root.geometry("560x320")
    root.resizable(False, False)
    root.configure(bg="#F3F5F8")
    root.attributes("-topmost", True)

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - 560) // 2
    y = (sh - 320) // 2
    root.geometry(f"560x320+{x}+{y}")

    header = tk.Frame(root, bg="#1F2A44", height=56)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text="Software Activation",
        bg="#1F2A44",
        fg="white",
        font=("Segoe UI", 13, "bold"),
    ).pack(anchor="w", padx=18, pady=(10, 0))

    tk.Label(
        header,
        text="Provide this code to your administrator and enter the activation key below.",
        bg="#1F2A44",
        fg="#D9E0EE",
        font=("Segoe UI", 9),
    ).pack(anchor="w", padx=18)

    body = tk.Frame(root, bg="#F3F5F8")
    body.pack(fill="both", expand=True, padx=18, pady=14)

    tk.Label(
        body,
        text="Activation Code",
        bg="#F3F5F8",
        fg="#1C2435",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w")

    code_row = tk.Frame(body, bg="#F3F5F8")
    code_row.pack(fill="x", pady=(6, 12))

    code_entry = tk.Entry(
        code_row,
        font=("Consolas", 12, "bold"),
        justify="center",
        readonlybackground="white",
        fg="#111827",
        relief="solid",
        bd=1,
    )
    code_entry.insert(0, code)
    code_entry.configure(state="readonly")
    code_entry.pack(side="left", fill="x", expand=True, ipady=8)

    copy_btn = tk.Button(
        code_row,
        text="Copy",
        font=("Segoe UI", 9, "bold"),
        bg="#0E7490",
        fg="white",
        activebackground="#0B6178",
        activeforeground="white",
        bd=0,
        padx=16,
        pady=8,
        cursor="hand2",
    )
    copy_btn.pack(side="left", padx=(10, 0))

    tk.Label(
        body,
        text="Activation Key",
        bg="#F3F5F8",
        fg="#1C2435",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w")

    key_entry = tk.Entry(
        body,
        font=("Consolas", 12),
        justify="center",
        relief="solid",
        bd=1,
    )
    key_entry.pack(fill="x", pady=(6, 8), ipady=8)

    hint = tk.Label(
        body,
        text="Format example: CHC-XXXX-XXXX-XXXX",
        bg="#F3F5F8",
        fg="#6B7280",
        font=("Segoe UI", 9),
    )
    hint.pack(anchor="w")

    button_row = tk.Frame(body, bg="#F3F5F8")
    button_row.pack(fill="x", pady=(16, 0))

    def do_copy():
        root.clipboard_clear()
        root.clipboard_append(code)
        copy_btn.config(text="Copied")
        root.after(1200, lambda: copy_btn.config(text="Copy"))

    def do_cancel():
        root.destroy()

    def do_confirm():
        key = key_entry.get().strip().upper()
        if not key:
            messagebox.showwarning("Activation", "Please enter the activation key.", parent=root)
            key_entry.focus_set()
            return
        result["key"] = key
        root.destroy()

    cancel_btn = tk.Button(
        button_row,
        text="Cancel",
        command=do_cancel,
        font=("Segoe UI", 9, "bold"),
        bg="#E5E7EB",
        fg="#111827",
        activebackground="#D1D5DB",
        activeforeground="#111827",
        bd=0,
        padx=18,
        pady=8,
        cursor="hand2",
    )
    cancel_btn.pack(side="right")

    confirm_btn = tk.Button(
        button_row,
        text="Confirm",
        command=do_confirm,
        font=("Segoe UI", 9, "bold"),
        bg="#2563EB",
        fg="white",
        activebackground="#1E4FD4",
        activeforeground="white",
        bd=0,
        padx=18,
        pady=8,
        cursor="hand2",
    )
    confirm_btn.pack(side="right", padx=(0, 8))

    copy_btn.config(command=do_copy)

    root.bind("<Return>", lambda _e: do_confirm())
    root.bind("<Escape>", lambda _e: do_cancel())
    root.protocol("WM_DELETE_WINDOW", do_cancel)

    key_entry.focus_set()
    root.mainloop()
    return result["key"]


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
    if os.path.exists(original_src):
        shutil.copy2(original_src, ORIGINAL_DLL)


def file_sha256(path):
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def refresh_original_from_bundle(force=False):
    bundle = get_bundle_dir()
    original_src = os.path.join(bundle, "source_original.dll")
    if not os.path.exists(original_src):
        return False
    try:
        if force:
            shutil.copy2(original_src, ORIGINAL_DLL)
            return True
        if not os.path.exists(ORIGINAL_DLL):
            shutil.copy2(original_src, ORIGINAL_DLL)
            return True
        src_hash = file_sha256(original_src)
        dst_hash = file_sha256(ORIGINAL_DLL)
        if src_hash and src_hash != dst_hash:
            shutil.copy2(original_src, ORIGINAL_DLL)
            return True
    except Exception as e:
        log_event(f"refresh_original_from_bundle_failed error={e}")
    return False


def apply_dll():
    if os.path.exists(CRACKED_DLL):
        dest_dir = os.path.dirname(TARGET_DLL)
        ensure_dir(dest_dir)
        shutil.copy2(CRACKED_DLL, TARGET_DLL)


def kill_app(target_pid=None, exclude_pids=None):
    excluded = set(exclude_pids or ())
    try:
        targets = []
        if target_pid:
            try:
                tpid = int(target_pid)
                if tpid not in excluded:
                    targets.append(tpid)
            except Exception:
                pass

        # Fallback sweep for any same-name stragglers not in excluded set.
        for pid in get_target_pids(exclude_pids=excluded):
            if pid not in targets:
                targets.append(pid)

        for pid in targets:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            log_event(f"taskkill pid={pid}")
    except Exception:
        pass


def is_pid_alive(pid):
    if not pid:
        return False
    try:
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
        )
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            return bool(ok and exit_code.value == STILL_ACTIVE)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return False
    return False


def get_target_pids(exclude_pids=None):
    excluded = set(exclude_pids or ())
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
                pid = int(parts[1])
                if pid in excluded:
                    continue
                pids.append(pid)
    except Exception:
        pass
    return pids


def wait_until_app_stopped(timeout_sec=120, target_pid=None):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        tracked = target_pid or software_pid[0]
        if tracked and is_pid_alive(tracked):
            time.sleep(0.25)
            continue
        if not get_target_pids(exclude_pids=internal_pids):
            return True
        time.sleep(0.25)
    return False


def restore():
    # Always refresh original.dll from bundled source_original.dll when available.
    refresh_original_from_bundle(force=True)
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
        log_event(f"launch_missing_target path={EXE_PATH}")
        return None
    try:
        p = subprocess.Popen(
            [EXE_PATH],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log_event(f"launch_popen_ok pid={p.pid}")
        return p
    except Exception as e:
        log_event(f"launch_popen_failed error={e}")
        try:
            os.startfile(EXE_PATH)
            time.sleep(1.5)
            r = subprocess.run(["tasklist"], capture_output=True, text=True)
            for line in r.stdout.split("\n"):
                if "CHC Geomatics Office 2.exe" in line:
                    pid = int(line.split()[1])
                    log_event(f"launch_startfile_ok pid={pid}")
                    return pid
            log_event("launch_startfile_no_pid")
        except Exception as e2:
            log_event(f"launch_startfile_failed error={e2}")
            pass
        return None


def start_restore_watchdog(app_pid=None, watch_usb=False):
    if not os.path.exists(ORIGINAL_DLL):
        return

    pid_target = str(int(app_pid) if app_pid else 0)
    watch_flag = "1" if watch_usb else "0"
    creation_flags = 0
    for flag_name in ["DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"]:
        creation_flags |= int(getattr(subprocess, flag_name, 0))

    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "--guardian",
                pid_target,
                watch_flag,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=True,
        )
        internal_pids.add(proc.pid)
    except Exception:
        pass


def ps_single_quote(text):
    return (text or "").replace("'", "''")


def start_restore_worker(target_pid=None, kill_target=False):
    pid_value = 0
    try:
        pid_value = int(target_pid or 0)
    except Exception:
        pid_value = 0

    ps = (
        "$ErrorActionPreference='SilentlyContinue'; "
        f"$pidTarget={pid_value}; "
        f"$killTarget={(1 if kill_target else 0)}; "
        f"$src='{ps_single_quote(ORIGINAL_DLL)}'; "
        f"$dst='{ps_single_quote(TARGET_DLL)}'; "
        "if ($killTarget -eq 1 -and $pidTarget -gt 0) { Stop-Process -Id $pidTarget -Force -ErrorAction SilentlyContinue }; "
        "$deadline=(Get-Date).AddMinutes(5); "
        "while ((Get-Date) -lt $deadline) { "
        "  if ($pidTarget -gt 0) { if (Get-Process -Id $pidTarget -ErrorAction SilentlyContinue) { Start-Sleep -Milliseconds 200; continue } }; "
        "  if (!(Test-Path $src)) { Start-Sleep -Milliseconds 400; continue }; "
        "  try { "
        "    Copy-Item -Path $src -Destination $dst -Force; "
        "    $h1=(Get-FileHash -Path $src -Algorithm SHA256).Hash; "
        "    $h2=(Get-FileHash -Path $dst -Algorithm SHA256).Hash; "
        "    if ($h1 -eq $h2) { exit 0 } "
        "  } catch { }; "
        "  Start-Sleep -Milliseconds 300; "
        "}; "
        "exit 1"
    )

    creation_flags = 0
    for flag_name in ["DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"]:
        creation_flags |= int(getattr(subprocess, flag_name, 0))

    try:
        proc = subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-Command",
                ps,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=True,
        )
        internal_pids.add(proc.pid)
        log_event(
            f"restore_worker_started pid={proc.pid} target_pid={pid_value} kill_target={kill_target}"
        )
        return True
    except Exception as e:
        log_event(f"restore_worker_start_failed error={e}")
        return False


def run_guardian_mode():
    if len(sys.argv) < 4:
        return

    try:
        tracked_pid = int(sys.argv[2])
    except Exception:
        tracked_pid = 0
    watch_usb = sys.argv[3] == "1"
    internal_pids.add(os.getpid())
    log_event(f"guardian_start tracked_pid={tracked_pid} watch_usb={watch_usb}")

    deadline = time.time() + (12 * 3600)
    while time.time() < deadline:
        if tracked_pid > 0 and not is_pid_alive(tracked_pid):
            break

        if tracked_pid <= 0:
            pids = get_target_pids(exclude_pids=internal_pids)
            if not pids:
                break

        if watch_usb and not os.path.exists(USB_ROOT):
            log_event("guardian_usb_removed")
            kill_app(target_pid=tracked_pid, exclude_pids=internal_pids)
            wait_until_app_stopped(timeout_sec=20, target_pid=tracked_pid)
            break

        time.sleep(0.25)

    restored = restore_with_wait(timeout_sec=300)
    log_event(f"guardian_restore_done ok={restored}")


def safe_exit(reason, kill_running=False):
    with shutdown_guard:
        if not monitoring[0]:
            return
        monitoring[0] = False
    log_event(f"safe_exit reason={reason} kill_running={kill_running} tracked_pid={software_pid[0]}")
    # Independent worker is the most reliable final safety net for repeated runs.
    start_restore_worker(target_pid=software_pid[0], kill_target=kill_running)

    if kill_running:
        # Keep in-process kill/wait as immediate path; worker above remains fallback.
        kill_app(target_pid=software_pid[0], exclude_pids=internal_pids)
        wait_until_app_stopped(timeout_sec=120, target_pid=software_pid[0])

    # Do a synchronous, long retry restore before final exit.
    restored = restore_with_wait(timeout_sec=120)
    log_event(f"safe_exit_restore_done ok={restored}")
    os._exit(0)


def monitor():
    last_hash_check = 0.0
    while monitoring[0]:
        time.sleep(0.5)

        now = time.time()
        if now - last_hash_check >= 1.0:
            last_hash_check = now
            try:
                original_hash = file_sha256(ORIGINAL_DLL)
                target_hash = file_sha256(TARGET_DLL)
                tracked = software_pid[0]
                proc = software_proc[0]
                app_running = False
                if tracked is not None and is_pid_alive(tracked):
                    app_running = True
                elif proc is not None and proc.poll() is None:
                    app_running = True
                elif get_target_pids(exclude_pids=internal_pids):
                    app_running = True

                if original_hash and target_hash and original_hash != target_hash and not app_running:
                    log_event("hash_guard_detected_mismatch_app_not_running")
                    safe_exit("hash_guard_restore", kill_running=False)
            except Exception as e:
                log_event(f"hash_guard_check_failed error={e}")

        # USB removed
        if not os.path.exists(USB_ROOT):
            log_event("monitor_detected_usb_removed")
            safe_exit("usb_removed", kill_running=True)

        # App closed: prefer tracked PID of launched process for deterministic behavior.
        tracked = software_pid[0]
        proc = software_proc[0]

        if tracked is not None and is_pid_alive(tracked):
            continue

        if proc is not None and proc.poll() is None:
            continue

        # Use same robust sequence as USB-unplug branch: kill any stragglers then restore.
        log_event("monitor_detected_app_closed")
        safe_exit("app_closed", kill_running=True)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--guardian":
        run_guardian_mode()
        return

    log_event("main_start")

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    pw = get_password()
    if not pw:
        show_error("USB Error", "Cannot detect USB identity. Run from a removable USB drive.")
        sys.exit(1)

    expected_key = gen_key(pw)

    already_licensed = check_lic(expected_key)

    if not already_licensed:
        key = ask_activation_key(pw)
        if not key:
            sys.exit(1)

        if key != expected_key:
            show_error("Activation", "Wrong key!")
            sys.exit(1)

        save_lic(expected_key)
        show_info("Activation", "Activation successful.")
    else:
        hide_console_window()

    hide_console_window()

    setup_dlls()

    # Self-heal stale state from previous crash/unplug before applying patched DLL.
    pre_restored = restore()
    log_event(f"startup_restore_done ok={pre_restored}")
    apply_dll()
    log_event("startup_apply_cracked_done")

    pid = launch()
    if not pid and pid != 0:
        log_event("launch_failed_enter_safe_exit")
        safe_exit("launch_failed", kill_running=False)
        return

    software_proc[0] = pid if hasattr(pid, "poll") else None
    software_pid[0] = pid.pid if hasattr(pid, "pid") else pid
    log_event(f"launch_done tracked_pid={software_pid[0]}")

    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
