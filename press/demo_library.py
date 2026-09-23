#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商店截圖用的示範圖庫 —— 一包可以直接存進手機的照片與影片。

為什麼有這支（2026-09-21）
────────────────────────
商店截圖改成在實機上拍。App 的每一個畫面都是從相簿長出來的，所以相簿本身要先
「演得像一個真實使用者」：
- 最近十天有密集的日常（首頁的「近 7 天」、整理卡片、圖庫的日期分組）。
- 有**同一次拍攝的連拍**（相似照片要有東西可以分組、挑最佳）—— 這裡刻意挑 Pexels
  上同一位攝影師同一場拍攝的連號照片，秒數只差幾秒，不是複製同一張。
- 往年的同一天（9/21–9/28 × 2023–2025 各有照片），「N 年前的今天」才有內容。
- 一部分照片帶地點，回憶頁與「附近」才不會都是「無位置資訊」。

拍攝時間與地點寫在 EXIF（DateTimeOriginal、OffsetTimeOriginal、GPS）。
iPhone 從「檔案」App 存進照片、Android 複製進 DCIM，都會照 EXIF 的時間歸位。

素材全部來自 Pexels（Pexels 授權：免費、可商用、不需標註來源）。
⛔ 使用者 2026-08-30 規定：素材不得有裸露（泳裝、裸上身都算）—— 挑選時已排除。

用法
────
  python demo_library.py                 # 以 2026-09-21 為「今天」產生
  python demo_library.py --shift-days 5  # 整包往後平移 5 天（晚幾天才拍時用）
