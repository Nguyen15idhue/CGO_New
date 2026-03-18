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

# License on USB (hidden), DLL in AppData only
USB_ROOT = os.path.dirname(sys.executable)
LICENSE_FILE = os.path.join(USB_ROOT, ".lic")

# DLL in AppData only
APPDATA_DIR = os.path.join(
    os.environ.get("APPDATA", ""), r"CHCNAV\CHC Geomatics Office 2"
)
DLL_STORAGE_DIR = os.path.join(APPDATA_DIR, "DLL_Storage")
CRACKED_DLL = os.path.join(DLL_STORAGE_DIR, "cracked.dll")
ORIGINAL_DLL = os.path.join(DLL_STORAGE_DIR, "original.dll")
TARGET_DLL = os.path.join(APPDATA_DIR, "CHC.CGO.Common.dll")
EXE_PATH = os.path.join(
    os.environ.get("APPDATA", ""),
    r"CHCNAV\CHC Geomatics Office 2\CHC Geomatics Office 2.exe",
)

software_pid = [None]
monitoring = [True]


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


def get_password():
    try:
        r = subprocess.run(
            ["wmic", "cpu", "get", "ProcessorId"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        cpu = r.stdout.strip().split("\n")[-1].strip()
        r = subprocess.run(
            ["wmic", "bios", "get", "SerialNumber"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        bios = r.stdout.strip().split("\n")[-1].strip()
        r = subprocess.run(
            ["wmic", "baseboard", "get", "SerialNumber"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        mb = r.stdout.strip().split("\n")[-1].strip()
        return (
            hashlib.sha256(f"{cpu}-{bios}-{mb}-150925".encode())
            .hexdigest()[:16]
            .upper()
        )
    except:
        return hashlib.sha256(b"DEFAULT-150925").hexdigest()[:16].upper()


def gen_key(pw):
    return f"CHC-{pw[:4]}-{pw[4:8]}-{pw[8:12]}"


def check_lic():
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        with open(LICENSE_FILE, "r") as f:
            return bool(json.load(f).get("key", ""))
    except:
        return False


def save_lic(key):
    with open(LICENSE_FILE, "w") as f:
        json.dump({"key": key, "time": time.time()}, f)


def setup_dlls():
    if not os.path.exists(DLL_STORAGE_DIR):
        os.makedirs(DLL_STORAGE_DIR)

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
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
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


def restore():
    if os.path.exists(ORIGINAL_DLL):
        dest_dir = os.path.dirname(TARGET_DLL)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy2(ORIGINAL_DLL, TARGET_DLL)


def launch():
    if not os.path.exists(EXE_PATH):
        return None
    try:
        p = subprocess.Popen(
            f'"{EXE_PATH}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return p.pid
    except:
        try:
            os.startfile(EXE_PATH)
            time.sleep(1)
            r = subprocess.run(["tasklist"], capture_output=True, text=True)
            for line in r.stdout.split("\n"):
                if "CHC Geomatics Office 2.exe" in line:
                    return int(line.split()[1])
        except:
            pass
        return None


def monitor():
    while monitoring[0]:
        time.sleep(0.5)
        # USB removed
        if not os.path.exists(USB_ROOT):
            kill_app()
            restore()
            monitoring[0] = False
            os._exit(0)
        # App closed
        if software_pid[0] and software_pid[0] != 0:
            try:
                r = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {software_pid[0]}"],
                    capture_output=True,
                    text=True,
                )
                if str(software_pid[0]) not in r.stdout:
                    restore()
                    monitoring[0] = False
                    os._exit(0)
            except:
                pass


def main():
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not check_lic():
        pw = get_password()
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

        if key != gen_key(pw):
            print("\nWrong key!")
            time.sleep(2)
            sys.exit(1)

        save_lic(gen_key(pw))
        print("\nOK!")
        time.sleep(1)

    setup_dlls()
    apply_dll()

    pid = launch()
    if not pid and pid != 0:
        sys.exit(1)

    software_pid[0] = pid

    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
