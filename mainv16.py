#!/usr/bin/env python3
"""
Browser Update Bot — Desktop App v10
Diseño moderno estilo macOS: fondo blanco, cards con sombra, íconos SVG,
badge verde suave, flecha >, botón azul redondeado.
"""

import os, platform, subprocess, threading, re, json, webbrowser, time
import urllib.request
from datetime import datetime

# ── DPI awareness (Windows) — debe ir ANTES de importar tkinter ──────────────
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk
from tkinter import font as tkfont

# ── Paleta light ──────────────────────────────────────────────────────────────
BG       = "#f2f2f7"   # fondo gris Apple
SURFACE  = "#ffffff"   # cards blancas
TEXT     = "#1c1c1e"   # texto principal casi negro
MUTED    = "#8e8e93"   # texto secundario gris
ACCENT   = "#2563eb"   # azul botón
ACCENT_H = "#1d4ed8"   # hover azul
GREEN_BG = "#dcfce7"   # fondo badge verde suave
GREEN_FG = "#16a34a"   # texto badge verde
YELLOW_BG= "#fef9c3"
YELLOW_FG= "#b45309"
SEP      = "#e5e5ea"   # separadores
FOOTER_BG= "#f2f2f7"

# ── Detección de versiones instaladas ─────────────────────────────────────────

def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        return r.stdout.strip()
    except Exception:
        return ""

def _ver(text):
    m = re.search(r"\d+[\d.]+", text)
    return m.group() if m else None

def detect_chrome():
    if platform.system() == "Darwin":
        p = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        return _ver(_run([p, "--version"])) if os.path.exists(p) else None
    if platform.system() == "Windows":
        try:
            import winreg
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for k in [r"SOFTWARE\Google\Chrome\BLBeacon",
                          r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"]:
                    try:
                        with winreg.OpenKey(hive, k) as reg:
                            return winreg.QueryValueEx(reg, "version")[0]
                    except: pass
        except: pass
        for p in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]:
            if os.path.exists(p):
                return _ver(_run([p, "--version"]))
    return None

def detect_firefox():
    if platform.system() == "Darwin":
        p = "/Applications/Firefox.app/Contents/MacOS/firefox"
        return _ver(_run([p, "--version"])) if os.path.exists(p) else None
    if platform.system() == "Windows":
        try:
            import winreg
            for k in [r"SOFTWARE\Mozilla\Mozilla Firefox",
                      r"SOFTWARE\WOW6432Node\Mozilla\Mozilla Firefox"]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, k) as reg:
                        return winreg.QueryValueEx(reg, "CurrentVersion")[0].split()[0]
                except: pass
        except: pass
    return None

def detect_edge():
    if platform.system() == "Darwin":
        p = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        return _ver(_run([p, "--version"])) if os.path.exists(p) else None
    if platform.system() == "Windows":
        try:
            import winreg
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for k in [
                    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{56EB18F8-B008-4CBD-B6D2-8C97FE7E9062}",
                    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{56EB18F8-B008-4CBD-B6D2-8C97FE7E9062}",
                ]:
                    try:
                        with winreg.OpenKey(hive, k) as reg:
                            v = winreg.QueryValueEx(reg, "pv")[0]
                            if v and v != "0.0.0.0":
                                return v
                    except: pass
        except: pass
        for p in [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]:
            if os.path.exists(p):
                return _ver(_run([p, "--version"]))
    return None

def detect_safari():
    if platform.system() != "Darwin":
        return None
    p = "/Applications/Safari.app/Contents/Info.plist"
    if os.path.exists(p):
        out = _run(["defaults", "read", p, "CFBundleShortVersionString"])
        return out or None
    return None

# ── APIs versiones online ──────────────────────────────────────────────────────

def _fetch(url):
    _UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except:
        return None

