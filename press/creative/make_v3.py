# -*- coding: utf-8 -*-
"""App Store 創意素材 v3（2026-10-07）—— 產品頁面測試（A/B）用的三個方向。

使用者看了 v2 放進 App Store 的樣子：「整個版面太空洞、很樸素，像 prototype」。v3 三個方向一起做，
放進「產品頁面最佳化」的三個版型（Treatment）比轉換率：

| 代號 | 方向 | 底 | 一句話 |
|---|---|---|---|
| A_wall   | 照片牆 | 夜藍 | 一整面爆滿的圖庫（壓暗當質感），巴哥犬從牆上空出的那一格被抽出來、落進「狗狗」 |
| B_poster | 大字海報 | 珊瑚 | 品牌色滿版、大字、相簿軌橫貫出血，照片從右上角一張接一張排隊落下 |
| C_phone  | 手機破框 | 米白＋珊瑚地板 | 手機站在相簿軌上，軌道從手機底部長出來橫跨整個畫面；地板上署名（隱私承諾＋拍簿） |

共同的規矩（沿用 v2 的 README 規矩表）：每種尺寸都看得到相簿軌、而且在安全區裡；字與主角在安全區裡；
圖示直接讀 Dart 原稿；相簿名稱放不下就縮；不放第三方商標的照片；不加發光、不做裝飾漸層。
安全區外不是空白 —— 搜尋結果在 iPhone 上整張 3:2 都看得到（使用者 2026-10-07 的截圖），所以外圍也要有東西。

    python make_v3.py                    # 三個方向 × 標題／搜尋 × 五語
    python make_v3.py B_poster en        # 只出某幾個
    python make_v3.py --video            # 影片：三個方向 × 標題（3840×1646）／搜尋（3240×2160）× 五語，一支約 3–5 分鐘
    python make_v3.py --video C_phone search zh-Hant --frames=38,60,100   # 只出幾格試看（build/creative/stills/）
    → store_assets/creative/<語言>/<代號>_<版位>_<寬>x<高>.png，總覽 store_assets/creative/總覽_v3.jpg
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import make_creative as mc
import photos
import pixel_icons

sys.stdout.reconfigure(encoding='utf-8')
W = mc.UNIT_W
PLACEMENTS = ('header', 'search')
# 影片版的底圖：MOTION＝{'lit': {要亮的格子}} 時，會動的東西（排隊的照片、手機裡的卡片、飛行中的照片）都不畫，
# 交給 Remotion（remotion/src/creative/CreativeLoop.tsx）；版面、字、軌道照畫 —— 跟靜態圖是同一份版面
MOTION = None
META = {}
DESIGNS = ('A_wall', 'B_poster', 'C_phone')

# 牆上的照片（不放巴哥犬 —— 它是被抽出來的那一張；不放印著店家品牌的奶茶）
WALL = ['latte_a', 'family_floor', 'taipei_101', 'cat_orange_face', 'flowers_a', 'mountain_a', 'boy_slide', 'shrimp',
        'friends_laugh', 'couple_city', 'bday_a', 'brunch', 'dog_autumn', 'sunset_city', 'kids_swing', 'croissant',
        'picnic_a', 'fireworks_a', 'girl_jump', 'hikers', 'latte_b', 'grandma_kid', 'salad', 'travel_a', 'cat_sleep',
        'selfie_a', 'dinner_a', 'flowers_b', 'mountain_b', 'friends_selfie', 'taipei_night', 'women_cafe', 'bday_c',
        'couple_picnic', 'dish', 'travel_b', 'cat_tabby', 'dad_kid', 'forest_walk', 'girl_eating', 'picnic_mom',
        'fireworks_b', 'grandpa_a', 'friends_row', 'latte_c', 'sunset_101', 'travel_c', 'women_park', 'dinner_b',
        'couple_park', 'friends_eat', 'family_living', 'cat_orange_sofa', 'boba_hand', 'bday_d', 'selfie_b',
        'picnic_b', 'couple_b', 'grandpa_b', 'friends_couch', 'cat_orange_warm', 'selfie_c']

# 隱私承諾（商店截圖第七張的大標，五語已定稿：site/press/*/07_privacy.html）
PROMISE = {
    'zh-Hant': '你的照片不離開你的手機', 'zh-Hans': '你的照片不离开你的手机',
    'en': 'Your photos never leave your phone', 'ja': '写真はスマホの外に出ません', 'ko': '사진은 휴대폰 밖으로 나가지 않아요',
}

CSS = '''
.h1 { font-family: var(--serif); font-weight: 700; line-height: 1.17; letter-spacing: .02em; white-space: nowrap; }
.h1 em { font-style: normal; }
.tile { position: absolute; border-radius: 26%; display: flex; align-items: center; justify-content: center; }
.tile svg { width: 56%; height: 56%; }
.lbl { position: absolute; text-align: center; font-family: var(--sans); white-space: nowrap; letter-spacing: .03em;
  color: #2F3A45; line-height: 1.1; }
.ph { position: absolute; overflow: hidden; background: #ccc; }
.ph img { width: 100%; height: 100%; object-fit: cover; display: block; }
.mascot { position: absolute; z-index: 22; }
.lk-light .lockup .wm { color: #FFF8F0; }
.lk-light .lockup .wm small { color: rgba(255,248,240,.66); }
'''


# 照片的陰影（設計單位）：靜態圖與影片同一份
SHADOW_PARTS = {
    'A_wall': [(0, 3, 8, 0, 'rgba(0,0,0,.45)'), (0, 40, 70, -20, 'rgba(0,0,0,.8)')],
    'B_poster': [(0, 3, 8, 0, 'rgba(90,30,20,.35)'), (0, 40, 70, -20, 'rgba(90,30,20,.7)')],
    'C_phone': [(0, 2, 4, 0, 'rgba(42,55,68,.22)'), (0, 26, 50, -16, 'rgba(42,55,68,.55)')],
}


def shadow_css(design, z=1.0):
    return ', '.join(f'{x * z:.1f}px {y * z:.1f}px {b * z:.1f}px {s * z:.1f}px {c}' for x, y, b, s, c in SHADOW_PARTS[design])


SHADOW = {d: shadow_css(d) for d in SHADOW_PARTS}


# ─────────────────────────────── 共用零件 ───────────────────────────────

def cap_height(ts):
    return ts * (.15 + 1 + .08 + .2 * 1.2 + .15)


def around(hero, hero_x, sp, x_min, x_max):
    """照 App 相簿軌的順序、以 hero 為中心往兩邊排，直到超出 [x_min, x_max]。"""
    order = mc.RAIL_ORDER
    hi = order.index(hero)
    k0 = -int((hero_x - x_min) // sp) - 1
    k1 = int((x_max - hero_x) // sp) + 1
    names = [order[(hi + k) % len(order)] for k in range(k0, k1 + 1)]
    return names, (lambda i: hero_x + (k0 + i) * sp)


def rail(loc, names, x_of, y, ts, left, right, lit, shadow):
    """相簿軌（顏色、圓角、比例量自 App 實機錄影：軌底 #FCFAF8、格子 #F0EAE1、點到的那一格 #A0ABB6）。"""
    li = mc.LOC_IDX[loc]
    pad, lbl = ts * .15, ts * .2
    ch = cap_height(ts)
    out = [f'<div style="position:absolute;left:{left}px;top:{y}px;width:{right - left}px;height:{ch}px;background:#FCFAF8;'
           f'border-radius:{ch * .36}px;z-index:20;box-shadow:inset 0 0 0 1px rgba(42,55,68,.05),{shadow}"></div>']
    pos = {}
    for i, n in enumerate(names):
        cx = x_of(i)
        on = n in lit
        s = ts * (1.08 if on else 1)
        out.append(f'<div class="tile" style="left:{cx - s / 2}px;top:{y + pad - (s - ts) / 2}px;width:{s}px;height:{s}px;'
                   f'background:{"#A0ABB6" if on else "#F0EAE1"};z-index:21">{pixel_icons.svg(n)}</div>')
        out.append(f'<div class="lbl fitw" style="left:{cx - ts * .58}px;width:{ts * 1.16}px;'
                   f'top:{y + pad + ts + ts * .08 + (s - ts) / 2}px;font-size:{lbl}px;font-weight:{700 if on else 500};'
                   f'z-index:21">{mc.ALBUM_NAMES[n][li]}</div>')
        pos[n] = (cx, y + pad)
    return '\n'.join(out), pos


