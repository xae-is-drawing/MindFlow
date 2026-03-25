import os
import sys
import tkinter as tk
from tkinter import simpledialog, colorchooser, Menu, Toplevel, Button
from PIL import Image, ImageTk, ImageSequence
import datetime
import requests
from io import BytesIO
import json
import re
import threading
import hashlib
from dataclasses import dataclass
from tkhtmlview import HTMLLabel

# Chemins : compatibles PyInstaller (frozen) et développement normal
if getattr(sys, "frozen", False):
    # Exécuté depuis le .exe PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
CACHE_DIR   = os.path.join(BASE_DIR, "cache")
NOTES_DIR   = os.path.join(CACHE_DIR, "notes")
IMG_CACHE   = os.path.join(CACHE_DIR, "img_cache")
CONFIG_PATH = os.path.join(CACHE_DIR, "config.json")

for d in (CACHE_DIR, NOTES_DIR, IMG_CACHE):
    os.makedirs(d, exist_ok=True)

# Dimensions
WIDTH  = 1920
HEIGHT = 1080

# Configuration
DEFAULT_BACKGROUNDS = [
    {"name": "🍂🌈", "url": "https://i.postimg.cc/NfKBTr1Y/Yukkel-Gui-Pride-Month.png"},
    {"name": "🍂🌃", "url": "https://i.postimg.cc/MH83GNbz/Yukkel-Gui-Night.png"},
    {"name": "🐸", "url": "https://i.postimg.cc/qRGDzQmx/Chilling-Frog.png"},
    {"name": "🦊💫", "url": "https://i.postimg.cc/KjZVNCK0/Fox-In-The-Stars2.png"}
]

DEFAULT_CONFIG = {
    "pk_token": "",
    "fronters_refresh_ms": 60000,
    "note_colors": ["#ffff88", "#aaffaa", "#aaddff", "#ffccaa", "#ffaacc"],
    "backgrounds": DEFAULT_BACKGROUNDS,
    "default_bg": "🍂🌈",
    "current_bg": "🍂🌈",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception as e:
            print(f"[ERREUR] Chargement config : {e}")
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERREUR] Sauvegarde config : {e}")


config = load_config()

# Cache disque pour les images téléchargées
def _cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def get_cached_image(url: str, size: tuple) -> ImageTk.PhotoImage | None:
    """Retourne l'image depuis le cache disque, ou la télécharge et la met en cache."""
    key  = _cache_key(url)
    path = os.path.join(IMG_CACHE, f"{key}_{size[0]}x{size[1]}.png")
    try:
        if os.path.exists(path):
            img = Image.open(path)
        else:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).resize(size, Image.Resampling.LANCZOS)
            img.save(path, "PNG")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[ERREUR] Image {url} : {e}")
        return None

# Clients PluralKit

def get_pluralkit_fronters() -> str:
    """Appelle l'API PluralKit v2 directement — fiable et sans dépendance async."""
    token = config.get("pk_token", "").strip()
    if not token:
        return ""
    try:
        headers = {"Authorization": token}
        r = requests.get("https://api.pluralkit.me/v2/systems/@me/fronters",
                         headers=headers, timeout=8)
        r.raise_for_status()
        members = r.json().get("members", [])
        noms = [m.get("display_name") or m.get("name", "?") for m in members]
        return ", ".join(noms) if noms else "Aucun en front"
    except Exception as e:
        print(f"[ERREUR PluralKit] {e}")
        return "Erreur PluralKit"

def init_pluralkit():
    token = config.get("pk_token", "").strip()
    if token:
        print(f"[INFO] PluralKit configuré (token: {token[:6]}...)")
    else:
        print("[INFO] Token PluralKit non configuré.")
init_pluralkit()


# Dataclass Note
@dataclass
class Note:
    window:        int
    frame:         object
    html_label:    object
    color:         str
    resize_handle: int
    move_handle:   int
    text:          str


