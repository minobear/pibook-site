#!/usr/bin/env bash
# 商店截圖輸出：無頭 Chrome 把每張畫板渲染成兩種商店尺寸的 PNG。
#   iOS 6.9"  : 1290×2796
#   Play 9:16 : 1080×1920
# 用法：bash render.sh [畫板編號…]（不帶參數＝全部）
#
# ⚠️ 為什麼不用 --force-device-scale-factor=3 ＋ 小視窗（舊版寫法）：
#    實測 `--window-size=360,640 --force-device-scale-factor=3` 的 CSS 視窗是
#    **490×489**（近正方形），版面先照 1:1 排好、再被拉伸成 9:16 —— 文字被裁、
#    比例走樣，而且沒有任何錯誤訊息，只能靠肉眼發現。
#    改成 DSF=1 ＋ 精算視窗（視窗要補上 16×151 的視窗外框），CSS 視窗才會剛好
#    等於輸出像素；版面大小由 press.js 的 zoom 統一放大。
#    另外每次用全新 profile，否則改了 press.css 會讀到磁碟快取的舊版。

set -e
cd "$(dirname "$0")"
CHROME="C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
HERE="$(cygpath -m "$(pwd)")"
ROOT="$(cygpath -m "$(cd ../.. && pwd)")"
OUT="$ROOT/store_assets"
mkdir -p "$OUT/ios_6.9" "$OUT/play_phone"

# 視窗外框補償（實測值：寬 +16、高 +151）
CHROME_W=16
CHROME_H=151

shot() { # $1=檔案 $2=輸出路徑 $3=目標寬 $4=目標高
  local win_w=$(( $3 + CHROME_W ))
  local win_h=$(( $4 + CHROME_H ))
  local prof; prof="$(mktemp -d)"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir="$prof" --disable-application-cache \
    --force-device-scale-factor=1 --window-size="$win_w,$win_h" \
    --virtual-time-budget=12000 \
    --screenshot="$2" "file:///$HERE/$1" 2>/dev/null
  python -c "
from PIL import Image
im = Image.open(r'$2')
if im.size != ($3, $4):
    im.crop((0, 0, $3, $4)).save(r'$2')
"
}

boards=("$@")
if [ ${#boards[@]} -eq 0 ]; then boards=(01 02 03 04 05 06 07); fi

for b in "${boards[@]}"; do
  f=$(ls ${b}_*.html 2>/dev/null | head -1)
  [ -z "$f" ] && { echo "跳過 $b（找不到畫板）"; continue; }
  name="${f%.html}"
  shot "$f" "$OUT/ios_6.9/${name}.png"    1290 2796
  shot "$f" "$OUT/play_phone/${name}.png" 1080 1920
  echo "✓ $name"
done
echo "輸出：store_assets/ios_6.9（1290×2796）與 store_assets/play_phone（1080×1920）"
