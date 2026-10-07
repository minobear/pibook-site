# -*- coding: utf-8 -*-
"""示範照片 → 手機原圖等級（4032px、加感光元件雜訊、3–4.5 MB）。

為什麼：示範圖庫是 Pexels 的 2400px 小圖（每張 0.5–1.5 MB）。成果頁上的「省下多少空間」照實際檔案算，
小圖只剩幾 MB，一點都不像真實情境（2026-10-02 整理那一輪的「約可省 1.2 MB」就是這樣；2026-10-06 相似照片
的成果頁也只有 4.5 MB）。真手機一張就 3–5 MB。EXIF（拍攝時間）原封不動帶過去 —— App 靠它分日期、分組。

    python bigify.py <來源資料夾> <輸出資料夾>
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

LONG = 4032


def bigify(src, dst, seed=7):
    im = Image.open(src)
    exif = im.info.get('exif')
    w, h = im.size
    s = LONG / max(w, h)
    big = im.convert('RGB').resize((round(w * s), round(h * s)), Image.LANCZOS)
    a = np.asarray(big).astype(np.float32)
    rng = np.random.default_rng(seed)
    # 感光元件雜訊：亮度為主、彩色很少（JPEG 壓不掉，檔案大小才會像真的）
    lum = rng.normal(0, 2.4, a.shape[:2])[..., None]
    chroma = rng.normal(0, 0.8, a.shape)
    a = np.clip(a + lum + chroma, 0, 255).astype(np.uint8)
    out = Image.fromarray(a)
    kw = dict(quality=93, subsampling=2, optimize=True)
    if exif:
        kw['exif'] = exif
    out.save(dst, **kw)
    return out.size, os.path.getsize(dst)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    src_dir, dst_dir = sys.argv[1], sys.argv[2]
    os.makedirs(dst_dir, exist_ok=True)
    for i, f in enumerate(sorted(glob.glob(os.path.join(src_dir, '*.jpg')))):
        size, n = bigify(f, os.path.join(dst_dir, os.path.basename(f)), seed=i)
        print(os.path.basename(f), size, f'{n / 1e6:.2f} MB')
