# -*- coding: utf-8 -*-
"""回憶頁示範影片：去掉片源裡的重複格、對齊成真 30fps（導演腳本 P7 的「輕量版」）。

    python dedup_video.py <原片> <輸出>

有些 Pexels 片源是 24fps 的內容做 3:2 pulldown 裝成 29.97fps（每 5 格就有 1 格跟前一格一樣），
25fps 的放進 30fps 成片也一樣每 6 格重複一格 —— 錄得再順，成片裡還是會有停格。
這裡把「跟前一格一模一樣」的格挑掉，剩下的每一格照 30fps 重新排時間（影片會稍微快一點，
但每一格都是原片的真畫面，不補幀、不模糊）。
"""
import subprocess
import sys

import numpy as np

sys.path.insert(0, __import__('os').path.dirname(__file__))
from rec import FF, _gray_frames  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
fr = _gray_frames(src, w=96, h=170)
d = np.array([np.abs(fr[i] - fr[i - 1]).mean() for i in range(1, len(fr))])
drop = [i + 1 for i in np.where(d < 0.05)[0]]
keep_expr = 'not(' + '+'.join(f'eq(n\,{i})' for i in drop) + ')' if drop else '1'
vf = f"select='{keep_expr}',setpts=N/30/TB"
subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-map', '0:v', '-vf', vf, '-r', '30', '-fps_mode', 'cfr',
                '-c:v', 'libx264', '-preset', 'slow', '-b:v', '6M', '-maxrate', '8M', '-bufsize', '12M',
                '-pix_fmt', 'yuv420p', '-map_metadata', '0', '-movflags', '+faststart+use_metadata_tags', dst],
               check=True)
out = _gray_frames(dst, w=96, h=170)
d2 = np.array([np.abs(out[i] - out[i - 1]).mean() for i in range(1, len(out))])
print(f'{src}: {len(fr)} 格 → 拿掉 {len(drop)} 格重複 → {len(out)} 格，剩下的重複 {int((d2 < 0.05).sum())} 格')
