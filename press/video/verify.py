# -*- coding: utf-8 -*-
"""成片驗收：規格（尺寸、幀率、長度、音軌）＋手機畫面範圍內的停格與閃黑。

    python verify.py <成片.mp4> ...
"""
import json
import subprocess
import sys

import numpy as np

sys.path.insert(0, __import__('os').path.dirname(__file__))
from rec import FF, FFPROBE  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
for src in sys.argv[1:]:
    info = json.loads(subprocess.run([FFPROBE, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', src],
                                     capture_output=True, text=True).stdout)
    v = next(s for s in info['streams'] if s['codec_type'] == 'video')
    a = [s for s in info['streams'] if s['codec_type'] == 'audio']
    W, H = int(v['width']), int(v['height'])
    w, h = W // 4, H // 4
    p = subprocess.run([FF, '-v', 'error', '-i', src, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                       capture_output=True)
    f = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w).astype(np.int16)
    # 手機螢幕：上緣約 1920 的 26%～98%、水平置中約 640/寬
    sw = 640 / W
    roi = f[:, int(h * 0.275):int(h * 0.97), int(w * (0.5 - sw / 2 + 0.02)):int(w * (0.5 + sw / 2 - 0.02))]
    d = np.array([np.abs(roi[i] - roi[i - 1]).mean() for i in range(1, len(roi))])
    # 停格：前一格和後一格都在明顯地動，中間這一格卻幾乎沒變（動作中卡一格）。
    # 「靜止→突然動」（點擊後介面瞬間反應、滑動起步）與「動→到底停住」不算 —— 那是動作本身的樣子。
    stalls = [round((i + 1) / 30, 2) for i in range(1, len(d) - 1) if d[i] < 0.15 and min(d[i - 1], d[i + 1]) > 3]
    m = roi.mean(axis=(1, 2))
    flashes = [round(i / 30, 2) for i in range(1, len(m) - 1) if m[i] < 0.5 * min(m[i - 1], m[i + 1]) and min(m[i - 1], m[i + 1]) > 40]
    print(f"{src.split('/')[-1]}: {W}×{H}, {v['codec_name']} {v['r_frame_rate']}fps, "
          f"{float(info['format']['duration']):.2f}s, 音軌 {a[0]['codec_name'] if a else '無'}, "
          f"{int(info['format']['size']) / 1e6:.1f} MB | 手機畫面停格 {stalls} | 閃黑 {flashes}")
