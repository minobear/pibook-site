#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Android 模擬器的系統列換成 iOS 的樣子 —— App Store 用的截圖與預覽影片。

為什麼有這支（2026-09-21 App Store 審查退件，Guideline 2.3.10）
──────────────────────────────────────────────────────────────
商店截圖與預覽影片都是在 Android 模擬器（Pixel 6、1080×2400）上實拍的。
畫框畫成 iPhone，框裡的狀態列卻是 Android 的：時間的字型、帶驚嘆號的 Wi-Fi、
三角形訊號、直立的電池。Apple 認定這是「非 iOS 的狀態列」，整批截圖退件。

做法
────
1. 把 Android 的時間、右上角圖示、底部手勢條「補掉」：只補圖示筆畫本身的像素，
   以框外一圈插值為初值、再用四鄰平均擴散。這一帶的背景幾乎都是素色；回憶頁是
   影片畫面、而且切換時內容會從狀態列底下經過 —— 只補筆畫才不會把經過的內容抹糊。
2. 照 iOS（Face ID 機型）的版位畫上時間、訊號、Wi-Fi、電池：時間在左耳、圖示在
   右耳，垂直置中對齊畫框上的動態島（`assets/phone.css` 的 `.phone::after`）。
3. 底部畫上 iOS 比例的 Home 指示條（134×5 pt）。
4. **顏色跟著 App 當下的狀態列走**：原本是深色圖示就畫黑的、淺色就畫白的。
   兩個平台吃的是同一份 `SystemUiOverlayStyle`，所以這正是同一頁在 iPhone 上的樣子。

⚠️ 時間的字型：iOS 用的是 SF Pro，Windows 上沒有，這裡用 Segoe UI Variable 的
Semibold（同屬新怪誕體，「9:41」四個字元幾乎分不出來）。

用法
────
  python ios_statusbar.py shots                  # 商店畫板用的 12 張 → <name>_hd_ios.jpg
  python ios_statusbar.py clips                  # （已停用：預覽影片 v2 起素材不含狀態列，見 DIRECTOR_SCRIPT.md P9）
  python ios_statusbar.py video IN.mp4 OUT.mp4   # 單獨處理一支錄影
  python ios_statusbar.py image IN OUT           # 單獨處理一張截圖
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
FFMPEG_DIR = HERE / 'remotion' / 'node_modules' / '@remotion' / 'compositor-win32-x64-msvc'
FONT = r'C:/Windows/Fonts/SegUIVar.ttf'

# ── 來源畫面 ────────────────────────────────────────────────────────────
W, H = 1080, 2400
SCREEN_PT = 390.0            # 畫框螢幕寬（CSS px ≈ pt）
K = W / SCREEN_PT            # 截圖像素 / pt

# Android 系統列在 1080×2400 上的位置（Pixel 6 模擬器、demo mode，含抗鋸齒，實測）
A_TIME = (52, 52, 113, 78)
A_ICONS = (892, 47, 1005, 80)
A_HANDLE = (398, 2363, 681, 2373)
PAD = 5                       # 補掉時往外多吃幾像素（JPEG 的漣漪與抗鋸齒邊）

# ── iOS 版位（pt，以 390 pt 寬的螢幕為準）──────────────────────────────
ISLAND_W = 92.0               # phone.css：.phone::after 寬 92
ISLAND_CY = 27.0              # 同上：top 26 − 邊框 12 + 高 26 / 2
EAR_CX = (SCREEN_PT - ISLAND_W) / 4          # 左耳中心 74.5
RIGHT_EAR_CX = SCREEN_PT - EAR_CX            # 右耳中心 315.5

TIME_PT = 17.0                # SF Pro Text Semibold 17
TIME_TRACK = -0.4

CELL_W, CELL_H = 17.0, 10.9   # 四格訊號
WIFI_R = 11.0                 # Wi-Fi 扇形半徑（寬 ≈ 15.6、高 11）
WIFI_HALF_ANGLE = 45.0
BAT_W, BAT_H = 24.5, 11.5     # 電池本體（外框 35%、電量 100%、電池蓋 40%）
BAT_CAP_GAP, BAT_CAP_W, BAT_CAP_H = 1.0, 1.35, 4.0
GAP = 5.0                     # 三個圖示之間

HOME_W, HOME_H = 134.0, 5.0   # Home 指示條

SS = 4                        # 超取樣倍數（抗鋸齒）
TOP_STRIP = 110               # 會被改到的頂部高度（px）
BOT_STRIP0 = 2340             # 會被改到的底部起點（px）


