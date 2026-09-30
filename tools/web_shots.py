#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商店畫板 → 官網圖片（assets/shots/<語言>/<名稱>-<寬>.webp，透明底）。

官網每一段自己就有標題、自己就有底色，要的只是「畫面本身」：手機，以及貼在手機上的
聚焦元件（相簿軌特寫、標註膠囊、手勢）。所以這裡不去裁商店截圖（那樣畫板的底色會
跟著進來，在官網上變成手機外面一圈米白色的框），而是用無頭 Chrome 以「官網模式」
（網址帶 ?web，見 press/press.css 最後一段）重新渲染畫板：不畫底色、標題、星芒、
品牌列，手機整支完整、不出血，背景透明，裁到內容邊界。

版面：每張圖都有一個「錨點」（有手機的板子是機身；隱私、相似照片是舞台上的內容），
由 press.js 回報。官網排版只算錨點那一塊 —— 伸出去的特寫與陰影以負邊距掛在外面，
不佔版面，所以五張手機在頁面上一樣大、邊緣對齊，不會因為某張多了一條特寫就縮小。
這支會直接改 index.html：每個 figure 的 style（--iw/--ml/--mt/--mb）、每張 img 的
width/height 與 sizes。

裁切範圍以五種語言的聯集為準 —— 同一段的五張圖尺寸完全一樣，換語言時版面不會跳。

用法（在官網 repo 根目錄）：
    python tools/web_shots.py          # 全部重做
    python tools/web_shots.py ja ko    # 只重做某幾種語言（裁切範圍仍以五語聯集計）
需要 Pillow 與 Chrome。
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PRESS = ROOT / 'press'
OUT = ROOT / 'assets' / 'shots'
INDEX = ROOT / 'index.html'
CHROME = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

# 語言代號 → 畫板所在資料夾（繁中畫板就在 press/ 根目錄）
LANGS = {'zh-Hant': '.', 'zh-Hans': 'zh-Hans', 'en': 'en', 'ja': 'ja', 'ko': 'ko'}
SHOTS = ['01_cover', '02_review', '03_similar', '04_gallery', '05_memory', '06_compress', '07_privacy']
WIDTHS = [480, 800, 1200]   # 1× / 2× / 3× 螢幕各有一份剛好夠用的，srcset 交給瀏覽器挑
QUALITY = 86
ALPHA_MIN = 4               # 陰影最外圈淡到看不見的部分不算進裁切範圍

# 畫板以高 932 CSS px 為基準、畫成 3 倍（與商店 1290×2796 同一個倍率）。
# 寬度比商店畫板寬：相簿軌特寫比手機寬，連同陰影要整條放得下。
BOARD_H = 932
SCALE = 3
WIN = (620 * SCALE, BOARD_H * SCALE)

# 錨點在頁面上的顯示寬度（px），與 assets/landing.css 的 --shot-w 同步 —— 只用來寫 sizes。
# (桌面, 窄螢幕上限 px, 窄螢幕 vw)
DISPLAY = {
    '01_cover': (312, 280, 70),
    '03_similar': (332, 312, 82),
    '07_privacy': (240, 240, 64),
}
DISPLAY_PHONE = (296, 280, 72)


def chrome(args, url):
    with tempfile.TemporaryDirectory() as prof:
        return subprocess.run(
            [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
             f'--user-data-dir={prof}', '--disable-application-cache',
             '--force-device-scale-factor=1', f'--window-size={WIN[0]},{WIN[1]}',
             '--virtual-time-budget=12000', '--default-background-color=00000000', *args, url],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)


def render(lang, shot, tmp):
    board = PRESS / LANGS[lang] / f'{shot}.html'
    if not board.exists():
        sys.exit(f'找不到畫板：{board}')
    url = board.resolve().as_uri() + '?web'
    png = Path(tmp) / f'{lang}_{shot}.png'
    chrome([f'--screenshot={png}'], url)
    im = Image.open(png).convert('RGBA')
    if im.size != WIN:
        sys.exit(f'{lang}/{shot}：截圖尺寸 {im.size} 不是 {WIN}，版面出事了')
    dom = chrome(['--dump-dom'], url).stdout
    m = re.search(r'<meta name="web-anchor" content="([^"]+)"', dom)
    if not m:
        sys.exit(f'{lang}/{shot}：讀不到錨點（press.js 沒跑到？）')
    l, t, r, b = (float(v) for v in m.group(1).split(','))
    cx = WIN[0] / 2
    anchor = (cx + l * SCALE, t * SCALE, cx + r * SCALE, b * SCALE)
    return im, anchor


