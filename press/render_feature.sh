#!/usr/bin/env bash
# Google Play 主題圖片（1024×500），中英各一張。
# 兩張共用同一份版面骨架，只換文案與實機截圖。
# 視窗外框補償與 DSF=1 的理由見 render.sh 的開頭註解。
set -e
cd "$(dirname "$0")"
CHROME="C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
HERE="$(cygpath -m "$(pwd)")"
ROOT="$(cygpath -m "$(cd ../.. && pwd)")"
OUT="$ROOT/store_assets/graphics"
mkdir -p "$OUT"

crop() {  # $1=輸出檔名（不含副檔名）
  python -c "
from PIL import Image
p = r'$OUT/$1.png'
im = Image.open(p).convert('RGB')
if im.size != (1024, 500):
    im = im.crop((0, 0, 1024, 500))
im.save(p)
import os
if not os.environ.get('PNG_ONLY'):
    im.save(r'$OUT/$1.jpg', 'JPEG', quality=92, optimize=True, progressive=True)
print('$1', im.size)
"
}

shot() {  # $1=畫板檔名  $2=輸出檔名（不含副檔名）
  local prof; prof="$(mktemp -d)"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir="$prof" --disable-application-cache \
    --force-device-scale-factor=1 --window-size="$((1024+16)),$((500+151))" \
    --virtual-time-budget=12000 \
    --screenshot="$OUT/$2.png" "file:///$HERE/$1" 2>/dev/null
  crop "$2"
}

shot feature_graphic.html    play_feature_graphic
shot feature_graphic_en.html play_feature_graphic_en
PNG_ONLY=1 shot feature_graphic_zh_hans.html play_feature_graphic_zh_hans