# ── 補洞 ────────────────────────────────────────────────────────────────

def _inpaint(a, box, pad=PAD):
    """用框外一圈像素往內插值，把框裡的東西抹掉。a：H×W×3 float32，就地修改。

    垂直與水平各插一次，依「離哪一邊比較近」加權 —— 素色背景兩者一樣，
    影片畫面則以離得近的那一邊為主，不會拉出條紋。
    """
    x0, y0, x1, y1 = box
    x0 -= pad
    y0 -= pad
    x1 += pad
    y1 += pad
    h = y1 - y0 + 1
    w = x1 - x0 + 1
    top = a[y0 - 3:y0, x0:x1 + 1].mean(axis=0)
    bot = a[y1 + 1:y1 + 4, x0:x1 + 1].mean(axis=0)
    left = a[y0:y1 + 1, x0 - 3:x0].mean(axis=1)
    right = a[y0:y1 + 1, x1 + 1:x1 + 4].mean(axis=1)
    ty = (np.arange(h, dtype=np.float32) + 1) / (h + 1)
    tx = (np.arange(w, dtype=np.float32) + 1) / (w + 1)
    v = top[None] * (1 - ty)[:, None, None] + bot[None] * ty[:, None, None]
    hz = left[:, None] * (1 - tx)[None, :, None] + right[:, None] * tx[None, :, None]
    dy = np.minimum(np.arange(h) + 1, h - np.arange(h)).astype(np.float32)
    dx = np.minimum(np.arange(w) + 1, w - np.arange(w)).astype(np.float32)
    wv = (1.0 / dy)[:, None]
    wh = (1.0 / dx)[None, :]
    a[y0:y1 + 1, x0:x1 + 1] = (v * wv[..., None] + hz * wh[..., None]) / (wv + wh)[..., None]


def _lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def glyph_mask(a):
    """Android 狀態列圖示「筆畫本身」的位置（TOP_STRIP × W 的布林陣列）。

    只補筆畫、不補整個框：回憶頁上下切換時，畫面內容會從狀態列底下經過，
    整框補掉會連經過的內容一起抹糊。背景是素色時，兩種做法的結果一樣。
    """
    lum = _lum(a[:TOP_STRIP].astype(np.float32))
    mask = np.zeros((TOP_STRIP, W), bool)
    for x0, y0, x1, y1 in (A_TIME, A_ICONS):
        ring = np.concatenate([
            lum[y0 - 9:y0 - 4, x0:x1 + 1].ravel(),
            lum[y1 + 5:y1 + 10, x0:x1 + 1].ravel(),
        ])
        bg = float(np.median(ring))
        inner = lum[y0 - 2:y1 + 3, x0 - 2:x1 + 3]
        contrast = max(bg - float(np.percentile(inner, 3)), float(np.percentile(inner, 97)) - bg)
        # 門檻跟著對比走：素色背景上抓得到最淡的抗鋸齒邊，影片背景上不把紋理當成筆畫
        mask[y0 - 2:y1 + 3, x0 - 2:x1 + 3] |= np.abs(inner - bg) > max(10.0, contrast * 0.2)
    # 抗鋸齒的淡邊與 JPEG 漣漪：往外長 2 像素
    grown = Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))
    return np.asarray(grown) > 0


def _fill(top, mask, guess, box, pad=PAD + 3, iters=150):
    """只補 mask 裡的像素：以框外插值為初值，再用四鄰平均反覆擴散收斂。"""
    x0, y0, x1, y1 = box
    ys = slice(y0 - pad, y1 + pad + 1)
    xs = slice(x0 - pad, x1 + pad + 1)
    m = mask[ys, xs]
    if not m.any():
        return
    r = top[ys, xs].copy()
    r[m] = guess[ys, xs][m]
    for _ in range(iters):
        avg = (np.roll(r, 1, 0) + np.roll(r, -1, 0) + np.roll(r, 1, 1) + np.roll(r, -1, 1)) * 0.25
        r[m] = avg[m]
    top[ys, xs] = r


