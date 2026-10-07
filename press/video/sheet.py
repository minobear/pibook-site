# -*- coding: utf-8 -*-
"""把一段影片的某幾格排成一張小圖（給人看）：python sheet.py in.mp4 out.jpg start end [step] [w]"""
import sys, subprocess, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rec import FF
src, dst, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
w = int(sys.argv[6]) if len(sys.argv) > 6 else 120
h = int(w * 2400 / 1080)
p = subprocess.run([FF, '-v', 'error', '-i', src, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                   capture_output=True)
f = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)
idx = list(range(a, min(b, len(f)), step))
cols = min(10, len(idx))
rows = (len(idx) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h), 'white')
for k, i in enumerate(idx):
    sheet.paste(Image.fromarray(f[i]), ((k % cols) * w, (k // cols) * h))
sheet.save(dst, quality=80)
print(dst, len(f), 'frames')
