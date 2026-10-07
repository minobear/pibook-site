#!/usr/bin/env bash
# 商店截圖輸出：無頭 Chrome 把每張畫板渲染成 PNG → 主 repo 的 store_assets/screenshots/<語言>/
# （繁中 zh-Hant、簡中 zh-Hans、en、ja、ko；zh 這個代號就是繁中畫板，放在 press/ 根目錄）。
#
# 同一套畫板、同一份素材，App Store 與 Google Play 共用（畫板完全不畫狀態列）。
# 只差「畫布尺寸」，因為兩家的比例規定互斥，一張圖不可能同時上兩邊：
#   1290x2796：App Store 的 iPhone 6.9 吋欄位（必填；6.5 吋等較小尺寸 Apple 會自動縮）
#   1080x1920：Google Play 手機截圖（Play 規定長邊不得超過短邊兩倍，1290x2796 會被擋）
# 用法：bash render.sh [畫板編號…]（不帶參數＝全部）
#   SIZES="1290x2796" bash render.sh   只出其中一種尺寸
#   LOCALES="zh en ja ko zh-Hans" bash render.sh   全部語言一起出（其他語言的畫板在 <語言>/，由 make_boards.py 產生）
#
# ⚠️ 為什麼不用 --force-device-scale-factor=3 ＋ 小視窗（舊版寫法）：
#    實測 `--window-size=360,640 --force-device-scale-factor=3` 的 CSS 視窗是
#    **490×489**（近正方形），版面先照 1:1 排好、再被拉伸成 9:16 —— 文字被裁、
#    比例走樣，而且沒有任何錯誤訊息，只能靠肉眼發現。
#    改成 DSF=1 ＋ 視窗直接開成輸出像素，版面大小由 press.js 的 zoom 統一放大。
#    另外每次用全新 profile，否則改了 press.css 會讀到磁碟快取的舊版。
#
# ⚠️ 視窗外框補償是 0（2026-09-23 實測）：新版 Chrome 的 --headless=new 在
#    --screenshot 模式下，CSS 視窗＝--window-size 整個大小。舊的「寬 +16、高 +151」
#    會讓 press.js 以 2947/932 的倍率排版、再被裁回 2796 —— 整張放大約 5%，
#    右緣與底部被切掉，而且沒有任何錯誤訊息。
#    驗法：在畫板上印出 innerWidth×innerHeight 與 zoom，1290x2796 應為 zoom=3。

set -e
cd "$(dirname "$0")"
CHROME="C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
HERE="$(cygpath -m "$(pwd)")"
ROOT="$(cygpath -m "$(cd ../.. && pwd)")"
OUT="$ROOT/store_assets/screenshots"

shot() { # $1=畫板 $2=輸出路徑 $3=寬 $4=高
  local prof; prof="$(mktemp -d)"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir="$prof" --disable-application-cache \
    --force-device-scale-factor=1 --window-size="$3,$4" \
    --virtual-time-budget=12000 \
    --screenshot="$2" "file:///$HERE/$1" 2>/dev/null
  # 一次性的 Chrome 設定檔用完就刪：一個約 10MB、留在 C 槽的暫存，
  # 2026-10-06 一輪出四種尺寸 × 五語就累積了 1GB 多（加上影片暫存把 C 槽寫滿過）。
  rm -rf "$prof"
  # Play 不收帶透明通道的 PNG —— 一律存成 RGB；尺寸不對就是版面出事了，直接停。
  python -c "
from PIL import Image
im = Image.open(r'$2')
assert im.size == ($3, $4), ('尺寸不對', im.size)
if im.mode != 'RGB':
    im.convert('RGB').save(r'$2')
"
}

LOCALES="${LOCALES:-zh}"
SIZES="${SIZES:-1290x2796 1080x1920}"

boards=("$@")
if [ ${#boards[@]} -eq 0 ]; then boards=(01 02 03 04 05 06 07); fi

for loc in $LOCALES; do
  if [ "$loc" = "zh" ]; then src="."; dst="$OUT/zh-Hant"; else src="$loc"; dst="$OUT/$loc"; fi
  for b in "${boards[@]}"; do
    f=$(ls $src/${b}_*.html 2>/dev/null | head -1)
    [ -z "$f" ] && { echo "跳過 $loc/$b（找不到畫板）"; continue; }
    name="$(basename "${f%.html}")"
    for sz in $SIZES; do
      mkdir -p "$dst/$sz"
      shot "$f" "$dst/$sz/${name}.png" "${sz%x*}" "${sz#*x}"
    done
    echo "✓ $loc/$name"
  done
  # 七張並排的總覽（給人看的，不上傳）
  python - "$dst" <<'PYEOF'
import sys, glob, os
from PIL import Image
d = sys.argv[1]
fs = sorted(glob.glob(os.path.join(d, '1290x2796', '0*.png')))
if fs:
    h = 932
    ims = [Image.open(f).convert('RGB').resize((430, h), Image.LANCZOS) for f in fs]
    gap = 24
    sheet = Image.new('RGB', (len(ims) * 430 + (len(ims) + 1) * gap, h + 2 * gap), (236, 232, 224))
    for i, im in enumerate(ims):
        sheet.paste(im, (gap + i * (430 + gap), gap))
    sheet.save(os.path.join(d, '總覽.jpg'), quality=88)
PYEOF
done
echo "輸出：store_assets/screenshots/<語言>/1290x2796（App Store）與 1080x1920（Google Play）"
