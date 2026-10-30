# Окно Элис как отдельная программа: тот же сервер шага 1 + своё окно на WebView2 (движок Edge),
# поэтому окно выглядит одинаково, какой бы браузер ни стоял у человека.
# Запуск: Элис.exe (или pythonw main.py). --selftest: окно само «бросает» тестовый файл и закрывается.
import sys, threading
import server
from server import log

try:
    import webview
except Exception as e:  # без pywebview окно не открыть — пишем в лог, а не молчим
    log("prog", "ПАДЕНИЕ", f"нет pywebview: {e!r}")
    raise

SELFTEST = "--selftest" in sys.argv

TEST_DROP = """
const dt = new DataTransfer();
dt.items.add(new File(['Узел;Длина, м\\nВДуз65;12,40\\n'], 'самопроверка.csv', {type: 'text/csv'}));
document.dispatchEvent(new DragEvent('dragenter', {dataTransfer: dt, bubbles: true}));
document.dispatchEvent(new DragEvent('drop', {dataTransfer: dt, bubbles: true}));
"""


def selftest(win):
    import time
    time.sleep(2)
    win.evaluate_js(TEST_DROP)
    time.sleep(3)
    log("prog", "самопроверка", "бросила тестовый файл, закрываю окно")
    win.destroy()


def raise_existing():
    """Элис уже открыта — не плодим второе окно, а поднимаем открытое (Дима 30.10)."""
    from urllib.request import Request, urlopen
    try:
        urlopen(Request(f"http://127.0.0.1:{server.PORT}/api/focus", data=b"{}", method="POST"), timeout=2)
        return True
    except Exception:
        return False


def watch_focus(win):
    while True:
        server.FOCUS.wait()
        server.FOCUS.clear()
        try:
            win.restore(); win.show(); win.on_top = True; win.on_top = False
            log("prog", "подняла окно", "второй запуск — показываю уже открытое")
        except Exception as e:
            log("prog", "НЕ ПОЛУЧИЛОСЬ поднять окно", repr(e))


def main():
    if not SELFTEST and server.already_running() and raise_existing():
        log("prog", "уже работает", "окно уже открыто — подняла его, второе не открываю")
        return
    # Самопроверка при открытом окне идёт на своём сервере, чтобы не мешать человеку.
    srv = server.make_server(0) if server.already_running() else server.make_server()
    if not srv:
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    win = webview.create_window("Элис", url, width=1600, height=950, maximized=not SELFTEST,
                                min_size=(900, 600), text_select=True)
    win.events.loaded += lambda: log("prog", "окно загрузилось", url)
    win.events.closed += lambda: log("prog", "окно закрыто", "")
    threading.Thread(target=watch_focus, args=(win,), daemon=True).start()
    log("prog", "открываю окно", f"pywebview {getattr(webview, '__version__', '?')}")
    webview.start(selftest if SELFTEST else None, win, gui="edgechromium")


if __name__ == "__main__":
    main()