def photo(name, cx, cy, size, rot, z=30, r=.13, pos='50% 50%', shadow=''):
    return (f'<div class="ph" style="left:{cx - size / 2}px;top:{cy - size / 2}px;width:{size}px;height:{size}px;'
            f'border-radius:{size * r}px;transform:rotate({rot}deg);box-shadow:{shadow};z-index:{z}">'
            f'<img src="{mc.ph(name)}" style="object-position:{pos}"></div>')


def dotted(x0, y0, qx, qy, x1, y1, w, color, z=26):
    """飛行路線：二次貝茲上的一串圓點。"""
    minx, miny = min(x0, qx, x1) - 30, min(y0, qy, y1) - 30
    Wd, Hd = max(x0, qx, x1) + 30 - minx, max(y0, qy, y1) + 30 - miny
    d = f'M{x0 - minx:.1f},{y0 - miny:.1f} Q{qx - minx:.1f},{qy - miny:.1f} {x1 - minx:.1f},{y1 - miny:.1f}'
    return (f'<svg style="position:absolute;left:{minx}px;top:{miny}px;width:{Wd}px;height:{Hd}px;z-index:{z};overflow:visible" '
            f'viewBox="0 0 {Wd} {Hd}"><path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" '
            f'stroke-dasharray="0 {w * 2.6}"/></svg>')