輸出：build/store_demo_library/（主 repo 已忽略 build/）與同名 .zip。
"""

import argparse
import concurrent.futures as cf
import datetime as dt
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image, ExifTags
from PIL.TiffImagePlugin import IFDRational

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CACHE = REPO / 'build' / 'store_demo_cache'
OUT = REPO / 'build' / 'store_demo_library'

TZ = dt.timezone(dt.timedelta(hours=8))   # 台灣時間

# 地點（大致的位置就好，回憶頁顯示的是反查出來的地名）
GPS = {
    'daan': (25.0268, 121.5434),        # 大安區的咖啡廳
    'daanpark': (25.0296, 121.5358),    # 大安森林公園
    'zhongshan': (25.0526, 121.5203),
    'ximen': (25.0421, 121.5081),
    'raohe': (25.0509, 121.5777),       # 饒河夜市
    'shilin': (25.0880, 121.5241),      # 士林夜市
    'xiangshan': (25.0275, 121.5760),   # 象山（看 101）
    'xinyi': (25.0339, 121.5645),
    'yangmingshan': (25.1557, 121.5478),
    'tamsui': (25.1686, 121.4389),
    'dadaocheng': (25.0580, 121.5070),
    'flowers': (25.0357, 121.5372),     # 建國假日花市
    'hehuan': (24.1422, 121.2715),      # 合歡山
    'bangkok': (13.7563, 100.5018),
}

# (Pexels 照片 id, 拍攝時間（台灣）, 地點)
# 同一分鐘、只差幾秒的那幾張＝同一次連拍 —— 相似照片的分組就是從這裡來的。
PHOTOS = [
    # ── 最近十天（首頁「近 7 天」、整理卡片、圖庫） ──────────────────
    ('6747870', '2026-09-21 08:42:10', 'daan'),        # 拿鐵拉花
    ('36005727', '2026-09-21 12:35:40', 'zhongshan'),  # 朋友在戶外座位
    ('765082', '2026-09-21 19:20:05', None),           # 晚餐
    ('5709521', '2026-09-20 11:05:12', 'daan'),        # 咖啡廳聊天
    ('5709242', '2026-09-20 11:07:48', 'daan'),
    ('36161182', '2026-09-20 15:22:30', 'ximen'),      # 吃點心
    ('27086303', '2026-09-20 18:40:12', None),         # ┐ 廚房自拍連拍
    ('27086312', '2026-09-20 18:40:14', None),         # │
    ('27087259', '2026-09-20 18:40:17', None),         # │
    ('27087246', '2026-09-20 18:40:21', None),         # ┘
    ('6954056', '2026-09-20 19:32:05', None),          # ┐ 朋友聚餐
    ('6954066', '2026-09-20 19:32:09', None),          # │
    ('6955635', '2026-09-20 19:33:40', None),          # │
    ('6955644', '2026-09-20 19:35:02', None),          # ┘
    ('8298421', '2026-09-19 10:15:02', 'daanpark'),    # ┐ 公園長椅全家福連拍
    ('8297670', '2026-09-19 10:15:04', 'daanpark'),    # │
    ('8297668', '2026-09-19 10:15:07', 'daanpark'),    # │
    ('8297498', '2026-09-19 10:16:30', 'daanpark'),    # │
    ('8298457', '2026-09-19 10:17:12', 'daanpark'),    # ┘
    ('14267667', '2026-09-19 14:10:25', 'daan'),       # 手搖飲
    ('7478010', '2026-09-19 19:05:18', 'raohe'),       # ┐ 夜市
    ('6147642', '2026-09-19 19:12:40', 'raohe'),       # │
    ('19044497', '2026-09-19 19:20:03', 'raohe'),      # │
    ('35651725', '2026-09-19 19:31:55', 'raohe'),      # │
    ('6147640', '2026-09-19 19:40:12', 'raohe'),       # ┘
    ('7336949', '2026-09-18 20:05:10', None),          # ┐ 生日派對連拍
    ('7336946', '2026-09-18 20:05:12', None),          # │
    ('7336963', '2026-09-18 20:05:15', None),          # │
    ('7336935', '2026-09-18 20:07:30', None),          # ┘
    ('116835', '2026-09-17 07:55:20', None),           # 貓
    ('16705976', '2026-09-17 19:45:10', 'xiangshan'),  # ┐ 101 夜景
    ('16705978', '2026-09-17 19:45:25', 'xiangshan'),  # ┘
    ('3693769', '2026-09-17 21:10:44', None),          # 貓
    ('34345889', '2026-09-17 21:12:05', None),
    ('39537967', '2026-09-16 09:10:30', 'xinyi'),      # 咖啡
    ('20693276', '2026-09-16 12:30:12', None),         # 午餐
    ('36627096', '2026-09-16 19:05:48', None),
    ('31240501', '2026-09-15 07:40:02', 'daanpark'),   # 遛狗
    ('34470228', '2026-09-15 07:45:36', 'daanpark'),
    ('8535898', '2026-09-15 16:20:03', 'daanpark'),    # 小孩溜滑梯
    ('8535889', '2026-09-15 16:21:40', 'daanpark'),
    ('6412836', '2026-09-14 15:30:10', None),          # 手搖飲
    ('13232354', '2026-09-14 18:02:33', 'tamsui'),     # 夕陽
    ('8532284', '2026-09-13 09:40:18', 'yangmingshan'),  # 爬山
    ('35689607', '2026-09-13 10:20:05', 'yangmingshan'),
    ('34533758', '2026-09-13 11:05:47', 'yangmingshan'),
    ('7669128', '2026-09-13 15:00:04', 'daanpark'),    # ┐ 野餐連拍
    ('7669177', '2026-09-13 15:00:09', 'daanpark'),    # │
    ('7669136', '2026-09-13 15:02:40', 'daanpark'),    # ┘
    ('7972386', '2026-09-12 16:30:02', 'ximen'),       # ┐ 街頭自拍連拍
    ('7973102', '2026-09-12 16:30:05', 'ximen'),       # │
    ('7972656', '2026-09-12 16:30:08', 'ximen'),       # │
    ('7972660', '2026-09-12 16:30:11', 'ximen'),       # ┘
    ('14651120', '2026-09-12 17:05:22', 'ximen'),      # 街景
    ('14685532', '2026-09-12 17:20:09', 'ximen'),

    # ── 上個月、上上個月（「近 30 天」與圖庫往下捲） ────────────────
    ('4881141', '2026-08-30 10:12:05', 'bangkok'),     # ┐ 曼谷旅行
    ('4881139', '2026-08-30 10:12:09', 'bangkok'),     # │
    ('4881147', '2026-08-30 11:40:20', 'bangkok'),     # │
    ('4881140', '2026-08-30 11:41:02', 'bangkok'),     # │
    ('4881164', '2026-08-30 13:05:44', 'bangkok'),     # ┘
    ('4881005', '2026-08-29 16:30:15', 'bangkok'),
    ('4881126', '2026-08-29 17:10:38', 'bangkok'),
    ('1317364', '2026-08-23 20:31:05', 'dadaocheng'),  # 煙火
    ('27068360', '2026-08-23 20:33:12', 'dadaocheng'),
    ('19720556', '2026-08-23 20:40:48', 'dadaocheng'),
    ('37796899', '2026-08-16 10:05:30', 'flowers'),    # 花市
    ('37796901', '2026-08-16 10:07:02', 'flowers'),
    ('3912425', '2026-08-09 15:10:18', None),          # 在家
    ('7114420', '2026-08-09 15:40:55', None),
    ('4617316', '2026-08-09 16:05:12', None),
    ('37576109', '2026-07-26 17:20:40', None),         # 朋友出遊
    ('20424752', '2026-07-26 17:25:03', None),
    ('33867307', '2026-07-26 17:40:29', None),
    ('19328868', '2026-07-12 11:00:14', 'zhongshan'),  # 早午餐
    ('5865690', '2026-07-12 11:02:37', 'zhongshan'),

    # ── 往年的同一天（9/21–9/28 × 2025、2024、2023）：「N 年前的今天」 ──
    ('36713424', '2025-09-21 14:30:12', 'daanpark'),
    ('13637596', '2025-09-22 17:55:40', 'xiangshan'),
    ('29020872', '2025-09-23 09:12:05', None),
    ('13335936', '2025-09-24 10:40:33', 'hehuan'),
    ('3937644', '2025-09-25 19:40:02', None),          # ┐ 聚餐
    ('3937667', '2025-09-25 19:40:06', None),          # ┘
    ('5275834', '2025-09-26 16:10:48', None),
    ('8889021', '2025-09-27 15:20:05', None),          # ┐ 自拍
    ('8889026', '2025-09-27 15:20:09', None),          # ┘
    ('16652400', '2025-09-28 08:30:20', 'daanpark'),
    ('5119589', '2024-09-21 11:10:40', 'daanpark'),
    ('4901940', '2024-09-22 10:30:15', 'bangkok'),
    ('34052564', '2024-09-23 10:05:30', 'zhongshan'),
    ('38867600', '2024-09-24 20:20:12', 'shilin'),
    ('1557697', '2024-09-25 16:45:03', None),
    ('16642634', '2024-09-26 18:05:44', 'xiangshan'),
    ('23495684', '2024-09-27 19:30:01', None),         # ┐ 生日
    ('23495685', '2024-09-27 19:30:04', None),         # ┘
    ('27530256', '2024-09-28 20:15:37', 'dadaocheng'),
    ('34360871', '2023-09-21 08:45:10', None),
    ('8794812', '2023-09-22 13:20:48', None),
    ('132263', '2023-09-23 19:10:05', None),
    ('12940112', '2023-09-24 15:05:22', None),
    ('28849884', '2023-09-25 11:20:40', 'xinyi'),
    ('11720365', '2023-09-26 18:30:18', 'xiangshan'),
    ('31139336', '2023-09-27 09:00:33', None),
    ('16420129', '2023-09-28 16:40:12', None),

    # ── 更早（圖庫的深度） ───────────────────────────────────────
    ('6324292', '2026-06-14 14:20:05', 'yangmingshan'),
    ('9578720', '2026-06-01 13:10:44', None),
    ('33735812', '2026-05-10 16:00:18', 'ximen'),
    ('4127427', '2026-04-05 12:40:30', 'daanpark'),
    ('11947714', '2026-02-14 15:30:12', None),
    ('8054853', '2025-12-25 18:00:40', None),
    ('5506093', '2025-07-19 11:00:05', 'yangmingshan'),
    ('949592', '2025-01-01 00:00:20', 'xinyi'),
]

# (Pexels 影片 id, 檔名後綴, 拍攝時間, 地點)：回憶頁第一個分頁就是影片
VIDEOS = [
    ('7102473', 'hd_1080_1920_30fps', '2026-09-19 10:25:30', 'daanpark'),   # 公園裡跳舞
    ('6864596', 'hd_1080_2048_25fps', '2026-09-17 21:15:02', None),         # 貓
    ('20267649', 'hd_1080_1920_60fps', '2025-09-23 20:10:40', 'xiangshan'), # 101 夜景
    ('7189543', 'hd_1080_1920_25fps', '2025-09-26 09:30:12', 'daanpark'),   # 狗鑽隧道
    ('8901124', 'hd_1080_1920_25fps', '2024-09-22 19:00:05', None),         # 生日蛋糕
    ('17492725', 'hd_1080_1920_30fps', '2023-09-24 20:30:48', 'dadaocheng'),  # 煙火
]

LONG_EDGE = 3000    # 接近手機原圖的大小，壓縮與省空間的數字才像真的
QUALITY = 90

README = """拍簿 Pibook 示範圖庫（商店截圖用）