def glyph_tone(a):
    """Android 狀態列的圖示是深色還是淺色：'dark' / 'light' / None（分不出來）。"""
    lum = _lum(a)
    votes = []
    for x0, y0, x1, y1 in (A_TIME, A_ICONS):
        inner = lum[y0:y1 + 1, x0:x1 + 1]
        ring = np.concatenate([
            lum[y0 - 9:y0 - 4, x0:x1 + 1].ravel(),
            lum[y1 + 5:y1 + 10, x0:x1 + 1].ravel(),
        ])
        bg = float(np.median(ring))
        d_dark = bg - float(np.percentile(inner, 3))
        d_light = float(np.percentile(inner, 97)) - bg
        if max(d_dark, d_light) >= 18:
            votes.append(('light' if d_light > d_dark else 'dark', max(d_dark, d_light)))
    if not votes:
        return None
    return max(votes, key=lambda v: v[1])[0]


def handle_color(a):
    """Android 手勢條的顏色；這一格沒有手勢條（沉浸式畫面）就回 None。"""
    x0, y0, x1, y1 = A_HANDLE
    core = a[y0 + 3:y1 - 2, x0 + 40:x1 - 40].reshape(-1, 3)
    around = np.concatenate([
        a[y0 - 9:y0 - 5, x0 + 40:x1 - 40].reshape(-1, 3),
        a[y1 + 5:y1 + 9, x0 + 40:x1 - 40].reshape(-1, 3),
    ])
    c = np.median(core, axis=0)
    bg = np.median(around, axis=0)
    if abs(float(_lum(c[None])[0]) - float(_lum(bg[None])[0])) < 15:
        return None
    return c


# ── iOS 圖示（每種顏色只畫一次）───────────────────────────────────────

def _time_mask(s):
    font = ImageFont.truetype(FONT, size=round(TIME_PT * s))
    font.set_variation_by_axes([600, 17])
    text = '9:41'
    pad = round(TIME_PT * s)
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + TIME_TRACK * s * (len(text) - 1)
    m = Image.new('L', (round(total) + pad * 2, pad * 3), 0)
    d = ImageDraw.Draw(m)
    x = pad
    for ch, adv in zip(text, widths):
        d.text((x, pad), ch, font=font, fill=255)
        x += adv + TIME_TRACK * s
    arr = np.asarray(m)
    ys, xs = np.nonzero(arr > 0)
    return m.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def _wifi_mask(s):
    """iOS 的 Wi-Fi：一個小扇形 + 兩道弧，角都是圓的（先畫尖角、再模糊＋二值化收圓）。"""
    half = np.radians(WIFI_HALF_ANGLE)
    wpt = 2 * WIFI_R * np.sin(half)
    margin = 2.0
    size = (round((wpt + margin * 2) * s), round((WIFI_R + margin * 2) * s))
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    apex = (margin + wpt / 2, margin + WIFI_R)
    bands = [(0.0, 3.55), (4.95, 7.35), (8.65, WIFI_R)]
    ts = np.linspace(-half, half, 64)
    for r0, r1 in bands:
        outer = [(apex[0] + r1 * np.sin(t), apex[1] - r1 * np.cos(t)) for t in ts]
        if r0 == 0:
            inner = [apex]
        else:
            inner = [(apex[0] + r0 * np.sin(t), apex[1] - r0 * np.cos(t)) for t in ts[::-1]]
        d.polygon([(x * s, y * s) for x, y in outer + inner], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.5 * s)).point(lambda v: 255 if v >= 128 else 0)
    return m, margin


