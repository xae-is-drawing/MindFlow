import os
import sys
import json
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import urllib.request
import urllib.error

GITHUB_USER   = "xae-is-drawing"
GITHUB_REPO   = "MindFlow"
GITHUB_BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/app"

TRACKED_FILES = ["version.txt", "main.py", "requirements.txt"]

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR      = os.path.join(BASE_DIR, "app")
LIB_DIR      = os.path.join(APP_DIR, "lib")
VERSION_FILE = os.path.join(APP_DIR, "version.txt")
MAIN_PY      = os.path.join(APP_DIR, "main.py")

os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(LIB_DIR, exist_ok=True)


def find_python() -> str:
    if not getattr(sys, "frozen", False):
        return sys.executable
    python = shutil.which("python") or shutil.which("python3")
    if python:
        return python
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe"),
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "python"


def fetch_text(url: str, timeout: int = 8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8").strip()
    except Exception as e:
        print(f"[LAUNCHER] {e}")
        return None


def download_file(url: str, dest: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with urllib.request.urlopen(url, timeout=15) as r:
            with open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        print(f"[LAUNCHER] {e}")
        return False


def local_version() -> str:
    if os.path.exists(VERSION_FILE):
        try:
            return open(VERSION_FILE, "r").read().strip()
        except Exception:
            pass
    return "0.0.0"


def install_deps():
    req_path = os.path.join(APP_DIR, "requirements.txt")
    if not os.path.exists(req_path):
        return
    subprocess.run(
        [find_python(), "-m", "pip", "install",
         "-r", req_path, "--target", LIB_DIR,
         "--quiet", "--disable-pip-version-check", "--upgrade"],
        check=False,
    )


class LauncherWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MindFlow - Démarrage")
        self.geometry("420x140")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.eval("tk::PlaceWindow . center")

        tk.Label(self, text="MindFlow", font=("Helvetica", 16, "bold"),
                 fg="white", bg="#1a1a2e").pack(pady=(18, 4))

        self.status_var = tk.StringVar(value="Verification des mises a jour...")
        tk.Label(self, textvariable=self.status_var,
                 font=("Helvetica", 10), fg="#aaaacc", bg="#1a1a2e").pack()

        self.bar = ttk.Progressbar(self, length=340, mode="indeterminate")
        self.bar.pack(pady=12)
        self.bar.start(12)

        threading.Thread(target=self._run, daemon=True).start()

    def set_status(self, text: str):
        self.after(0, lambda: self.status_var.set(text))

    def set_progress(self, value: int, maximum: int = 100):
        def _do():
            self.bar.stop()
            self.bar.config(mode="determinate", maximum=maximum, value=value)
        self.after(0, _do)

    def _run(self):
        local_v  = local_version()
        remote_v = fetch_text(f"{RAW_BASE}/version.txt")

        if remote_v is None:
            self.set_status("Pas de connexion - version locale.")
        elif remote_v == local_v:
            self.set_status(f"Version {local_v} - deja a jour")
        else:
            self.set_status(f"Mise a jour {local_v} -> {remote_v}...")
            self._do_update(remote_v)

        import time
        time.sleep(1.2)
        self.after(0, self._ready)

    def _do_update(self, new_version: str):
        files = list(TRACKED_FILES)
        manifest = fetch_text(f"{RAW_BASE}/assets_manifest.json")
        if manifest:
            try:
                files += [f"assets/{f}" for f in json.loads(manifest)]
            except Exception:
                pass

        for i, rel in enumerate(files, 1):
            self.set_status(f"Telechargement : {rel} ({i}/{len(files)})")
            self.set_progress(i, len(files))
            download_file(f"{RAW_BASE}/{rel}",
                          os.path.join(APP_DIR, rel.replace("/", os.sep)))

        self.set_status("Installation des dependances...")
        install_deps()

    def _ready(self):
        if not os.path.exists(MAIN_PY):
            self.set_status("ERREUR : main.py introuvable")
            return
        self.quit()


if __name__ == "__main__":
    # Install initiale si lib/ est vide
    req_path = os.path.join(APP_DIR, "requirements.txt")
    if os.path.exists(req_path) and not os.listdir(LIB_DIR):
        root = tk.Tk()
        root.title("MindFlow")
        root.geometry("420x140")
        root.configure(bg="#1a1a2e")
        root.eval("tk::PlaceWindow . center")
        tk.Label(root, text="MindFlow", font=("Helvetica", 16, "bold"),
                 fg="white", bg="#1a1a2e").pack(pady=(18, 4))
        tk.Label(root, text="Installation initiale...",
                 font=("Helvetica", 10), fg="#aaaacc", bg="#1a1a2e").pack()
        bar = ttk.Progressbar(root, length=340, mode="indeterminate")
        bar.pack(pady=12)
        bar.start(12)
        root.update()

        def _install():
            install_deps()
            root.after(0, root.quit)

        threading.Thread(target=_install, daemon=True).start()
        root.mainloop()
        root.destroy()

    win = LauncherWindow()
    win.mainloop()
    win.destroy()

    if os.path.exists(MAIN_PY):
        python = find_python()

        # Préfère pythonw.exe (sans fenêtre console noire)
        pythonw = python.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python = pythonw

        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = LIB_DIR + (os.pathsep + existing if existing else "")

        log_path = os.path.join(BASE_DIR, "mindflow_error.log")
        try:
            # CREATE_NO_WINDOW : pas de fenêtre console noire (Windows uniquement)
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [python, MAIN_PY],
                cwd=APP_DIR,
                env=env,
                creationflags=CREATE_NO_WINDOW,
            )
            # Popen est non-bloquant : le launcher se ferme immédiatement
        except Exception as e:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(str(e))