內容：{photos} 張照片、{videos} 支影片（素材來自 Pexels，免費可商用）。
拍攝時間與地點已寫在檔案裡，存進手機後會自動排到對應的日期。
設計給 {today} 前後幾天拍截圖用：最近十天、往年同一天都有照片。

iPhone
1. 把這個 zip 存到「檔案」App，點一下解壓縮。
2. 打開資料夾 → 右上「⋯」→「選擇」→「全選」→ 分享 →「儲存 N 個項目」。
3. 拍完截圖後：照片 App →「最近儲存」→ 全選 → 刪除，再到「最近刪除」清掉。

Android
1. 解壓縮後，把整個資料夾複製到手機的 DCIM 底下。
2. 拍完後刪掉那個資料夾。
"""


def _gps_ifd(lat, lon):
    def dms(v):
        v = abs(v)
        d = int(v)
        m = int((v - d) * 60)
        s = round(((v - d) * 60 - m) * 60 * 100)
        return (IFDRational(d, 1), IFDRational(m, 1), IFDRational(s, 100))
    return {0: b'\x02\x03\x00\x00',
            1: 'N' if lat >= 0 else 'S', 2: dms(lat),
            3: 'E' if lon >= 0 else 'W', 4: dms(lon)}


def _download(url, dst):
    # 用 curl 而不是 urllib：這台 Windows 上 Python 3.9 的憑證庫過期了，
    # urllib 會 CERTIFICATE_VERIFY_FAILED（curl 走系統的憑證，沒有這個問題）。
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + '.part')
    subprocess.run(['curl', '-s', '-f', '-L', '--retry', '3', '-o', str(tmp), url], check=True)
    tmp.replace(dst)
    return dst


def _when(s, shift):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S') + dt.timedelta(days=shift)


def build_photo(pid, when, place, out_dir):
    src = _download(
        f'https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg'
        f'?auto=compress&cs=tinysrgb&w=2400',
        CACHE / 'photos' / f'{pid}.jpg')
    im = Image.open(src).convert('RGB')
    im.thumbnail((LONG_EDGE, LONG_EDGE), Image.LANCZOS)
    stamp = when.strftime('%Y:%m:%d %H:%M:%S')
    exif = Image.Exif()
    exif[0x0132] = stamp                                  # DateTime
    exif[ExifTags.IFD.Exif] = {0x9003: stamp, 0x9004: stamp,   # DateTimeOriginal/Digitized
                               0x9010: '+08:00', 0x9011: '+08:00', 0x9012: '+08:00'}
    if place:
        exif[ExifTags.IFD.GPSInfo] = _gps_ifd(*GPS[place])
    name = out_dir / f'IMG_{when:%Y%m%d_%H%M%S}.jpg'
    im.save(name, quality=QUALITY, exif=exif, optimize=True)
    ts = when.replace(tzinfo=TZ).timestamp()
    os.utime(name, (ts, ts))
    return name


def build_video(vid, variant, when, place, out_dir):
    src = _download(
        f'https://videos.pexels.com/video-files/{vid}/{vid}-{variant}.mp4',
        CACHE / 'videos' / f'{vid}-{variant}.mp4')
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = 'ffmpeg'
    local = when.replace(tzinfo=TZ)
    utc = local.astimezone(dt.timezone.utc)
    name = out_dir / f'VID_{when:%Y%m%d_%H%M%S}.mp4'
    args = [ffmpeg, '-v', 'error', '-y', '-i', str(src), '-map', '0', '-c', 'copy',
            '-map_metadata', '-1',
            '-metadata', f'creation_time={utc:%Y-%m-%dT%H:%M:%S.000000Z}',
            '-movflags', 'use_metadata_tags',
            '-metadata', f'com.apple.quicktime.creationdate={local:%Y-%m-%dT%H:%M:%S%z}']
    if place:
        lat, lon = GPS[place]
        args += ['-metadata', f'com.apple.quicktime.location.ISO6709={lat:+08.4f}{lon:+09.4f}/']
    args.append(str(name))
    subprocess.run(args, check=True)
    ts = local.timestamp()
    os.utime(name, (ts, ts))
    return name


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('--shift-days', type=int, default=0,
                    help='整包往後平移幾天（晚幾天才拍時用）')
    a = ap.parse_args()

    today = dt.date(2026, 9, 21) + dt.timedelta(days=a.shift_days)
    folder = OUT / f'Pibook示範圖庫_{today:%m%d}'
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    with cf.ThreadPoolExecutor(8) as ex:
        jobs = [ex.submit(build_photo, pid, _when(t, a.shift_days), place, folder)
                for pid, t, place in PHOTOS]
        jobs += [ex.submit(build_video, vid, var, _when(t, a.shift_days), place, folder)
                 for vid, var, t, place in VIDEOS]
        done = [j.result() for j in jobs]

    names = {p.name for p in done}
    if len(names) != len(done):
        raise SystemExit('有兩個檔案撞到同一秒 —— 檢查 PHOTOS 裡的時間')

    (folder / '先看我.txt').write_text(
        README.format(photos=len(PHOTOS), videos=len(VIDEOS),
                      today=f'{today.month}/{today.day}'),
        encoding='utf-8')

    zip_path = folder.with_suffix('.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as z:   # JPEG／MP4 本來就壓過了
        for p in sorted(folder.iterdir()):
            z.write(p, f'{folder.name}/{p.name}')
    size = sum(p.stat().st_size for p in folder.iterdir())
    print(f'✓ {len(PHOTOS)} 張照片、{len(VIDEOS)} 支影片，共 {size / 1e6:.0f} MB')
    print(f'  {zip_path}')

    # 手機版：拆成幾個 30 MiB 以下的 zip —— 對話傳檔到手機端的上限是 30 MiB，
    # 超過的只會出現在桌面 App。每一包都是完整可獨立解壓的 zip（不是分卷壓縮）。
    parts_dir = OUT / f'分批_{today:%m%d}'
    if parts_dir.exists():
        shutil.rmtree(parts_dir)
    parts_dir.mkdir()
    readme = folder / '先看我.txt'
    media = [p for p in folder.iterdir() if p != readme]
    cap = int(29.4 * 1024 * 1024) - readme.stat().st_size - 64 * 1024
    bins = []
    for p in sorted(media, key=lambda p: p.stat().st_size, reverse=True):
        s = p.stat().st_size
        for b in bins:
            if b[0] + s <= cap:
                b[0] += s
                b[1].append(p)
                break
        else:
            bins.append([s, [p]])
    for i, (_, group) in enumerate(bins, 1):
        part = parts_dir / f'{folder.name}_{i}of{len(bins)}.zip'
        with zipfile.ZipFile(part, 'w', zipfile.ZIP_STORED) as z:
            for p in sorted(group + [readme]):
                z.write(p, f'{folder.name}/{p.name}')
    print(f'  手機版：{parts_dir}（{len(bins)} 包）')


if __name__ == '__main__':
    main()