def _statusbar_alpha():
    """整條頂部的 alpha（0..1，float32，TOP_STRIP × W）。"""
    s = K * SS
    full = np.zeros((TOP_STRIP * SS, W * SS), np.float32)

    def paste(mask, left_px, top_px, weight=1.0):
        arr = np.asarray(mask, np.float32) / 255.0 * weight
        x0, y0 = round(left_px), round(top_px)
        h, w = arr.shape
        region = full[y0:y0 + h, x0:x0 + w]
        np.maximum(region, arr[:region.shape[0], :region.shape[1]], out=region)

    cy = ISLAND_CY * s

    # 時間：墨跡框置中在左耳中心
    tm = _time_mask(s)
    paste(tm, EAR_CX * s - tm.width / 2, cy - tm.height / 2)

    # 右側三個圖示，整組置中在右耳
    wifi_w = 2 * WIFI_R * np.sin(np.radians(WIFI_HALF_ANGLE))
    bat_total = BAT_W + BAT_CAP_GAP + BAT_CAP_W
    group = CELL_W + GAP + wifi_w + GAP + bat_total
    x = RIGHT_EAR_CX - group / 2

    # 訊號：四格，由矮到高，底部對齊
    cell = Image.new('L', (round((CELL_W + 2) * s), round((CELL_H + 2) * s)), 0)
    dc = ImageDraw.Draw(cell)
    bar_w = 3.0
    bar_gap = (CELL_W - bar_w * 4) / 3
    for i, bh in enumerate((3.9, 6.2, 8.6, CELL_H)):
        bx = 1 + i * (bar_w + bar_gap)
        dc.rounded_rectangle(
            [bx * s, (1 + CELL_H - bh) * s, (bx + bar_w) * s - 1, (1 + CELL_H) * s - 1],
            radius=0.9 * s, fill=255)
    paste(cell, (x - 1) * s, cy - (CELL_H / 2 + 1) * s)
    x += CELL_W + GAP

    # Wi-Fi
    wm, margin = _wifi_mask(s)
    paste(wm, (x - margin) * s, cy - (WIFI_R / 2 + margin) * s)
    x += wifi_w + GAP

    # 電池：外框 35%、電量滿格 100%、電池蓋 40%
    bw = round((bat_total + 2) * s)
    bh = round((BAT_H + 2) * s)
    body = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(body).rounded_rectangle(
        [1 * s, 1 * s, (1 + BAT_W) * s - 1, (1 + BAT_H) * s - 1],
        radius=3.6 * s, outline=255, width=round(1.0 * s))
    level = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(level).rounded_rectangle(
        [(1 + 2.0) * s, (1 + 2.0) * s, (1 + BAT_W - 2.0) * s - 1, (1 + BAT_H - 2.0) * s - 1],
        radius=1.7 * s, fill=255)
    cap = Image.new('L', (bw, bh), 0)
    cap_x = 1 + BAT_W + BAT_CAP_GAP
    ImageDraw.Draw(cap).rounded_rectangle(
        [cap_x * s, (1 + BAT_H / 2 - BAT_CAP_H / 2) * s,
         (cap_x + BAT_CAP_W) * s - 1, (1 + BAT_H / 2 + BAT_CAP_H / 2) * s - 1],
        radius=0.65 * s, fill=255)
    top_px = cy - (BAT_H / 2 + 1) * s
    left_px = (x - 1) * s
    paste(body, left_px, top_px, 0.35)
    paste(level, left_px, top_px, 1.0)
    paste(cap, left_px, top_px, 0.40)

    img = Image.fromarray((full * 255).round().astype(np.uint8), 'L')
    img = img.resize((W, TOP_STRIP), Image.BOX)
    return np.asarray(img, np.float32) / 255.0


def _home_alpha():
    """底部 Home 指示條的 alpha（float32，(H − BOT_STRIP0) × W）。"""
    s = K * SS
    hgt = H - BOT_STRIP0
    m = Image.new('L', (W * SS, hgt * SS), 0)
    x0, y0, x1, y1 = A_HANDLE
    cx = (x0 + x1 + 1) / 2 * SS
    cy = ((y0 + y1 + 1) / 2 - BOT_STRIP0) * SS
    hw = HOME_W / 2 * s
    hh = HOME_H / 2 * s
    ImageDraw.Draw(m).rounded_rectangle(
        [cx - hw, cy - hh, cx + hw - 1, cy + hh - 1], radius=hh, fill=255)
    m = m.resize((W, hgt), Image.BOX)
    return np.asarray(m, np.float32) / 255.0


_TOP_ALPHA = None
_HOME_ALPHA = None
TONE_RGB = {'dark': np.array([0, 0, 0], np.float32),
            'light': np.array([255, 255, 255], np.float32)}


def iosify(a, tone=None, mask=None, handle=None, detect=True):
    """就地把一格畫面（H×W×3 float32）的系統列換成 iOS 樣式。

    tone / mask / handle 由呼叫端給（影片：整支用同一組，見 process_video）；
    detect=True 時從這一格自己判斷（截圖）。
    """
    global _TOP_ALPHA, _HOME_ALPHA
    if _TOP_ALPHA is None:
        _TOP_ALPHA = _statusbar_alpha()
        _HOME_ALPHA = _home_alpha()
    if detect:
        tone = glyph_tone(a) or 'dark'
        mask = glyph_mask(a)
        handle = handle_color(a)
    top = a[:TOP_STRIP]
    guess = top.copy()
    for box in (A_TIME, A_ICONS):
        _inpaint(guess, box)
    for box in (A_TIME, A_ICONS):
        _fill(top, mask, guess, box)
    col = TONE_RGB[tone]
    al = _TOP_ALPHA[..., None]
    a[:TOP_STRIP] = a[:TOP_STRIP] * (1 - al) + col * al
    if handle is not None:
        _inpaint(a, A_HANDLE, pad=3)
        al = _HOME_ALPHA[..., None]
        a[BOT_STRIP0:] = a[BOT_STRIP0:] * (1 - al) + np.asarray(handle, np.float32) * al
    return a


