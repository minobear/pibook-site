# -*- coding: utf-8 -*-
"""把觸控指示圈疊到實機錄影上。

兩個關鍵決定（都是被使用者打回來過的）：

1. **指示圈必須先出現、App 反應才跟上。** 只靠「發出 input tap 的時刻」對時是錯的
   —— screenrecord 啟動與腳本起跑之間有一個未知的常數偏移，整批指示圈會系統性
   晚半拍。所以改成**從影片本身量出 App 反應的起始幀**（逐幀差分），
   再把接觸瞬間排在那之前。
2. **要夠強烈。** 細細一圈在縮到手機大小之後根本看不見。用「預備環 → 接觸閃光
   → 擴散環」三段，白芯配深色描邊，亮底暗底都看得見。
"""
import os, sys, glob, json, math, subprocess
from PIL import Image, ImageDraw, ImageChops, ImageFilter

SP = os.path.dirname(os.path.abspath(__file__))
FF = subprocess.run([sys.executable, "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip()

FPS = 30
PRE  = 0.17   # 預備：指示圈開始出現到接觸
POST = 0.42   # 接觸到收乾淨


def extract(src, work):
    if os.path.isdir(work):
        for f in glob.glob(work + "/*.jpg"):
            os.remove(f)
    else:
        os.makedirs(work)
    subprocess.run([FF, "-y", "-i", src, "-vf", "fps=%d" % FPS, "-q:v", "2",
                    work + "/f%04d.jpg"], capture_output=True)
    return sorted(glob.glob(work + "/f*.jpg"))


def onsets(frames, roi, n, min_gap=0.5, search_from=0.0):
    """在 roi 內逐幀差分，取變化量的前 n 個「上升起點」。"""
    prev = None
    diffs = []
    for i, f in enumerate(frames):
        im = Image.open(f).convert("L").crop(roi).resize((120, 260))
        if prev is not None:
            d = ImageChops.difference(im, prev)
            diffs.append(sum(d.getdata()) / (120.0 * 260))
        else:
            diffs.append(0.0)
        prev = im
    # 找局部峰值，再往前回溯到「開始動」的那一幀
    picked = []
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    for i in order:
        t = i / float(FPS)
        if t < search_from:
            continue
        if any(abs(t - p) < min_gap for p in picked):
            continue
        picked.append(t)
        if len(picked) == n:
            break
    picked.sort()
    # 回溯：往前找到 diff 掉到峰值 12% 以下的那一幀 = 真正的起始
    starts = []
    for t in picked:
        i = int(round(t * FPS))
        thr = diffs[i] * 0.12
        j = i
        while j > 0 and diffs[j - 1] > thr and (i - j) < 8:
            j -= 1
        starts.append(j / float(FPS))
    return starts, diffs


def ring(size, t, x, y, hold=0.0):
    """回傳一張 RGBA 疊層。t=0 是接觸瞬間，負值是預備。

    幾何刻意做大（擴散環最大半徑 300px ≒ 手機寬的 55%）—— 這支影片最後只佔
    畫布約四成寬，細一圈在那個尺寸上等於沒有。"""
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    def circle(dr, cx, cy, r, fill=None, outline=None, width=1):
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)

    def glow(r, alpha):
        g = Image.new("RGBA", size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        circle(gd, x, y, r, fill=(255, 255, 255, alpha))
        return g.filter(ImageFilter.GaussianBlur(r * 0.42))

    if hold > 0 and -hold <= t < 0:
        # 長按：對準環停在原地，外圈順時針填滿代表「按著不放」
        q = 1 - (-t / hold)
        rr = 94.0
        lay = Image.alpha_composite(lay, glow(150, 70))
        d = ImageDraw.Draw(lay)
        circle(d, x, y, rr + 6, outline=(14, 24, 36, 130), width=15)
        circle(d, x, y, rr, outline=(255, 255, 255, 150), width=11)
        d.arc([x - rr, y - rr, x + rr, y + rr], -90, -90 + int(360 * q),
              fill=(255, 255, 255, 250), width=13)
        circle(d, x, y, 46, fill=(255, 255, 255, 120))
        return lay

    if t < 0:
        tt = t + hold
        p = min(1.0, max(0.0, (tt + PRE) / PRE))
        e = 1 - (1 - p) ** 3
        rr = 232 - 138 * e
        a = int(235 * e)
        lay = Image.alpha_composite(lay, glow(int(rr * 0.7), int(60 * e)))
        d = ImageDraw.Draw(lay)
        circle(d, x, y, rr + 6, outline=(14, 24, 36, int(a * 0.5)), width=15)
        circle(d, x, y, rr, outline=(255, 255, 255, a), width=11)
        circle(d, x, y, 12 + 36 * e, fill=(255, 255, 255, int(110 * e)))
    else:
        p = min(1.0, t / POST)
        e = 1 - (1 - p) ** 2
        lay = Image.alpha_composite(lay, glow(int(150 + 110 * e), int(120 * (1 - e) ** 1.4)))
        d = ImageDraw.Draw(lay)
        cr = 94 - 44 * e
        ca = int(150 * (1 - e) ** 0.75)   # 半透明：底下那顆相簿要看得見
        circle(d, x, y, cr, fill=(255, 255, 255, ca))
        circle(d, x, y, cr, outline=(255, 255, 255, int(250 * (1 - e) ** 0.6)), width=max(3, int(14 - 9 * e)))
        circle(d, x, y, cr + 8, outline=(14, 24, 36, int(150 * (1 - e) ** 0.6)), width=5)
        rr = 94 + 206 * e
        wdt = max(3, int(20 - 17 * e))
        ra = int(245 * (1 - e) ** 1.15)
        circle(d, x, y, rr + wdt, outline=(14, 24, 36, int(ra * 0.40)), width=wdt + 6)
        circle(d, x, y, rr, outline=(255, 255, 255, ra), width=wdt)
    return lay


def run(src, dst, points, roi, search_from=0.0, lead=0.10):
    frames = extract(src, SP + "/tapwork")
    starts, diffs = onsets(frames, roi, len(points), search_from=search_from)
    print("偵測到的 App 反應起始:", ["%.3f" % s for s in starts])
    contacts = [s - lead for s in starts]
    print("指示圈接觸時刻      :", ["%.3f" % c for c in contacts])

    out = SP + "/tapout"
    if os.path.isdir(out):
        for f in glob.glob(out + "/*.jpg"):
            os.remove(f)
    else:
        os.makedirs(out)

    for i, f in enumerate(frames):
        t = i / float(FPS)
        im = Image.open(f).convert("RGBA")
        drew = False
        for (cx, cy), c in zip(points, contacts):
            dt = t - c
            if -PRE <= dt <= POST:
                im = Image.alpha_composite(im, ring(im.size, dt, cx, cy))
                drew = True
        im.convert("RGB").save(out + "/f%04d.jpg" % i, quality=94)
    subprocess.run([FF, "-y", "-framerate", str(FPS), "-i", out + "/f%04d.jpg",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", dst],
                   capture_output=True)
    print("寫出", dst)
    return contacts


def onset_in(frames, roi, lo, hi):
    """在指定時間窗與 ROI 內找變化峰值，再回溯到真正的起始幀。
       多點各自給窗與 ROI —— 全域取前 N 大在有捲動／滑動的片段裡會全部選到滑動。"""
    i0, i1 = max(1, int(lo * FPS)), min(len(frames) - 1, int(hi * FPS))
    prev = Image.open(frames[i0 - 1]).convert("L").crop(roi).resize((110, 110))
    vals = {}
    for i in range(i0, i1 + 1):
        im = Image.open(frames[i]).convert("L").crop(roi).resize((110, 110))
        vals[i] = sum(ImageChops.difference(im, prev).getdata()) / (110.0 * 110)
        prev = im
    peak = max(vals, key=lambda k: vals[k])
    thr = vals[peak] * 0.12
    j = peak
    while j - 1 in vals and vals[j - 1] > thr and (peak - j) < 8:
        j -= 1
    return j / float(FPS)


def run_windows(src, dst, marks, lead=0.12):
    """marks: [{"xy":[x,y], "roi":[l,t,r,b], "win":[lo,hi]}]"""
    frames = extract(src, SP + "/tapwork")
    contacts = []
    for m in marks:
        st = onset_in(frames, tuple(m["roi"]), m["win"][0], m["win"][1])
        contacts.append(st - lead)
        print("反應起始 %.3f -> 接觸 %.3f" % (st, st - lead))
    out = SP + "/tapout"
    if os.path.isdir(out):
        for f in glob.glob(out + "/*.jpg"):
            os.remove(f)
    else:
        os.makedirs(out)
    for i, f in enumerate(frames):
        t = i / float(FPS)
        im = Image.open(f).convert("RGBA")
        for m, c in zip(marks, contacts):
            dt = t - c
            h = m.get("hold", 0.0)
            if -PRE - h <= dt <= POST:
                im = Image.alpha_composite(im, ring(im.size, dt, m["xy"][0], m["xy"][1], h))
        im.convert("RGB").save(out + "/f%04d.jpg" % i, quality=94)
    subprocess.run([FF, "-y", "-framerate", str(FPS), "-i", out + "/f%04d.jpg",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", dst],
                   capture_output=True)
    print("寫出", dst)
    return contacts


if __name__ == "__main__":
    cfg = json.loads(sys.argv[1])
    if "marks" in cfg:
        run_windows(cfg["src"], cfg["dst"], cfg["marks"], cfg.get("lead", 0.12))
    else:
        run(cfg["src"], cfg["dst"], [tuple(p) for p in cfg["points"]],
            tuple(cfg["roi"]), cfg.get("from", 0.0), cfg.get("lead", 0.10))