def headline(loc, x, y, w, h, fs_zh, fs_other, ink, em, lockup=False, light=False):
    """大標：垂直置中在 (x, y, w, h) 裡；字放不下就縮（FIT_JS，下限 70%）。"""
    fs = fs_zh if loc.startswith('zh') else fs_other
    lock = ''
    if lockup:
        lk = mc.lockup(mc.TEXT[loc], fs * .58, fs * .36, fs * .16)
        lock = f'<div class="{"lk-light" if light else ""}" style="margin-bottom:{fs * .3}px">{lk}</div>'
    two = mc.TEXT2[loc]['two'].replace('<em>', f'<em style="color:{em}">')
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;display:flex;flex-direction:column;'
            f'justify-content:center;z-index:40">{lock}<h1 class="h1 fit" style="font-size:{fs}px;color:{ink};width:{w}px">{two}</h1></div>')


class Frame:
    def __init__(self, placement):
        spec = mc.SPECS[placement]
        self.zoom = spec['w'] / W
        self.H = spec['h'] / self.zoom
        self.sx0, self.sy0, self.sx1, self.sy1 = [v / self.zoom for v in spec['safe']]
        self.sw, self.sh = self.sx1 - self.sx0, self.sy1 - self.sy0
        self.spec = spec


# ─────────────────────── A：照片牆（爆滿的圖庫 → 抽出一張歸檔） ───────────────────────

A = {
    'search': dict(ts=140, hero_at=.77, pug=270, wall=168, hole=(1480, 150), h1=(116, 84), lockup=True, mascot=210),
    'header': dict(ts=92, hero_at=.8, pug=176, wall=122, hole=(1520, 70), h1=(70, 52), lockup=False, mascot=140),
}


def design_a(placement, loc):
    f, L = Frame(placement), A[placement]
    els = []
    # 牆：以「空出來那一格」為中心轉 -6°（洞的位置就不會跑掉），超出畫布；壓一層夜藍讓它退成質感
    t = L['wall']
    g = t * .07
    hx, hy = L['hole']
    cols = int(W * 1.6 / (t + g)) + 2
    rows = int(f.H * 1.9 / (t + g)) + 2
    c0, r0 = cols // 2, rows // 2
    cells, k = [], 0
    for r_ in range(rows):
        for c in range(cols):
            x = hx - t / 2 + (c - c0) * (t + g)
            y = hy - t / 2 + (r_ - r0) * (t + g)
            if (c, r_) == (c0, r0):
                cells.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{t}px;height:{t}px;border-radius:{t * .11}px;'
                             f'border:{t * .02}px dashed rgba(246,196,83,.92);z-index:3"></div>')
                continue
            if x > W + t * 2 or y > f.H + t * 2 or x < -t * 3 or y < -t * 3:
                continue
            n = WALL[(k * 7 + r_ * 3) % len(WALL)]
            k += 1
            cells.append(f'<div class="ph" style="left:{x}px;top:{y}px;width:{t}px;height:{t}px;border-radius:{t * .11}px;z-index:1">'
                         f'<img src="{mc.ph(n)}"></div>')
    els.append(f'<div style="position:absolute;inset:0;transform:rotate(-6deg);transform-origin:{hx}px {hy}px">' + ''.join(cells) +
               f'<div style="position:absolute;left:-2000px;top:-2000px;width:6000px;height:6000px;background:rgba(19,28,38,.80);z-index:2"></div></div>')
    # 相簿軌（貼安全區下緣）
    ts = L['ts']
    sp = ts * 1.18
    ry = f.sy1 - cap_height(ts)
    names, xo = around('dog', f.sx0 + f.sw * L['hero_at'], sp, -ts, W + ts)
    r_html, pos = rail(loc, names, xo, ry, ts, xo(0) - ts * .66, xo(len(names) - 1) + ts * .66,
                       MOTION['lit'] if MOTION else {'dog'}, '0 2px 4px rgba(0,0,0,.4), 0 40px 90px -30px rgba(0,0,0,.85)')
    els.append(r_html)
    dx, dy = pos['dog']
    ps = L['pug']
    pcx, pcy = dx - ts * .2, dy - ps * .62
    qx, qy = hx - ts * .3, (hy + pcy) / 2
    els.append(dotted(hx, hy, qx, qy, pcx, pcy, ts * .065, 'rgba(246,196,83,.95)'))
    if not MOTION:
        els.append(photo('pug', pcx, pcy, ps, -8, pos='42% 55%',
                         shadow='0 3px 8px rgba(0,0,0,.45), 0 40px 70px -20px rgba(0,0,0,.8)'))
    # 影片：下一張從牆上那個洞裡被抽出來（一出現就是牆上那一格的大小、跟牆一樣轉 -6°），直接到最前面
    META.update(mode='queue', ts=ts, sp=sp, pos=pos, hero=dict(x=pcx, y=pcy, size=ps, rot=-8),
                path=dict(x0=hx, y0=hy, qx=qx, qy=qy), slots=[], entry=dict(q=0, scale=t / ps, rot=-6, o=0))
    els.append(mc.mascot_el(pos['cake'][0] + ts * .45, ry + ts * .04, L['mascot']))
    # 字：左邊，右緣從巴哥犬（轉了 8°）的外框再退一點
    pug_left = pcx - ps * .5 * (math.cos(math.radians(8)) + math.sin(math.radians(8)))
    top = f.sy0 - (f.sh * .2 if L['lockup'] else 0)
    els.append(headline(loc, f.sx0, top, pug_left - ts * .3 - f.sx0, ry - ts * .15 - top, *L['h1'],
                        ink='#F4F1EA', em='#F6C453', lockup=L['lockup'], light=True))
    return f'<div class="board" style="background:#16212C">' + '\n'.join(els) + '</div>'