# ── 截圖 ────────────────────────────────────────────────────────────────

# 商店畫板（press/0*.html、press/en/0*.html）用到的那 12 張
SHOTS = ['home', 'review', 'compress', 'similar', 'memory', 'browse_photos']


def process_image(src, dst):
    im = Image.open(src).convert('RGB')
    if im.size != (W, H):
        raise SystemExit(f'{src}: 尺寸 {im.size}，這支只認 {W}×{H} 的 Pixel 6 截圖')
    a = np.asarray(im, np.float32).copy()
    iosify(a)
    Image.fromarray(a.clip(0, 255).round().astype(np.uint8)).save(
        dst, quality=95, subsampling=0, optimize=True)


def cmd_shots():
    base = SITE / 'assets' / 'shots'
    for sub in ('', 'en'):
        for name in SHOTS:
            src = base / sub / f'{name}_hd.jpg'
            dst = base / sub / f'{name}_hd_ios.jpg'
            process_image(src, dst)
            print('✓', dst.relative_to(SITE))


# ── 影片 ────────────────────────────────────────────────────────────────

def _ff(name):
    # ⚠️ Remotion 附的 ffmpeg 是精簡版，沒有 rawvideo 的讀寫 —— 逐格處理非用完整版不可。
    #    ffmpeg 用 imageio-ffmpeg 帶的那一份；它不附 ffprobe，探尺寸用 Remotion 的就夠。
    if name == 'ffmpeg':
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return 'ffmpeg'
    exe = FFMPEG_DIR / f'{name}.exe'
    return str(exe) if exe.exists() else name


def _frames(src, vf=None, rows=None):
    """逐格讀出 RGB（rows=(y0, h) 時只裁那一段，第一輪判斷顏色用）。"""
    args = [_ff('ffmpeg'), '-v', 'error', '-i', str(src)]
    h = H
    if rows is not None:
        y0, h = rows
        args += ['-vf', f'crop={W}:{h}:0:{y0}']
    args += ['-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    size = W * h * 3
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, W, 3)
    p.wait()


def _mask_quality(a, tone):
    """這一格適不適合拿來量 Android 圖示的筆畫：圖示夠清楚、框外那一圈夠素、
    框裡沒有別的東西經過。

    三個條件缺一不可（回憶影片踩過兩個）：
    - 只看「素不素」會挑到全黑的那幾格 —— 背景很素，但深色圖示疊在深色背景上
      幾乎看不見，量出來是空的。
    - 只看「對比」會挑到切換中的那幾格 —— 白色的字從狀態列底下經過，對比最高，
      量到的卻是那行字。所以只算「跟圖示同一個方向」的對比，反方向的要扣分。
    """
    lum = _lum(a[:TOP_STRIP].astype(np.float32))
    total = 0.0
    for x0, y0, x1, y1 in (A_TIME, A_ICONS):
        ring = np.concatenate([
            lum[y0 - 9:y0 - 4, x0:x1 + 1].ravel(),
            lum[y1 + 5:y1 + 10, x0:x1 + 1].ravel(),
        ])
        bg = float(np.median(ring))
        inner = lum[y0:y1 + 1, x0:x1 + 1]
        darker = bg - float(np.percentile(inner, 3))
        lighter = float(np.percentile(inner, 97)) - bg
        same, other = (darker, lighter) if tone == 'dark' else (lighter, darker)
        total += same - 2.0 * float(ring.std()) - 2.0 * max(0.0, other)
    return total


def _smooth(values, fallback, radius=4):
    """逐格判斷的結果會在轉場那幾格抖動 —— 前後各看幾格取多數，缺值補最近的。"""
    n = len(values)
    known = [i for i, v in enumerate(values) if v is not None]
    filled = []
    for i in range(n):
        if values[i] is not None:
            filled.append(values[i])
        elif known:
            j = min(known, key=lambda k: abs(k - i))
            filled.append(values[j])
        else:
            filled.append(fallback)
    out = []
    for i in range(n):
        win = filled[max(0, i - radius):i + radius + 1]
        out.append(max(set(win), key=win.count))
    return out


