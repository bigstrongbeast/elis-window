# -*- coding: utf-8 -*-
"""Сборщик лонгрида: из одного текстового файла с маркерами делает HTML-страницу
(Artifact) и папку приложений attach\\, которые страница открывает кнопкой «посмотреть».

Зачем: страницы всех сессий собираются одним шаблоном (longread_template.html рядом со
скриптом). Правка вида в шаблоне доходит до всех страниц, ручной вёрстки нет.

Запуск:
    python -X utf8 -I C:\\Users\\admin\\Documents\\Claude\\_tools\\longread_build.py <вход.md> <выход.html>

Что получится:
    <выход.html>           страница (без <html>/<head>/<body>: обёртку добавляет Artifact)
    <папка выхода>\\attach\\  приложения: текст -> <имя>.html с <pre>, картинки как есть,
                           папка -> листинг с содержимым небольших текстовых файлов
    <выход>_files.json     карта для публикации: {"attach/<имя>.html": "<абс. путь>", ...}
                           (параметр files инструмента Artifact)
    Публиковать: Artifact(file_path=<выход.html>, files=<карта>, capabilities={"db": {}}).
    В конце сборщик сам проверяет: теги сбалансированы, id не повторяются, весь текст
    входа есть в выходе. Код возврата 0 = всё в порядке, 1 = проверка не прошла, 2 = ошибка входа.

Формат входа (UTF-8; маркеры с начала строки; текст после маркеров вставляется как есть):
    @title: <2-4 слова>                @subtitle: <строка>
    @db_collection: <имя>              @layout: tabs        (необязательно: разделы-вкладки)
    @intro                             абзацы до следующего маркера; абзацы через пустую строку
    @section <id> | <Заголовок> | <подпись мелко, можно пусто>
    @row <id> | <СТАТУС> | <строчка 1: заголовок> | <строчка 2: короткое пояснение>
      <отступ 2 пробела: раскрываемое пояснение; абзацы через пустую строку>
      @files: <абс. путь>; <абс. путь>          (кнопка «посмотреть» на каждый)
      @link: <url> | <текст>
    @tri <id> | <что> | <где> | <дата> | <что внутри> | <предложение>   (такие же вложенные строки)
    @group <id> | <Заголовок группы> | <подпись мелко, можно пусто>   подзаголовок внутри раздела: строки под ним
                                            идут отдельным списком (для нумерованных групп: 1. ..., 2. ...)
    @question <id> | <текст вопроса>
    @table <id> | <Заголовок> | <колонка 1> | <колонка 2> | ...
      | <ячейка> | <ячейка> | ... |
    @links <id> | <Заголовок>
      - <текст> | <абс. путь или url>
    @tasks <id> | <Заголовок>
      - <СРОЧНО|СЕГОДНЯ|ПОТОМ|ОТЛОЖЕНО|СДЕЛАНО|ЖДЁТ: кого> | <текст> | <@t:ISO, можно пусто>
    @confirm <id> | <текст кнопки> | <подсказка под кнопкой>
    @note <текст мелким>
    @aside <id> | <Заголовок>               боковая колонка (одна на страницу)
      - <номер> | <тема> | <текст> | <путь или url к файлу, можно пусто>
    @raw <абс. путь к .html или .svg>       вставить файл как есть в текущий раздел (блок-схема);
                                            файла нет - предупреждение сборщика и пропуск.
                                            Внутри вставляемого файла строка <!--@@SRC <абс. путь> @<с>-<по>-->
                                            заменяется скрытым <textarea class="hf-src" data-f="<имя файла>" data-from="<с>">
                                            с этими строками файла (без @<с>-<по> - весь файл): код для кликабельных схем.
    @link: #<id элемента страницы> | <текст>   внутри @row: кнопка-якорь (перелёт к элементу, раскрывает свёрнутое)
Внутри текста: **жирный**, `код`, [текст](url или абс. путь к файлу), [#12] (ссылка на строку
12 боковой колонки; если @aside нет - на проблему, куда попал номер 12 по @note «Старые номера →
проблемы: 12→pb3, ...» раздела problems, а без карты - на строку p-12), @t:2026-10-30T22:35:00+03:00 (относительное время: «3 ч назад»,
«через 16 ч», «вчера 22:35»; браузер пересчитывает раз в минуту, при наведении полная дата;
без пояса времени считается московское).

Поведение: @row с рычажком из трёх квадратных ячеек (нет / пусто / да), строки СДЕЛАНО уходят в свёрнутую группу
«сделано (N)» внизу раздела; @tri с тремя кнопками; неперекинутые строки стоят выше; в шапке
раздела счётчик «не перекинуто: N» (считает строки и уборку, кроме свёрнутых «сделано»).
У каждой строки @row и @tri есть квадратная кнопка «Решено» (✓): в документ пишется done: true и
done_at, строка переезжает в «Архив» (последняя вкладка, создаётся сама, если есть хоть одна такая
строка; в режиме без вкладок это раздел в конце страницы). В архиве кнопка «вернуть» (done: false)
возвращает строку в её раздел. Ряд вкладок липкий и лежит выше сетки колонок.
База: документы <db_collection>/<id>; без базы страница работает, но не сохраняет.
В шапку сборщик сам ставит «собрано @t:<время ПК>».
@tasks в два столбика (на телефоне один под другим): слева «Сегодня» (СРОЧНО и СЕГОДНЯ, строки
пронумерованы 1, 2, 3... по порядку источника) и ниже «Близкие» (ПОТОМ и ЖДЁТ, без номеров); справа
«Полный список» (все строки подряд, включая ОТЛОЖЕНО; СДЕЛАНО - свёрнутой группой «сделано (N)») и в
конце ссылка из первой строки @links, где в тексте есть «489» (свод хотелок), если такая строка есть.
"""
import datetime
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, 'longread_template.html')

ID_RE = re.compile(r'^[A-Za-z0-9_\-.~:@+]{1,100}$')
NUM_RE = re.compile(r'^[A-Za-z0-9_.~-]{1,40}$')
MSK = datetime.timezone(datetime.timedelta(hours=3))

TEXT_EXTS = {'.md', '.markdown', '.txt', '.json', '.jsonl', '.py', '.ps1', '.psm1', '.csv', '.tsv',
             '.log', '.html', '.htm', '.css', '.js', '.mjs', '.ts', '.xml', '.yml', '.yaml', '.bat',
             '.cmd', '.ini', '.toml', '.cfg', '.sh', '.sql', '.srt', '.vtt', '.tex', '.rst'}
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico'}
COPY_EXTS = {'.pdf'}
MAX_TEXT = 1500 * 1024          # дальше текст приложения обрезается
DIR_INLINE_MAX = 30 * 1024      # текстовые файлы папки до 30 КБ показываются внутри листинга
DIR_INLINE_BUDGET = 600 * 1024  # общий предел встроенного текста на одну папку
DIR_LIST_CAP = 500
DIR_DEPTH = 3
SKIP_DIRS = {'node_modules', '__pycache__', '.git', '.venv', 'venv'}

WARN = []
NUMS = set()          # номера строк боковой колонки (для [#N])
REFMAP = {}           # без @aside: старый номер -> id проблемы (из @note «Старые номера → проблемы: 1→pb1, ...» раздела problems)
HAS_ASIDE = [False]   # есть ли на странице боковая колонка
ATT = None            # реестр приложений
BASE_DIR = '.'        # папка входного файла (для относительных путей)
LIST_N = [0]
IDS = {'archive': 'вкладка «Архив» (id занят сборщиком)'}
HOTELKI = {}          # ссылка на свод хотелок: первая строка @links с «489» в тексте (идёт в конец правой колонки задач)


