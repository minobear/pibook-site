#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商店截圖 → 官網圖片（assets/shots/<語言>/<名稱>-<寬>.webp）。

商店截圖是「標題＋副標＋畫面」一整張；官網每一段自己就有標題與說明，
同一句話不該在同一個畫面上出現兩次，所以這裡只留下畫面：
從第一個視覺元素（手機、插圖、星星）往上留一點呼吸空間裁切，
裁切範圍內若還有副標的殘字，用上下兩列背景做垂直內插補掉（背景是柔和漸層，看不出接縫）。

裁切位置以繁中那張為準，五種語言共用 —— 同一段的五張圖尺寸完全一樣，
頁面預留的框不會因為換語言而跳動。若換了商店截圖的版面，記得同步 index.html
裡每張圖的 height 屬性（這支會印出新的尺寸）。

用法（在官網 repo 根目錄）：
    python tools/web_shots.py                      # 預設讀 ../store_assets/screenshots（官網放在主 repo 的 site/ 底下時）
    python tools/web_shots.py --src <截圖資料夾>     # 其他擺法
    python tools/web_shots.py ja ko                # 只重做某幾種語言
需要 Pillow（pip install pillow）。
"""

import argparse
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'shots'
LANGS = ['zh-Hant', 'zh-Hans', 'en', 'ja', 'ko']
SHOTS = ['01_cover', '02_review', '03_similar', '04_gallery', '05_memory', '06_compress', '07_privacy']
WIDTHS = [480, 800, 1200]   # 1× / 2× / 3× 螢幕各有一份剛好夠用的，srcset 交給瀏覽器挑
MARGIN = 84                  # 第一個視覺元素上方保留的空間（以 1290 寬計）
QUALITY = 82


def ink_rows(im, y0, y1):
    """[y0, y1) 之間，哪幾列有「不是平滑背景」的東西。背景以該列左右兩端做線性估計。"""
    px = im.load()
    w = im.size[0]
    rows = []
    for y in range(y0, y1):
        left, right = px[4, y], px[w - 5, y]
        hit = 0
        for x in range(0, w, 2):
            t = x / (w - 1)
            p = px[x, y]
            if sum(abs(p[i] - (left[i] + (right[i] - left[i]) * t)) for i in range(3)) > 70:
                hit += 1
                if hit > 1:
                    break
        rows.append(hit > 1)
    return rows


def runs_of(flags, base):
    out, start = [], None
    for i, flag in enumerate(flags + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            out.append((base + start, base + i))
            start = None
    return out


def subtitle_end(im):
    """標題區（眉標、大標、副標）最後一列的下一列。"""
    runs = runs_of(ink_rows(im, 0, 1200), 0)
    return max(e for s, e in runs if s < 760 and e < 800)


def visual_start(im):
    after = subtitle_end(im) + 1
    for i, flag in enumerate(ink_rows(im, after, min(after + 600, im.size[1]))):
        if flag:
            return after + i
    return after


def paint_out(im, top, vis):
    """把 [top, vis) 裡殘留的副標，用上下兩列背景做垂直內插蓋掉。"""
    px = im.load()
    w = im.size[0]
    for r0, r1 in runs_of(ink_rows(im, top, vis), top):
        a, b = max(top - 1, r0 - 4), min(vis - 2, r1 + 3)
        xs = []
        for y in range(r0, r1):
            left, right = px[4, y], px[w - 5, y]
            for x in range(w):
                t = x / (w - 1)
                if sum(abs(px[x, y][i] - (left[i] + (right[i] - left[i]) * t)) for i in range(3)) > 30:
                    xs.append(x)
        if not xs:
            continue
        x0, x1 = max(0, min(xs) - 10), min(w - 1, max(xs) + 10)
        for x in range(x0, x1 + 1):
            pa, pb = px[x, a], px[x, b]
            for y in range(a + 1, b):
                t = (y - a) / (b - a)
                px[x, y] = tuple(round(pa[i] + (pb[i] - pa[i]) * t) for i in range(3))


def find_src(arg):
    candidates = [Path(arg)] if arg else [ROOT.parent / 'store_assets' / 'screenshots',
                                          ROOT.parent / 'Pibook' / 'store_assets' / 'screenshots']
    for c in candidates:
        if (c / 'zh-Hant' / '1290x2796').is_dir():
            return c
    sys.exit('找不到商店截圖（<src>/<語言>/1290x2796/*.png）。用 --src 指定。')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('langs', nargs='*', help='只重做這幾種語言（預設全部）')
    ap.add_argument('--src', help='store_assets/screenshots 資料夾')
    args = ap.parse_args()
    src = find_src(args.src)
    langs = args.langs or LANGS

    for shot in SHOTS:
        ref = Image.open(src / 'zh-Hant' / '1290x2796' / f'{shot}.png').convert('RGB')
        vis = visual_start(ref)
        top = vis - MARGIN
        print(f'{shot}: 裁切自第 {top} 列，輸出比例 1290×{ref.size[1] - top}')
        for lang in langs:
            im = Image.open(src / lang / '1290x2796' / f'{shot}.png').convert('RGB')
            if abs(visual_start(im) - vis) > 2:
                print(f'  ⚠️ {lang} 的畫面起點與繁中不同，請目視確認這一張')
            paint_out(im, top, vis)
            crop = im.crop((0, top, im.size[0], im.size[1]))
            os.makedirs(OUT / lang, exist_ok=True)
            for width in WIDTHS:
                height = round(crop.size[1] * width / crop.size[0])
                crop.resize((width, height), Image.LANCZOS).save(
                    OUT / lang / f'{shot}-{width}.webp', 'WEBP', quality=QUALITY, method=6)


if __name__ == '__main__':
    main()
