#!/usr/bin/env bash
# App Preview 影片（App Store 用）
#   886×1920、30fps、H.264、含一條靜音 AAC（Apple 硬性要求：沒有音軌會被退件）
#   長度必須落在 15–30 秒之間。
#
# 素材全部是實機錄的原檔（1080×2400）或實機截圖，這裡只做裁切、Ken Burns、
# 字卡與轉場。片段之間用 xfade 交叉溶解，最後統一輸出。
#
# 用法：PIBOOK_REC_DIR=<素材資料夾> bash build.sh
#       → store_assets/app_preview_ios.mp4
#
# 兩個踩過的坑（改動前先讀）：
#  1. 字幕 PNG 一定要 `-loop 1 -t <長度>`。單張圖只有一格，overlay 的 enable
#     視窗落在它 EOF 之後就整段不合成 —— 畫面上什麼字都沒有，也不會報錯。
#  2. zoompan 每 d 格輸出才吃一格輸入。餵「有限長度」的輸入會把長度乘上 d
#     （實測 2.8 秒的字卡變成 23 分鐘）。正解：輸入無限、用 -frames:v 收尾。

set -e
cd "$(dirname "$0")"
SRC="${PIBOOK_REC_DIR:?請設定 PIBOOK_REC_DIR＝存放實機錄影原檔的資料夾}"
OUT="$(cd ../../.. && pwd)/store_assets"
mkdir -p "$OUT"
FF="$(python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')"
W=886; H=1920; FPS=30
TMP="$(mktemp -d)"

# 1080×2400 的錄影 → 886×1920：先等比縮到寬 886（得 886×1969），再上下裁一點。
CROP="scale=${W}:-2:flags=lanczos,crop=${W}:${H}:0:25,fps=${FPS},format=yuv420p"
CAPFADE="format=rgba,fade=t=in:st=0.25:d=0.35:alpha=1,fade=t=out:st=2.2:d=0.5:alpha=1"

clip() { # $1=來源 $2=起 $3=長度 $4=字幕png $5=輸出
  "$FF" -y -ss "$2" -t "$3" -i "$1" -loop 1 -t "$3" -i "$4" -filter_complex \
    "[0:v]setpts=PTS-STARTPTS,${CROP}[v];[1:v]${CAPFADE}[c];[v][c]overlay=0:0:enable='between(t,0.25,2.7)'[o]" \
    -map "[o]" -an -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$TMP/$5" 2>/dev/null
}

kb() { # $1=圖 $2=長度 $3=字幕png $4=輸出
  local frames
  frames=$(python -c "print(int($2*$FPS))")
  "$FF" -y -loop 1 -i "$1" -loop 1 -t "$2" -i "$3" -filter_complex \
    "[0:v]scale=2658:-2:flags=lanczos,zoompan=z='min(1.0+0.00042*on,1.14)':d=${frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},format=yuv420p[v];[1:v]${CAPFADE}[c];[v][c]overlay=0:0:enable='between(t,0.25,2.7)'[o]" \
    -map "[o]" -an -frames:v "$frames" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$TMP/$4" 2>/dev/null
}

card() { # $1=圖 $2=長度 $3=輸出
  local frames
  frames=$(python -c "print(int($2*$FPS))")
  "$FF" -y -loop 1 -i "$1" -filter_complex \
    "[0:v]scale=1772:-2:flags=lanczos,zoompan=z='min(1.0+0.00030*on,1.06)':d=${frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},format=yuv420p[v]" \
    -map "[v]" -an -frames:v "$frames" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$TMP/$3" 2>/dev/null
}

echo "· 產生片段"
card card_start.png                      2.8            s0.mp4
clip "$SRC/review_demo_src.mp4"  0.4 5.6 cap_review.png   s1.mp4
clip "$SRC/album_demo_src.mp4"   0.6 5.2 cap_album.png    s2.mp4
kb   "$SRC/compress_still.png"       4.6 cap_compress.png s3.mp4
clip "$SRC/memory_demo_src.mp4"  7.0 5.4 cap_memory.png   s4.mp4
kb   "$SRC/similar_still.png"        4.2 cap_similar.png  s5.mp4
card card_end.png                        3.0            s6.mp4

echo "· 交叉溶解串接"
python - "$TMP" "$FF" "$OUT" 0.4 "$FPS" <<'PYEOF'
import subprocess, sys, os
TMP, FF, OUT, XF, FPS = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5])
segs = ['s0.mp4','s1.mp4','s2.mp4','s3.mp4','s4.mp4','s5.mp4','s6.mp4']
def dur(p):
    o = subprocess.run([FF,'-i',p], capture_output=True).stderr.decode('utf-8','replace')
    for line in o.splitlines():
        if 'Duration:' in line:
            h,m,s = line.split('Duration:')[1].split(',')[0].strip().split(':')
            return int(h)*3600+int(m)*60+float(s)
    raise SystemExit('no duration: '+p)
ds = [dur(os.path.join(TMP,s)) for s in segs]
print('  片段長度：', ' '.join('%.1f'%d for d in ds))
inputs = []
for s in segs:
    inputs += ['-i', os.path.join(TMP,s)]
parts, last, off = [], '0:v', 0.0
for i in range(1, len(segs)):
    off += ds[i-1] - XF
    out = 'x%d' % i
    parts.append("[%s][%d:v]xfade=transition=fade:duration=%s:offset=%.3f[%s]" % (last, i, XF, off, out))
    last = out
total = sum(ds) - XF*(len(segs)-1)
cmd = [FF,'-y'] + inputs + [
    '-f','lavfi','-t','%.3f'%total,'-i','anullsrc=channel_layout=stereo:sample_rate=44100',
    '-filter_complex', ';'.join(parts),
    '-map','[%s]'%last, '-map','%d:a'%len(segs),
    '-c:v','libx264','-profile:v','high','-level','4.0','-crf','19','-preset','slow',
    '-pix_fmt','yuv420p','-r',str(FPS),
    '-c:a','aac','-b:a','128k','-ar','44100','-ac','2',
    '-movflags','+faststart', os.path.join(OUT,'app_preview_ios.mp4')]
r = subprocess.run(cmd, capture_output=True)
if r.returncode: raise SystemExit(r.stderr.decode('utf-8','replace')[-1500:])
print('  總長 %.2f 秒（App Store 允收 15–30 秒）' % total)
PYEOF

"$FF" -i "$OUT/app_preview_ios.mp4" 2>&1 | grep -E "Duration|Stream #"
echo "輸出：store_assets/app_preview_ios.mp4"