class BuildError(Exception):
    pass


def fail(msg, lineno=None):
    raise BuildError(('строка %d: ' % lineno if lineno else '') + msg)


def warn(msg):
    if msg not in WARN:     # одна и та же строка может выводиться в двух колонках задач
        WARN.append(msg)


def esc(s):
    return html.escape(s, quote=True)


# ---------------- имена, размеры, даты ----------------
_TR = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
       'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
       'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh',
       'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
       'і': 'i', 'ї': 'yi', 'є': 'ye', 'ґ': 'g'}


def safe_name(stem):
    s = ''.join(_TR.get(ch, ch) for ch in stem.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:50].strip('-')
    return s or 'file'


def fmt_size(n):
    if n < 1024:
        return '%d Б' % n
    if n < 1024 * 1024:
        return ('%.1f КБ' % (n / 1024)).replace('.', ',')
    return ('%.1f МБ' % (n / 1024 / 1024)).replace('.', ',')


def fmt_date(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%d.%m.%Y %H:%M')


# ---------------- время @t:ISO ----------------
T_PATTERN = (r'@t:(?P<t>\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?'
             r'(?:Z|[+-]\d{2}:?\d{2})?)')


def parse_iso(raw):
    s = raw.strip().replace(' ', 'T')
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        dt = datetime.datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return dt.replace(microsecond=0)


def time_text(raw):
    dt = parse_iso(raw)
    if dt is None:
        return '@t:' + raw
    return dt.astimezone(MSK).strftime('%d.%m %H:%M')


def render_time(raw):
    dt = parse_iso(raw)
    if dt is None:
        warn('не разобрано время @t:' + raw)
        return esc('@t:' + raw)
    m = dt.astimezone(MSK)
    return '<time class="rt" datetime="%s" title="%s">%s</time>' % (
        esc(dt.isoformat()), esc(m.strftime('%d.%m.%Y %H:%M') + ' МСК'), esc(m.strftime('%d.%m %H:%M')))


# ---------------- разметка внутри текста ----------------
TOKEN_RE = re.compile(
    r'`(?P<code>[^`\n]+)`'
    r'|\[(?P<ltext>[^\]\n]+)\]\((?P<lurl>[^)\n]+)\)'
    r'|\*\*(?P<bold>.+?)\*\*'
    r'|\[#(?P<ref>[A-Za-z0-9_.~-]+)\]'
    r'|' + T_PATTERN +
    r'|(?P<bare>https?://[^\s<>"`]+)')


def ref_target(n):
    """[#N] -> id элемента страницы или None. С боковой колонкой: p-N. Без неё: проблема из карты
    «Старые номера → проблемы» (REFMAP); нет карты - строка p-N, если такая есть."""
    if n in NUMS:
        return 'p-' + n
    if HAS_ASIDE[0]:
        return None
    if REFMAP:
        return REFMAP.get(n)
    return 'p-' + n if ('p-' + n) in IDS else None


def link_html(href, inner):
    if href.startswith('#'):
        return '<a href="%s">%s</a>' % (esc(href), inner)
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(href), inner)


def make_href(url):
    """-> href или None (если ссылку сделать нельзя)."""
    u = url.strip()
    if re.match(r'^https?://', u, re.I) or re.match(r'^(mailto|tel):', u, re.I) or u.startswith('#'):
        return u
    if (re.match(r'^[A-Za-z]:[\\/]', u) or u.startswith('\\\\') or u.startswith('/')
            or os.path.exists(os.path.join(BASE_DIR, u))):
        info = ATT.add(u)
        return info['rel'] if info['ok'] else None
    warn('ссылка без понятного адреса: ' + u)
    return None


def inline(s, nolinks=False):
    out = []
    pos = 0
    for m in TOKEN_RE.finditer(s):
        out.append(esc(s[pos:m.start()]))
        pos = m.end()
        g = m.groupdict()
        if g['code'] is not None:
            out.append('<code>%s</code>' % esc(g['code']))
        elif g['ltext'] is not None:
            inner = inline(g['ltext'], True)
            href = None if nolinks else make_href(g['lurl'])
            out.append(link_html(href, inner) if href else inner)
        elif g['bold'] is not None:
            out.append('<b>%s</b>' % inline(g['bold'], nolinks))
        elif g['ref'] is not None:
            n = g['ref']
            target = ref_target(n)
            if target:
                if nolinks:
                    out.append(esc('#' + n))
                else:
                    out.append('<a class="pref" href="#%s" data-goto="%s">#%s</a>' % (esc(target), esc(target), esc(n)))
            else:
                if HAS_ASIDE[0]:
                    warn('[#%s]: в боковой колонке нет такого номера' % n)
                elif REFMAP:
                    warn('[#%s]: номера нет в @note «Старые номера → проблемы»' % n)
                else:
                    warn('[#%s]: нет боковой колонки, карты «Старые номера → проблемы» и строки p-%s' % (n, n))
                out.append(esc(m.group(0)))
        elif g['t'] is not None:
            out.append(render_time(g['t']))
        else:
            url = g['bare']
            tail = ''
            while url and (url[-1] in '.,;:!?' or (url[-1] == ')' and url.count(')') > url.count('('))):
                tail = url[-1] + tail
                url = url[:-1]
            out.append((esc(url) if nolinks else link_html(url, esc(url))) + esc(tail))
    out.append(esc(s[pos:]))
    return ''.join(out)


def plain(s):
    """Текст так, как он виден на странице (для aria-label и проверки)."""
    def rep(m):
        g = m.groupdict()
        if g['code'] is not None:
            return g['code']
        if g['ltext'] is not None:
            return plain(g['ltext'])
        if g['bold'] is not None:
            return plain(g['bold'])
        if g['ref'] is not None:
            return ('#' + g['ref']) if ref_target(g['ref']) else m.group(0)
        if g['t'] is not None:
            return time_text(g['t'])
        return m.group(0)
    return TOKEN_RE.sub(rep, s)


# ---------------- шаблон ----------------
def load_template(path):
    text = open(path, encoding='utf-8').read()
    chunks = re.split(r'^<!--@@PART (\w+)-->[ \t]*\r?\n', text, flags=re.M)
    parts = {}
    for i in range(1, len(chunks), 2):
        parts[chunks[i]] = chunks[i + 1]
    for need in ('tokens', 'common', 'page', 'attach'):
        if need not in parts:
            fail('в шаблоне нет части «%s»' % need)
    return parts


def fill(tpl, vals):
    def rep(m):
        k = m.group(1)
        if k not in vals:
            raise BuildError('в шаблоне неизвестный плейсхолдер @@%s@@' % k)
        return vals[k]
    return re.sub(r'@@([A-Z_]+)@@', rep, tpl)


# ---------------- приложения ----------------
def decode_bytes(raw, truncated):
    for cut in ((0, 1, 2, 3) if truncated else (0,)):
        try:
            return raw[:len(raw) - cut].decode('utf-8-sig')
        except UnicodeDecodeError:
            continue
    return raw.decode('cp1251', errors='replace')


def looks_text(raw):
    return b'\x00' not in raw[:8192]