# ─────────────────────── B：大字海報（品牌色滿版、軌道出血、照片排隊落下） ───────────────────────

B = {
    'search': dict(ts=170, hero_at=.8, pug=330, h1=(100, 74), lockup=True, mascot=270, motif=104,
                   queue=[(.68, 'boba_hand', -6), (.40, 'bday_a', 9)]),
    'header': dict(ts=104, hero_at=.82, pug=196, h1=(66, 50), lockup=False, mascot=170, motif=74,
                   queue=[(.68, 'boba_hand', -6), (.40, 'bday_a', 9)]),
}


def motif(m, H, color_filter, opacity):
    """底紋：App 的相簿像素圖示排成磚牆，單色、極淡（品牌自己的紋理，取代大面積的純色空白）。"""
    step = m * 2.05
    out = []
    k = 0
    for r_ in range(int(H / step) + 2):
        for c in range(int(W / step) + 2):
            x = c * step + (step / 2 if r_ % 2 else 0) - step * .3
            y = r_ * step - step * .2
            n = mc.RAIL_ORDER[(k * 5 + r_) % len(mc.RAIL_ORDER)]
            k += 1
            out.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{m}px;height:{m}px">{pixel_icons.svg(n)}</div>')
    return (f'<div style="position:absolute;inset:0;z-index:0;filter:{color_filter};opacity:{opacity}">' + ''.join(out) + '</div>')


def design_b(placement, loc):
    f, L = Frame(placement), B[placement]
    els = [motif(L['motif'], f.H, 'brightness(0)', .075)]
    ts = L['ts']
    sp = ts * 1.17
    ry = f.sy1 - cap_height(ts)
    names, xo = around('dog', f.sx0 + f.sw * L['hero_at'], sp, -ts * 2, W + ts * 2)
    r_html, pos = rail(loc, names, xo, ry, ts, -ts, W + ts, MOTION['lit'] if MOTION else {'dog'},
                       f'0 3px 6px rgba(90,30,20,.25), 0 {ts * .3}px {ts * .55}px -{ts * .18}px rgba(90,30,20,.6)')
    els.append(r_html)
    dx, dy = pos['dog']
    ps = L['pug']
    pcx, pcy = dx - ts * .12, dy - ps * .5
    # 一串照片從右上角排隊落進「狗狗」：沿著同一條弧線、越遠越小
    x0, y0 = W + ps * .2, -ps * .5
    qx, qy = (x0 + pcx) / 2 + ps * .5, (y0 + pcy) / 2 - ps * .2
    els.append(dotted(x0, y0, qx, qy, pcx, pcy, ts * .065, 'rgba(255,226,166,.9)', z=25))
    slots = []
    for q, n, rot in L['queue']:
        bx = (1 - q) ** 2 * x0 + 2 * (1 - q) * q * qx + q ** 2 * pcx
        by = (1 - q) ** 2 * y0 + 2 * (1 - q) * q * qy + q ** 2 * pcy
        sc = .36 + .44 * q
        slots.append(dict(q=q, scale=sc, rot=rot))
        if not MOTION:
            els.append(photo(n, bx, by, ps * sc, rot, z=27, shadow=SHADOW['B_poster']))
    if not MOTION:
        els.append(photo('pug', pcx, pcy, ps, -8, pos='42% 55%', shadow=SHADOW['B_poster']))
    META.update(mode='queue', ts=ts, sp=sp, pos=pos, hero=dict(x=pcx, y=pcy, size=ps, rot=-8),
                path=dict(x0=x0, y0=y0, qx=qx, qy=qy), slots=slots, entry=None)
    els.append(mc.mascot_el(pos['cake'][0] + ts * .5, ry + ts * .04, L['mascot']))
    pug_left = pcx - ps * .5 * (math.cos(math.radians(8)) + math.sin(math.radians(8)))
    top = f.sy0 - (f.sh * .22 if L['lockup'] else 0)
    els.append(headline(loc, f.sx0, top, pug_left - ts * .25 - f.sx0, ry - ts * .12 - top, *L['h1'],
                        ink='#FFF8F0', em='#FFE2A6', lockup=L['lockup'], light=True))
    return f'<div class="board" style="background:#D46C58">' + '\n'.join(els) + '</div>'