# Fenêtre Paramètres
class SettingsWindow(Toplevel):
    def __init__(self, master, on_save_callback=None):
        super().__init__(master)
        self.title("⚙️ Paramètres")
        self.geometry("540x640")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 5}

        # PluralKit
        set_pk = tk.LabelFrame(self, text="🤖 PluralKit", font=("Helvetica", 11, "bold"), padx=8, pady=6)
        set_pk.pack(fill="x", padx=12, pady=4)
        tk.Label(set_pk, text="Token :").grid(row=0, column=0, sticky="w")
        self.pk_token_var = tk.StringVar(value=config.get("pk_token", ""))
        tk.Entry(set_pk, textvariable=self.pk_token_var, width=42, show="*").grid(row=0, column=1, **pad)
        tk.Label(set_pk, text="Refresh (ms) :").grid(row=1, column=0, sticky="w")
        self.fronters_refresh_var = tk.IntVar(value=config.get("fronters_refresh_ms", 60000))
        tk.Spinbox(set_pk, from_=5000, to=300000, increment=5000,
                   textvariable=self.fronters_refresh_var, width=10).grid(row=1, column=1, sticky="w", **pad)

        # Couleurs post-its
        set_couleurs = tk.LabelFrame(self, text="🗒️ Couleurs préférées des post-its",
                           font=("Helvetica", 11, "bold"), padx=8, pady=6)
        set_couleurs.pack(fill="x", padx=12, pady=4)
        self.colors_frame = tk.Frame(set_couleurs)
        self.colors_frame.pack(fill="x")
        self.color_vars = list(config.get("note_colors", DEFAULT_CONFIG["note_colors"]))
        self._refresh_color_list()
        tk.Button(set_couleurs, text="+ Ajouter une couleur", command=self._add_color).pack(pady=4)

        # Fonds d'écran
        set_fonds = tk.LabelFrame(self, text="🖼️ Fonds d'écran",
                           font=("Helvetica", 11, "bold"), padx=8, pady=6)
        set_fonds.pack(fill="x", padx=12, pady=4)

        self.bg_vars = [dict(b) for b in config.get("backgrounds", DEFAULT_BACKGROUNDS)]
        self._default_bg_var  = tk.StringVar(value=config.get("default_bg", ""))
        self._current_bg_var  = tk.StringVar(value=config.get("current_bg", ""))

        self.bg_list_frame = tk.Frame(set_fonds)
        self.bg_list_frame.pack(fill="x")
        self._refresh_bg_list()
        tk.Button(set_fonds, text="+ Ajouter un fond", command=self._add_bg).pack(pady=4)

        tk.Button(self, text="💾  Sauvegarder", font=("Helvetica", 11, "bold"),
                  bg="#4CAF50", fg="white", command=self._save).pack(pady=16)

    def _refresh_color_list(self):
        for w in self.colors_frame.winfo_children():
            w.destroy()
        for i, color in enumerate(self.color_vars):
            row = tk.Frame(self.colors_frame)
            row.pack(fill="x", pady=1)
            tk.Label(row, bg=color, width=4, relief="ridge").pack(side="left", padx=4)
            tk.Label(row, text=color).pack(side="left", padx=4)
            tk.Button(row, text="✏️", width=3,
                      command=lambda idx=i: self._edit_color(idx)).pack(side="left", padx=2)
            tk.Button(row, text="🗑️", width=3,
                      command=lambda idx=i: self._delete_color(idx)).pack(side="left", padx=2)

    def _add_color(self):
        c = colorchooser.askcolor(title="Choisir une couleur")[1]
        if c:
            self.color_vars.append(c)
            self._refresh_color_list()

    def _edit_color(self, idx):
        c = colorchooser.askcolor(title="Modifier la couleur", color=self.color_vars[idx])[1]
        if c:
            self.color_vars[idx] = c
            self._refresh_color_list()

    def _delete_color(self, idx):
        if len(self.color_vars) > 1:
            self.color_vars.pop(idx)
            self._refresh_color_list()

    def _refresh_bg_list(self):
        for w in self.bg_list_frame.winfo_children():
            w.destroy()
        tk.Label(self.bg_list_frame, text="Nom", width=12, anchor="w").grid(row=0, column=0, padx=4)
        tk.Label(self.bg_list_frame, text="URL", width=30, anchor="w").grid(row=0, column=1, padx=4)
        tk.Label(self.bg_list_frame, text="Défaut").grid(row=0, column=2, padx=2)
        tk.Label(self.bg_list_frame, text="Actuel").grid(row=0, column=3, padx=2)
        for i, bg in enumerate(self.bg_vars):
            tk.Label(self.bg_list_frame, text=bg["name"], width=12, anchor="w").grid(row=i+1, column=0, padx=4)
            tk.Label(self.bg_list_frame, text=bg["url"][:35] + "…" if len(bg["url"]) > 35 else bg["url"],
                     width=30, anchor="w").grid(row=i+1, column=1, padx=4)
            tk.Radiobutton(self.bg_list_frame, variable=self._default_bg_var,
                           value=bg["name"]).grid(row=i+1, column=2)
            tk.Radiobutton(self.bg_list_frame, variable=self._current_bg_var,
                           value=bg["name"]).grid(row=i+1, column=3)
            tk.Button(self.bg_list_frame, text="✏️", width=3,
                      command=lambda idx=i: self._edit_bg(idx)).grid(row=i+1, column=4, padx=2)
            tk.Button(self.bg_list_frame, text="🗑️", width=3,
                      command=lambda idx=i: self._delete_bg(idx)).grid(row=i+1, column=5, padx=2)

    def _add_bg(self):
        win = tk.Toplevel(self)
        win.title("Nouveau fond d'écran")
        win.geometry("420x120")
        tk.Label(win, text="Nom :").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        name_var = tk.StringVar()
        tk.Entry(win, textvariable=name_var, width=36).grid(row=0, column=1, padx=8)
        tk.Label(win, text="URL :").grid(row=1, column=0, padx=8, sticky="w")
        url_var = tk.StringVar()
        tk.Entry(win, textvariable=url_var, width=36).grid(row=1, column=1, padx=8)
        def _confirm():
            name, url = name_var.get().strip(), url_var.get().strip()
            if name and url:
                self.bg_vars.append({"name": name, "url": url})
                self._refresh_bg_list()
                win.destroy()
        tk.Button(win, text="Ajouter", command=_confirm).grid(row=2, column=1, pady=8, sticky="e")

    def _edit_bg(self, idx):
        bg = self.bg_vars[idx]
        win = tk.Toplevel(self)
        win.title("Modifier le fond")
        win.geometry("420x120")
        tk.Label(win, text="Nom :").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        name_var = tk.StringVar(value=bg["name"])
        tk.Entry(win, textvariable=name_var, width=36).grid(row=0, column=1, padx=8)
        tk.Label(win, text="URL :").grid(row=1, column=0, padx=8, sticky="w")
        url_var = tk.StringVar(value=bg["url"])
        tk.Entry(win, textvariable=url_var, width=36).grid(row=1, column=1, padx=8)
        def _confirm():
            self.bg_vars[idx] = {"name": name_var.get().strip(), "url": url_var.get().strip()}
            self._refresh_bg_list()
            win.destroy()
        tk.Button(win, text="Enregistrer", command=_confirm).grid(row=2, column=1, pady=8, sticky="e")

    def _delete_bg(self, idx):
        if len(self.bg_vars) > 1:
            self.bg_vars.pop(idx)
            self._refresh_bg_list()

    def _save(self):
        config["pk_token"] = self.pk_token_var.get().strip()
        config["fronters_refresh_ms"] = self.fronters_refresh_var.get()
        config["note_colors"] = self.color_vars
        config["backgrounds"] = self.bg_vars
        config["default_bg"] = self._default_bg_var.get()
        config["current_bg"] = self._current_bg_var.get()
        save_config(config)
        init_pluralkit()
        if self.on_save_callback:
            self.on_save_callback()
        self.destroy()