class Attach:
    def __init__(self, out_dir, parts):
        self.dir = os.path.join(out_dir, 'attach')
        self.parts = parts
        self.items = {}
        self.used = set()
        self.order = []

    def _unique(self, stem, ext):
        base = safe_name(stem)
        name = base + ext
        n = 2
        while name.lower() in self.used:
            name = '%s-%d%s' % (base, n, ext)
            n += 1
        self.used.add(name.lower())
        return name

    def _page(self, title, body):
        vals = {'TITLE': esc(title), 'BODY': body, 'TOKENS': self.parts['tokens'].strip('\n'),
                'COMMON': self.parts['common'].strip('\n')}
        return fill(self.parts['attach'], vals)

    def _write(self, info, name, content, binary=False):
        os.makedirs(self.dir, exist_ok=True)
        out = os.path.join(self.dir, name)
        if binary:
            with open(out, 'wb') as f:
                f.write(content)
        else:
            with open(out, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
        info.update(ok=True, rel='attach/' + name, out=out)
        self.order.append(info)

    def add(self, raw_path):
        p = raw_path.strip().strip('"').strip("'")
        if not os.path.isabs(p):
            p = os.path.join(BASE_DIR, p)
        p = os.path.abspath(p)
        key = os.path.normcase(p)
        if key in self.items:
            return self.items[key]
        info = {'src': p, 'name': os.path.basename(p.rstrip('\\/')) or p, 'ok': False,
                'rel': None, 'out': None, 'kind': None, 'note': ''}
        self.items[key] = info
        if not os.path.exists(p):
            info['note'] = 'файл не найден'
            warn('приложение не найдено: ' + p)
            return info
        try:
            if os.path.isdir(p):
                self._dir(info)
            else:
                self._file(info)
        except OSError as e:
            info['note'] = 'не прочитался'
            warn('приложение не прочиталось: %s (%s)' % (p, e))
        return info

    def _file(self, info):
        p = info['src']
        stem, ext = os.path.splitext(os.path.basename(p))
        ext = ext.lower()
        if ext in IMG_EXTS or ext in COPY_EXTS:
            info['kind'] = 'image' if ext in IMG_EXTS else 'pdf'
            name = self._unique(stem, ext)
            with open(p, 'rb') as f:
                data = f.read()
            self._write(info, name, data, binary=True)
            return
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            raw = f.read(MAX_TEXT + 1)
        if ext in TEXT_EXTS or (looks_text(raw) and ext not in ('.exe', '.dll', '.zip', '.docx', '.xlsx', '.pptx', '.mp4', '.mp3')):
            info['kind'] = 'text'
            truncated = len(raw) > MAX_TEXT
            text = decode_bytes(raw[:MAX_TEXT], truncated)
            body = ['<a class="back" href="../">← назад к странице</a>',
                    '<h1>%s</h1>' % esc(info['name']),
                    '<p class="src"><code>%s</code> · %s · %s</p>' % (esc(p), fmt_size(size), fmt_date(os.path.getmtime(p)))]
            if truncated:
                body.append('<p class="src">показаны первые %s из %s</p>' % (fmt_size(MAX_TEXT), fmt_size(size)))
            body.append('<pre>%s%s</pre>' % ('\n' if text.startswith('\n') else '', esc(text)))
            name = self._unique(stem, '.html')
            self._write(info, name, self._page(info['name'], '\n'.join(body)))
            return
        info['note'] = 'формат не показывается'
        warn('формат не показывается в браузере: ' + p)

    def _dir(self, info):
        root = info['src']
        entries = []
        capped = [False]

        def rec(d, depth, rel):
            try:
                names = sorted(os.listdir(d), key=lambda n: (not os.path.isdir(os.path.join(d, n)), n.lower()))
            except OSError:
                return
            for n in names:
                if len(entries) >= DIR_LIST_CAP:
                    capped[0] = True
                    return
                full = os.path.join(d, n)
                isdir = os.path.isdir(full)
                if isdir and n in SKIP_DIRS:
                    continue
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                entries.append({'rel': rel + n + ('/' if isdir else ''), 'dir': isdir,
                                'size': 0 if isdir else st.st_size, 'mtime': st.st_mtime,
                                'full': full, 'depth': depth})
                if isdir and depth < DIR_DEPTH:
                    rec(full, depth + 1, rel + n + '/')
        rec(root, 1, '')
        info['kind'] = 'dir'
        nfiles = sum(1 for e in entries if not e['dir'])
        ndirs = len(entries) - nfiles
        body = ['<a class="back" href="../">← назад к странице</a>',
                '<h1>%s</h1>' % esc(info['name']),
                '<p class="src"><code>%s</code> · файлов: %d, папок: %d%s</p>' % (
                    esc(root), nfiles, ndirs, ' (показаны первые %d)' % DIR_LIST_CAP if capped[0] else '')]
        if entries:
            body.append('<div class="tbl"><table class="dt dirs"><thead><tr><th scope="col">Имя</th>'
                        '<th scope="col">Размер</th><th scope="col">Дата</th></tr></thead><tbody>')
            for e in entries:
                body.append('<tr><td class="nm" data-label="Имя"><code>%s</code></td><td class="num" data-label="Размер">%s</td>'
                            '<td class="num" data-label="Дата">%s</td></tr>' % (
                                esc(e['rel']), '' if e['dir'] else fmt_size(e['size']), fmt_date(e['mtime'])))
            body.append('</tbody></table></div>')
        else:
            body.append('<p class="src">папка пуста</p>')
        inl = []
        budget = DIR_INLINE_BUDGET
        for e in entries:
            if e['dir'] or e['size'] > DIR_INLINE_MAX or e['size'] > budget:
                continue
            ext = os.path.splitext(e['full'])[1].lower()
            if ext in IMG_EXTS or ext in COPY_EXTS:
                continue
            try:
                with open(e['full'], 'rb') as f:
                    raw = f.read(DIR_INLINE_MAX + 1)
            except OSError:
                continue
            if not (ext in TEXT_EXTS or (ext == '' and looks_text(raw))):
                continue
            if b'\x00' in raw[:8192]:
                continue
            budget -= e['size']
            inl.append((e, decode_bytes(raw, False)))
        if inl:
            body.append('<h2>Текстовые файлы до %d КБ</h2>' % (DIR_INLINE_MAX // 1024))
            for e, text in inl:
                body.append('<details><summary><code>%s</code><span class="sz">%s</span></summary><pre>%s%s</pre></details>' % (
                    esc(e['rel']), fmt_size(e['size']), '\n' if text.startswith('\n') else '', esc(text)))
        name = self._unique(os.path.basename(root.rstrip('\\/')) or 'folder', '.html')
        self._write(info, name, self._page(info['name'], '\n'.join(body)))


# ---------------- разбор входа ----------------
def register_id(kind, i, no):
    if not ID_RE.match(i) or i in ('.', '..'):
        fail('id «%s» не годится (латиница, цифры и _ - . ~ : @ +, до 100 знаков)' % i, no)
    if i in IDS:
        fail('id «%s» уже занят (%s)' % (i, IDS[i]), no)
    IDS[i] = kind


def split_n(rest, n, no, need, what):
    parts = [x.strip() for x in rest.split('|', n)]
    if len(parts) < need:
        fail('%s: ожидалось полей не меньше %d, найдено %d: %s' % (what, need, len(parts), rest[:80]), no)
    while len(parts) < n + 1:
        parts.append('')
    return parts


def paragraphs(lines):
    paras, cur = [], []
    for l in lines:
        if l == '':
            if cur:
                paras.append(cur)
                cur = []
        else:
            cur.append(l)
    if cur:
        paras.append(cur)
    return paras


def parse(path):
    text = open(path, encoding='utf-8-sig').read()
    doc = {'meta': {}, 'intro': [], 'sections': [], 'aside': None, 'expect': []}
    ex = doc['expect'].append
    sec = None       # текущий раздел
    cur = None       # блок, принимающий вложенные строки
    mode = None
    for no, raw in enumerate(text.split('\n'), 1):
        line = raw.rstrip('\r')
        s = line.strip()
        indented = line[:1] in (' ', '\t')
        if not s:
            if cur is not None and cur['kind'] in ('row', 'tri'):
                cur['body'].append('')
            elif mode == 'intro':
                doc['intro'].append('')
            continue
        if indented and cur is not None:
            nested(cur, s, no, ex)
            continue
        if indented and mode == 'intro':
            doc['intro'].append(s)
            continue
        if indented:
            fail('строка с отступом, но выше нет @row / @tri / @table / @links / @tasks / @aside', no)
        m = re.match(r'^@([A-Za-z_]+):?[ \t]*(.*)$', line)
        if not m:
            if mode == 'intro':
                doc['intro'].append(s)
                continue
            fail('строка вне маркера: ' + s[:60], no)
        key, rest = m.group(1).lower(), m.group(2).strip()
        if key in ('title', 'subtitle', 'db_collection', 'layout'):
            doc['meta'][key] = rest
            cur, mode = None, None
            continue
        if key == 'intro':
            if sec is not None:
                fail('@intro должен идти до первого @section', no)
            cur, mode = None, 'intro'
            if rest:
                doc['intro'].append(rest)
            continue
        if key == 'section':
            p = split_n(rest, 2, no, 2, '@section')
            register_id('section', p[0], no)
            sec = {'id': p[0], 'title': p[1], 'sub': p[2], 'items': []}
            doc['sections'].append(sec)
            ex(p[1])
            if p[2]:
                ex(p[2])
            cur, mode = None, None
            continue
        if key == 'aside':
            if doc['aside'] is not None:
                fail('@aside может быть только один', no)
            p = split_n(rest, 1, no, 1, '@aside')
            register_id('aside', p[0], no)
            cur = {'kind': 'aside', 'id': p[0], 'title': p[1], 'items': []}
            doc['aside'] = cur
            if p[1]:
                ex(p[1])
            mode = None
            continue
        if sec is None:
            fail('маркер @%s вне раздела (выше нет @section)' % key, no)
        mode = None
        cur = None
        items = sec['items']
        if key == 'row':
            p = split_n(rest, 3, no, 3, '@row')
            register_id('row', p[0], no)
            cur = {'kind': 'row', 'id': p[0], 'status': p[1], 'title': p[2], 'sub': p[3], 'body': [], 'files': [], 'links': []}
            items.append(('row', cur))
            ex(p[1]); ex(p[2])
            if p[3]:
                ex(p[3])
        elif key == 'tri':
            p = split_n(rest, 5, no, 6, '@tri')
            register_id('tri', p[0], no)
            cur = {'kind': 'tri', 'id': p[0], 'what': p[1], 'where': p[2], 'date': p[3], 'inside': p[4], 'prop': p[5],
                   'body': [], 'files': [], 'links': []}
            items.append(('tri', cur))
            for x in p[1:]:
                if x:
                    ex(x)
        elif key == 'group':
            p = split_n(rest, 2, no, 2, '@group')
            register_id('group', p[0], no)
            items.append(('group', {'id': p[0], 'title': p[1], 'sub': p[2]}))
            ex(p[1])
            if p[2]:
                ex(p[2])
        elif key == 'question':
            p = split_n(rest, 1, no, 2, '@question')
            register_id('question', p[0], no)
            items.append(('question', {'id': p[0], 'text': p[1]}))
            ex(p[1])
        elif key == 'table':
            p = [x.strip() for x in rest.split('|')]
            while len(p) > 3 and p[-1] == '':
                p.pop()
            if len(p) < 3:
                fail('@table: нужны id, заголовок и хотя бы одна колонка', no)
            register_id('table', p[0], no)
            cur = {'kind': 'table', 'id': p[0], 'title': p[1], 'cols': p[2:], 'rows': []}
            items.append(('table', cur))
            for x in p[1:]:
                if x:
                    ex(x)
        elif key == 'links':
            p = split_n(rest, 1, no, 1, '@links')
            register_id('links', p[0], no)
            cur = {'kind': 'links', 'id': p[0], 'title': p[1], 'items': []}
            items.append(('links', cur))
            if p[1]:
                ex(p[1])
        elif key == 'tasks':
            p = split_n(rest, 1, no, 1, '@tasks')
            register_id('tasks', p[0], no)
            cur = {'kind': 'tasks', 'id': p[0], 'title': p[1], 'items': []}
            items.append(('tasks', cur))
            if p[1]:
                ex(p[1])
        elif key == 'confirm':
            p = split_n(rest, 2, no, 2, '@confirm')
            register_id('confirm', p[0], no)
            items.append(('confirm', {'id': p[0], 'label': p[1], 'hint': p[2]}))
            ex(p[1])
            if p[2]:
                ex(p[2])
        elif key == 'raw':
            if not rest:
                fail('@raw без пути к файлу', no)
            items.append(('raw', {'path': rest}))
        elif key == 'note':
            if not rest:
                fail('@note без текста', no)
            items.append(('note', rest))
            ex(rest)
        else:
            fail('неизвестный маркер @' + key, no)
    # проверки
    meta = doc['meta']
    if not meta.get('title'):
        fail('нет строки @title:')
    if meta.get('layout', 'strip') not in ('tabs', 'strip'):
        fail('@layout: допустимо tabs')
    ex(meta['title'])
    if meta.get('subtitle'):
        ex(meta['subtitle'])
    doc['intro'] = trim_blank(doc['intro'])
    for l in doc['intro']:
        if l:
            ex(l)
    if doc['aside']:
        for it in doc['aside']['items']:
            if it['num'] in NUMS:
                fail('в @aside номер «%s» повторяется' % it['num'])
            NUMS.add(it['num'])
    HAS_ASIDE[0] = bool(doc['aside'])
    if not doc['aside']:
        # боковой колонки нет: [#N] ведёт в проблему по карте из @note раздела problems
        for s_ in doc['sections']:
            if s_['id'] != 'problems':
                continue
            for kind_, val_ in s_['items']:
                if kind_ == 'note' and 'Старые номера' in val_:
                    for a_, b_ in re.findall(r'(\d+)\s*→\s*([A-Za-z0-9_.~-]+)', val_):
                        if b_ not in IDS:
                            fail('в карте «Старые номера → проблемы»: %s→%s, а проблемы с id «%s» нет' % (a_, b_, b_))
                        REFMAP[a_] = b_
    return doc


def trim_blank(lines):
    while lines and lines[0] == '':
        lines = lines[1:]
    while lines and lines[-1] == '':
        lines = lines[:-1]
    return lines


def nested(cur, s, no, ex):
    k = cur['kind']
    if k in ('row', 'tri'):
        m = re.match(r'^@files?:?[ \t]*(.*)$', s)
        if m:
            for x in m.group(1).split(';'):
                if x.strip():
                    cur['files'].append(x.strip())
            return
        m = re.match(r'^@link:?[ \t]*(.*)$', s)
        if m:
            p = [x.strip() for x in m.group(1).split('|', 1)]
            if not p[0]:
                fail('@link: без адреса', no)
            cur['links'].append((p[0], p[1] if len(p) > 1 else ''))
            if len(p) > 1 and p[1]:
                ex(p[1])
            return
        cur['body'].append(s)
        ex(s)
    elif k == 'table':
        if not s.startswith('|'):
            fail('строка таблицы должна начинаться с «|»', no)
        t = s[1:]
        if t.endswith('|'):
            t = t[:-1]
        cells = [c.strip() for c in t.split('|')]
        if all(re.match(r'^:?-{2,}:?$', c) for c in cells if c) and any(cells):
            return
        cur['rows'].append(cells)
        for c in cells:
            if c:
                ex(c)
    elif k == 'links':
        if not s.startswith('-'):
            fail('строка списка ссылок: «- текст | путь или url»', no)
        t = s[1:].strip()
        if '|' not in t:
            fail('строка списка ссылок: «- текст | путь или url»', no)
        text, target = [x.strip() for x in t.rsplit('|', 1)]
        cur['items'].append((text, target))
        ex(text)
        if '489' in text and not HOTELKI:
            HOTELKI.update(text=text, target=target)
    elif k == 'tasks':
        if not s.startswith('-'):
            fail('строка задач: «- МЕТКА | текст | @t:время»', no)
        p = split_n(s[1:].strip(), 2, no, 2, 'строка задач')
        cur['items'].append((p[0], p[1], p[2]))
        ex(p[0]); ex(p[1])
        if p[2]:
            ex(p[2])
    elif k == 'aside':
        if not s.startswith('-'):
            fail('строка боковой колонки: «- номер | тема | текст | путь или url»', no)
        p = split_n(s[1:].strip(), 3, no, 3, 'строка боковой колонки')
        if not NUM_RE.match(p[0]):
            fail('номер «%s» не годится для якоря (латиница, цифры . _ ~ -)' % p[0], no)
        cur['items'].append({'num': p[0], 'topic': p[1], 'text': p[2], 'path': p[3]})
        ex(p[0]); ex(p[1]); ex(p[2])


# ---------------- сборка HTML ----------------
def badge_class(status):
    first = status.split()[0].upper() if status.split() else ''
    return {'СДЕЛАНО': 'done', 'ПРЕДЛАГАЮ': 'prop', 'ОТВЕТ': 'ans', 'ВОПРОС': 'ask'}.get(first, 'after')


def is_done(status):
    return status.strip().upper().startswith('СДЕЛАНО')


def view_btn(href, label='посмотреть'):
    return '<a class="view" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(href), label)


def file_links(files, links):
    parts = []
    for p in files:
        info = ATT.add(p)
        if info['ok']:
            parts.append('<span class="fl">%s<code>%s</code></span>' % (view_btn(info['rel']), esc(info['name'])))
        else:
            parts.append('<span class="fl missing"><code>%s</code><span>%s</span></span>' % (esc(info['name']), esc(info['note'])))
    for url, text in links:
        href = make_href(url)
        label = inline(text or url, True)
        if href and href.startswith('#'):
            parts.append('<span class="fl"><a class="view" href="%s" data-goto="%s">%s</a></span>' % (esc(href), esc(href[1:]), label))
        elif href:
            parts.append('<span class="fl"><a class="view" href="%s" target="_blank" rel="noopener">%s</a></span>' % (esc(href), label))
        else:
            parts.append('<span class="fl missing"><span>%s</span><span>ссылка не открывается</span></span>' % label)
    return parts


def para_html(lines):
    return '<p>%s</p>' % '<br>'.join(inline(l) for l in lines)


def details_html(body):
    paras = paragraphs(body)
    if not paras:
        return ''
    return ('<details class="more"><summary>подробнее</summary><div class="more-body">%s</div></details>'
            % ''.join(para_html(p) for p in paras))


DONE_BTN = ('<button type="button" class="donebtn" aria-label="Решено: убрать в архив" '
            'title="Решено: убрать в архив">&#10003;</button>')


def from_html(src):
    return '<div class="from">из раздела: %s</div>' % inline(src, True) if src else ''


def render_row(r, idx, src=''):
    rid = r['id']
    label = esc(plain(r['title']))
    h = ['<article class="row" id="%s" data-doc="%s" data-kind="row" data-idx="%d" data-state="">' % (esc(rid), esc(rid), idx),
         '<div class="r-main">%s<span class="badge %s">%s</span>' % (from_html(src), badge_class(r['status']), esc(r['status'])),
         '<div class="r-title">%s</div>' % inline(r['title'])]
    if r['sub']:
        h.append('<div class="r-sub">%s</div>' % inline(r['sub']))
    h.append('</div>')
    h.append('<div class="lever" role="radiogroup" aria-label="Ответ: %s" data-v="">'
             '<button type="button" role="radio" aria-checked="false" data-v="no" title="нет">нет</button>'
             '<button type="button" role="radio" aria-checked="true" data-v="" title="не перекинуто" aria-label="не перекинуто"></button>'
             '<button type="button" role="radio" aria-checked="false" data-v="yes" title="да">да</button></div>' % label)
    tools = []
    d = details_html(r['body'])
    if d:
        tools.append(d)
    tools.extend(file_links(r['files'], r['links']))
    tools.append('<button type="button" class="notebtn" aria-expanded="false">заметка</button>')
    tools.append('<span class="saved" aria-live="polite"></span>')
    tools.append(DONE_BTN)
    h.append('<div class="tools">%s</div>' % ''.join(tools))
    h.append('<div class="r-note" hidden><textarea class="note" id="note_%s" rows="2" placeholder="в чём проблема" '
             'aria-label="В чём проблема: %s"></textarea></div>' % (esc(rid), label))
    h.append('</article>')
    return '\n'.join(h)


def render_tri(t, idx, src=''):
    tid = t['id']
    label = esc(plain(t['what']))
    meta = ''.join('<span>%s</span>' % inline(x) for x in (t['where'], t['date']) if x)
    h = ['<article class="tri" id="%s" data-doc="%s" data-kind="tri" data-idx="%d" data-state="">' % (esc(tid), esc(tid), idx),
         '<div class="r-main">%s<div class="r-title">%s</div>' % (from_html(src), inline(t['what']))]
    if meta:
        h.append('<div class="t-meta">%s</div>' % meta)
    if t['inside']:
        h.append('<div class="r-sub">%s</div>' % inline(t['inside']))
    if t['prop']:
        h.append('<div class="t-prop"><span class="lab">предлагаю</span>%s</div>' % inline(t['prop']))
    h.append('</div>')
    h.append('<div class="seg" role="radiogroup" aria-label="Что делать: %s">'
             '<button type="button" role="radio" aria-checked="false" data-v="archive">в архив</button>'
             '<button type="button" role="radio" aria-checked="false" data-v="delete">удалить</button>'
             '<button type="button" role="radio" aria-checked="false" data-v="keep">оставить</button></div>' % label)
    tools = []
    d = details_html(t['body'])
    if d:
        tools.append(d)
    tools.extend(file_links(t['files'], t['links']))
    tools.append('<span class="saved" aria-live="polite"></span>')
    tools.append(DONE_BTN)
    h.append('<div class="tools">%s</div>' % ''.join(tools))
    h.append('</article>')
    return '\n'.join(h)


def render_question(q):
    qid = q['id']
    return '\n'.join([
        '<article class="q" id="%s" data-doc="%s" data-kind="q">' % (esc(qid), esc(qid)),
        '<p class="qt">%s</p>' % inline(q['text']),
        '<textarea class="note" id="ans_%s" rows="3" placeholder="твой ответ" aria-label="Твой ответ: %s"></textarea>' % (esc(qid), esc(plain(q['text']))),
        '<div class="saved" aria-live="polite"></div>',
        '</article>'])


def render_table(t):
    cols = t['cols']
    h = ['<div class="tblwrap" id="%s">' % esc(t['id'])]
    if t['title']:
        h.append('<h3 class="t-title">%s</h3>' % inline(t['title']))
    h.append('<div class="tbl"><table class="dt"><thead><tr>%s</tr></thead><tbody>' %
             ''.join('<th scope="col">%s</th>' % inline(c, True) for c in cols))
    for row in t['rows']:
        cells = list(row) + [''] * (len(cols) - len(row))
        tds = []
        for i, c in enumerate(cells):
            lab = esc(plain(cols[i])) if i < len(cols) else ''
            tds.append('<td data-label="%s">%s</td>' % (lab, inline(c)))
        h.append('<tr>%s</tr>' % ''.join(tds))
    h.append('</tbody></table></div></div>')
    return '\n'.join(h)


def link_li(text, target):
    href = make_href(target)
    if href:
        btn = view_btn(href)
    else:
        btn = '<span class="fl missing"><span>не открывается</span></span>'
    return '<li><span class="lt">%s</span>%s</li>' % (inline(text, True), btn)


def render_links(b):
    h = ['<div class="links" id="%s">' % esc(b['id'])]
    if b['title']:
        h.append('<h3 class="t-title">%s</h3>' % inline(b['title']))
    h.append('<ul class="lk">')
    for text, target in b['items']:
        h.append(link_li(text, target))
    h.append('</ul></div>')
    return '\n'.join(h)


def task_kind(label):
    w = label.strip().upper().replace('Ё', 'Е')
    if w.startswith('СРОЧНО'):
        return 'urgent'
    if w.startswith('СЕГОДНЯ'):
        return 'today'
    if w.startswith('ПОТОМ'):
        return 'later'
    if w.startswith('ОТЛОЖЕНО'):
        return 'hold'
    if w.startswith('СДЕЛАНО'):
        return 'done'
    if w.startswith('ЖДЕТ'):
        return 'waitd' if 'ДИМ' in w[4:] else 'waito'
    return 'misc'


def render_task(label, text, when, num=None, uid='', with_id=False):
    """Одна строка задачи (одна и та же в любой колонке); num - видимый номер в левой колонке «Сегодня».
    uid - общий ключ задачи (data-tk, одинаковый во всех колонках); id ставится только на одну копию (with_id),
    потому что id на странице не повторяются."""
    k = task_kind(label)
    n = '<span class="tk-n" aria-hidden="true">%d</span>' % num if num else ''
    attrs = ' data-k="%s"' % k
    if uid:
        attrs += ' data-tk="%s"' % esc(uid)
        if with_id:
            attrs += ' id="%s"' % esc(uid)
    return '<li class="tl-%s"%s>%s<span class="badge tk-%s">%s</span><span class="tk-x">%s</span>%s</li>' % (
        k, attrs, n, k, esc(label), inline(text), '<span class="tk-t">%s</span>' % inline(when) if when else '')


def task_list(items, numbered=False, uids=None, with_id=False):
    """Список строк задач; numbered - нумерованный (<ol>), номера ставит сборщик по порядку источника.
    uids - ключи задач (в том же порядке, что items); with_id - ставить ли на строки id."""
    tag = 'ol' if numbered else 'ul'
    lis = ''.join(render_task(l, t, w, i if numbered else None, uids[i - 1] if uids else '', with_id)
                  for i, (l, t, w) in enumerate(items, 1))
    return '<%s class="tk%s">%s</%s>' % (tag, ' tk-num' if numbered else '', lis, tag)


# статусы для полосы кнопок над задачами: (вид, подпись кнопки); «ждёт других» - только если такие есть
TASK_FILTERS = [('urgent', 'Срочно'), ('today', 'Сегодня'), ('waitd', 'Ждёт тебя'), ('waito', 'Ждёт других'),
                ('later', 'Потом'), ('hold', 'Отложено'), ('done', 'Сделано')]


def task_short(text, n=90):
    """Первые ~n символов видимого текста задачи, по границе слова."""
    s = ' '.join(plain(text).split())
    if len(s) <= n:
        return s
    cut = s[:n]
    if ' ' in cut[n // 2:]:
        cut = cut[:cut.rindex(' ')]
    return cut.rstrip(' ,;:.-') + '…'


def render_tasks(b):
    """Два столбика. Слева «Сегодня» (СРОЧНО, СЕГОДНЯ - с номерами) и «Близкие» (ПОТОМ, ЖДЁТ).
    Справа «Полный список»: все строки подряд (в том числе ОТЛОЖЕНО), СДЕЛАНО - свёрнутой группой,
    в конце ссылка на свод хотелок («489»), если она есть в источнике."""
    # у каждой задачи свой ключ <id блока>-t<номер в источнике>; не должен совпасть с чужим id
    uid_of = {}
    for i, it in enumerate(b['items'], 1):
        u = '%s-t%d' % (b['id'], i)
        while u in IDS:
            u += '_'
        IDS[u] = 'task'
        uid_of[id(it)] = u
    openi = [it for it in b['items'] if task_kind(it[0]) != 'done']
    donei = [it for it in b['items'] if task_kind(it[0]) == 'done']
    today = [it for it in openi if task_kind(it[0]) in ('urgent', 'today')]
    near = [it for it in openi if task_kind(it[0]) in ('later', 'waitd', 'waito')]
    uids = lambda lst: [uid_of[id(it)] for it in lst]
    empty = '<p class="tk-empty">пусто</p>'
    h = ['<div class="tasks" id="%s">' % esc(b['id'])]
    if b['title']:
        h.append('<h3 class="t-title">%s</h3>' % inline(b['title']))
    # полоса кнопок-статусов со счётом (клик - оставить только этот статус; повторный клик или «Все» - снять)
    cnt = {}
    for it in b['items']:
        k = task_kind(it[0])
        cnt[k] = cnt.get(k, 0) + 1
    bar = ['<button type="button" class="tk-f tk-f-all" data-f="all" aria-pressed="true">Все</button>']
    for k, name in TASK_FILTERS:
        if k == 'waito' and not cnt.get(k):
            continue
        bar.append('<button type="button" class="tk-f tk-f-%s" data-f="%s" aria-pressed="false"%s>%s <b>%d</b></button>' % (
            k, k, '' if cnt.get(k) else ' disabled', name, cnt.get(k, 0)))
    h.append('<div class="tk-bar" role="group" aria-label="Фильтр задач по статусу">%s</div>' % ''.join(bar))
    # компактный нумерованный список всех открытых задач; клик по строке - перелёт к задаче в столбцах
    if openi:
        rows = []
        for i, it in enumerate(openi, 1):
            k = task_kind(it[0])
            rows.append('<li data-k="%s"><button type="button" class="tkx-i" data-tk-go="%s">'
                        '<span class="tkx-n">%d</span><span class="badge tk-%s">%s</span><span class="tkx-x">%s</span>'
                        '</button></li>' % (k, esc(uid_of[id(it)]), i, k, esc(it[0]), esc(task_short(it[1]))))
        h.append('<details class="tkx" open><summary>Список задач (%d)</summary><ol class="tkx-l">%s</ol></details>' % (
            len(openi), ''.join(rows)))
    h.append('<div class="tk-cols">')
    h.append('<div class="tk-col tk-left"><h4 class="tk-h">Сегодня</h4>%s<h5 class="tk-h2">Близкие</h5>%s</div>' % (
        task_list(today, True, uids(today)) if today else empty, task_list(near, False, uids(near)) if near else empty))
    right = ['<h4 class="tk-h">Полный список</h4>']
    if openi:
        right.append(task_list(openi, False, uids(openi), True))
    if donei:
        right.append('<details class="done-group"><summary>сделано (%d)</summary>%s</details>' % (
            len(donei), task_list(donei, False, uids(donei), True)))
    if HOTELKI:
        right.append('<ul class="lk tk-lk">%s</ul>' % link_li(HOTELKI['text'], HOTELKI['target']))
    h.append('<div class="tk-col tk-right">%s</div>' % ''.join(right))
    h.append('</div>')
    h.append('</div>')
    return '\n'.join(h)


def render_confirm(c):
    cid = c['id']
    h = ['<div class="confirm" id="%s" data-doc="%s" data-kind="confirm">' % (esc(cid), esc(cid)),
         '<button type="button" class="goldbtn">%s</button>' % esc(c['label'])]
    if c['hint']:
        h.append('<p class="hint">%s</p>' % inline(c['hint']))
    h.append('<div class="saved" aria-live="polite"></div></div>')
    return '\n'.join(h)


def new_list_id():
    LIST_N[0] += 1
    return LIST_N[0]


def render_section(sec, tabs, first):
    sid = sec['id']
    src = plain(sec['title'])
    toggles = [it for k, it in sec['items'] if k in ('row', 'tri')]
    open_toggles = [it for it in toggles if not (it.get('status') and is_done(it['status']))]
    done_rows = [it for k, it in sec['items'] if k == 'row' and is_done(it['status'])]
    attrs = ' data-sec="%s"' % esc(sid)
    if tabs:
        attrs += ' role="tabpanel" aria-labelledby="tab-%s"' % esc(sid)
        if not first:
            attrs += ' hidden'
    else:
        attrs += ' aria-labelledby="%s-h"' % esc(sid)
    out = ['<section class="sec" id="%s"%s>' % (esc(sid), attrs)]
    head = '<h2 id="%s-h">%s</h2>' % (esc(sid), inline(sec['title'], True))
    if toggles:
        head += '<span class="cnt" data-cnt hidden>не перекинуто: %d</span>' % len(open_toggles)
    out.append('<div class="sec-head">%s</div>' % head)
    if sec['sub']:
        out.append('<p class="h-sub">%s</p>' % inline(sec['sub']))
    run, run_kind = [], None

    def close_run():
        nonlocal run, run_kind
        if run:
            if run_kind == 'list':
                out.append('<div class="list" data-list="%d">\n%s\n</div>' % (new_list_id(), '\n'.join(run)))
            else:
                out.append('<div class="qs">\n%s\n</div>' % '\n'.join(run))
        run, run_kind = [], None

    for kind, it in sec['items']:
        if kind == 'row' and is_done(it['status']):
            continue
        if kind in ('row', 'tri', 'question'):
            want = 'qs' if kind == 'question' else 'list'
            if run_kind != want:
                close_run()
                run_kind = want
            if kind == 'row':
                run.append(render_row(it, len(run), src))
            elif kind == 'tri':
                run.append(render_tri(it, len(run), src))
            else:
                run.append(render_question(it))
            continue
        close_run()
        if kind == 'group':
            out.append('<h3 class="t-title grp" id="%s">%s</h3>' % (esc(it['id']), inline(it['title'], True)))
            if it['sub']:
                out.append('<p class="h-sub">%s</p>' % inline(it['sub']))
        elif kind == 'table':
            out.append(render_table(it))
        elif kind == 'links':
            out.append(render_links(it))
        elif kind == 'tasks':
            out.append(render_tasks(it))
        elif kind == 'confirm':
            out.append(render_confirm(it))
        elif kind == 'note':
            out.append('<p class="small">%s</p>' % inline(it))
        elif kind == 'raw':
            out.append(render_raw(it))
    close_run()
    if done_rows:
        out.append('<details class="done-group" data-done><summary>сделано (<span data-donen>%d</span>)<span class="dg-no" data-doneno hidden></span></summary>'
                   '<div class="list" data-list="%d">\n%s\n</div></details>' % (
                       len(done_rows), new_list_id(), '\n'.join(render_row(r, i, src) for i, r in enumerate(done_rows))))
    out.append('</section>')
    return '\n'.join(out)


def read_raw(path):
    """Содержимое .html / .svg для вставки как есть. None, если файла нет."""
    p = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.isfile(p):
        warn('@raw: файл не найден, пропущен: ' + p)
        return None
    with open(p, 'rb') as f:
        raw = f.read()
    text = decode_bytes(raw, False)
    text = re.sub(r'^\s*<\?xml[^>]*\?>', '', text)
    text = re.sub(r'<!doctype[^>]*>', '', text, flags=re.I)
    m = re.search(r'<body[^>]*>(.*)</body>', text, re.S | re.I)
    if m:
        styles = ''.join(re.findall(r'<style[^>]*>.*?</style>', text[:m.start()], re.S | re.I))
        text = styles + m.group(1)
    return text.strip()


SRC_RE = re.compile(r'<!--@@SRC[ \t]+(.+?)(?:[ \t]+@(\d+)-(\d+))?[ \t]*-->')
SRC_MAX = 300 * 1024


def src_block(m):
    """<!--@@SRC путь @с-по--> -> скрытый textarea со строками файла (код для схем берёт сборщик, не руки)."""
    p = m.group(1).strip().strip('"')
    if not os.path.isfile(p) or os.path.getsize(p) > SRC_MAX:
        warn('@@SRC: файл не найден или слишком велик: ' + p)
        return ''
    with open(p, 'rb') as f:
        text = decode_bytes(f.read(), False).replace('\r\n', '\n')
    lines = text.split('\n')
    a = int(m.group(2)) if m.group(2) else 1
    b = int(m.group(3)) if m.group(3) else len(lines)
    chunk = '\n'.join(lines[a - 1:b])
    return ('<textarea class="hf-src" hidden readonly tabindex="-1" aria-hidden="true" data-f="%s" data-from="%d">\n%s</textarea>'
            % (esc(os.path.basename(p)), a, esc(chunk)))


def render_raw(it):
    text = read_raw(it['path'])
    if text is None:
        return ''
    text = SRC_RE.sub(src_block, text)
    return '<div class="raw" data-raw="%s">\n%s\n</div>' % (esc(os.path.basename(it['path'])), text)


def render_archive(tabs):
    h = ['<section class="sec archive" id="archive" data-sec="archive"%s>' % (
        ' role="tabpanel" aria-labelledby="tab-archive" hidden' if tabs else ' aria-labelledby="archive-h"')]
    h.append('<div class="sec-head"><h2 id="archive-h">Архив</h2><span class="cnt" data-arch-cnt hidden>в архиве: 0</span></div>')
    h.append('<p class="h-sub">Решённые строки. Кнопка «вернуть» отправляет строку назад в её раздел.</p>')
    h.append('<p class="aside-empty" data-arch-empty>Пока ничего не решено.</p>')
    h.append('<div class="list" data-list="%d" data-archive></div>' % new_list_id())
    h.append('</section>')
    return '\n'.join(h)


def render_aside(a):
    aid = a['id']
    h = ['<aside class="aside" id="%s" aria-labelledby="%s-h">' % (esc(aid), esc(aid))]
    h.append('<h2 id="%s-h">%s</h2>' % (esc(aid), inline(a['title'], True)))
    h.append('<input type="search" class="aside-q" id="%s_q" data-aside-q placeholder="фильтр по тексту" aria-label="Фильтр списка по тексту" autocomplete="off">' % esc(aid))
    h.append('<p class="aside-empty" data-aside-empty hidden>ничего не найдено</p>')
    h.append('<ol class="ap">')
    for it in a['items']:
        n = esc(it['num'])
        btn = ''
        if it['path']:
            href = make_href(it['path'])
            btn = view_btn(href) if href else '<span class="fl missing"><span>не открывается</span></span>'
        h.append('<li class="ai" id="p-%s"><a class="num" href="#p-%s" data-goto="p-%s">%s</a>'
                 '<div class="ai-b"><div class="ai-t">%s</div><div class="ai-x">%s</div>%s</div></li>' % (
                     n, n, n, n, inline(it['topic']), inline(it['text']), btn))
    h.append('</ol></aside>')
    return '\n'.join(h)


# ---------------- проверки ----------------
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Bal(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = {}
        self.dups = []

    def _ids(self, attrs):
        for k, v in attrs:
            if k == 'id' and v:
                if v in self.ids:
                    self.dups.append(v)
                self.ids[v] = True

    def handle_starttag(self, tag, attrs):
        self._ids(attrs)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self._ids(attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.errors.append('лишний </%s> в строке %d' % (tag, self.getpos()[0]))

    def result(self):
        errs = list(self.errors)
        for tag, ln in self.stack:
            errs.append('не закрыт <%s> из строки %d' % (tag, ln))
        for d in self.dups:
            errs.append('повторяется id="%s"' % d)
        return errs


class Txt(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def balance(page):
    b = Bal()
    b.feed(page)
    b.close()
    return b.result()


# ---------------- main ----------------
def build(src, out):
    global ATT, BASE_DIR
    BASE_DIR = os.path.dirname(os.path.abspath(src))
    out = os.path.abspath(out)
    out_dir = os.path.dirname(out)
    os.makedirs(out_dir, exist_ok=True)
    parts = load_template(TEMPLATE_PATH)
    doc = parse(src)
    meta = doc['meta']
    title_plain = plain(meta['title'])
    if len(title_plain.split()) not in (2, 3, 4):
        warn('в заголовке «%s» не 2-4 слова' % title_plain)
    col = meta.get('db_collection') or safe_name(os.path.splitext(os.path.basename(out))[0])
    if not meta.get('db_collection'):
        warn('нет @db_collection, взято «%s»' % col)
    if not ID_RE.match(col) or '/' in col:
        fail('@db_collection «%s» не годится (латиница, цифры и _ - . ~ : @ +)' % col)
    ATT = Attach(out_dir, parts)
    tabs = meta.get('layout') == 'tabs'
    if tabs and not doc['sections']:
        fail('@layout: tabs без разделов')

    now_iso = datetime.datetime.now().astimezone().isoformat()
    body = ['<div id="nodb" hidden>галочки не сохраняются: открой страницу в claude.ai</div>']
    head = '<header class="top"><h1>%s</h1><div class="goldbar"></div>' % esc(title_plain)
    if meta.get('subtitle'):
        head += '<p class="subtitle">%s</p>' % inline(meta['subtitle'])
    head += '<p class="built">%s</p></header>' % inline('собрано @t:' + now_iso)
    body.append(head)
    intro = [paras for paras in paragraphs(doc['intro'])]
    if intro:
        body.append('<div class="intro">%s</div>' % ''.join(para_html(p) for p in intro))
    has_toggles = any(k in ('row', 'tri') for s in doc['sections'] for k, _ in s['items'])
    if tabs:
        # ряд вкладок лежит прямо в .wrap, выше сетки: его липкость живёт до конца страницы
        tb = ['<div class="tabs" role="tablist" aria-label="Разделы">']
        for i, s in enumerate(doc['sections']):
            sid = esc(s['id'])
            tb.append('<button type="button" role="tab" id="tab-%s" data-tab="%s" aria-controls="%s" aria-selected="%s" tabindex="%d">%s'
                      '<span class="tab-n" data-tabn="%s" hidden></span></button>' % (
                          sid, sid, sid, 'true' if i == 0 else 'false', 0 if i == 0 else -1, inline(s['title'], True), sid))
        if has_toggles:
            tb.append('<button type="button" role="tab" id="tab-archive" data-tab="archive" aria-controls="archive" '
                      'aria-selected="false" tabindex="-1">Архив<span class="tab-n" data-tabn="archive" hidden>0</span></button>')
        tb.append('</div>')
        body.append(''.join(tb))
    body.append('<div class="layout">')
    body.append('<div class="main%s">' % (' tabbed' if tabs else ''))
    for i, s in enumerate(doc['sections']):
        body.append(render_section(s, tabs, i == 0))
    if has_toggles:
        body.append(render_archive(tabs))
    body.append('</div>')
    if doc['aside']:
        body.append(render_aside(doc['aside']))
    body.append('</div>')

    vals = {'TITLE': esc(title_plain), 'COLLECTION': col, 'BODY': '\n'.join(body),
            'TOKENS': parts['tokens'].strip('\n'), 'COMMON': parts['common'].strip('\n'),
            'WRAPCLASS': (' has-aside' if doc['aside'] else '') + (' has-tabs' if tabs else '')}
    page = fill(parts['page'], vals)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)

    files = {}
    for info in ATT.order:
        files[info['rel']] = info['out']
    files_path = os.path.splitext(out)[0] + '_files.json'
    with open(files_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)

    # проверка 1: теги и повторы id (страница и все приложения)
    problems = ['страница: ' + e for e in balance(page)]
    for info in ATT.order:
        if info['rel'].endswith('.html'):
            with open(info['out'], encoding='utf-8') as f:
                problems += ['%s: %s' % (info['rel'], e) for e in balance(f.read())]

    # проверка 2: весь текст входа есть в видимом тексте страницы
    p = Txt()
    p.feed(page)
    text = norm(''.join(p.buf))
    missing = []
    for e in doc['expect']:
        e2 = norm(plain(e))
        if e2 and e2 not in text:
            missing.append(e2)

    counts = {}
    for s in doc['sections']:
        for k, _ in s['items']:
            counts[k] = counts.get(k, 0) + 1
    kinds = {}
    for info in ATT.order:
        kinds[info['kind']] = kinds.get(info['kind'], 0) + 1
    notfound = sum(1 for i in ATT.items.values() if not i['ok'])
    db_docs = sum(counts.get(k, 0) for k in ('row', 'tri', 'question', 'confirm'))

    print('собрано: %s (%d КБ)' % (out, round(len(page.encode('utf-8')) / 1024)))
    print('разделов=%d, ' % len(doc['sections']) + ', '.join('%s=%d' % (k, v) for k, v in sorted(counts.items())) +
          (', aside=%d' % len(doc['aside']['items']) if doc['aside'] else '') +
          ', документов базы=%d, вкладки=%s' % (db_docs, 'да' if tabs else 'нет'))
    print('приложения: %d (%s), не найдено/не показано: %d -> %s' % (
        len(ATT.order), ', '.join('%s=%d' % (k, v) for k, v in sorted(kinds.items())) or 'нет', notfound, files_path))
    print('теги и id: %s' % ('в порядке' if not problems else 'ОШИБКИ %d' % len(problems)))
    for e in problems:
        print('  ' + e)
    print('текст входа в выходе: не найдено %d' % len(missing))
    for e in missing:
        print('  НЕТ:', e[:140])
    for w in WARN:
        print('предупреждение:', w, file=sys.stderr)
    return 0 if not problems and not missing else 1


def main(argv):
    if len(argv) != 3:
        print('Запуск: python -X utf8 -I longread_build.py <вход.md> <выход.html>', file=sys.stderr)
        return 2
    try:
        return build(argv[1], argv[2])
    except BuildError as e:
        print('ОШИБКА: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