# ─────────────────────── C：手機破框（軌道從手機底部長出來） ───────────────────────

# App 整理頁的實機幾何（1080×2260 錄影格的比例；錄影格裁掉了狀態列，真的螢幕比它長 ≈5.5%）
CARD = (20 / 1080, 232 / 2260, 1060 / 1080, 1790 / 2260)
CARD_R = 40 / 1080
SCR_AR = 2.17
TOP_OFF = .055
ICON = {
    'heart': ('<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round">'
              '<path d="M12 20.5s-7.5-4.6-7.5-10.1A4.2 4.2 0 0 1 12 7.6a4.2 4.2 0 0 1 7.5 2.8c0 5.5-7.5 10.1-7.5 10.1z"/></svg>'),
    'expand': ('<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
               '<circle cx="12" cy="12" r="9.2"/><path d="M8.5 13.6 12 10.1l3.5 3.5"/></svg>'),
    'close': ('<svg viewBox="0 0 24 24" fill="none" stroke="#2A3744" stroke-width="2.2" stroke-linecap="round">'
              '<path d="M7 7l10 10M17 7 7 17"/></svg>'),
    'more': ('<svg viewBox="0 0 24 24" fill="#2A3744"><circle cx="6" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/>'
             '<circle cx="18" cy="12" r="1.8"/></svg>'),
}
C = {
    'search': dict(ts=150, phone_x=.8, phone_top=26, h1=(112, 84), lockup=True, sign=40, mascot=('camera', 200),
                   fallers=[('latte_a', 'coffee', 150, -7), ('flowers_a', 'flower', 150, 6)]),
    'header': dict(ts=96, phone_x=.83, phone_top=14, h1=(70, 52), lockup=False, sign=26, mascot=('beach', 140),
                   fallers=[('latte_a', 'coffee', 104, -7), ('flowers_a', 'flower', 104, 6),
                            ('taipei_101', 'city', 104, 6), ('mountain_a', 'mountain', 104, -6)]),
}
C_CSS = '''
.paperglow::before { content: ""; position: absolute; inset: 0; z-index: 0; background:
    radial-gradient(ellipse 55% 70% at 4% -8%, rgba(232,128,110,.16), transparent 70%),
    radial-gradient(ellipse 55% 70% at 98% -4%, rgba(91,122,146,.13), transparent 70%); }
.floor { position: absolute; left: 0; right: 0; bottom: 0; z-index: 2; background: #DE7A65; }
.sign { position: absolute; left: 0; right: 0; z-index: 3; display: flex; justify-content: center; align-items: center;
  color: #FFF8F0; font-family: var(--sans); font-weight: 500; letter-spacing: .05em; white-space: nowrap; }
.sign .dot { width: .3em; height: .3em; border-radius: 50%; background: rgba(255,248,240,.6); }
'''


