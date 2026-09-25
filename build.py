#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _partials/ 底下的共用片段展開到每一頁，並檢查每一段文字都有五種語言。

為什麼是「就地展開」而不是「src → dist」：
GitHub Pages 直接服務 repo 裡的檔案，沒有建置步驟。所以頁面檔本身就是成品 ——
共用片段以標記包住，這支腳本負責把標記之間的內容換成 _partials/ 的最新版本。
好處是原始 HTML 裡就有頁首頁尾（爬蟲、關掉 JS 都看得到、也不會有版面跳動），
而要改的地方仍然只有一處。

語言：每一段文字的五種語言都寫在同一份 HTML 裡，以 lang 屬性標記
（zh-Hant／zh-Hans／en／ja／ko），相鄰的一串就是同一段話的五個版本。
新增或改寫文案時，**五種都要到齊** —— 少了一種，那個語言的訪客會看到一個空洞，
而且畫面上不會有任何錯誤。`--check` 會把這種段落一條一條列出來。

用法：
    python build.py            # 展開（改完 _partials/ 就跑這個）
    python build.py --check    # 只檢查：共用區塊有沒有人手改、每段是不是五語到齊
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTIALS = ROOT / '_partials'

# 要展開的頁面。press/ 是產圖用的素材、不是網站頁面，不列入。
PAGES = [
    ROOT / 'index.html',
    ROOT / '404.html',
    ROOT / 'privacy' / 'index.html',
    ROOT / 'terms' / 'index.html',
    ROOT / 'support' / 'index.html',
    ROOT / 'delete-account' / 'index.html',
]

PARTIAL_NAMES = ('head', 'header', 'footer')

# 網站支援的語言。順序也是語言選單的順序。
LANGS = ('zh-Hant', 'zh-Hans', 'en', 'ja', 'ko')

LEADING_COMMENT = re.compile(r'\A\s*<!--.*?-->\s*', re.DOTALL)


def write_utf8(path: Path, text: str) -> None:
    # 明確指定 LF：在 Windows 上跑也不要把整份檔案換成 CRLF。
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def load_partial(name: str) -> str:
    """讀一份片段，並拿掉開頭那段「這是唯一的一份」的說明註解 ——
    那是寫給維護者看的，不需要出現在每一頁的原始碼裡。"""
    text = (PARTIALS / f'{name}.html').read_text(encoding='utf-8')
    return LEADING_COMMENT.sub('', text).strip('\n')


def expand(html: str, name: str, body: str) -> str:
    open_tag = f'<!-- @partial:{name} -->'
    close_tag = f'<!-- @/partial:{name} -->'
    pattern = re.compile(
        re.escape(open_tag) + r'.*?' + re.escape(close_tag), re.DOTALL)
    if not pattern.search(html):
        raise SystemExit(f'找不到 {open_tag} … {close_tag} 標記')
    return pattern.sub(lambda _: f'{open_tag}\n{body}\n{close_tag}', html)


# ── 五語到齊檢查 ─────────────────────────────────────────────────────────

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
BETWEEN_OK = re.compile(r'^(\s|<!--.*?-->)*$', re.DOTALL)


class _Node:
    def __init__(self, tag, attrs, start, parent):
        self.tag, self.attrs, self.start, self.parent = tag, attrs, start, parent
        self.end = start
        self.children = []


class _Parser(HTMLParser):
    """只為了知道每個元素在原始碼裡的起訖位置與父子關係。"""

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src = src
        self.lines = [0] + [m.end() for m in re.finditer('\n', src)]
        self.root = _Node('#root', {}, 0, None)
        self.stack = [self.root]
        self.errors = []

    def _pos(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs), self._pos(), self.stack[-1])
        node.end = node.start + len(self.get_starttag_text())
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = _Node(tag, dict(attrs), self._pos(), self.stack[-1])
        node.end = node.start + len(self.get_starttag_text())
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        end = self.src.index('>', self._pos()) + 1
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                if i != len(self.stack) - 1:
                    self.errors.append(f'第 {self.src.count(chr(10), 0, end) + 1} 行：</{tag}> 之前有沒關上的元素')
                for n in self.stack[i:]:
                    n.end = end
                del self.stack[i:]
                return


def language_problems(src: str) -> list:
    """相鄰、帶 lang 的兄弟元素是同一段話的各語言版本；每一串都要五語到齊。"""
    parser = _Parser(src)
    parser.feed(src)
    parser.close()
    problems = list(parser.errors)

    def line(node):
        return src.count('\n', 0, node.start) + 1

    def is_variant(node):
        return 'lang' in node.attrs and node.tag != 'html'

    def report(run):
        langs = [n.attrs['lang'] for n in run]
        missing = [l for l in LANGS if l not in langs]
        unknown = sorted({l for l in langs if l not in LANGS})
        if missing:
            problems.append(f'第 {line(run[0])} 行：少了 {", ".join(missing)}')
        if unknown:
            problems.append(f'第 {line(run[0])} 行：不認得的語言 {", ".join(unknown)}')

    def nested(node):
        for ch in node.children:
            # 語言選單的每一項本來就用各自的文字寫，不是「同一段話的版本」。
            if is_variant(ch) and 'lang-menu' not in _classes_up(ch):
                problems.append(f'第 {line(ch)} 行：lang 元素裡又包了 lang 元素（會被當成另一種語言藏起來）')
            nested(ch)

    def walk(node):
        run, prev_end = [], None
        for ch in node.children:
            if is_variant(ch):
                if run and not BETWEEN_OK.match(src[prev_end:ch.start]):
                    report(run)
                    run = []
                run.append(ch)
                prev_end = ch.end
                nested(ch)
            else:
                if run:
                    report(run)
                    run = []
                if 'lang-menu' not in ch.attrs.get('class', '').split():
                    walk(ch)
        if run:
            report(run)

    walk(parser.root)
    return problems


def _classes_up(node):
    out = []
    while node is not None:
        out.extend(node.attrs.get('class', '').split())
        node = node.parent
    return out


def main() -> int:
    check_only = '--check' in sys.argv
    partials = {name: load_partial(name) for name in PARTIAL_NAMES}

    stale = []
    for page in PAGES:
        original = page.read_text(encoding='utf-8')
        updated = original
        for name, body in partials.items():
            updated = expand(updated, name, body)
        if updated == original:
            continue
        stale.append(page.relative_to(ROOT).as_posix())
        if not check_only:
            write_utf8(page, updated)

    gaps = {}
    for page in PAGES:
        found = language_problems(page.read_text(encoding='utf-8'))
        if found:
            gaps[page.relative_to(ROOT).as_posix()] = found

    if check_only:
        failed = False
        if stale:
            failed = True
            print('這些頁面的共用區塊與 _partials/ 不一致：')
            for name in stale:
                print(f'  - {name}')
            print('跑 `python build.py` 重新展開。')
        if gaps:
            failed = True
            print('這些段落沒有五語到齊（' + '／'.join(LANGS) + '）：')
            for name, found in gaps.items():
                for item in found:
                    print(f'  - {name} {item}')
        if failed:
            return 1
        print(f'全部 {len(PAGES)} 頁與 _partials/ 一致，每一段都有五種語言。')
        return 0

    if stale:
        print('已更新：')
        for name in stale:
            print(f'  - {name}')
    else:
        print(f'全部 {len(PAGES)} 頁已經是最新的。')
    if gaps:
        print('⚠️ 還有段落沒有五語到齊，跑 `python build.py --check` 看清單。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
