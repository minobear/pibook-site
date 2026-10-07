#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 App 裡的相簿像素圖示（lib/core/design/pibook_album_icons.dart）轉成 SVG。

為什麼不是截圖：商店素材是 4K，像素圖要放大到幾百 px 還是方方正正的格子 ——
直接讀 Dart 裡那份原稿（字元格＋共用色票），每一格畫成一個方塊，放多大都不糊。
圖示本身一格都不改，跟使用者在 App 裡看到的是同一份。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DART = REPO / 'lib' / 'core' / 'design' / 'pibook_album_icons.dart'


def _load():
    src = DART.read_text(encoding='utf-8')
    pal_src = src[src.index('const Map<String, Color> _palette'):]
    pal_src = pal_src[:pal_src.index('};')]
    palette = {k: '#' + v[2:] for k, v in re.findall(r"'(.)':\s*Color\(0x([0-9A-Fa-f]{8})\)", pal_src)}
    icons = {}
    for m in re.finditer(r"PibookAlbumIcon\(\s*'([^']+)',\s*'([^']+)',\s*\[(.*?)\]", src, re.S):
        rows = re.findall(r"'([^']*)'", m.group(3))
        if rows and all(len(r) == len(rows[0]) for r in rows):
            icons.setdefault(m.group(1), rows)
    return palette, icons


PALETTE, ICONS = _load()


def svg(name, size=None):
    """一段 inline SVG（viewBox 為格數、crispEdges；不帶寬高時由 CSS 決定大小）。"""
    rows = ICONS[name]
    n = len(rows)
    parts = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == '.':
                x += 1
                continue
            x2 = x
            while x2 < len(row) and row[x2] == ch:      # 同一列連續同色合併成一條，檔案小很多
                x2 += 1
            parts.append(f'<rect x="{x}" y="{y}" width="{x2 - x}" height="1" fill="{PALETTE[ch]}"/>')
            x = x2
    wh = f' width="{size}" height="{size}"' if size else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}"{wh} '
            f'shape-rendering="crispEdges">{"".join(parts)}</svg>')
