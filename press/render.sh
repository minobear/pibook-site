#!/usr/bin/env bash
# 商店截圖輸出：無頭 Chrome 把每張畫板渲染成兩種商店尺寸的 PNG。
#   iOS 6.9"  : 430×932 視窗 × 3 = 1290×2796
#   Play 9:16 : 360×640 視窗 × 3 = 1080×1920
# 用法：bash render.sh [畫板編號…]（不帶參數＝全部）

set -e
cd "$(dirname "$0")"
CHROME="C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
HERE="$(cygpath -m "$(pwd)")"
OUT="$(cygpath -m "$(cd ../.. && pwd)")/store_assets"
mkdir -p "$OUT/ios_6.9" "$OUT/play_phone"

boards=("$@")
if [ ${#boards[@]} -eq 0 ]; then boards=(01 02 03 04 05 06); fi

for b in "${boards[@]}"; do
  f=$(ls ${b}_*.html 2>/dev/null | head -1)
  [ -z "$f" ] && { echo "跳過 $b（找不到畫板）"; continue; }
  name="${f%.html}"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=3 --window-size=430,932 \
    --virtual-time-budget=10000 \
    --screenshot="$OUT/ios_6.9/${name}.png" "file:///$HERE/$f" 2>/dev/null
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=3 --window-size=360,640 \
    --virtual-time-budget=10000 \
    --screenshot="$OUT/play_phone/${name}.png" "file:///$HERE/$f" 2>/dev/null
  echo "✓ $name"
done
echo "輸出：store_assets/ios_6.9（1290×2796）與 store_assets/play_phone（1080×1920）"
