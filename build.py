#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _partials/ 底下的共用片段展開到每一頁。

為什麼是「就地展開」而不是「src → dist」：
GitHub Pages 直接服務 repo 裡的檔案，沒有建置步驟。所以頁面檔本身就是成品 ——
共用片段以標記包住，這支腳本負責把標記之間的內容換成 _partials/ 的最新版本。
好處是原始 HTML 裡就有頁首頁尾（爬蟲、關掉 JS 都看得到、也不會有版面跳動），
而要改的地方仍然只有一處。

用法：
    python build.py            # 展開（改完 _partials/ 就跑這個）
    python build.py --check    # 只檢查有沒有人手改了展開後的內容，不寫檔
"""

import re
import sys
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


def main() -> int:
    check_only = '--check' in sys.argv
    partials = {name: load_partial(name) for name in ('header', 'footer')}

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

    if check_only:
        if stale:
            print('這些頁面的共用區塊與 _partials/ 不一致：')
            for name in stale:
                print(f'  - {name}')
            print('跑 `python build.py` 重新展開。')
            return 1
        print(f'全部 {len(PAGES)} 頁與 _partials/ 一致。')
        return 0

    if stale:
        print('已更新：')
        for name in stale:
            print(f'  - {name}')
    else:
        print(f'全部 {len(PAGES)} 頁已經是最新的。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
