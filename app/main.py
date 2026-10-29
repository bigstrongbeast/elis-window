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


def main():
    # У каждого окна свой сервер: закроют первое окно — второе не останется без сервера.
    if server.already_running():
        log("prog", "уже работает", "одно окно уже открыто — у этого будет свой сервер")
        srv = server.make_server(0)
    else:
        srv = server.make_server()
    if not srv:
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    win = webview.create_window("Элис", url, width=1600, height=950, maximized=not SELFTEST,
                                min_size=(900, 600), text_select=True)
    win.events.loaded += lambda: log("prog", "окно загрузилось", url)
    win.events.closed += lambda: log("prog", "окно закрыто", "")
    log("prog", "открываю окно", f"pywebview {getattr(webview, '__version__', '?')}")
    webview.start(selftest if SELFTEST else None, win, gui="edgechromium")


if __name__ == "__main__":
    main()