def process_video(src, dst):
    probe = subprocess.run(
        [_ff('ffprobe'), '-v', 'error', '-select_streams', 'v', '-show_entries',
         'stream=width,height,r_frame_rate', '-of', 'csv=p=0', str(src)],
        capture_output=True, text=True, check=True).stdout.strip().split(',')
    w, h, rate = int(probe[0]), int(probe[1]), probe[2]
    if (w, h) != (W, H):
        raise SystemExit(f'{src}: 尺寸 {w}×{h}，這支只認 {W}×{H} 的 Pixel 6 錄影')

    # 第一輪：只讀頂部與底部。
    #
    # 狀態列的深淺是頁面主題決定的，不會隨內容變 —— 逐格判斷反而會被「從狀態列
    # 底下滑過的內容」騙到（回憶頁上下切換那幾格，白色的字與圖示經過，就被當成
    # 淺色圖示）。所以整支影片取多數決、用同一個顏色。
    # Android 圖示的筆畫位置同理：挑最適合量的五格（見 _mask_quality）各量一次、
    # 過半數都認定是筆畫的才算，整支共用。同一支錄影的系統列不會變，但不同錄影
    # 可能少一個圖示（回憶那支沒有訊號三角形），所以不能拿截圖量到的直接套用。
    votes = {'dark': 0, 'light': 0}
    best = {'dark': [], 'light': []}   # 各自的 (quality, 頂部條)
    frames = 0
    for top in _frames(src, rows=(0, TOP_STRIP)):
        frames += 1
        t = glyph_tone(top)
        if t:
            votes[t] += 1
        for k, pool in best.items():
            pool.append((_mask_quality(top, k), frames, top.copy()))
            pool.sort(key=lambda b: -b[0])
            del pool[5:]
    tone = 'light' if votes['light'] > votes['dark'] else 'dark'
    count = np.zeros((TOP_STRIP, W), np.int32)
    for _, _, top in best[tone]:
        count += glyph_mask(top)
    mask = count >= 3
    handles = []
    for bot in _frames(src, rows=(2340, 60)):
        pad = np.zeros((H, W, 3), np.float32)
        pad[2340:] = bot
        c = handle_color(pad)
        handles.append(None if c is None else tuple(int(v) for v in c))
    present = _smooth([None if c is None else True for c in handles], False)

    # 第二輪：整格讀進來、改好、送去編碼
    enc = subprocess.Popen(
        [_ff('ffmpeg'), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', rate, '-i', '-',
         '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p',
         '-r', rate, str(dst)],
        stdin=subprocess.PIPE)
    last_handle = None
    n = 0
    for i, frame in enumerate(_frames(src)):
        a = frame.astype(np.float32)
        c = handles[i] if i < len(handles) else None
        if c is not None:
            last_handle = c
        hc = (c or last_handle) if (i < len(present) and present[i]) else None
        iosify(a, tone=tone, mask=mask, handle=hc, detect=False)
        enc.stdin.write(a.clip(0, 255).round().astype(np.uint8).tobytes())
        n += 1
    enc.stdin.close()
    if enc.wait() != 0 or n == 0 or n != frames:
        raise SystemExit(f'{src}: 處理失敗（讀到 {n} 格、第一輪 {frames} 格）')
    print(f'✓ {dst}（{n} 格；圖示 {tone}，逐格投票 {votes}）')


CLIPS = ['review', 'album', 'similar', 'compress', 'memory', 'library']


def cmd_clips():
    # 2026-10-03 起預覽影片 v2 的素材在錄影時就裁掉了系統列（DIRECTOR_SCRIPT.md P9），不再需要換狀態列。
    raise SystemExit('預覽影片 v2 不再需要換狀態列：素材本來就不含系統列（見 DIRECTOR_SCRIPT.md P9）')
    src_dir = HERE / 'remotion' / 'public' / 'clips'
    out_dir = src_dir / 'ios'
    out_dir.mkdir(exist_ok=True)
    for name in CLIPS:
        process_video(src_dir / f'{name}.mp4', out_dir / f'{name}.mp4')


def main():
    # Windows 主控台預設 cp950，印不出 ✓
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == 'shots':
        cmd_shots()
    elif cmd == 'clips':
        cmd_clips()
    elif cmd == 'video' and len(sys.argv) == 4:
        process_video(Path(sys.argv[2]), Path(sys.argv[3]))
    elif cmd == 'image' and len(sys.argv) == 4:
        process_image(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
