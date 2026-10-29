# Окно Элис, шаг 1: локальный сервер без Claude.
# Принимает перетащенные файлы в папку «Входящие», отдаёт их просмотрщику,
# пишет лог на каждое действие (свои и со страницы) в logs\elis_ГГГГ-ММ-ДД.log.
# Запуск: pythonw server.py  — поднимает сервер и открывает окно Chrome --app.
import json, mimetypes, os, re, shutil, socket, subprocess, sys, threading, time, traceback, urllib.parse
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8765
# Файлы и лог человека живут вне папки программы — обновление Элис их не тронет.
DATA = os.path.join(os.path.expanduser("~"), "Documents", "Elis")
CFG = {"inbox": os.path.join(DATA, "inbox"), "logs": os.path.join(DATA, "logs")}
try:
    with open(os.path.join(ROOT, "elis_config.json"), encoding="utf-8") as f:
        CFG.update(json.load(f))
except FileNotFoundError:
    pass
INBOX, LOGS = CFG["inbox"], CFG["logs"]
os.makedirs(INBOX, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)
_lock = threading.Lock()


def log(src, event, detail=""):
    """Одна строка лога: время | откуда | событие | подробности."""
    now = datetime.now()
    line = f"{now:%H:%M:%S}.{now.microsecond // 1000:03d} | {src:<6} | {event} | {detail}\n"
    with _lock, open(os.path.join(LOGS, f"elis_{now:%Y-%m-%d}.log"), "a", encoding="utf-8") as f:
        f.write(line)


def excepthook(t, v, tb):
    log("server", "ПАДЕНИЕ", "".join(traceback.format_exception(t, v, tb)).replace("\n", " ⏎ "))
sys.excepthook = excepthook


def safe_name(name):
    name = os.path.basename(name.replace("\\", "/")).strip() or "файл"
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)


def free_path(name):
    """Не перетирать: «акт.pdf» → «акт (2).pdf»."""
    base, ext = os.path.splitext(name)
    path, n = os.path.join(INBOX, name), 2
    while os.path.exists(path):
        path, n = os.path.join(INBOX, f"{base} ({n}){ext}"), n + 1
    return path


def human(n):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.1f} {unit}"
        n /= 1024


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # stderr у pythonw нет — пишем в свой лог
        pass

    def send(self, code, body=b"", ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def js(self, obj, code=200):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(url.path)
        try:
            if path == "/":
                with open(os.path.join(ROOT, "index.html"), "rb") as f:
                    self.send(200, f.read(), "text/html; charset=utf-8")
            elif path in ("/elis.ico", "/elis_face.png"):
                p = os.path.join(ROOT, path[1:])
                with open(p, "rb") as f:
                    self.send(200, f.read(), mimetypes.guess_type(p)[0] or "image/png")
            elif path == "/api/ping":
                self.js({"ok": True, "inbox": INBOX})
            elif path == "/api/files":
                items = []
                for e in os.scandir(INBOX):
                    if e.is_file():
                        st = e.stat()
                        items.append({"name": e.name, "size": st.st_size, "mtime": st.st_mtime})
                items.sort(key=lambda x: -x["mtime"])
                self.js({"inbox": INBOX, "files": items})
            elif path == "/api/log":
                q = urllib.parse.parse_qs(url.query)
                n = int(q.get("n", ["40"])[0])
                p = os.path.join(LOGS, f"elis_{datetime.now():%Y-%m-%d}.log")
                lines = open(p, encoding="utf-8").read().splitlines()[-n:] if os.path.exists(p) else []
                self.js({"lines": lines})
            elif path.startswith("/f/"):
                p = os.path.join(INBOX, safe_name(path[3:]))
                if not os.path.isfile(p):
                    log("server", "нет файла", path[3:])
                    return self.js({"error": "нет такого файла"}, 404)
                size = os.path.getsize(p)
                ctype = mimetypes.guess_type(p)[0] or "application/octet-stream"
                if ctype.startswith("text/") or p.lower().endswith((".csv", ".txt", ".dxf")):
                    ctype = "text/plain; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
                self.end_headers()
                with open(p, "rb") as f:
                    shutil.copyfileobj(f, self.wfile, 1 << 20)
                log("server", "показала файл", f"{os.path.basename(p)} · {human(size)} · {ctype}")
            else:
                self.js({"error": "нет такого адреса"}, 404)
        except (ConnectionResetError, BrokenPipeError):
            log("server", "окно оборвало связь", path)
        except Exception:
            log("server", "ОШИБКА", f"GET {path} ⏎ " + traceback.format_exc().replace("\n", " ⏎ "))
            self.js({"error": "ошибка на сервере, смотри лог"}, 500)

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            if url.path == "/api/upload":
                name = safe_name(q.get("name", ["файл"])[0])
                path = free_path(name)
                t0, got = time.time(), 0
                log("server", "принимаю файл", f"{name} · {human(length)}")
                with open(path + ".part", "wb") as f:
                    while got < length:
                        chunk = self.rfile.read(min(1 << 20, length - got))
                        if not chunk:
                            break
                        f.write(chunk)
                        got += len(chunk)
                if got != length:
                    os.remove(path + ".part")
                    log("server", "ФАЙЛ НЕ ДОШЁЛ", f"{name} · пришло {human(got)} из {human(length)}")
                    return self.js({"error": f"пришло {human(got)} из {human(length)}"}, 400)
                os.replace(path + ".part", path)
                dt = max(time.time() - t0, 0.001)
                log("server", "файл сохранён", f"{os.path.basename(path)} · {human(got)} · {dt:.1f} с")
                self.js({"ok": True, "name": os.path.basename(path), "size": got})
            elif url.path == "/api/log":
                data = json.loads(self.rfile.read(length) or b"{}")
                log("окно", str(data.get("event", "?"))[:80], str(data.get("detail", ""))[:2000])
                self.js({"ok": True})
            else:
                self.js({"error": "нет такого адреса"}, 404)
        except (ConnectionResetError, BrokenPipeError):
            log("server", "ФАЙЛ НЕ ДОШЁЛ", "окно оборвало связь посреди передачи")
        except Exception:
            log("server", "ОШИБКА", f"POST {url.path} ⏎ " + traceback.format_exc().replace("\n", " ⏎ "))
            self.js({"error": "ошибка на сервере, смотри лог"}, 500)


def already_running():
    try:
        with urlopen(f"http://127.0.0.1:{PORT}/api/ping", timeout=1) as r:
            return json.load(r).get("ok")
    except Exception:
        return False


def find_chrome():
    for p in (os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
              os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")):
        if os.path.exists(p):
            return p


def open_window():
    chrome = find_chrome()
    if not chrome:
        log("server", "ОШИБКА", "не нашла Chrome — окно не открыть")
        return
    subprocess.Popen([chrome, f"--app=http://127.0.0.1:{PORT}/", "--start-maximized"])
    log("server", "открыла окно", chrome)


def make_server(port=PORT):
    """Поднять сервер; port=0 — любой свободный; None — порт занят чужой программой."""
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    except OSError as e:
        log("server", "ОШИБКА", f"порт {port} занят чужой программой: {e}")
        return None
    log("server", "старт", f"{socket.gethostname()} · python {sys.version.split()[0]} · порт {srv.server_address[1]}"
        f" · входящие: {INBOX} · лог: {LOGS}")
    return srv


def main():
    if "--no-window" not in sys.argv and already_running():
        log("server", "уже работает", "просто открываю ещё окно")
        return open_window()
    srv = make_server()
    if not srv:
        return
    if "--no-window" not in sys.argv:
        threading.Timer(0.3, open_window).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