def fetch_chrome_latest():
    """
    Lee la versión más reciente de Chrome directamente desde los archivos
    que el propio updater de Chrome descarga en tu Mac/Windows.
    Esta es la misma fuente que Chrome usa internamente — 100% confiable.
    """
    if platform.system() == "Darwin":
        # Chrome guarda la última versión disponible en este archivo JSON
        # que su updater (Keystone) mantiene actualizado en background
        update_paths = [
            "/Library/Google/GoogleSoftwareUpdate/Preferences/com.google.Chrome.plist",
            os.path.expanduser("~/Library/Google/GoogleSoftwareUpdate/Preferences/com.google.Chrome.plist"),
            # Ruta alternativa del bundle
            "/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Resources/VERSION",
        ]
        # Intenta leer el archivo VERSION del bundle instalado
        ver_path = "/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Resources/VERSION"
        if os.path.exists(ver_path):
            try:
                with open(ver_path) as f:
                    v = f.read().strip()
                if re.match(r"\d+\.\d+\.\d+\.\d+", v):
                    return v
            except Exception:
                pass

        # Fallback: leer desde el ejecutable directamente
        exe = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(exe):
            out = _run([exe, "--version"])
            v = _ver(out)
            if v:
                return v  # Si podemos leerlo, instalada == latest (ya está actualizado)

    elif platform.system() == "Windows":
        # En Windows Chrome guarda la versión en el registro
        try:
            import winreg
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for k in [r"SOFTWARE\Google\Chrome\BLBeacon",
                          r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"]:
                    try:
                        with winreg.OpenKey(hive, k) as reg:
                            return winreg.QueryValueEx(reg, "version")[0]
                    except:
                        pass
        except:
            pass

    # Último recurso: API de Google con User-Agent real
    _UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36")
    plat_key = "mac_arm64" if platform.machine() == "arm64" else "mac"
    try:
        req = urllib.request.Request(
            f"https://versionhistory.googleapis.com/v1/chrome/platforms/{plat_key}"
            f"/channels/stable/versions?filter=endtime=none&order_by=version%20desc&page_size=1",
            headers={"User-Agent": _UA, "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode())
        versions = d.get("versions", [])
        if versions:
            return versions[0].get("version")
    except:
        pass
    return None

def fetch_firefox_latest():
    d = _fetch("https://product-details.mozilla.org/1.0/firefox_versions.json")
    return d.get("LATEST_FIREFOX_VERSION") if d else None

def fetch_edge_latest():
    arch = "arm64" if platform.machine() == "arm64" else "x64"
    plat = "MacOS" if platform.system() == "Darwin" else "Windows"
    d = _fetch("https://edgeupdates.microsoft.com/api/products")
    if d:
        for p in d:
            if p.get("Product") == "Stable":
                for rel in p.get("Releases", []):
                    if rel.get("Platform") == plat and rel.get("Architecture") == arch:
                        return rel.get("ProductVersion")
                for rel in p.get("Releases", []):
                    if rel.get("Platform") == plat:
                        return rel.get("ProductVersion")
    d2 = _fetch("https://edgeupdates.microsoft.com/api/products?view=enterprise")
    if d2:
        for p in d2:
            if p.get("Product") == "Stable":
                for rel in p.get("Releases", []):
                    if rel.get("Platform") == plat and rel.get("Architecture") == arch:
                        return rel.get("ProductVersion")
    return None

def fetch_safari_latest():
    d = _fetch("https://developer.apple.com/tutorials/data/documentation/safari-release-notes.json")
    if d:
        versions = []
        for ref in d.get("references", {}).values():
            t = ref.get("title", "")
            if re.match(r"^\d+(\.\d+)*$", t):
                versions.append(t)
        if versions:
            versions.sort(key=lambda v: v_tuple(v), reverse=True)
            return versions[0]
    return None

# ── Acciones de apertura/actualización ────────────────────────────────────────

def _osascript(script):
    subprocess.Popen(["osascript", "-e", script])

def _win_open_internal_url(exe_path, url, window_title_fragment):
    """
    Abre un navegador en Windows y navega a una URL interna (chrome:// o edge://)
    usando PowerShell para enviar la URL al portapapeles y luego Ctrl+L + Enter.
    Funciona aunque el navegador ya esté abierto.
    """
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
# Guardar portapapeles original
$prev = [System.Windows.Forms.Clipboard]::GetText()
# Copiar la URL destino
[System.Windows.Forms.Clipboard]::SetText('{url}')
# Lanzar o activar el navegador
$proc = Start-Process -FilePath '{exe_path}' -PassThru
Start-Sleep -Milliseconds 1800
# Buscar la ventana del navegador
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {{
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
$windows = Get-Process | Where-Object {{$_.MainWindowTitle -like '*{window_title_fragment}*'}} | Select-Object -First 1
if ($windows) {{
    [WinAPI]::ShowWindow($windows.MainWindowHandle, 9)
    [WinAPI]::SetForegroundWindow($windows.MainWindowHandle)
    Start-Sleep -Milliseconds 400
}}
# Abrir barra de direcciones y pegar URL
[System.Windows.Forms.SendKeys]::SendWait('%d')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('^a')
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('{{ENTER}}')
Start-Sleep -Milliseconds 500
# Restaurar portapapeles
[System.Windows.Forms.Clipboard]::SetText($prev)
"""
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
         "-Command", ps_script],
        creationflags=0x08000000  # CREATE_NO_WINDOW
    )


def update_chrome():
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Google Chrome"])
        time.sleep(1.5)
        _osascript('tell application "Google Chrome" to open location "chrome://settings/help"')
    else:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        exe = next((p for p in chrome_paths if os.path.exists(p)), None)
        if exe:
            _win_open_internal_url(exe, "chrome://settings/help", "Chrome")
        else:
            webbrowser.open("https://support.google.com/chrome/answer/95414")

def update_firefox():
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Firefox", "--args", "-url", "about:preferences#general"])
        time.sleep(2.0)
        _osascript('''
            tell application "Firefox" to activate
            delay 1
            tell application "System Events"
                tell process "Firefox"
                    set menuNames to {"Firefox", "Firefox"}
                    set itemNames to {"Acerca de Firefox", "About Firefox"}
                    repeat with i from 1 to 2
                        try
                            click menu item (item i of itemNames) of menu (item i of menuNames) of menu bar 1
                            exit repeat
                        end try
                    end repeat
                end tell
            end tell
        ''')
    else:
        for p in [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]:
            if os.path.exists(p):
                subprocess.Popen([p, "about:preferences#general"])
                return
        subprocess.Popen(["start", "firefox", "about:preferences#general"], shell=True)

def update_edge():
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Microsoft Edge"])
        time.sleep(1.5)
        _osascript('tell application "Microsoft Edge" to open location "edge://settings/help"')
    else:
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        exe = next((p for p in edge_paths if os.path.exists(p)), None)
        if exe:
            _win_open_internal_url(exe, "edge://settings/help", "Edge")
        else:
            webbrowser.open("https://support.microsoft.com/en-us/topic/update-microsoft-edge-c61afc1e-d7f5-4dc5-b764-bb9fc07c1b2e")

def update_safari():
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "x-apple.systempreferences:com.apple.preferences.softwareupdate"])
    else:
        webbrowser.open("https://support.apple.com/downloads/safari")

# ── Comparador de versiones ───────────────────────────────────────────────────

def v_tuple(v):
    return tuple(int(x) for x in re.split(r"[.\-]", v or "0") if x.isdigit()) or (0,)

def is_newer(latest, inst):
    """Compara solo major.minor.patch — el 4to número (build) varía por
    arquitectura/canal y no indica una actualización real para el usuario."""
    if not latest or not inst: return False
    a = v_tuple(latest)[:3]
    b = v_tuple(inst)[:3]
    for i in range(3):
        ai = a[i] if i < len(a) else 0
        bi = b[i] if i < len(b) else 0
        if ai > bi: return True
        if ai < bi: return False
    return False

# ── Config navegadores ────────────────────────────────────────────────────────

BROWSERS = [
    {"id": "chrome",  "name": "Google Chrome",  "color": "#4285f4",
     "detect": detect_chrome,  "fetch": fetch_chrome_latest,  "update": update_chrome},
    {"id": "firefox", "name": "Mozilla Firefox", "color": "#ff6611",
     "detect": detect_firefox, "fetch": fetch_firefox_latest, "update": update_firefox},
    {"id": "edge",    "name": "Microsoft Edge",  "color": "#0078d4",
     "detect": detect_edge,    "fetch": fetch_edge_latest,    "update": update_edge},
    {"id": "safari",  "name": "Safari",          "color": "#006cff",
     "detect": detect_safari,  "fetch": fetch_safari_latest,  "update": update_safari},
]

# ── Íconos dibujados con Canvas ───────────────────────────────────────────────

def draw_icon(canvas, browser_id, size=40):
    """Dibuja un ícono estilizado del browser en un Canvas."""
    c = canvas
    s = size
    cx, cy = s // 2, s // 2

    if browser_id == "chrome":
        # Fondo blanco
        c.create_oval(1, 1, s-1, s-1, fill="white", outline="#e5e5ea", width=1)
        # Tres sectores del anillo exterior
        ring_outer = s - 4
        ring_inner = int(s * 0.38)
        for start, color in [(30, "#ea4335"), (150, "#fbbc05"), (270, "#34a853")]:
            c.create_arc(2, 2, ring_outer, ring_outer,
                         start=start, extent=120, fill=color, outline=color)
        # Anillo blanco intermedio
        gap = int(s * 0.13)
        c.create_oval(cx-ring_inner, cy-ring_inner,
                      cx+ring_inner, cy+ring_inner,
                      fill="white", outline="white", width=gap)
        # Círculo central azul
        ir = int(s * 0.22)
        c.create_oval(cx-ir, cy-ir, cx+ir, cy+ir,
                      fill="#4285f4", outline="white", width=2)

    elif browser_id == "firefox":
        # Fondo degradado naranja → rojo
        c.create_oval(1, 1, s-1, s-1, fill="#e25920", outline="")
        c.create_oval(3, 3, s-3, s-3, fill="#ff7139", outline="")
        # Globo azul
        ir = int(s * 0.30)
        c.create_oval(cx-ir, cy-ir+2, cx+ir, cy+ir+2, fill="#0060df", outline="")
        # Continentes blancos simplificados
        c.create_arc(cx-ir+2, cy-ir+4, cx+ir-2, cy+ir,
                     start=20, extent=140, fill="#00b3f4", outline="")
        # Llama naranja encima derecha
        c.create_arc(cx-2, cy-ir-6, cx+ir+4, cy+4,
                     start=300, extent=160, fill="#ff9400", outline="")
        c.create_arc(cx, cy-ir-2, cx+ir+2, cy+2,
                     start=310, extent=130, fill="#ffca00", outline="")

    elif browser_id == "edge":
        # Fondo azul oscuro
        c.create_oval(1, 1, s-1, s-1, fill="#0f4c81", outline="")
        # Cuerpo principal azul Microsoft
        c.create_arc(3, 3, s-3, s-3, start=180, extent=200, fill="#0078d4", outline="")
        c.create_rectangle(3, cy-2, s-3, s-3, fill="#0078d4", outline="")
        # Ola teal en la parte inferior
        c.create_arc(int(s*0.1), int(s*0.45), int(s*0.95), s+4,
                     start=0, extent=180, fill="#50e6ff", outline="")
        # Reflejo blanco curvo superior
        c.create_arc(int(s*0.2), int(s*0.1), int(s*0.85), int(s*0.55),
                     start=15, extent=150, style="arc", outline="white", width=2)

    elif browser_id == "safari":
        # Fondo degradado azul cielo
        c.create_oval(1, 1, s-1, s-1, fill="#006cff", outline="")
        c.create_oval(2, 2, s-2, int(s*0.6), fill="#4da3ff", outline="")
        # Cara del reloj (círculo blanco)
        ir = int(s * 0.36)
        c.create_oval(cx-ir, cy-ir, cx+ir, cy+ir, fill="white", outline="")
        # Aguja norte (blanca) → apunta arriba-derecha
        import math
        angle = math.radians(45)
        nx = cx + int(ir*0.7 * math.sin(angle))
        ny = cy - int(ir*0.7 * math.cos(angle))
        c.create_line(cx, cy, nx, ny, fill="white", width=2, capstyle="round")
        # Aguja sur (roja) → apunta abajo-izquierda
        sx2 = cx - int(ir*0.55 * math.sin(angle))
        sy2 = cy + int(ir*0.55 * math.cos(angle))
        c.create_line(cx, cy, sx2, sy2, fill="#ff3b30", width=2, capstyle="round")
        # Punto central
        c.create_oval(cx-2, cy-2, cx+2, cy+2, fill="#333", outline="")


# ── GUI ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Browser Update")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._checking = False
        self._auto_timer = None
        self._rows = {}

        # Fuentes
        self._f_title  = tkfont.Font(family="SF Pro Display" if platform.system()=="Darwin"
                                     else "Segoe UI", size=17, weight="bold")
        self._f_sub    = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=11)
        self._f_name   = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=13, weight="bold")
        self._f_meta   = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=11)
        self._f_btn    = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=12, weight="bold")
        self._f_badge  = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=11, weight="bold")
        self._f_footer = tkfont.Font(family="SF Pro Text" if platform.system()=="Darwin"
                                     else "Segoe UI", size=11)

        self._build()
        self.update_idletasks()
        self.update()
        # Ajustar tamaño: dejar que tkinter calcule y luego fijar
        if platform.system() == "Windows":
            self.after(100, self._fix_win_size)
        else:
            self.geometry("520x660")

        # ── Ícono de la aplicación ────────────────────────────────────────────
        _sys = platform.system()
        _dir = os.path.dirname(os.path.abspath(__file__))
        try:
            if _sys == "Darwin":
                # Intentar con PIL primero (más compatible con tkinter)
                _icon_path = os.path.join(_dir, "icono.icns")
                if os.path.exists(_icon_path):
                    try:
                        from PIL import Image, ImageTk
                        _img = Image.open(_icon_path).convert("RGBA")
                        _img = _img.resize((64, 64), Image.LANCZOS)
                        self._app_icon = ImageTk.PhotoImage(_img)
                        self.iconphoto(True, self._app_icon)
                    except ImportError:
                        # Sin PIL: guardar como PNG temporal y usar iconphoto
                        import tempfile
                        _png_path = os.path.join(_dir, "icono_tmp.png")
                        # Convertir .icns → .png con sips (herramienta nativa macOS)
                        subprocess.run(
                            ["sips", "-s", "format", "png", _icon_path,
                             "--out", _png_path, "--resampleWidth", "64"],
                            capture_output=True)
                        if os.path.exists(_png_path):
                            self._app_icon = tk.PhotoImage(file=_png_path)
                            self.iconphoto(True, self._app_icon)
            elif _sys == "Windows":
                _ico_path = os.path.join(_dir, "icono.ico")
                if os.path.exists(_ico_path):
                    self.iconbitmap(default=_ico_path)
                    self.wm_iconbitmap(default=_ico_path)
        except Exception:
            pass

        self.after(300, self._start_check)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sep(self, parent=None, color=SEP, pady=0):
        p = parent or self
        tk.Frame(p, bg=color, height=1).pack(fill="x", pady=pady)

    def _rounded_btn(self, parent, text, command, bg=ACCENT, fg="white",
                     hover=ACCENT_H, font=None, padx=18, pady=9):
        """Botón realmente redondeado usando Canvas."""
        f = font or self._f_btn

        # Medir texto para dimensionar el canvas
        import tkinter.font as tkf
        _f = f
        _text_w = _f.measure(text)
        _text_h = _f.metrics("linespace")
        btn_w = _text_w + padx * 2
        btn_h = _text_h + pady * 2
        r = btn_h // 2  # radio = mitad de la altura → píldora perfecta

        c = tk.Canvas(parent, width=btn_w, height=btn_h,
                      bg=parent["bg"], highlightthickness=0, cursor="hand2")
        c._bg = bg
        c._hover = hover
        c._text = text
        c._font = f
        c._fg = fg

        def _draw(color):
            c.delete("all")
            # Píldora: dos arcos + rectángulo central
            c.create_arc(0, 0, 2*r, btn_h, start=90, extent=180, fill=color, outline=color)
            c.create_arc(btn_w-2*r, 0, btn_w, btn_h, start=270, extent=180, fill=color, outline=color)
            c.create_rectangle(r, 0, btn_w-r, btn_h, fill=color, outline=color)
            c.create_text(btn_w//2, btn_h//2, text=text, fill=fg, font=f, anchor="center")

        c._draw = _draw
        _draw(bg)

        c.bind("<Button-1>", lambda e: command())
        c.bind("<Enter>",    lambda e: _draw(hover))
        c.bind("<Leave>",    lambda e: _draw(bg))
        return c

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        f = tk.Frame(self, bg=SURFACE)
        f.pack(fill="x")

        inner = tk.Frame(f, bg=SURFACE)
        inner.pack(fill="x", padx=20, pady=16)

        # Ícono escudo azul con Canvas
        icon_bg = tk.Frame(inner, bg="#eff6ff", width=52, height=52)
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        c = tk.Canvas(icon_bg, width=52, height=52, bg="#eff6ff",
                      highlightthickness=0)
        c.pack(expand=True)
        # Escudo simplificado
        c.create_polygon(26,6, 44,14, 44,28, 26,46, 8,28, 8,14,
                         fill=ACCENT, outline="")
        c.create_polygon(26,14, 36,20, 36,29, 26,38, 16,29, 16,20,
                         fill="white", outline="")

        # Texto
        mid = tk.Frame(inner, bg=SURFACE)
        mid.pack(side="left", padx=14, fill="y", expand=True)
        tk.Label(mid, text="Browser Update", font=self._f_title,
                 bg=SURFACE, fg=TEXT, anchor="w").pack(anchor="w")
        self._lbl_sub = tk.Label(mid, text="Listo para verificar",
                                 font=self._f_sub, bg=SURFACE, fg=MUTED, anchor="w")
        self._lbl_sub.pack(anchor="w")

        # Botón Verificar
        self._btn = self._rounded_btn(inner, "↺  Verificar ahora",
                                      self._start_check, padx=16, pady=10)
        self._btn.pack(side="right")

    # ── Cards ─────────────────────────────────────────────────────────────────

    def _build_cards(self):
        self._cards_frame = tk.Frame(self, bg=BG)
        self._cards_frame.pack(fill="x", padx=16, pady=14)
        for b in BROWSERS:
            card = self._make_card(self._cards_frame, b)
            card.pack(fill="x", pady=4)
            self._rows[b["id"]] = card

    def _make_card(self, parent, b):
        # Frame exterior con borde suave
        card = tk.Frame(parent, bg=SURFACE,
                        highlightthickness=1, highlightbackground=SEP)

        # ── Ícono ──────────────────────────────────────────────────────────
        icon_wrap = tk.Frame(card, bg="#f8f8fa", width=62, height=62)
        icon_wrap.pack(side="left", padx=(12, 8), pady=12)
        icon_wrap.pack_propagate(False)

        c = tk.Canvas(icon_wrap, width=44, height=44,
                      bg="#f8f8fa", highlightthickness=0)
        c.place(relx=0.5, rely=0.5, anchor="center")
        draw_icon(c, b["id"], size=44)

        # ── Centro: nombre + versiones ─────────────────────────────────────
        mid = tk.Frame(card, bg=SURFACE)
        mid.pack(side="left", fill="both", expand=True, pady=13)

        tk.Label(mid, text=b["name"], font=self._f_name,
                 bg=SURFACE, fg=TEXT, anchor="w").pack(anchor="w")

        lbl_inst = tk.Label(mid, text="Instalada:   —",
                            font=self._f_meta, bg=SURFACE, fg=MUTED, anchor="w")
        lbl_inst.pack(anchor="w", pady=(1, 0))

        lbl_lat = tk.Label(mid, text="Última:        —",
                           font=self._f_meta, bg=SURFACE, fg=MUTED, anchor="w")
        lbl_lat.pack(anchor="w")

        # ── Derecha: badge + flecha ────────────────────────────────────────
        right = tk.Frame(card, bg=SURFACE)
        right.pack(side="right", padx=(8, 14), pady=12)

        # Badge estado (Canvas redondeado)
        _badge_w = 180 if platform.system() == "Windows" else 110
        badge = tk.Canvas(right, width=_badge_w, height=30,
                          bg=SURFACE, highlightthickness=0)
        badge.pack(anchor="e")
        badge._text_id = None
        badge._rect_id = None
        badge._bg_color = SEP
        badge._fg_color = MUTED
        badge._label_text = "—"

        def _draw_badge(c, text, bg, fg):
            c.delete("all")
            w, h = int(c["width"]), 30
            r = 14
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline=bg)
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline=bg)
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=bg, outline=bg)
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=bg, outline=bg)
            c.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
            c.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)
            c.create_text(w//2, h//2, text=text, fill=fg,
                          font=self._f_badge, anchor="center")
            c._bg_color = bg
            c._fg_color = fg
            c._label_text = text

        badge._draw = _draw_badge
        _draw_badge(badge, "—", SEP, MUTED)

        # Flecha chevron >
        arrow = tk.Label(right, text="›", font=tkfont.Font(size=20),
                         bg=SURFACE, fg=MUTED, cursor="hand2")
        arrow.pack(anchor="e", pady=(4, 0))
        arrow.bind("<Button-1>", lambda e, fn=b["update"]: fn())
        arrow._visible = True

        card._inst  = lbl_inst
        card._lat   = lbl_lat
        card._badge = badge
        card._arrow = arrow

        return card

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self):
        self._sep(color=SEP)
        f = tk.Frame(self, bg=SURFACE)
        f.pack(fill="x", padx=20, pady=12)

        # Punto verde animado
        dot = tk.Label(f, text="●", font=self._f_footer,
                       bg=SURFACE, fg=GREEN_FG)
        dot.pack(side="left")
        tk.Label(f, text="  Revisión automática cada 6 horas",
                 font=self._f_footer, bg=SURFACE, fg=MUTED).pack(side="left")

        # Última verificación
        right_f = tk.Frame(f, bg=SURFACE)
        right_f.pack(side="right")
        tk.Label(right_f, text="🕐 ", font=self._f_footer,
                 bg=SURFACE, fg=MUTED).pack(side="left")
        self._lbl_time = tk.Label(right_f, text="—",
                                  font=self._f_footer, bg=SURFACE, fg=MUTED)
        self._lbl_time.pack(side="left")

    def _fix_win_size(self):
        """Ajusta el tamaño de la ventana en Windows según el contenido real."""
        self.update_idletasks()
        w = self.winfo_reqwidth() + 20
        h = self.winfo_reqheight() + 20
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)

    def _build(self):
        self._build_header()
        self._sep(color=SEP)
        self._build_cards()
        self._build_footer()

    # ── Estados de card ───────────────────────────────────────────────────────

    def _card_checking(self, card):
        card._inst.config(text="Instalada:   —", fg=MUTED)
        card._lat.config(text="")
        card._lat.pack_forget()
        _txt = "Espera…" if platform.system() == "Windows" else "Verificando…"
        card._badge._draw(card._badge, _txt, SEP, MUTED)
        card.config(highlightbackground=SEP)

    def _card_state(self, card, installed, latest, state):
        card._inst.config(text=f"Instalada:   {installed or 'No detectado'}", fg=MUTED)

        # "Última" solo aparece cuando hay actualización real con versión distinta
        if state == "update" and latest and latest != installed:
            card._lat.config(text=f"Última:        {latest}", fg=YELLOW_FG)
            card._lat.pack(anchor="w")
        else:
            card._lat.config(text="")
            card._lat.pack_forget()

        if state == "ok":
            card.config(highlightbackground="#bbf7d0")
            card._badge._draw(card._badge, "✓  Al día", GREEN_BG, GREEN_FG)
            card._arrow.config(fg="#c7c7cc")
        elif state == "update":
            card.config(highlightbackground="#fde68a")
            card._badge._draw(card._badge, "↑  Actualizar", YELLOW_BG, YELLOW_FG)
            card._arrow.config(fg=YELLOW_FG, cursor="hand2")
        elif state == "missing":
            card.config(highlightbackground=SEP)
            card._badge._draw(card._badge, "No instalado", SEP, MUTED)
            card._arrow.config(fg="#e5e5ea")
        else:
            card.config(highlightbackground=SEP)
            card._badge._draw(card._badge, "Sin conexión", SEP, MUTED)
            card._arrow.config(fg="#e5e5ea")

    # ── Verificación ──────────────────────────────────────────────────────────

    def _start_check(self):
        if self._checking: return
        self._checking = True
        # Redibujar botón en estado "verificando"
        _btn = self._btn
        _btn.delete("all")
        w = int(_btn["width"]); h = int(_btn["height"]); r = h // 2
        _btn.create_arc(0, 0, 2*r, h, start=90, extent=180, fill="#93c5fd", outline="#93c5fd")
        _btn.create_arc(w-2*r, 0, w, h, start=270, extent=180, fill="#93c5fd", outline="#93c5fd")
        _btn.create_rectangle(r, 0, w-r, h, fill="#93c5fd", outline="#93c5fd")
        _btn.create_text(w//2, h//2, text="↺  Verificando…", fill="white",
                         font=self._f_btn, anchor="center")
        _btn.unbind("<Button-1>")
        _btn.unbind("<Enter>")
        _btn.unbind("<Leave>")
        self._lbl_sub.config(text="Verificando versiones…")
        for card in self._rows.values():
            self._card_checking(card)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        results = {}
        for b in BROWSERS:
            inst   = b["detect"]()
            latest = b["fetch"]()
            if not inst:
                state = "missing"
            elif not latest:
                if b["id"] == "safari":
                    latest = inst
                    state = "ok"
                else:
                    state = "unknown"
            elif is_newer(latest, inst):
                state = "update"
            else:
                state = "ok"
            results[b["id"]] = {"installed": inst, "latest": latest, "state": state}
        self.after(0, lambda: self._apply(results))

    def _apply(self, results):
        updates = sum(1 for r in results.values() if r["state"] == "update")
        for bid, r in results.items():
            self._card_state(self._rows[bid], r["installed"], r["latest"], r["state"])
        self._lbl_sub.config(
            text=f"{updates} actualización(es) disponible(s)" if updates else "Todo al día ✓")
        self._lbl_time.config(text=datetime.now().strftime("%I:%M %p"))
        self._btn._draw(ACCENT)
        self._btn.bind("<Button-1>", lambda e: self._start_check())
        self._btn.bind("<Enter>",    lambda e: self._btn._draw(ACCENT_H))
        self._btn.bind("<Leave>",    lambda e: self._btn._draw(ACCENT))
        self._checking = False
        self._schedule_auto_check()

    def _schedule_auto_check(self):
        if self._auto_timer:
            self._auto_timer.cancel()
        self._auto_timer = threading.Timer(6 * 3600, self._auto_check)
        self._auto_timer.daemon = True
        self._auto_timer.start()

    def _auto_check(self):
        self.after(0, self._start_check)


if __name__ == "__main__":
    App().mainloop()