def design_c(placement, loc):
    f, L = Frame(placement), C[placement]
    els = []
    ts = L['ts']
    ch = cap_height(ts)
    ry = f.sy1 - ch
    rmid = ry + ch / 2
    # 手機：上緣完整露出（動態島＋圓角＝一眼認得出是手機）；螢幕下緣藏在相簿軌後面 ——
    # App 裡相簿軌本來就在螢幕最下面，看起來就是軌道從手機底部長出來、往兩邊一路延伸出去
    top = L['phone_top']
    scr_bottom = ry + ch * .8
    scr_w = (scr_bottom - top) / (SCR_AR + .07)
    scr_h = scr_w * SCR_AR
    bez = scr_w * .035
    pcx = f.sx0 + f.sw * L['phone_x']
    sx, sy = pcx - scr_w / 2, top + bez
    pr = scr_w * .17
    els.append(f'<div style="position:absolute;left:{sx - bez}px;top:{top}px;width:{scr_w + 2 * bez}px;height:{scr_h + 2 * bez}px;'
               f'border-radius:{pr + bez}px;background:#232C36;z-index:10;box-shadow:inset 0 0 0 {bez * .2}px #55606C,'
               f'0 4px 10px rgba(42,55,68,.18),0 {scr_w * .12}px {scr_w * .3}px -{scr_w * .08}px rgba(42,55,68,.45)"></div>')
    ky = (2260 / 1080) / SCR_AR
    cx0, cy0, cx1, cy1 = CARD
    card_x, card_y = cx0 * scr_w, (TOP_OFF + cy0 * ky) * scr_h
    card_w, card_h = (cx1 - cx0) * scr_w, (cy1 - cy0) * ky * scr_h
    ic, btn = scr_w * .062, scr_w * .11
    btn_y = (TOP_OFF + 46 / 2260 * ky) * scr_h
    pw, ph_ = scr_w * .4, scr_w * .12
    chip = 'background:#fff;box-shadow:0 1px 3px rgba(42,55,68,.12)'
    els.append(
        f'<div style="position:absolute;left:{sx}px;top:{sy}px;width:{scr_w}px;height:{scr_h}px;border-radius:{pr}px;'
        f'background:#F9F5ED;overflow:hidden;z-index:11">'
        f'<div style="position:absolute;left:{scr_w * .04}px;top:{btn_y}px;width:{btn}px;height:{btn}px;border-radius:50%;{chip};'
        f'padding:{btn * .26}px">{ICON["close"]}</div>'
        f'<div style="position:absolute;right:{scr_w * .04}px;top:{btn_y}px;width:{btn}px;height:{btn}px;border-radius:50%;{chip};'
        f'padding:{btn * .24}px">{ICON["more"]}</div>'
        f'<div style="position:absolute;left:{scr_w / 2 - pw / 2}px;top:{btn_y + btn / 2 - ph_ / 2}px;width:{pw}px;height:{ph_}px;'
        f'border-radius:{ph_}px;{chip};display:flex;align-items:center;justify-content:center;'
        f'font:600 {scr_w * .045}px var(--sans);color:#2A3744;letter-spacing:.04em">1 / 10</div>'
        + ('' if MOTION else
           f'<div class="ph" style="left:{card_x + card_w * .05}px;top:{card_y - scr_w * .03}px;width:{card_w * .9}px;height:{card_h}px;'
           f'border-radius:{CARD_R * scr_w}px;opacity:.8"><img src="{mc.ph("boba_hand")}"></div>'
           f'<div class="ph" style="left:{card_x}px;top:{card_y}px;width:{card_w}px;height:{card_h}px;border-radius:{CARD_R * scr_w}px;'
           f'box-shadow:0 {scr_w * .01}px {scr_w * .03}px rgba(42,55,68,.14)"><img src="{mc.ph("pug")}" style="object-position:42% 50%">'
           f'<div style="position:absolute;right:{scr_w * .055}px;bottom:{scr_w * .035}px;display:flex;gap:{scr_w * .036}px">'
           f'<div style="width:{ic}px;height:{ic}px">{ICON["heart"]}</div><div style="width:{ic}px;height:{ic}px">{ICON["expand"]}</div>'
           f'</div></div>')
        + '</div>')
    els.append(f'<div style="position:absolute;left:{pcx - scr_w * .15}px;top:{sy + scr_w * .03}px;width:{scr_w * .3}px;'
               f'height:{scr_w * .088}px;border-radius:{scr_w}px;background:#0D1116;z-index:12"></div>')
    # 相簿軌：從手機底部長出來、兩端出血到畫布外
    sp = ts * 1.167
    names, xo = around('dog', pcx - sp * .5, sp, -ts * 2, W + ts * 2)
    r_html, pos = rail(loc, names, xo, ry, ts, -ts, W + ts, MOTION['lit'] if MOTION else {'cake'},
                       f'0 2px 4px rgba(90,40,30,.14), 0 {ts * .3}px {ts * .6}px -{ts * .22}px rgba(90,40,30,.45)')
    els.append(r_html)
    # 上一張（生日）剛從手機裡被點進「生日」：縮小、正落進那一格
    tcx, ttop = pos['cake']
    fly = ts * 1.12
    if not MOTION:
        els.append(photo('bday_a', tcx + ts * .18, ttop - fly * .55, fly, 8, shadow=SHADOW['C_phone']))
        els.append(mc.SPARK.format(x=tcx + ts * .62, y=ttop - fly * 1.2, s=ts * .16, c='#F6C453'))
    META.update(mode='phone', ts=ts, sp=sp, pos=pos, phone=dict(
        clip=dict(x=sx, y=sy, w=scr_w, h=ry - sy, r=pr),
        card=dict(x=sx + card_x, y=sy + card_y, w=card_w, h=card_h, r=CARD_R * scr_w),
        back=dict(x=sx + card_x + card_w * .05, y=sy + card_y - scr_w * .03, w=card_w * .9, h=card_h, o=.8),
        icon=dict(size=ic, right=scr_w * .055, bottom=scr_w * .035, gap=scr_w * .036)))
    # 兩側：其他照片也正落進自己的相簿（安全區外）
    for name, album, size, rot in L['fallers']:
        if album in pos and not (f.sx0 - size * .6 < pos[album][0] < f.sx1 + size * .6):
            ax, ay = pos[album]
            els.append(photo(name, ax, ay - ts * .95, size, rot, z=24,
                             shadow='0 1px 3px rgba(42,55,68,.18), 0 22px 44px -14px rgba(42,55,68,.5)'))
    ma, mw = L['mascot']
    if ma in pos:
        els.append(mc.mascot_el(pos[ma][0], ry + ts * .04, mw))
    # 地板（軌道中線以下一塊品牌珊瑚）＋署名
    els.append(f'<div class="floor" style="top:{rmid}px"></div>')
    fs = L['sign']
    cy = (ry + ch + f.H) / 2
    els.append(f'<div class="sign lk-light" style="top:{cy - fs}px;height:{fs * 2}px;font-size:{fs}px;gap:{fs * .9}px">'
               f'{mc.lockup(mc.TEXT[loc], fs * 1.7, fs * 1.05, fs * .45)}<span class="dot"></span><span>{PROMISE[loc]}</span></div>')
    top_ = f.sy0 - (f.sh * .2 if L['lockup'] else 0)
    els.append(headline(loc, f.sx0, top_, (sx - bez) - f.sw * .06 - f.sx0, ry - ts * .12 - top_, *L['h1'],
                        ink='#2A3744', em='#C75F4E', lockup=L['lockup']))
    return f'<div class="board paperglow">' + '\n'.join(els) + '</div>'


