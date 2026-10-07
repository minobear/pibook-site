#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""App Store 創意素材（iOS 27 起的「標題和搜尋結果」）—— 產生畫板、渲染成上傳用的 PNG。

規格（App Store Connect → 參考資料 → Creative assets specifications，2026-10-06 讀）：

| 版位 | 比例 | 尺寸 | 格式 | 安全區（Apple 官方 Sketch 範本） |
|---|---|---|---|---|
| 產品頁標題 header | 21:9 | 3840×1646 | jpg/png | x 1097–2743、y 493–1154（置中 1646×661） |
| 搜尋結果 search | 3:2 | 3840×2560（最小 1920×1280） | jpg/png | x 836–3004、y 765–1795（置中 2168×1030） |
| 通用 universal（兩個版位共用一張） | 16:9 | 5244×2950 | **只收 png** | x 1921–3323、y 660–1622（偏上，不是置中） |

安全區以外的地方在某些裝置（iPad 橫向、大螢幕）看得到、在 iPhone 直向會被裁掉或被
App 名稱與「取得」按鈕蓋住 —— 所以**字與主角一律放在安全區內**，區外只放「看到更好、
看不到也不缺」的東西。圖片不能有透明通道（Apple 規定）。

畫面（v2，2026-10-06）：App 底部那條相簿軌放大成橫跨畫布的「相簿架」（像素圖示與 App 是同一份原稿，
pixel_icons.py 直接讀 Dart），巴哥犬正飛進「狗狗」那一格、後面還排著兩張，皮皮趴在軌道上探頭。
字只講兩個動作：點一下歸檔、滑一下刪除。底色是 App 圖示的珊瑚紅（夜色、紙色是 A/B 測試用的備案）。

用法：
  python make_creative.py                      # 全部版位 × 全部語言（珊瑚版），順便出總覽圖
  python make_creative.py header zh-Hant       # 只出某幾個（版位、語言可混著寫）
  python make_creative.py --preview ...        # 另外輸出「安全區」檢查圖（build/creative/preview/，不上傳）
  python make_creative.py --night / --paper    # 夜色版／紙色版（產品頁 A/B 測試的備案；可與 --coral 一起寫）
  python make_creative.py --video [版位] [語言] # 影片版（header、search；Remotion，見 render_video；主題旗標同上）
  python make_creative.py --video header en --frames=38,60   # 只出幾格靜態圖試看（build/creative/stills/）
  python make_creative.py --finalize           # 只重做影片的配樂與色彩標記

輸出：store_assets/creative/<語言>/<版位>_<寬>x<高>.png（.mp4）
畫板（中間產物）：build/creative/boards/*.html（主 repo 的 build/ 已忽略）
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding='utf-8')   # Windows 主控台預設 cp950，印不出 ✓
import photos  # noqa: E402

REPO = HERE.parents[2]
SITE = HERE.parents[1]
BUILD = REPO / 'build' / 'creative'
BOARDS = BUILD / 'boards'
OUT = REPO / 'store_assets' / 'creative'
CHROME = r'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
REMOTION = SITE / 'press' / 'remotion'
# 影片版（Remotion）：版位 → (composition, 寬, 高)。搜尋結果不用最大的 3840×2560 —— 它超過 H.264
# level 5.2 的畫面上限（9,437,184 像素），不少解碼器直接拒收；3240×2160 仍是 3:2、在 Apple 的範圍內。
VIDEO_SPECS = {'header': ('CreativeHeader', 3840, 1646), 'search': ('CreativeSearch', 3240, 2160)}
# 暫存（Chrome 的一次性設定檔、Remotion 的影格）一律放這裡、用完就刪：系統暫存在 C 槽，
# 一支 4K 影片的影格就要 1.3GB，2026-10-06 把 C 槽寫滿過一次（ENOSPC，渲染到一半中斷）。
TMP = BUILD / 'tmp'

SPECS = {
    'header': dict(w=3840, h=1646, safe=(1097, 493, 2743, 1154)),
    'search': dict(w=3840, h=2560, safe=(836, 765, 3004, 1795)),
    'universal': dict(w=5244, h=2950, safe=(1921, 660, 3323, 1622)),
}
# 畫板以「寬 1920」為設計單位，渲染時用 zoom 放大到實際像素（照片與文字都在最終解析度上點陣化）
UNIT_W = 1920
LOCALES = ['zh-Hant', 'zh-Hans', 'en', 'ja', 'ko']

FONT_LINKS = {
    'zh-Hant': 'family=Noto+Sans+TC:wght@500;700&family=Noto+Serif+TC:wght@600;700;900',
    'zh-Hans': 'family=Noto+Sans+SC:wght@500;700&family=Noto+Serif+SC:wght@600;700;900',
    'en': 'family=Noto+Sans:wght@500;700&family=Noto+Serif:wght@600;700;900&family=Noto+Serif+TC:wght@700',
    'ja': 'family=Noto+Sans+JP:wght@500;700&family=Noto+Serif+JP:wght@600;700;900',
    # 韓文沒有宋體（使用者裁示：橫畫在明朝是髮絲級）→ 標題也用黑體
    'ko': 'family=Noto+Sans+KR:wght@500;700;800;900',
}
FONT_VARS = {
    'zh-Hant': ('"Noto Sans TC"', '"Noto Serif TC"'),
    'zh-Hans': ('"Noto Sans SC"', '"Noto Serif SC"'),
    'en': ('"Noto Sans"', '"Noto Serif"'),
    'ja': ('"Noto Sans JP"', '"Noto Serif JP"'),
    'ko': ('"Noto Sans KR"', '"Noto Sans KR"'),
}

# 文案：沿用商店截圖與 App 裡已經定稿的譯法（make_boards.py「滑一下 就整理好一張」那一句），不另外發明。
TEXT = {
    'zh-Hant': dict(wordmark='拍簿', wordmark_sub='PIBOOK'),
    'zh-Hans': dict(wordmark='拍簿', wordmark_sub='PIBOOK'),
    'en': dict(wordmark='Pibook', wordmark_sub=''),
    'ja': dict(wordmark='Pibook', wordmark_sub=''),
    'ko': dict(wordmark='Pibook', wordmark_sub=''),
}


def furl(p):
    return 'file:///' + str(p).replace('\\', '/')


MOTION = False   # True＝影片版的底圖：整個場景照畫，只是不畫會動的照片、不點亮任何一格（交給 Remotion）
MOTION_LIT = set()  # 影片版第二張底圖：只點亮這幾格（裁下來給 Remotion 疊在底圖上淡入淡出）


def ph(name):
    return furl(photos.OUT / f'{name}.jpg')


def icon_url():
    return furl(SITE / 'assets' / 'app_icon.png')


def head(loc, title, unit_h, extra_css=''):
    sans, serif = FONT_VARS[loc]
    return f'''<!DOCTYPE html>
<html lang="{loc}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{FONT_LINKS[loc]}&display=block">
<style>
:root {{
  --canvas: #FBF7F0; --paper: #FFFFFF; --sunken: #F1ECE3; --divider: #E6DED1;
  --ink: #2A3744; --ink-soft: #5C6A78; --ink-fade: #98A3AE;
  --blue: #5B7A92; --blue-deep: #3F5A72; --blue-soft: #A9C0D2;
  --coral: #E8806E; --coral-deep: #C75F4E; --gold: #F6C453;
  --sans: {sans}, "Noto Sans TC", system-ui, sans-serif;
  --serif: {serif}, "Noto Serif TC", Georgia, serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: {UNIT_W}px; height: {unit_h}px; overflow: hidden; background: var(--canvas); }}
body {{ font-family: var(--sans); color: var(--ink); -webkit-font-smoothing: antialiased; }}
.board {{ position: relative; width: {UNIT_W}px; height: {unit_h}px; overflow: hidden; background: var(--canvas); }}
img {{ display: block; }}
{extra_css}
</style>
</head>
<body>
'''


def tail(zoom):
    # zoom 寫在最後：所有座標都是設計單位，整塊等比放大到輸出像素
    return f'''<script>document.documentElement.style.zoom = {zoom};</script>
</body>
</html>
'''


# ───────────────────────────── 共用元件 ─────────────────────────────

LOCKUP_CSS = '''
.lockup { display: inline-flex; align-items: center; }
.lockup img { box-shadow: 0 1px 2px rgba(42,55,68,.16), 0 12px 24px -12px rgba(42,55,68,.45); }
.lockup .wm { font-family: var(--serif); font-weight: 700; letter-spacing: .04em; color: var(--ink); line-height: 1; }
.lockup .wm small { font-size: .5em; letter-spacing: .26em; color: var(--ink-fade); margin-left: .55em; font-weight: 600; }
'''


def lockup(t, icon_px, word_px, gap):
    sub = f'<small>{t["wordmark_sub"]}</small>' if t['wordmark_sub'] else ''
    return (f'<div class="lockup" style="gap:{gap}px">'
            f'<img src="{icon_url()}" style="width:{icon_px}px;height:{icon_px}px;'
            f'border-radius:{icon_px * .225}px">'
            f'<span class="wm" style="font-size:{word_px}px">{t["wordmark"]}{sub}</span></div>')


NIGHT_CSS = '''
/* 夜色版：底色取自截圖「回憶」那張的夜藍（#24374C → #1E2F40）、字改米白、強調色改金
   （與 Google Play 主視覺同一套）。照片的白邊在深底上自己會跳出來 —— 陰影加深，不加任何光暈。 */