# Whiteboard
class Whiteboard(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("MindBoard")
        self.geometry("800x600")
        self.configure(bg="white")

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.notes: list[Note] = []
        self.recent_colors = list(config.get("note_colors", ["#ffff88"]))

        self.canvas.bind("<Double-1>", self.add_note)
        self.protocol("WM_DELETE_WINDOW", lambda: [self.save_notes(), self.destroy()])
        self.load_notes()

    #  Markdown
    def _inline(self, text: str) -> str:
        text = text.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        text = text.replace("[ ]", "&#x2610;")
        text = text.replace("[x]", "&#x2611;")
        text = text.replace("[X]", "&#x2611;")
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.*?)__",     r"<u>\1</u>", text)
        text = re.sub(r"~~(.*?)~~",     r'<span style="text-decoration:line-through">\1</span>', text)
        text = re.sub(r"\*(.*?)\*",     r"<i>\1</i>", text)
        text = re.sub(r"`(.*?)`",       r"<code>\1</code>", text)
        text = re.sub(r"!\[.*?\]\((.*?)\)", r'<img src="\1" width="100">', text)
        return text

    def markdown_to_html(self, text: str) -> str:
        try:
            output = []
            in_list = False
            pending_blank = 0

            for raw_line in text.split("\n"):
                # Ligne vide
                if raw_line.strip() == "":
                    pending_blank += 1
                    continue

                # Item de liste
                m_list = re.match(r"^([ \t]*)- (.*)", raw_line)
                if m_list:
                    indent_px = len(m_list.group(1).expandtabs(4)) * 10
                    if not in_list:
                        if pending_blank > 0 and output:
                            output.append("<br>")
                        pending_blank = 0
                        output.append("<ul style='margin:2px 0; padding-left:18px'>")
                        in_list = True
                    elif pending_blank > 0:
                        output.append("<br>")
                        pending_blank = 0
                    output.append(
                        f"<li style='margin-left:{indent_px}px; padding-left:4px; "
                        f"list-style-position:outside'>{self._inline(m_list.group(2))}</li>"
                    )
                    continue

                # Continuation d'item (ligne indentée, pas un tiret)
                if in_list and raw_line.startswith((" ", "\t")) and not re.match(r"^[ \t]*- ", raw_line):
                    if pending_blank == 0 and output:
                        last = output[-1]
                        if last.endswith("</li>"):
                            output[-1] = last[:-5] + f"<br>&nbsp;&nbsp;&nbsp;&nbsp;{self._inline(raw_line.strip())}</li>"
                        pending_blank = 0
                        continue

                # Fin de liste
                if in_list:
                    output.append("</ul>")
                    in_list = False
                    if pending_blank > 0:
                        output.append("<br>")
                    pending_blank = 0

                # Lignes vides hors liste
                if pending_blank > 0:
                    output.append("<br>" * pending_blank)
                    pending_blank = 0

                # Titres
                for lvl, tag in ((r"^### (.*)", "h3"), (r"^## (.*)", "h2"), (r"^# (.*)", "h1")):
                    m = re.match(lvl, raw_line)
                    if m:
                        output.append(f"<{tag} style='margin:2px 0'>{self._inline(m.group(1))}</{tag}>")
                        break
                else:
                    output.append(self._inline(raw_line) + "<br>")

            if in_list:
                output.append("</ul>")

            html = "".join(output)
            html = re.sub(r"(<br>)+(<(?:ul|h[123]))", r"\2", html)
            html = re.sub(r"(</(?:ul|h[123])>)(<br>)+", r"\1<br>", html)
            return (
                '<div style="padding:8px; margin:0; line-height:1.5; font-family:Arial,sans-serif;">'
                + html + "</div>"
            )
        except Exception as e:
            print(f"[ERREUR Markdown] {e}")
            return text

    # Notes
    def save_notes(self):
        data = []
        for n in self.notes:
            x, y = self.canvas.coords(n.window)
            data.append({"x": x, "y": y,
                         "w": n.frame.winfo_width(), "h": n.frame.winfo_height(),
                         "text": n.text, "color": n.color})
        with open(os.path.join(NOTES_DIR, "notes.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_notes(self):
        path = os.path.join(NOTES_DIR, "notes.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for nd in json.load(f):
                    self.add_note(event=None, preset_data=nd)
        except Exception as e:
            print(f"[ERREUR] Chargement notes : {e}")

    def choose_color_with_history(self) -> str:
        win = Toplevel(self)
        win.title("Choisir une couleur")
        var = tk.StringVar(value=self.recent_colors[-1] if self.recent_colors else "#ffff88")

        def pick_new():
            c = colorchooser.askcolor(title="Couleur personnalisée")[1]
            if c:
                if c not in self.recent_colors:
                    self.recent_colors.append(c)
                    if len(self.recent_colors) > 10:
                        self.recent_colors = self.recent_colors[-10:]
                var.set(c)
                win.destroy()

        Button(win, text="Nouvelle couleur...", command=pick_new).pack(pady=5)
        for col in reversed(self.recent_colors):
            Button(win, bg=col, width=20, command=lambda c=col: [var.set(c), win.destroy()]).pack(pady=2)
        win.wait_window()
        return var.get()

    def add_note(self, event, preset_data=None):
        default_color = self.recent_colors[-1] if self.recent_colors else "#ffff88"
        if preset_data:
            x, y   = preset_data["x"], preset_data["y"]
            text   = preset_data["text"]
            color  = preset_data.get("color", default_color)
            w, h   = preset_data["w"], preset_data["h"]
        else:
            x, y = event.x, event.y
            text = simpledialog.askstring("Post-it", "Contenu de la note :", parent=self)
            if text is None:
                return
            color = self.choose_color_with_history() or default_color
            w, h  = 200, 150

        frame     = tk.Frame(self.canvas, width=w, height=h, bg=color)
        frame.pack_propagate(False)
        html_text = HTMLLabel(frame, background=color, html=self.markdown_to_html(text))
        html_text.pack(fill="both", expand=True)

        window        = self.canvas.create_window(x, y, window=frame, anchor="nw")
        move_handle   = self.canvas.create_rectangle(x-5, y-5, x+20, y+20, fill="black", tags="move")
        resize_handle = self.canvas.create_rectangle(x+w-15, y+h-15, x+w+5, y+h+5, fill="black", tags="resize")

        self.canvas.tag_bind("move", "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind("move", "<Leave>", lambda e: self.canvas.config(cursor=""))

        note = Note(window, frame, html_text, color, resize_handle, move_handle, text)
        self.notes.append(note)

        self.canvas.tag_bind(move_handle,   "<B1-Motion>", lambda e, n=note: self.move_note(e, n))
        self.canvas.tag_bind(resize_handle, "<B1-Motion>", lambda e, n=note: self.resize_note(e, n))
        html_text.bind("<Button-3>",       lambda e, n=note: self.show_context_menu(e, n))
        html_text.bind("<Double-Button-1>", lambda e, n=note: self.edit_note(n))

    def edit_note(self, note: Note):
        win = tk.Toplevel(self)
        win.title("Modifier la note")
        win.geometry("500x400")

        area = tk.Text(win, wrap="word", font=("Arial", 12), tabs=("1c",))
        area.pack(fill="both", expand=True)
        area.insert("1.0", note.text)
        area.bind("<Tab>", lambda e: (area.insert(tk.INSERT, "\t"), "break")[1])

        def save():
            note.text = area.get("1.0", "end-1c")
            note.html_label.set_html(self.markdown_to_html(note.text))
            self.save_notes()
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", save)
        tk.Button(win, text="Enregistrer", command=save).pack()

    def move_note(self, event, note: Note):
        x, y = event.x, event.y
        self.canvas.coords(note.window, x, y)
        bbox = self.canvas.bbox(note.window)
        if bbox:
            x1, y1, x2, y2 = bbox
            w, h = x2-x1, y2-y1
            self.canvas.coords(note.resize_handle, x+w-15, y+h-15, x+w+5, y+h+5)
            self.canvas.coords(note.move_handle,   x-5,    y-5,    x+20,  y+20)

    def resize_note(self, event, note: Note):
        x1, y1 = self.canvas.coords(note.window)
        nw = max(event.x - x1, 100)
        nh = max(event.y - y1, 50)
        note.frame.config(width=nw, height=nh)
        self.canvas.itemconfig(note.window, width=nw, height=nh)
        self.canvas.coords(note.resize_handle, x1+nw-15, y1+nh-15, x1+nw+5, y1+nh+5)
        self.canvas.coords(note.move_handle,   x1-5,     y1-5,     x1+20,   y1+20)

    def delete_note(self, note: Note):
        note.frame.destroy()
        self.canvas.delete(note.resize_handle)
        self.canvas.delete(note.move_handle)
        self.canvas.delete(note.window)
        self.notes.remove(note)

    def show_context_menu(self, event, note: Note):
        m = Menu(self, tearoff=0)
        m.add_command(label="Changer la couleur", command=lambda: self.change_note_color(note))
        m.add_command(label="Supprimer",          command=lambda: self.delete_note(note))
        m.post(event.x_root, event.y_root)

    def change_note_color(self, note: Note):
        c = self.choose_color_with_history()
        if c:
            note.color = c
            note.frame.config(bg=c)
            note.html_label.config(background=c)

# Application principale
class MindFlowApp(tk.Tk):
    def __init__(self, bg_url: str):
        super().__init__()
        self.title("MindFlow")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(bg="black")

        # État timer
        self.timer_running       = False
        self.timer_paused        = False
        self.afficher_idle       = True
        self.total_seconds       = 30 * 60
        self.total_initial_seconds = 30 * 60
        self.arbre_stage         = 0
        self.idle_gif_frames     = []
        self.current_frame       = 0

        # GIF actif/pausé selon visibilité fenêtre
        self._window_visible = True
        self.bind("<Map>",   lambda e: setattr(self, "_window_visible", True))
        self.bind("<Unmap>", lambda e: setattr(self, "_window_visible", False))

        # Canvas principal
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Image de fond (thread secondaire pour ne pas bloquer le démarrage)
        self.bg_image    = None
        self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw")
        # Délayé via after() pour s'assurer que la mainloop est démarrée
        self.after(50, lambda: threading.Thread(target=self._load_bg_async, args=(bg_url,), daemon=True).start())

        # Horloge
        self.time_text = self.canvas.create_text(
            WIDTH/2.5, HEIGHT/3.5, text="", font=("Helvetica", 48), fill="white")
        self.date_text = self.canvas.create_text(
            WIDTH/2.5, HEIGHT/3.5+60, text="", font=("Helvetica", 20), fill="white")
        self.update_clock()

        # Arbre / timer : centré sur le tiers droit
        self.TIMER_CX = int(WIDTH * 2 / 3) # centre horizontal du bloc timer/arbre

        self.season       = self._get_season()
        self.arbre_images = self._load_arbre_images(self.season)
        self.arbre_image_id = self.canvas.create_image(self.TIMER_CX, HEIGHT // 3, image=None)

        self.timer_text = self.canvas.create_text(
            self.TIMER_CX, HEIGHT // 3 + 190,
            text=self.format_time(self.total_seconds),
            font=("Helvetica", 24), fill="white")

        self.start_button = tk.Button(self, text="Lancer le focus", command=self.start_timer)
        self.pause_button = tk.Button(self, text="Pause",           command=self.pause_or_continue_timer)
        self.reset_button = tk.Button(self, text="Réinitialiser",   command=self.reset_timer)
        self.plus_button  = tk.Button(self, text="+", font=("Arial", 14, "bold"), command=self.increase_time)
        self.minus_button = tk.Button(self, text="−", font=("Arial", 14, "bold"), command=self.decrease_time)

        self.start_button_id = self.canvas.create_window(self.TIMER_CX,      HEIGHT // 3 + 230, window=self.start_button)

        # Boutons + et - du timer de part et d'autre du minuteur
        self.minus_button_id = self.canvas.create_window(self.TIMER_CX - 60, HEIGHT // 3 + 190, window=self.minus_button)
        self.plus_button_id  = self.canvas.create_window(self.TIMER_CX + 60, HEIGHT // 3 + 190, window=self.plus_button)

        BTN_W, BTN_H = 3, 1   # Taille commune pour les boutons, en unités tkinter (caractères)

        # Bouton paramètres (tout à gauche)
        settings_btn = tk.Button(self, text="⚙", font=("Arial", 14), relief="raised",
                                  bg="black", fg="white", cursor="hand2",
                                  width=BTN_W, height=BTN_H,
                                  command=self.open_settings)
        self.canvas.create_window(20, 20, window=settings_btn, anchor="nw")

        # Fronteurs PluralKit  (à droite du bouton settings)
        self.fronters_label = self.canvas.create_text(
            80, 33, text="", font=("Helvetica", 12), fill="white", anchor="w")
        self.after(200, self._refresh_fronteurs)

        # Bouton tableau blanc (coin haut droit)
        icon_path = os.path.join(ASSETS_DIR, "notes", "note_icon.jpg")
        if os.path.exists(icon_path):
            note_icon = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)
            self.note_imgtk = ImageTk.PhotoImage(note_icon)
            self.note_btn = tk.Button(self, image=self.note_imgtk, command=self.open_whiteboard,
                                  borderwidth=0, bg="black", cursor="hand2")
        else:
            self.note_btn = tk.Button(self, text="📋", font=("Arial", 14), relief="raised",
                                  bg="black", fg="white", cursor="hand2",
                                  width=BTN_W, height=BTN_H,
                                  command=self.open_whiteboard)
        self.note_btn.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne") # place() pour garantir l'affichage au premier plan (à la place de create_window)

        # GIF idle
        self._load_idle_gif(os.path.join(ASSETS_DIR, "arbre", "arbre_idle.gif"))
        self._animate_idle_gif()

    # Fond
    def _load_bg_async(self, url: str):
        """Télécharge/cache l'image de fond dans un thread, puis met à jour le canvas."""
        img = get_cached_image(url, (WIDTH, HEIGHT))
        if img:
            # Les mises à jour tkinter DOIVENT se faire dans le thread principal
            self.after(0, lambda i=img: self._apply_bg(i))

    def _apply_bg(self, img: ImageTk.PhotoImage):
        self.bg_image = img
        self.canvas.itemconfig(self.bg_image_id, image=self.bg_image)

    def change_background(self, url: str):
        """Charge et applique un fond d'écran depuis une URL."""
        if not url:
            return
        def _fetch():
            img = get_cached_image(url, (WIDTH, HEIGHT))
            if img:
                self.after(0, lambda i=img: self._apply_bg(i))
        threading.Thread(target=_fetch, daemon=True).start()

    # Horloge
    def update_clock(self):
        now = datetime.datetime.now()
        self.canvas.itemconfigure(self.time_text, text=now.strftime("%H:%M:%S"))
        self.canvas.itemconfigure(self.date_text, text=now.strftime("%d/%m/%Y"))
        self.after(1000, self.update_clock)

    # Fronteurs
    def _refresh_fronteurs(self):
        """Lance la récupération PluralKit dans un thread."""
        threading.Thread(target=self._fetch_fronteurs, daemon=True).start()

    def _fetch_fronteurs(self):
        texte = get_pluralkit_fronters()
        if texte:
            self.after(0, lambda t=texte: self.canvas.itemconfigure(self.fronters_label, text=t))
        self.after(config.get("fronters_refresh_ms", 60000), self._refresh_fronteurs)

    # Timer
    def format_time(self, s: int) -> str:
        m, s = divmod(s, 60)
        return f"{m:02}:{s:02}"

    def increase_time(self):
        if not self.timer_running:
            self.total_seconds += 60
            self.canvas.itemconfigure(self.timer_text, text=self.format_time(self.total_seconds))

    def decrease_time(self):
        if not self.timer_running and self.total_seconds > 60:
            self.total_seconds -= 60
            self.canvas.itemconfigure(self.timer_text, text=self.format_time(self.total_seconds))

    def start_timer(self):
        if not self.arbre_images:
            print("[ERREUR] Images d'arbre manquantes.")
            return
        self.timer_running         = True
        self.timer_paused          = False
        self.afficher_idle         = False
        self.total_initial_seconds = self.total_seconds
        self.canvas.itemconfigure(self.arbre_image_id, image=self.arbre_images[0])
        self.canvas.delete(self.start_button_id)
        self.canvas.delete(self.plus_button_id)
        self.canvas.delete(self.minus_button_id)
        self.pause_button.config(text="Pause")
        self.pause_button_id = self.canvas.create_window(self.TIMER_CX-50, 600, window=self.pause_button)
        self.reset_button_id = self.canvas.create_window(self.TIMER_CX+50, 600, window=self.reset_button)
        self.update_timer()

    def pause_or_continue_timer(self):
        if self.timer_paused:
            self.timer_paused = False
            self.pause_button.config(text="Pause")
            self.update_timer()
        else:
            self.timer_paused = True
            self.pause_button.config(text="Continuer")

    def reset_timer(self):
        self.timer_running         = False
        self.timer_paused          = False
        self.afficher_idle         = True
        self.total_seconds         = 30 * 60
        self.total_initial_seconds = 30 * 60
        self.arbre_stage           = 0
        self.canvas.itemconfigure(self.timer_text, text=self.format_time(self.total_seconds))
        self.canvas.delete(self.pause_button_id)
        self.canvas.delete(self.reset_button_id)
        self.start_button_id = self.canvas.create_window(self.TIMER_CX,    600, window=self.start_button)
        self.plus_button_id  = self.canvas.create_window(self.TIMER_CX+50, 500, window=self.plus_button)
        self.minus_button_id = self.canvas.create_window(self.TIMER_CX-50, 500, window=self.minus_button)
        if self.arbre_images:
            self.canvas.itemconfigure(self.arbre_image_id, image=self.arbre_images[0])
        if self.idle_gif_frames:
            self.canvas.itemconfigure(self.arbre_image_id, image=self.idle_gif_frames[0])
            self.current_frame = 0

    def update_timer(self):
        if not self.timer_running or self.timer_paused:
            return
        self.canvas.itemconfigure(self.timer_text, text=self.format_time(self.total_seconds))
        progress = self.total_seconds / self.total_initial_seconds if self.total_initial_seconds else 0
        stage = 3 if self.total_seconds == 0 else (0 if progress > 2/3 else (1 if progress > 1/3 else 2))
        stage = min(stage, len(self.arbre_images) - 1)
        if stage != self.arbre_stage:
            self.arbre_stage = stage
            self.canvas.itemconfigure(self.arbre_image_id, image=self.arbre_images[stage])
        self.total_seconds -= 1
        if self.total_seconds >= 0:
            self.after(1000, self.update_timer)
        else:
            self.timer_running = False
            self.timer_paused  = False
            for attr in ("pause_button_id", "reset_button_id"):
                if hasattr(self, attr):
                    self.canvas.delete(getattr(self, attr))
            self.reset_button_id = self.canvas.create_window(self.TIMER_CX, 600, window=self.reset_button)

    # Arbre / GIF
    def _get_season(self) -> str:
        m = datetime.datetime.now().month
        return ("hiver" if m in [12,1,2] else
                "printemps" if m in [3,4,5] else
                "ete" if m in [6,7,8] else "automne")

    def _load_arbre_images(self, saison: str) -> list:
        path   = os.path.join(ASSETS_DIR, "arbre", saison)
        images = []
        if os.path.exists(path):
            for f in sorted(os.listdir(path)):
                if f.endswith(".jpg"):
                    img = Image.open(os.path.join(path, f)).resize((200, 300))
                    images.append(ImageTk.PhotoImage(img))
        return images

    def _load_idle_gif(self, gif_path: str):
        if os.path.exists(gif_path):
            img = Image.open(gif_path)
            self.idle_gif_frames = [
                ImageTk.PhotoImage(frame.copy().resize((232, 264)))
                for frame in ImageSequence.Iterator(img)
            ]

    def _animate_idle_gif(self):
        # Ne joue le GIF que si la fenêtre est visible, l'idle est actif, et le timer n'est pas en cours
        if self._window_visible and self.afficher_idle and not self.timer_running and self.idle_gif_frames:
            self.current_frame = (self.current_frame + 1) % len(self.idle_gif_frames)
            self.canvas.itemconfigure(self.arbre_image_id, image=self.idle_gif_frames[self.current_frame])
        self.after(100, self._animate_idle_gif)

    # Divers
    def open_settings(self):
        SettingsWindow(self, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        """Appelé après la sauvegarde des paramètres : relance les services."""
        self.after(0, self._refresh_fronteurs)
        # Appliquer le fond courant si changé
        current_name = config.get("current_bg", "")
        bgs = {b["name"]: b["url"] for b in config.get("backgrounds", [])}
        url = bgs.get(current_name, "")
        if url:
            self.change_background(url)

    def open_whiteboard(self):
        Whiteboard(self)

# Lancement
if __name__ == "__main__":
    # Récupère l'URL du fond courant depuis la config
    _bgs     = {b["name"]: b["url"] for b in config.get("backgrounds", DEFAULT_BACKGROUNDS)}
    _current = config.get("current_bg", DEFAULT_CONFIG["current_bg"])
    bg_url   = _bgs.get(_current, DEFAULT_BACKGROUNDS[0]["url"])
    app = MindFlowApp(bg_url)
    app.mainloop()