BUILD = {'A_wall': design_a, 'B_poster': design_b, 'C_phone': design_c}


def render(design, placement, loc):
    f = Frame(placement)
    body = BUILD[design](placement, loc)
    html = mc.head(loc, f'{design} {placement} {loc}', f.H, mc.LOCKUP_CSS + CSS + C_CSS) + body + mc.FIT_JS + mc.FITW_JS + mc.tail(f.zoom)
    mc.BOARDS.mkdir(parents=True, exist_ok=True)
    board = mc.BOARDS / f'v3_{design}_{placement}_{loc}.html'
    board.write_text(html, encoding='utf-8')
    out = mc.OUT / loc / f'{design}_{placement}_{f.spec["w"]}x{f.spec["h"]}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    mc.chrome_shot(board, out, f.spec['w'], f.spec['h'])
    Image.open(out).convert('RGB').save(out, optimize=True)      # Apple：不能有透明通道
    print(f'✓ {out.relative_to(mc.REPO)}', flush=True)
    return out


def render_video(design, placement, loc, frames=None):
    """影片版（一張 3 秒、六張一輪＝18 秒、60fps、無縫循環）：Chrome 烤兩張底圖 —— 一張哪一格都沒亮、
    一張三個目標格都亮著，把亮格裁下來；Remotion 只動照片（A、B：沿路線排隊；C：手機裡的卡片飛出來）與亮格。"""
    global MOTION
    import json
    import os
    import shutil
    import subprocess
    comp, Wpx, Hpx = mc.VIDEO_SPECS[placement]
    f = Frame(placement)
    zoom = Wpx / W
    z = lambda v: v * zoom  # noqa: E731
    pub = mc.REMOTION / 'public' / 'creative'
    for d in ('photos', 'plates'):
        (pub / d).mkdir(parents=True, exist_ok=True)
    key = f'v3_{design}_{placement}_{loc}'
    plates = {}
    targets = {a for _, a, _ in mc.VIDEO_ITEMS}
    for tag, lit in (('plate', set()), ('lit', targets)):
        MOTION = {'lit': lit}
        META.clear()
        try:
            body = BUILD[design](placement, loc)
        finally:
            MOTION = None
        html = mc.head(loc, key, f.H, mc.LOCKUP_CSS + CSS + C_CSS) + body + mc.FIT_JS + mc.FITW_JS + mc.tail(zoom)
        board = mc.BOARDS / f'{key}_{tag}.html'
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text(html, encoding='utf-8')
        png = mc.BUILD / 'motion' / f'{key}_{tag}.png'
        png.parent.mkdir(parents=True, exist_ok=True)
        mc.chrome_shot(board, png, Wpx, Hpx)
        plates[tag] = Image.open(png).convert('RGB')
    meta = dict(META)
    plates['plate'].save(pub / 'plates' / f'{key}.png')
    for name, _, _ in mc.VIDEO_ITEMS:
        shutil.copy2(photos.OUT / f'{name}.jpg', pub / 'photos' / f'{name}.jpg')
    ts, sp, pos = meta['ts'], meta['sp'], meta['pos']
    items = []
    for n, a, p in mc.VIDEO_ITEMS:
        cx, top = pos[a]
        box = [round(z(v)) for v in (cx - sp / 2, top - ts * .1, cx + sp / 2, top + ts * 1.4)]
        lit_path = pub / 'plates' / f'{key}_{a}.png'
        plates['lit'].crop(box).save(lit_path)
        items.append(dict(photo=f'creative/photos/{n}.jpg', pos=p, album=a,
                          lit=dict(src=f'creative/plates/{key}_{a}.png', x=box[0], y=box[1], w=box[2] - box[0], h=box[3] - box[1]),
                          tx=z(cx), ty=z(top + ts / 2)))
    scale = lambda d: {k: (z(v) if k not in ('o', 'q', 'scale', 'rot') else v) for k, v in d.items()}  # noqa: E731
    scene = dict(mode=meta['mode'], placement=placement, loc=loc, zoom=zoom, plate=f'creative/plates/{key}.png',
                 shadow=shadow_css(design, zoom), ts=z(ts), items=items,
                 hero=scale(meta.get('hero', dict(x=0, y=0, size=1, rot=0))),
                 path=scale(meta.get('path', dict(x0=0, y0=0, qx=0, qy=0))),
                 slots=[dict(q=s_['q'], scale=s_['scale'], rot=s_['rot']) for s_ in sorted(meta.get('slots', []), key=lambda d: -d['q'])])
    if meta.get('entry'):
        scene['entry'] = meta['entry']
    if meta['mode'] == 'phone':
        scene['phone'] = {k: scale(v) for k, v in meta['phone'].items()}
    props = mc.BUILD / 'motion' / f'{key}.json'
    props.write_text(json.dumps(dict(scene=scene), ensure_ascii=False), encoding='utf-8')
    mc.TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(mc.TMP), TMP=str(mc.TMP))
    if frames:
        outs = []
        for fr in str(frames).split(','):
            out = mc.BUILD / 'stills' / f'{key}_{fr}.png'
            out.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(f'npx remotion still src/creative/index.ts {comp} "{out}" --props="{props}" --frame={fr} --log=error',
                           cwd=mc.REMOTION, shell=True, check=True, env=env)
            outs.append(out)
            print(f'✓ {out.relative_to(mc.REPO)}', flush=True)
        return outs
    out = mc.OUT / loc / f'{design}_{placement}_{Wpx}x{Hpx}.mp4'
    cmd = (f'npx remotion render src/creative/index.ts {comp} "{out}" --props="{props}" '
           f'--codec=h264 --crf=15 --pixel-format=yuv420p --image-format=jpeg --jpeg-quality=96 '
           f'--color-space=bt709 --concurrency=6 --log=error')
    subprocess.run(cmd, cwd=mc.REMOTION, shell=True, check=True, env=env)
    mc.finalize_video(out)
    print(f'✓ {out.relative_to(mc.REPO)}', flush=True)
    return out


