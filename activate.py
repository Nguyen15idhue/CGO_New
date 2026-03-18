import sys
import os
import hashlib
import json
import time

LICENSE_FILE = os.path.join(
    os.environ.get("APPDATA", ""), r"CHCNAV\CHC Geomatics Office 2\license.dat"
)
APPDATA_DIR = os.path.join(
    os.environ.get("APPDATA", ""), r"CHCNAV\CHC Geomatics Office 2"
)
DLL_STORAGE_DIR = os.path.join(APPDATA_DIR, "DLL_Storage")
TARGET_DLL = os.path.join(APPDATA_DIR, "CHC.CGO.Common.dll")
CRACKED_DLL_PATH = os.path.join(DLL_STORAGE_DIR, "cracked.dll")
ORIGINAL_DLL_PATH = os.path.join(DLL_STORAGE_DIR, "original.dll")
EXE_PATH = os.path.join(
    os.environ.get("APPDATA", ""),
    r"CHCNAV\CHC Geomatics Office 2\CHC Geomatics Office 2.exe",
)


def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def generate_key(password):
    return f"CHC-{password[:4]}-{password[4:8]}-{password[8:12]}"


# Create activation window using tkinter
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Activate")
root.geometry("350x150")
root.resizable(False, False)

try:
    root.eval("tk::PlaceWindow . center")
except:
    pass

tk.Label(root, text="Enter Activation Key:", font=("Arial", 11)).pack(pady=20)

key_entry = tk.Entry(root, font=("Courier", 12), justify="center", width=25)
key_entry.pack()
key_entry.focus()

result = [False]


def activate():
    key = key_entry.get().strip().upper()
    if key:
        # Save license
        with open(LICENSE_FILE, "w") as f:
            json.dump({"master_key": key, "activated": time.time()}, f)
        result[0] = True
        messagebox.showinfo("Success", "Activation successful!")
        root.destroy()


def cancel():
    root.destroy()


tk.Button(
    root, text="Activate", command=activate, bg="green", fg="white", width=10
).pack(pady=15)

key_entry.bind("<Return>", lambda e: activate())

root.mainloop()

if result[0]:
    # Setup and launch
    if not os.path.exists(DLL_STORAGE_DIR):
        os.makedirs(DLL_STORAGE_DIR)

    bundle_dir = get_bundle_dir()
    cracked_src = os.path.join(bundle_dir, "source_crack.dll")
    original_src = os.path.join(bundle_dir, "source_original.dll")

    if os.path.exists(cracked_src) and not os.path.exists(CRACKED_DLL_PATH):
        import shutil

        shutil.copy2(cracked_src, CRACKED_DLL_PATH)
    if os.path.exists(original_src) and not os.path.exists(ORIGINAL_DLL_PATH):
        import shutil

        shutil.copy2(original_src, ORIGINAL_DLL_PATH)

    # Copy cracked DLL
    dest_dir = os.path.dirname(TARGET_DLL)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    if os.path.exists(CRACKED_DLL_PATH):
        import shutil

        shutil.copy2(CRACKED_DLL_PATH, TARGET_DLL)

    # Launch software
    import subprocess

    try:
        subprocess.Popen([EXE_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass
