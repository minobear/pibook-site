# -*- coding: utf-8 -*-
"""跑版稽核：同一組畫面在各語言各拍一次 UI 樹，找出「中文一行、別的語言變兩行」的地方。

    python audit_wrap.py            # zh 當基準，比 en ja ko
    python audit_wrap.py ja         # 只比日文（基準仍是 zh）

原理：版位的左右邊界是版面決定的、跟字無關 → 同一個 (x1, x2) 的節點在每個語言
都是同一格。把每一格依由上到下的順序配對，高度比中文高出一截＝折行了。
輸出 _shoot_tmp/wrap_report.txt（純文字，不必看截圖）。

要多稽核一個畫面：在 SCREENS 加一筆（名字、怎麼走過去）。
"""
import json
import os
import sys
import time

import shoot_locale as s

# (名字, 走到那裡的動作)。每一筆都從 App 冷啟開始走，彼此不相依。
SCREENS = [
    ('首頁', lambda: None),
    ('首頁下半', lambda: (s.sh('input swipe 540 1900 540 700 400'), time.sleep(2))),
    ('工具', lambda: (s.tap(739, 2297), time.sleep(4))),
    ('相似照片', lambda: (s.tap(739, 2297), time.sleep(4), s.tap(540, 980), time.sleep(7))),
    ('照片壓縮', lambda: (s.tap(739, 2297), time.sleep(4), s.tap(540, 1518), time.sleep(6))),
    ('我的', lambda: (s.tap(939, 2297), time.sleep(4))),
    ('我的下半', lambda: (s.tap(939, 2297), time.sleep(4), s.sh('input swipe 540 1900 540 700 400'), time.sleep(2))),
    ('圖庫合輯', lambda: (s.tap(340, 2297), time.sleep(5), s.tap(700, 202), time.sleep(4))),
    ('整理頁', lambda: (s.open_today(),)),
]


def capture(loc):
    s.set_locale(loc)
    out = {}
    for name, go in SCREENS:
        s.restart_app(12)
        s.dismiss_tips()
        go()
        s.dismiss_tips()
        out[name] = [(l, b) for l, b in s.dump() if l.strip() and (b[3] - b[1]) < 400]
        from PIL import Image
        Image.open(s.screencap('w.png')).convert('RGB').crop((0, 100, 1080, 2360)).resize((300, 628))             .save(os.path.join(s.TMP, f'wrap_{loc}_{SCREENS.index((name, go))}.jpg'), quality=80)
        s.log(loc, name, len(out[name]))
    with open(os.path.join(s.TMP, f'wrap_{loc}.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    return out


def compare(base, other, loc):
    lines = []
    for screen, nodes in other.items():
        groups = {}
        for l, b in base.get(screen, []):
            groups.setdefault((b[0], b[2]), []).append((b[1], b[3] - b[1], l))
        mine = {}
        for l, b in nodes:
            mine.setdefault((b[0], b[2]), []).append((b[1], b[3] - b[1], l))
        for slot, items in mine.items():
            ref = sorted(groups.get(slot, []))
            for (y, h, l), (_, rh, rl) in zip(sorted(items), ref):
                if h > rh + 18 and h > rh * 1.25:
                    lines.append(f'[{loc}] {screen}  x={slot[0]}–{slot[1]}  高 {rh}→{h}\n'
                                 f'    中文：{rl.replace(chr(10), " / ")[:60]}\n'
                                 f'    {loc}：{l.replace(chr(10), " / ")[:60]}')
    return lines


def sheets(locs):
    """每個畫面一張並排圖：中文｜其他語言。看圖比看數字準（容器高度固定的卡片，折行不會改變節點高度）。"""
    from PIL import Image, ImageDraw
    for i, (name, _) in enumerate(SCREENS):
        cols = [l for l in ['zh'] + locs if os.path.exists(os.path.join(s.TMP, f'wrap_{l}_{i}.jpg'))]
        sheet = Image.new('RGB', (310 * len(cols), 650), 'white')
        d = ImageDraw.Draw(sheet)
        for c, l in enumerate(cols):
            sheet.paste(Image.open(os.path.join(s.TMP, f'wrap_{l}_{i}.jpg')), (c * 310, 20))
            d.text((c * 310 + 4, 2), l, fill='black')
        sheet.save(os.path.join(s.TMP, f'sheet_{i}.jpg'), quality=80)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(s.TMP, exist_ok=True)
    locs = sys.argv[1:] or ['en', 'ja', 'ko']
    base_p = os.path.join(s.TMP, 'wrap_zh.json')
    base = capture('zh')
    report = []
    for loc in locs:
        report += compare(base, capture(loc), loc)
    p = os.path.join(s.TMP, 'wrap_report.txt')
    open(p, 'w', encoding='utf-8').write('\n'.join(report) + '\n')
    sheets(locs)
    s.log('折行可疑處', len(report), '→', p, '；並排圖 sheet_*.jpg')