def bbox(im):
    return im.getchannel('A').point(lambda a: 255 if a >= ALPHA_MIN else 0).getbbox()


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def pct(v):
    return f'{v * 100:.2f}%'


def update_index(shot, size, layout):
    """把 index.html 裡這一段的 figure 版面與圖片尺寸換成新的。"""
    # newline='' ：原樣保留檔案本來的換行（index.html 是 CRLF），不要整份被改寫
    with open(INDEX, encoding='utf-8', newline='') as f:
        html = f.read()
    iw, ml, mt, mb = layout
    desk, cap, vw = DISPLAY.get(shot, DISPLAY_PHONE)
    sizes = (f'(max-width: 880px) calc(min({cap}px, {vw}vw) * {iw:.4f}), '
             f'calc({desk}px * {iw:.4f})')
    style = f'--iw:{pct(iw)};--ml:{pct(ml)};--mt:{pct(mt)};--mb:{pct(mb)}'

    fig_re = re.compile(r'(<figure class="shot-card[^"]*")(?: style="[^"]*")?(>)(.*?)(</figure>)', re.S)
    hit = 0

    def fix_fig(m):
        nonlocal hit
        if f'/assets/shots/zh-Hant/{shot}-' not in m.group(3):
            return m.group(0)
        hit += 1
        body = re.sub(r'width="\d+" height="\d+"', f'width="{size[0]}" height="{size[1]}"', m.group(3))
        body = re.sub(r'sizes="[^"]*"', f'sizes="{sizes}"', body)
        return f'{m.group(1)} style="{style}"{m.group(2)}{body}{m.group(4)}'

    html = fig_re.sub(fix_fig, html)
    if hit != 1:
        sys.exit(f'index.html 裡找到 {hit} 個 {shot} 的 figure（應該剛好一個）')
    with open(INDEX, 'w', encoding='utf-8', newline='') as f:
        f.write(html)


def main():
    sys.stdout.reconfigure(encoding='utf-8')   # Windows 主控台預設 cp950，印不出 ✓ ⚠️
    ap = argparse.ArgumentParser()
    ap.add_argument('langs', nargs='*', help='只重做這幾種語言（預設全部）')
    args = ap.parse_args()
    out_langs = args.langs or list(LANGS)
    for lang in out_langs:
        if lang not in LANGS:
            sys.exit(f'不認得的語言：{lang}（可用：{" ".join(LANGS)}）')
    if not os.path.exists(CHROME):
        sys.exit(f'找不到 Chrome：{CHROME}')

    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(4) as pool:
        for shot in SHOTS:
            # 裁切範圍取五語聯集，所以就算只重做一種語言也要五種都渲染一次
            jobs = {lang: pool.submit(render, lang, shot, tmp) for lang in LANGS}
            got = {lang: j.result() for lang, j in jobs.items()}

            ref = got['zh-Hant'][1]
            for lang, (_, a) in got.items():
                if max(abs(p - q) for p, q in zip(a, ref)) > 2 * SCALE:
                    print(f'  ⚠️ {lang} 的錨點與繁中差超過 2pt，請目視確認這一張')
            crop = union([bbox(im) for im, _ in got.values()])
            cw, ch = crop[2] - crop[0], crop[3] - crop[1]
            ax0, ay0, ax1, ay1 = ref
            aw = ax1 - ax0
            # 全部以「錨點寬度」為 100%（CSS 的百分比邊距連上下都是以寬度計）
            layout = (cw / aw, (crop[0] - ax0) / aw, (crop[1] - ay0) / aw, (ay1 - crop[3]) / aw)

            for lang in out_langs:
                im = got[lang][0].crop(crop)
                os.makedirs(OUT / lang, exist_ok=True)
                for width in WIDTHS:
                    height = round(ch * width / cw)
                    im.resize((width, height), Image.LANCZOS).save(
                        OUT / lang / f'{shot}-{width}.webp', 'WEBP', quality=QUALITY, method=6)

            size = (WIDTHS[-1], round(ch * WIDTHS[-1] / cw))
            update_index(shot, size, layout)
            print(f'✓ {shot}: 裁切 {cw}×{ch}，錨點 {aw:.0f}×{ay1 - ay0:.0f}，'
                  f'圖寬＝錨點的 {layout[0] * 100:.1f}%')


if __name__ == '__main__':
    main()