html, body { background: #1C2A37; }
.board.night { background: linear-gradient(170deg, #26394D 0%, #1E2D3C 55%, #1A2733 100%); }
.board.night::before { background:
    radial-gradient(ellipse 30% 70% at 92% 50%, rgba(232,128,110,.10), transparent 70%),
    radial-gradient(ellipse 30% 70% at 8% 50%, rgba(142,174,198,.12), transparent 70%); }
.night h1 { color: #F4F1EA; }
.night h1 em { color: #F6C453; }
.night .lockup .wm { color: #F4F1EA; }
.night .lockup .wm small { color: rgba(244,241,234,.55); }
'''

SPARK = ('<svg class="spark" style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;z-index:40" '
         'viewBox="0 0 24 24"><path d="M12 0C13 7 17 11 24 12 17 13 13 17 12 24 11 17 7 13 0 12 7 11 11 7 12 0Z" '
         'fill="{c}"/></svg>')

FIT_JS = '''<script>
/* 標題自動縮到放得下（像 Flutter 的 FittedBox）：五種語言字寬不同，固定字級總有一種會撞到卡片。
   只縮不放大，下限是原字級的 70% —— 再小就該回頭改文案，不是硬塞；縮不下去就畫紅框，檢查圖一眼看得到。 */
document.fonts.ready.then(function () {
  document.querySelectorAll('.fit').forEach(function (el) {
    var fs = parseFloat(getComputedStyle(el).fontSize), min = fs * .7;
    while (el.scrollWidth > el.clientWidth + .5 && fs > min) { fs -= .5; el.style.fontSize = fs + 'px'; }
    if (el.scrollWidth > el.clientWidth + .5) { el.style.outline = '6px solid red'; }
  });
});
</script>
'''

SCENE_META = {}


# ═══════════════════════════════════ v2：相簿軌是主角 ═══════════════════════════════════
# 2026-10-06 使用者第二輪：「左邊整理好的圖庫、右邊亂丟的照片」沒人看得懂；只滑卡保留跟滿街的滑卡 App
# 一模一樣 —— 拍簿跟別人不一樣的是「點一下就收進相簿」與自訂的像素相簿圖示。所以 v2：
# App 底部那條相簿軌放大成一條橫跨整個畫布的「相簿架」，照片正飛進其中一格（App 裡點相簿的那一下：
# 那一格變藍、彈一下、照片縮小飛進去）。字只講兩個動作：點一下歸檔、滑一下刪除。

import math  # noqa: E402

import pixel_icons  # noqa: E402

# 相簿架上的相簿（左→右）。中間那幾本（家人 旅行 美食 狗狗 生日 最愛 貓咪）是示範圖庫真的有的，
# 也是落在 iPhone 看得到的那一條裡；兩側是一般人常建的相簿，讓 iPad 上看得到「圖示可以自己挑」的豐富。
RAIL_ORDER = ['tent', 'city', 'camera', 'beach', 'coffee', 'baby', 'friends', 'family', 'plane', 'food', 'dog',
              'cake', 'heart', 'cat', 'flower', 'mountain', 'music', 'dessert', 'gift', 'ball', 'home']
LOC_IDX = {'zh-Hant': 0, 'zh-Hans': 1, 'en': 2, 'ja': 3, 'ko': 4}
# 名稱：示範圖庫那八本照 shoot_locale.ALBUMS（App 截圖裡的字），其餘照 CLAUDE.md 譯名表的語氣補
ALBUM_NAMES = {
    'family': ['家人', '家人', 'Family', '家族', '가족'],
    'plane': ['旅行', '旅行', 'Travel', '旅行', '여행'],
    'food': ['美食', '美食', 'Food', 'ごはん', '음식'],
    'heart': ['最愛', '最爱', 'Favourites', 'お気に入り', '즐겨찾기'],
    'dog': ['狗狗', '狗狗', 'Dogs', '犬', '강아지'],
    'cake': ['生日', '生日', 'Birthday', '誕生日', '생일'],
    'cat': ['貓咪', '猫咪', 'Cats', '猫', '고양이'],
    'flower': ['花草', '花草', 'Flowers', '花', '꽃'],
    'coffee': ['咖啡', '咖啡', 'Coffee', 'カフェ', '카페'],
    'baby': ['寶寶', '宝宝', 'Baby', '赤ちゃん', '아기'],
    'friends': ['好友', '好友', 'Friends', '友だち', '친구'],
    'beach': ['海邊', '海边', 'Beach', '海', '바다'],
    'camera': ['攝影', '摄影', 'Photos', '写真', '사진'],
    'city': ['城市', '城市', 'City', '街歩き', '도시'],
    'tent': ['露營', '露营', 'Camping', 'キャンプ', '캠핑'],
    'mountain': ['登山', '登山', 'Hiking', '山歩き', '등산'],
    'music': ['演唱會', '演唱会', 'Concerts', 'ライブ', '콘서트'],
    'dessert': ['甜點', '甜点', 'Desserts', 'スイーツ', '디저트'],
    'gift': ['禮物', '礼物', 'Gifts', 'プレゼント', '선물'],
    'ball': ['運動', '运动', 'Sports', 'スポーツ', '운동'],
    'home': ['我家', '我家', 'Home', 'おうち', '우리 집'],
}
# 大標（2026-10-06 使用者定案）：歸檔放第一句、刪除放第二句。
# - 第一版「滑一下保留」被否決：在內建相簿裡滑一下也只是看下一張，照片本來就留著，等於沒說。
# - 「滑一下刪除」放第一句太負面（第一眼就叫人刪照片）→ 歸檔在前（也是畫面上正在發生的事、拍簿跟別人不一樣的地方），
#   強調色只給歸檔那一句。用「刪除」不用「丟棄」（使用者指定）。
TEXT2 = {
    'zh-Hant': dict(two='<em>點一下歸檔</em><br>滑一下刪除', one='<em>點一下歸檔</em>，滑一下刪除'),
    'zh-Hans': dict(two='<em>点一下归档</em><br>划一下删除', one='<em>点一下归档</em>，划一下删除'),
    'en': dict(two='<em>Tap to file away.</em><br>Swipe to delete.', one='<em>Tap to file away.</em> Swipe to delete.'),
    'ja': dict(two='<em>タップでアルバムへ</em><br>スワイプで削除', one='<em>タップでアルバムへ</em>、スワイプで削除'),
    'ko': dict(two='<em>눌러서 앨범으로</em><br>밀어서 삭제', one='<em>눌러서 앨범으로</em>, 밀어서 삭제'),
}

RAIL2_CSS = '''
/* 相簿軌：顏色、圓角、比例量自 App 實機錄影（r2_album）—— 軌底 #FCFAF8、格子 #F0EAE1、點到的那一格 #A0ABB6 */
.rail2 { position: absolute; z-index: 20; background: #FCFAF8;
  box-shadow: inset 0 0 0 1px rgba(42,55,68,.05), 0 2px 4px rgba(0,0,0,.28), 0 34px 70px -28px rgba(0,0,0,.7); }
.rtile { position: absolute; z-index: 21; background: #F0EAE1; border-radius: 28%;
  display: flex; align-items: center; justify-content: center; }
.rtile svg { width: 54%; height: 54%; }
.rtile.on { background: #A0ABB6; }
.rlbl { position: absolute; z-index: 21; text-align: center; color: #2F3A45; font-family: var(--sans); font-weight: 500;
  white-space: nowrap; line-height: 1.1; letter-spacing: .02em; }
.rlbl.on { font-weight: 700; }
.fly { position: absolute; z-index: 25; border-radius: 14%; overflow: hidden; background: #ccc;
  box-shadow: 0 2px 5px rgba(0,0,0,.32), 0 26px 46px -16px rgba(0,0,0,.62); }
.fly img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ring { position: absolute; z-index: 27; border-radius: 50%; }
.trail { position: absolute; z-index: 24; overflow: visible; }
.copy2 { position: absolute; z-index: 30; display: flex; flex-direction: column; justify-content: center; }
.copy2 h1 { font-family: var(--serif); font-weight: 700; color: #F4F1EA; line-height: 1.22; letter-spacing: .01em;
  white-space: nowrap; }
.copy2 h1 em { font-style: normal; color: #F6C453; }
.copy2 .lockup .wm { color: #F4F1EA; }
.copy2 .lockup .wm small { color: rgba(244,241,234,.55); }
'''


PAPER2_CSS = '''
/* 紙色版：與七張商店截圖同一個底（#FBF7F0＋極淡的珊瑚／書藍光暈）、墨色字、珊瑚強調 */
.board.paper::before { content: ""; position: absolute; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 60% 70% at 8% -10%, rgba(232,128,110,.14), transparent 70%),
    radial-gradient(ellipse 60% 70% at 96% 0%, rgba(91,122,146,.12), transparent 70%),
    radial-gradient(ellipse 80% 60% at 50% 115%, rgba(169,192,210,.22), transparent 72%); }
.paper .copy2 h1 { color: var(--ink); }
.paper .copy2 h1 em { color: var(--coral-deep); }
.paper .copy2 .lockup .wm { color: var(--ink); }
.paper .copy2 .lockup .wm small { color: var(--ink-fade); }
.paper .rail2 { box-shadow: inset 0 0 0 1px rgba(42,55,68,.06), 0 2px 4px rgba(42,55,68,.10), 0 30px 60px -26px rgba(42,55,68,.42); }
.paper .fly { box-shadow: 0 1px 2px rgba(42,55,68,.16), 0 18px 34px -12px rgba(42,55,68,.42); }
.mascot { position: absolute; z-index: 22; }
'''


CORAL2_CSS = '''
/* 珊瑚版：App 圖示底部那一塊珊瑚紅當底（品牌色），字用米白、強調用淡金 */
html, body { background: #C9634F; }
.board.coral { background: linear-gradient(175deg, #DA7762 0%, #C9624E 100%); }
.coral .copy2 h1 { color: #FFF8F0; }
.coral .copy2 h1 em { color: #FFE2A6; }
.coral .copy2 .lockup .wm { color: #FFF8F0; }
.coral .copy2 .lockup .wm small { color: rgba(255,248,240,.7); }
.coral .rail2 { box-shadow: inset 0 0 0 1px rgba(42,55,68,.06), 0 2px 4px rgba(90,30,20,.2), 0 30px 60px -26px rgba(90,30,20,.55); }
.coral .fly { box-shadow: 0 1px 2px rgba(90,30,20,.25), 0 18px 34px -12px rgba(90,30,20,.5); }
'''


def mascot_el(cx, ledge_y, w):
    """皮皮趴在邊緣上探頭（pipi_peeking）：圖的下緣不是切平線 —— 最下面 11.6% 是垂在線下的手指，
    要對齊的是切平線（assets/mascot/README.md）。"""
    h = w * 389 / 480
    top = ledge_y - h * (1 - .116)
    return (f'<img class="mascot" src="{furl(SITE / "assets" / "mascot" / "pipi_peeking.webp")}" '
            f'style="left:{cx - w / 2}px;top:{top}px;width:{w}px;height:{h}px">')


def rail2(loc, y_top, ts, hero_x, hero='dog', x_from=None, x_to=None, lit=None):
    """橫跨畫布的相簿軌。hero 那一本的格子中心落在 hero_x；回傳 (元素, {相簿: (中心x, 格子上緣y)}, 軌高)。"""
    lit = {hero} if lit is None else lit
    sp = ts * 1.167                    # 格距（App：方塊 126、間距 21）
    # 膠囊兩端留在畫布裡（看得出是 App 的那條軌，不是一條被裁掉的色帶）
    x_from = ts * .5 if x_from is None else x_from
    x_to = UNIT_W - ts * .5 if x_to is None else x_to
    pad = ts * .15
    lbl = ts * .21
    cap_h = pad + ts + ts * .07 + lbl * 1.15 + pad * 1.05
    li = LOC_IDX[loc]
    hi = RAIL_ORDER.index(hero)
    edge = ts * .16 + ts / 2          # 第一格的中心離膠囊邊多遠
    k0 = math.ceil((x_from + edge - hero_x) / sp)
    k1 = math.floor((x_to - edge - hero_x) / sp)
    left = hero_x + k0 * sp - edge
    right = hero_x + k1 * sp + edge
    out = [f'<div class="rail2" style="left:{left}px;top:{y_top}px;width:{right - left}px;'
           f'height:{cap_h}px;border-radius:{cap_h * .36}px"></div>']
    pos = {}
    for k in range(k0, k1 + 1):
        name = RAIL_ORDER[(hi + k) % len(RAIL_ORDER)]
        cx = hero_x + k * sp
        on = name in lit
        s = ts * (1.08 if on else 1)
        tx, ty = cx - s / 2, y_top + pad - (s - ts) / 2
        pos[name] = (cx, y_top + pad)
        out.append(f'<div class="rtile{" on" if on else ""}" style="left:{tx}px;top:{ty}px;width:{s}px;height:{s}px">'
                   f'{pixel_icons.svg(name)}</div>')
        out.append(f'<div class="rlbl fitw{" on" if on else ""}" style="left:{cx - sp / 2}px;width:{sp}px;'
                   f'top:{y_top + pad + ts + ts * .07 + (s - ts) / 2}px;font-size:{lbl}px">{ALBUM_NAMES[name][li]}</div>')
    return out, pos, cap_h


def fly_el(name, cx, cy, size, rot, z=25, pos='50% 50%'):
    return (f'<div class="fly" style="left:{cx - size / 2}px;top:{cy - size / 2}px;width:{size}px;height:{size}px;'
            f'transform:rotate({rot}deg);z-index:{z}"><img src="{ph(name)}" style="object-position:{pos}"></div>')


def trail_el(x0, y0, x1, y1, bend, width, color='rgba(246,196,83,.85)', ctrl=None):
    """飛行路線：一條往下彎的虛線弧（起點較淡、靠近相簿那一端較實）。ctrl＝二次貝茲的控制點（不給就用 bend 推）。"""
    if ctrl:
        cx, cy = ctrl
    else:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = -(y1 - y0), (x1 - x0)
        L = math.hypot(nx, ny) or 1
        cx, cy = mx + nx / L * bend, my + ny / L * bend
    minx, miny = min(x0, x1, cx) - 20, min(y0, y1, cy) - 20
    W, H = max(x0, x1, cx) + 20 - minx, max(y0, y1, cy) + 20 - miny
    d = f'M{x0 - minx:.1f},{y0 - miny:.1f} Q{cx - minx:.1f},{cy - miny:.1f} {x1 - minx:.1f},{y1 - miny:.1f}'
    return (f'<svg class="trail" style="left:{minx}px;top:{miny}px;width:{W}px;height:{H}px" viewBox="0 0 {W} {H}">'
            f'<defs><linearGradient id="tg{int(x0)}{int(y0)}" gradientUnits="userSpaceOnUse" x1="{x0 - minx}" y1="{y0 - miny}"'
            f' x2="{x1 - minx}" y2="{y1 - miny}"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<path d="{d}" fill="none" stroke="url(#tg{int(x0)}{int(y0)})" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-dasharray="{width * .1} {width * 2.4}"/></svg>')


FITW_JS = '''<script>
/* 相簿名稱放不下就縮（跟 App 的相簿軌一樣：名稱縮到放得下，不折行、不截斷） */
document.fonts.ready.then(function () {
  document.querySelectorAll('.fitw').forEach(function (el) {
    var fs = parseFloat(getComputedStyle(el).fontSize), min = fs * .6;
    el.style.overflow = 'hidden';
    while (el.scrollWidth > el.clientWidth + .5 && fs > min) { fs -= .25; el.style.fontSize = fs + 'px'; }
  });
});
</script>
'''


def scene2(placement, loc, theme, L, out_w=None):
    spec = SPECS[placement]
    zoom = spec['w'] / UNIT_W
    unit_h = round(spec['h'] / zoom, 3)
    sx0, sy0, sx1, sy1 = [v / zoom for v in spec['safe']]
    if out_w:
        zoom = out_w / UNIT_W
    sw, sh = sx1 - sx0, sy1 - sy0
    t, t2 = TEXT[loc], TEXT2[loc]
    css = LOCKUP_CSS + RAIL2_CSS + PAPER2_CSS
    els = []
    ts = L['tile']
    # 相簿軌：底緣貼著安全區下緣（往下多出的一點是軌道的陰影，不影響）
    cap_h = ts * .15 + ts + ts * .07 + ts * .21 * 1.15 + ts * .15 * 1.05
    rail_top = sy1 - cap_h + L.get('rail_dy', 0)
    hero_x = sx0 + sw * L['hero_at']
    r_els, pos, _ = rail2(loc, rail_top, ts, hero_x, lit=set(MOTION_LIT) if MOTION else None)
    els += r_els
    hx, hy = pos['dog']
    # 主角：巴哥犬正飛進「狗狗」（縮小中、略往左上傾）
    fs_ = L['fly']
    fcx, fcy = hx + L['fly_dx'] * ts, hy - L['fly_dy'] * ts
    if not MOTION:
        els.append(fly_el('pug', fcx, fcy, fs_, -9, pos='42% 55%'))
    # 路線：二次貝茲 P0 → P1（控制點）→ P2（主角的位置）。先在高處往右、再往下落 —— 整條都在標題外面
    #（影片版的照片沿這條線一張接一張移動，第一版的路線掠過標題右上角）
    if L.get('path'):
        (p0x, p0y), (p1x, p1y) = L['path']
        x0, y0, qx, qy = fcx + p0x * ts, fcy + p0y * ts, fcx + p1x * ts, fcy + p1y * ts
    else:
        x0, y0 = fcx + L['trail'][0] * ts, fcy + L['trail'][1] * ts
        mx_, my_ = (x0 + fcx) / 2, (y0 + fcy) / 2
        nx_, ny_ = -(fcy - y0), (fcx - x0)
        ln = math.hypot(nx_, ny_) or 1
        qx, qy = mx_ + nx_ / ln * L['trail'][2] * ts, my_ + ny_ / ln * L['trail'][2] * ts
    els.append(trail_el(x0, y0, fcx, fcy, 0, ts * .055, ctrl=(qx, qy)))
    # 排在後面的兩張：沿著同一條路線、越遠越小 —— 讀起來是「一張接一張」，不是一張孤零零的照片
    slots = []
    for tq, scale, rot, name in L.get('queue', []):
        bx = (1 - tq) ** 2 * x0 + 2 * (1 - tq) * tq * qx + tq ** 2 * fcx
        by = (1 - tq) ** 2 * y0 + 2 * (1 - tq) * tq * qy + tq ** 2 * fcy
        slots.append(dict(q=tq, scale=scale, rot=rot, x=bx, y=by))
        if not MOTION:
            els.append(fly_el(name, bx, by, fs_ * scale, rot, z=24))
    if L.get('mascot'):
        mx, mw = L['mascot']
        els.append(mascot_el(sx0 + sw * mx, rail_top + ts * .04, mw))
    # 兩側：其他照片也正往各自的相簿落下（安全區外，iPad 上看得到）。
    # 跟字、主角重疊的那幾張自動跳過 —— 第一版有一張咖啡壓到標題。
    keep_out = [(sx0 - 20, sy0 - 40, sx1 + 20, rail_top)]
    for name, album, dy, size, rot in L.get('extras', []):
        if album not in pos:
            continue
        ax, ay = pos[album]
        cx, cy = ax, ay - dy * ts
        box = (cx - size * .6, cy - size * .6, cx + size * .6, cy + size * .6)
        if any(box[0] < k[2] and box[2] > k[0] and box[1] < k[3] and box[3] > k[1] for k in keep_out):
            continue
        els.append(fly_el(name, cx, cy, size, rot, z=23))
    # 字
    fs = L['h1_zh'] if loc.startswith('zh') else L['h1_other']
    lock = lockup(t, fs * .62, fs * .38, fs * .18) if L.get('lockup', True) else ''
    if L.get('stack'):
        els.append(f'''<div class="copy2" style="left:{sx0 + 10}px;top:{sy0 + sh * .04}px;width:{sw - 20}px;align-items:center;text-align:center">
  {f'<div style="margin-bottom:{fs * .3}px">{lock}</div>' if lock else ''}
  <h1 class="fit" style="font-size:{fs}px;width:100%">{t2['one']}</h1>
</div>''')
    else:
        # 字欄的右緣＝主角照片（轉了 9° 的外框）左緣再留 24：寬度從「旁邊那個東西實際佔到哪裡」推出來
        hero_left = fcx - fs_ * .5 * (math.cos(math.radians(9)) + math.sin(math.radians(9)))
        cw = min(L['copy_w'] * sw, hero_left - 24 - (sx0 + L['pad']))
        els.append(f'''<div class="copy2" style="left:{sx0 + L['pad']}px;top:{sy0}px;height:{rail_top - sy0 - L.get('copy_gap', 10)}px;width:{cw}px">
  {f'<div style="margin-bottom:{fs * .3}px">{lock}</div>' if lock else ''}
  <h1 class="fit" style="font-size:{fs}px">{t2['two']}</h1>
</div>''')
    for (dx, dy, s, c) in L.get('sparks', []):
        els.append(SPARK.format(x=sx0 + dx * sw, y=sy0 + dy * sh, s=s, c=c))
    css += NIGHT_CSS if theme == 'night' else (CORAL2_CSS if theme == 'coral' else '')
    body = f'<div class="board {theme}">\n' + '\n'.join(els) + '\n</div>\n'
    html = head(loc, f'{placement} {loc}', unit_h, css) + body + FIT_JS + FITW_JS + tail(zoom)
    SCENE_META.clear()
    SCENE_META.update(placement=placement, loc=loc, zoom=zoom, unit_h=unit_h, rail_pos=pos, tile=ts,
                      rail_top=rail_top, hero_x=hero_x, hero=dict(x=fcx, y=fcy, size=fs_, rot=-9),
                      path=dict(x0=x0, y0=y0, qx=qx, qy=qy), slots=slots)
    return html, unit_h


LAYOUTS2 = {
    'header': dict(tile=104, hero_at=.68, fly=150, fly_dx=-.2, fly_dy=1.02, trail=(-4.6, -2.2, -.7), path=((-3.4, -2.9), (-.4, -2.7)), mascot=(.9, 210), queue=[(.35, .42, 8, 'bday_a'), (.68, .62, -4, 'boba_hand')], 
                   h1_zh=60, h1_other=48, pad=22, copy_w=.6, lockup=False,
                   extras=[('latte_a', 'coffee', 1.9, 104, -8), ('taipei_101', 'city', 2.7, 112, 6),
                           ('mountain_b', 'tent', 1.7, 100, -5), ('couple_city', 'heart', 2.3, 112, 7),
                           ('cat_orange_face', 'cat', 1.6, 104, -6), ('flowers_a', 'flower', 2.9, 96, 5),
                           ('mountain_a', 'mountain', 1.9, 108, -9)],
                   sparks=[(.66, .03, 22, '#F6C453'), (.97, .52, 15, '#E8806E')]),
    'search': dict(tile=132, hero_at=.66, fly=212, fly_dx=-.32, fly_dy=1.18, trail=(-4.4, -2.4, -.8), path=((-3.4, -2.9), (-.4, -2.7)), mascot=(.89, 270), queue=[(.35, .42, 8, 'bday_a'), (.68, .62, -4, 'boba_hand')], 
                   h1_zh=80, h1_other=62, pad=30, copy_w=.58, lockup=True,
                   extras=[('latte_a', 'coffee', 1.9, 132, -8), ('taipei_101', 'city', 3.0, 140, 6),
                           ('mountain_b', 'tent', 1.8, 126, -5), ('couple_city', 'heart', 2.5, 140, 7),
                           ('cat_orange_face', 'cat', 1.7, 132, -6), ('flowers_a', 'flower', 3.2, 124, 5),
                           ('mountain_a', 'mountain', 2.0, 136, -9), ('family_floor', 'family', 4.6, 150, -4),
                           ('boy_slide', 'baby', 3.6, 126, 8), ('shrimp', 'food', 5.0, 132, 6)],
                   sparks=[(.6, .05, 26, '#F6C453'), (.98, .46, 18, '#E8806E')]),
    'universal': dict(tile=80, hero_at=.56, fly=104, fly_dx=.18, fly_dy=.86, trail=(-2.8, -.7, -.5), mascot=(.86, 150), 
                      h1_zh=38, h1_other=30, stack=True, lockup=True,
                      extras=[('latte_a', 'coffee', 1.9, 92, -8), ('taipei_101', 'city', 3.0, 98, 6),
                              ('mountain_b', 'tent', 1.8, 88, -5), ('couple_city', 'heart', 2.5, 98, 7),
                              ('cat_orange_face', 'cat', 1.7, 92, -6), ('flowers_a', 'flower', 3.2, 86, 5),
                              ('mountain_a', 'mountain', 2.0, 94, -9), ('family_floor', 'family', 4.8, 104, -4),
                              ('boy_slide', 'baby', 3.8, 88, 8), ('shrimp', 'food', 5.2, 92, 6),
                              ('friends_laugh', 'friends', 5.6, 94, 5)],
                      sparks=[(.06, .5, 16, '#F6C453'), (.96, .62, 12, '#E8806E')]),
}

BUILDERS = {p: (lambda loc, theme='coral', out_w=None, _p=p: scene2(_p, loc, theme, LAYOUTS2[_p], out_w))
            for p in LAYOUTS2}


# ───────────────────────────── 渲染 ─────────────────────────────

def render(placement, loc, preview=False, theme='night'):
    spec = SPECS[placement]
    html, _ = BUILDERS[placement](loc, theme)
    BOARDS.mkdir(parents=True, exist_ok=True)
    tag = placement if theme == 'coral' else f'{placement}_{theme}'
    board = BOARDS / f'{tag}_{loc}.html'
    board.write_text(html, encoding='utf-8')
    out_dir = OUT / loc
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{tag}_{spec["w"]}x{spec["h"]}.png'
    chrome_shot(board, out, spec['w'], spec['h'])
    im = Image.open(out)
    assert im.size == (spec['w'], spec['h']), ('尺寸不對', placement, loc, im.size)
    # Apple：不能有透明通道 → 一律存成 RGB
    im.convert('RGB').save(out, optimize=True)
    if preview:
        make_preview(placement, loc, out, tag)
    print(f'✓ {out.relative_to(REPO)}')
    return out


def make_preview(placement, loc, out, tag):
    spec = SPECS[placement]
    im = Image.open(out).convert('RGB')
    d = ImageDraw.Draw(im, 'RGBA')
    x0, y0, x1, y1 = spec['safe']
    lw = max(6, spec['w'] // 500)
    # 安全區外壓暗，一眼看出「iPhone 上可能看不到」的範圍
    shade = (20, 24, 30, 120)
    d.rectangle((0, 0, spec['w'], y0), fill=shade)
    d.rectangle((0, y1, spec['w'], spec['h']), fill=shade)
    d.rectangle((0, y0, x0, y1), fill=shade)
    d.rectangle((x1, y0, spec['w'], y1), fill=shade)
    d.rectangle((x0, y0, x1, y1), outline=(0, 230, 90, 255), width=lw)
    pv = BUILD / 'preview'
    pv.mkdir(parents=True, exist_ok=True)
    s = 1600 / spec['w']
    im.resize((1600, round(spec['h'] * s)), Image.LANCZOS).save(pv / f'{tag}_{loc}_safe.jpg', quality=88)
    # 只看安全區那一塊（≈ iPhone 直向上真正看得清楚的範圍）
    crop = Image.open(out).convert('RGB').crop(spec['safe'])
    crop.thumbnail((1000, 1000), Image.LANCZOS)
    crop.save(pv / f'{tag}_{loc}_safezone.jpg', quality=90)


def chrome_shot(html_path, out, w, h, transparent=False):
    TMP.mkdir(parents=True, exist_ok=True)
    prof = tempfile.mkdtemp(prefix='pbcr_', dir=TMP)
    args = [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
            f'--user-data-dir={prof}', '--disable-application-cache',
            '--force-device-scale-factor=1', f'--window-size={w},{h}',
            '--virtual-time-budget=15000', '--run-all-compositor-stages-before-draw']
    if transparent:
        args.append('--default-background-color=00000000')
    try:
        subprocess.run(args + [f'--screenshot={out}', furl(html_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    with Image.open(out) as im:
        assert im.size == (w, h), ('尺寸不對', out, im.size)


# 影片版的六張：照片 → 收進哪一本（靜態圖＝第一輪第 38 格：狗狗那格亮著、巴哥犬在前、奶茶與生日照排在後面）。
# - 目標只用狗狗與左右緊鄰的兩格：試過「旅行」（左邊第二格），照片落下時得從「美食」上面掠過，看起來像收錯相簿。
# - 六張、不是三張（使用者 2026-10-06）：三張一輪時，剛收進相簿的那張下一秒就從隊伍最後面又冒出來。
#   隊伍裡同時有三張（最前面＋後面兩格），第 k 張收走時進場的是第 k+3 張 —— 要它是「畫面上沒有、剛剛也沒收過」的，
#   一輪至少要六張。循環播放總要回到起點，所以最後三輪進場的是開頭那三張，但那時距離它們被收走已經 9 秒。
# - 不能跟兩側落下的照片（LAYOUTS2 的 extras）重複：同一張圖同時出現兩次很怪。
VIDEO_ITEMS = [('pug', 'dog', '42% 55%'), ('boba_hand', 'food', '50% 50%'), ('bday_a', 'cake', '50% 50%'),
               ('dog_autumn', 'dog', '38% 62%'), ('brunch', 'food', '50% 55%'), ('bday_b', 'cake', '50% 58%')]
LOOP_SEC = 3 * len(VIDEO_ITEMS)
# 照片陰影（設計單位）—— 與靜態圖各主題的 .fly 相同；Remotion 那邊照這份畫
FLY_SHADOW = {
    'coral': [(0, 1, 2, 0, 'rgba(90,30,20,.25)'), (0, 18, 34, -12, 'rgba(90,30,20,.5)')],
    'night': [(0, 2, 5, 0, 'rgba(0,0,0,.32)'), (0, 26, 46, -16, 'rgba(0,0,0,.62)')],
    'paper': [(0, 1, 2, 0, 'rgba(42,55,68,.16)'), (0, 18, 34, -12, 'rgba(42,55,68,.42)')],
}


def render_video(placement, loc, frames=None, theme='coral'):
    """影片版：Chrome 先把「整個場景，但不畫排隊的照片、不點亮任何一格」烤成底圖；Remotion 只動照片與亮起的那一格。
    一張 3 秒：那一格先亮（像 App 裡點了相簿）→ 照片縮小飛進去 → 後面的往前遞補 → 那一格熄掉。六張一輪＝18 秒。
    三個主題（珊瑚、夜色、紙色）都有影片：A/B 測試要比的是同一種東西（影片對影片）。"""
    global MOTION
    comp, W, H = VIDEO_SPECS[placement]
    zoom = W / UNIT_W
    pub = REMOTION / 'public' / 'creative'
    for d in ('photos', 'plates'):
        (pub / d).mkdir(parents=True, exist_ok=True)
    # 兩張底圖：一張什麼都沒亮、一張四個目標格都亮著 —— 亮的那格從第二張裁下來（連同皮皮的手、字重），
    # Remotion 疊上去淡入淡出，跟靜態圖那一格逐像素相同
    global MOTION_LIT
    plates = {}
    key = placement if theme == 'coral' else f'{placement}_{theme}'
    for tag, lit in (('plate', set()), ('lit', {a for _, a, _ in VIDEO_ITEMS})):
        MOTION, MOTION_LIT = True, lit
        try:
            html, unit_h = BUILDERS[placement](loc, theme, W)
        finally:
            MOTION, MOTION_LIT = False, set()
        board = BOARDS / f'{key}_{tag}_{loc}.html'
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text(html, encoding='utf-8')
        png = BUILD / 'motion' / f'{key}_{tag}_{loc}.png'
        png.parent.mkdir(parents=True, exist_ok=True)
        chrome_shot(board, png, W, H)
        plates[tag] = Image.open(png).convert('RGB')
    meta = dict(SCENE_META)
    plate = pub / 'plates' / f'{key}_{loc}.png'
    plates['plate'].save(plate)
    for name, _, _ in VIDEO_ITEMS:
        shutil.copy2(photos.OUT / f'{name}.jpg', pub / 'photos' / f'{name}.jpg')
    ts = meta['tile']
    z = lambda v: v * zoom  # noqa: E731
    pos = meta['rail_pos']
    sp = ts * 1.167
    items = []
    for n, a, p in VIDEO_ITEMS:
        cx, top = pos[a]
        # 裁切框：左右各半個格距（不碰鄰格）、上緣含放大 8% 的那一圈、下緣含名稱
        box = [round(z(v)) for v in (cx - sp / 2, top - ts * .1, cx + sp / 2, top + ts * 1.4)]
        crop = plates['lit'].crop(box)
        lit_path = pub / 'plates' / f'{key}_{loc}_{a}.png'
        crop.save(lit_path)
        items.append(dict(photo=f'creative/photos/{n}.jpg', pos=p, album=a,
                          lit=dict(src=f'creative/plates/{key}_{loc}_{a}.png', x=box[0], y=box[1],
                                   w=box[2] - box[0], h=box[3] - box[1]),
                          tx=z(cx), ty=z(top + ts / 2)))
    h, pa = meta['hero'], meta['path']
    shadow = ', '.join(f'{x * zoom:.1f}px {y * zoom:.1f}px {b * zoom:.1f}px {sp_ * zoom:.1f}px {c}'
                       for x, y, b, sp_, c in FLY_SHADOW[theme])
    scene = dict(placement=placement, loc=loc, zoom=zoom, plate=f'creative/plates/{key}_{loc}.png', shadow=shadow,
                 ts=z(ts), hero=dict(x=z(h['x']), y=z(h['y']), size=z(h['size']), rot=h['rot']),
                 path=dict(x0=z(pa['x0']), y0=z(pa['y0']), qx=z(pa['qx']), qy=z(pa['qy'])),
                 slots=[dict(q=sl['q'], scale=sl['scale'], rot=sl['rot']) for sl in sorted(meta['slots'], key=lambda d: -d['q'])],
                 items=items)
    props = BUILD / 'motion' / f'{key}_{loc}.json'
    props.parent.mkdir(parents=True, exist_ok=True)
    props.write_text(json.dumps(dict(scene=scene), ensure_ascii=False), encoding='utf-8')
    TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(TMP), TMP=str(TMP))
    if frames:      # 試看：只出幾格靜態圖（--frames=33,42,70）
        outs = []
        for f in str(frames).split(','):
            out = BUILD / 'stills' / f'{key}_{loc}_{f}.png'
            out.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(f'npx remotion still src/creative/index.ts {comp} "{out}" --props="{props}" --frame={f} --log=error',
                           cwd=REMOTION, shell=True, check=True, env=env)
            outs.append(out)
            print(f'✓ {out.relative_to(REPO)}', flush=True)
        return outs
    out = OUT / loc / f'{key}_{W}x{H}.mp4'
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = (f'npx remotion render src/creative/index.ts {comp} "{out}" --props="{props}" '
           f'--codec=h264 --crf=15 --pixel-format=yuv420p --image-format=jpeg --jpeg-quality=96 '
           f'--color-space=bt709 --concurrency=6 --log=error')
    subprocess.run(cmd, cwd=REMOTION, shell=True, check=True, env=env)
    finalize_video(out)
    print(f'✓ {out.relative_to(REPO)}', flush=True)
    return out


def finalize_video(path):
    """Remotion 輸出 → 上傳版：換上與畫面同長的循環配樂（loop_music.py）、補齊 BT.709 色彩標記（不重新編碼畫面）。
    Remotion 自己會塞一條靜音 AAC，而且色彩只標了矩陣、沒標原色與轉換曲線 —— 兩個都在這裡處理。"""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    music = BUILD / f'loop_{LOOP_SEC}s.wav'
    if not music.exists():
        subprocess.run([sys.executable, str(HERE / 'loop_music.py'), str(len(VIDEO_ITEMS))], check=True)
    tmp = path.with_suffix('.tmp.mp4')
    subprocess.run([ff, '-v', 'error', '-y', '-i', str(path), '-i', str(music),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                    '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
                    '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
                    '-t', str(LOOP_SEC), '-movflags', '+faststart', str(tmp)], check=True)
    tmp.replace(path)
    print(f'✓ 配樂＋色彩標記 {path.relative_to(REPO)}', flush=True)


def overview():
    """五語 × 三版位並排的總覽（給人看的，不上傳）→ store_assets/creative/總覽.jpg"""
    h = 300
    rows = []
    for loc in LOCALES:
        ims = []
        for p in ('header', 'search', 'universal'):
            sp = SPECS[p]
            im = Image.open(OUT / loc / f'{p}_{sp["w"]}x{sp["h"]}.png').convert('RGB')
            ims.append(im.resize((round(im.size[0] * h / im.size[1]), h), Image.LANCZOS))
        rows.append(ims)
    gap = 16
    W = max(sum(i.size[0] for i in r) + gap * (len(r) + 1) for r in rows)
    sheet = Image.new('RGB', (W, len(rows) * (h + gap) + gap), (236, 232, 224))
    for k, r in enumerate(rows):
        x = gap
        for im in r:
            sheet.paste(im, (x, gap + k * (h + gap)))
            x += im.size[0] + gap
    sheet.save(OUT / '總覽.jpg', quality=88)
    print(f'✓ {(OUT / "總覽.jpg").relative_to(REPO)}', flush=True)


def main(argv):
    preview = '--preview' in argv
    themes = [t for t in ('coral', 'night', 'paper') if f'--{t}' in argv] or ['coral']
    args = [a for a in argv if not a.startswith('--')]
    locs = [a for a in args if a in LOCALES] or LOCALES
    photos.prep()
    if '--overview' in argv:
        overview()
        return
    if '--finalize' in argv:     # 只重做配樂與色彩標記（影片已經渲染好）
        for f in sorted(OUT.glob('*/*.mp4')):
            if not locs or f.parent.name in locs:
                finalize_video(f)
        return
    if '--video' in argv:
        frames = next((a.split('=', 1)[1] for a in argv if a.startswith('--frames=')), None)
        for p in [a for a in args if a in VIDEO_SPECS] or list(VIDEO_SPECS):
            for th in themes:
                for loc in locs:
                    render_video(p, loc, frames, th)
        return
    placements = [a for a in args if a in BUILDERS] or list(BUILDERS)
    for p in placements:
        for loc in locs:
            for th in themes:
                render(p, loc, preview, th)
    if 'coral' in themes and set(placements) == set(BUILDERS) and set(locs) == set(LOCALES):
        overview()


if __name__ == '__main__':
    main(sys.argv[1:])