def overview(locs):
    """總覽：每個方向一列（標題＋搜尋），每種語言一欄 → store_assets/creative/總覽_v3.jpg（給人看的，不上傳）"""
    h, gap = 260, 14
    rows = []
    for d in DESIGNS:
        for loc in locs:
            ims = []
            for p in PLACEMENTS:
                sp = mc.SPECS[p]
                im = Image.open(mc.OUT / loc / f'{d}_{p}_{sp["w"]}x{sp["h"]}.png').convert('RGB')
                ims.append(im.resize((round(im.size[0] * h / im.size[1]), h), Image.LANCZOS))
            rows.append(ims)
    per_row = len(locs)
    tile_w = sum(i.size[0] for i in rows[0]) + gap
    sheet = Image.new('RGB', (per_row * tile_w + gap, len(DESIGNS) * (h + gap) + gap), (236, 232, 224))
    for k, ims in enumerate(rows):
        x = gap + (k % per_row) * tile_w
        y = gap + (k // per_row) * (h + gap)
        for im in ims:
            sheet.paste(im, (x, y))
            x += im.size[0] + 4
    out = mc.OUT / '總覽_v3.jpg'
    sheet.save(out, quality=86)
    print(f'✓ {out.relative_to(mc.REPO)}')


def main(argv):
    designs = [a for a in argv if a in DESIGNS] or list(DESIGNS)
    places = [a for a in argv if a in PLACEMENTS] or list(PLACEMENTS)
    locs = [a for a in argv if a in mc.LOCALES] or mc.LOCALES
    photos.prep()
    if '--video' in argv:
        frames = next((a.split('=', 1)[1] for a in argv if a.startswith('--frames=')), None)
        for d in designs:
            for p in places:
                for loc in locs:
                    render_video(d, p, loc, frames)
        return
    for d in designs:
        for p in places:
            for loc in locs:
                render(d, p, loc)
    if designs == list(DESIGNS) and places == list(PLACEMENTS):
        overview(locs)


if __name__ == '__main__':
    main(sys.argv[1:])
