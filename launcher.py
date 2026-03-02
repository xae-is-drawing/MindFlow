import os
import sys
import json
import hashlib
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import urllib.request
import urllib.error

GITHUB_USER    = "xae-is-drawing"
GITHUB_REPO    = "MindFlow"
GITHUB_BRANCH  = "main"
# URL de base pour les fichiers raw
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/app"

# Fichiers à surveiller pour les mises à jour (chemins relatifs à app/)
TRACKED_FILES = [
    "version.txt",
    "main.py",
    "requirements.txt",
]

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR     = os.path.join(BASE_DIR, "app")
VERSION_FILE = os.path.join(APP_DIR, "version.txt")
MAIN_PY      = os.path.join(APP_DIR, "main.py")

os.makedirs(APP_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Utilitaires réseau
# ---------------------------------------------------------------------------
def fetch_text(url: str, timeout: int = 8) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8").strip()
    except Exception as e:
        print(f"[LAUNCHER] fetch_text({url}) : {e}")
        return None


def download_file(url: str, dest: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with urllib.request.urlopen(url, timeout=15) as r:
            with open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        print(f"[LAUNCHER] download_file({url}) : {e}")
        return False


def local_version() -> str:
    if os.path.exists(VERSION_FILE):
        try:
            return open(VERSION_FILE, "r").read().strip()
        except Exception:
            pass
    return "0.0.0"


def remote_version() -> str | None:
    return fetch_text(f"{RAW_BASE}/version.txt")


# ---------------------------------------------------------------------------
# Fenêtre de progression (tkinter, thread-safe via after())
# ---------------------------------------------------------------------------
class LauncherWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MindFlow - Démarrage")
        self.geometry("420x140")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.eval("tk::PlaceWindow . center")

        tk.Label(self, text="❇️  MindFlow", font=("Helvetica", 16, "bold"),
                 fg="white", bg="#1a1a2e").pack(pady=(18, 4))

        self.status_var = tk.StringVar(value="Vérification des mises à jour…")
        tk.Label(self, textvariable=self.status_var,
                 font=("Helvetica", 10), fg="#aaaacc", bg="#1a1a2e").pack()

        self.bar = ttk.Progressbar(self, length=340, mode="indeterminate")
        self.bar.pack(pady=12)
        self.bar.start(12)

        # Lance la logique de mise à jour dans un thread daemon
        threading.Thread(target=self._update_and_launch, daemon=True).start()

    def set_status(self, text: str):
        self.after(0, lambda: self.status_var.set(text))

    def set_progress(self, value: int, maximum: int = 100):
        """Passe en mode déterminé et affiche la progression."""
        def _do():
            self.bar.stop()
            self.bar.config(mode="determinate", maximum=maximum, value=value)
        self.after(0, _do)

    def _update_and_launch(self):
        local_v  = local_version()
        remote_v = remote_version()

        if remote_v is None:
            self.set_status("⚠️ Pas de connexion : lancement de la version locale.")
        elif remote_v == local_v:
            self.set_status(f"✅ Version {local_v} : déjà à jour")
        else:
            self.set_status(f"🔃 Mise à jour {local_v} → {remote_v}...")
            self._do_update(remote_v)

        # Laisser le temps de lire le statut
        import time
        time.sleep(1.2)

        # Lancer main.py et fermer le launcher
        self.after(0, self._launch_app)

    def _do_update(self, new_version: str):
        files_to_update = list(TRACKED_FILES)

        # Récupérer le manifeste assets
        manifest_url = f"{RAW_BASE}/assets_manifest.json"
        manifest_txt = fetch_text(manifest_url)
        if manifest_txt:
            try:
                extra = json.loads(manifest_txt)  # liste de chemins relatifs
                files_to_update += [f"assets/{f}" for f in extra]
            except Exception:
                pass

        total = len(files_to_update)
        for i, rel_path in enumerate(files_to_update, 1):
            self.set_status(f"Téléchargement : {rel_path} ({i}/{total})")
            self.set_progress(i, total)
            url  = f"{RAW_BASE}/{rel_path}"
            dest = os.path.join(APP_DIR, rel_path.replace("/", os.sep))
            download_file(url, dest)

        # Installer / Mettre à jour les dépendances si requirements.txt a changé
        req_path = os.path.join(APP_DIR, "requirements.txt")
        if os.path.exists(req_path):
            self.set_status("Installation des dépendances…")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_path,
                 "--quiet", "--disable-pip-version-check"],
                check=False,
            )

    def _launch_app(self):
        if not os.path.exists(MAIN_PY):
            self.set_status("❌ - main.py introuvable : vérifie ta connexion.")
            return

        # quit() sort du mainloop proprement — le code après win.mainloop()
        # dans __main__ se charge alors de lancer main.py
        self.quit()


# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    win = LauncherWindow()
    win.mainloop()
    # Le mainloop du launcher est terminé — on peut maintenant créer
    # une nouvelle fenêtre tkinter sans conflit
    win.destroy()
    if os.path.exists(MAIN_PY):
        os.chdir(APP_DIR)
        import importlib.util
        spec = importlib.util.spec_from_file_location("__main__", MAIN_PY)
        module = importlib.util.module_from_spec(spec)
        module.__file__ = MAIN_PY
        spec.loader.exec_module(module)