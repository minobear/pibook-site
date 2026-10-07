#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""創意素材影片（產品頁標題／搜尋結果）的配樂：與畫面同長（一張照片一小節）、首尾無縫的原創循環。

Apple 的說法：搜尋結果裡一律靜音、產品頁預設靜音（使用者可以打開）—— 所以畫面本身就要成立，
聲音只是「品牌的質感」：一小段循環的音樂，不要重的音效、不要突然的大聲。

- 音色、樂器、和弦全部沿用預覽影片的配樂（site/press/video/music.py，「紙與木」：木琴、和弦墊、
  輕的大鼓與沙鈴，C 大調）—— 從標題影片點開預覽影片，聽起來是同一家。
- 80 BPM：一小節 3 秒＝畫面上一張照片的週期；六張一輪＝六小節（C – G – Am – F – C – G）＝ 18 秒，
  最後的 G 接回開頭的 C。
- 每張照片收進相簿的那一刻放 App 自己的「收進相簿」音效（assets/sfx/file_away.wav）。
- 無縫：整段算三輪、加殘響之後只取中間那一輪 —— 開頭帶著上一輪的殘響尾巴，接回去聽不出接縫。

用法：python loop_music.py [小節數，預設 6]   → build/creative/loop_<秒數>s.wav
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'video'))
import music as M  # noqa: E402

BPM = 80
BEAT = 60 / BPM            # 0.75 秒
BAR = BEAT * 4             # 3 秒＝一張卡
FILE_AT = 1.12             # 每小節第幾秒照片收進相簿（與 Remotion 的 T.land 相同）
# 和弦：C – G – Am – F 一路循環（取 music.py 的同一組和弦配置）。小節數＝照片張數，由 make_creative 傳進來；
# 六小節＝ C G Am F C G，最後的 G 接回開頭的 C
CYCLE = [0, 1, 2, 3]


def prog(bars):
    return [CYCLE[i % len(CYCLE)] for i in range(bars)]


def out_path(bars):
    return os.path.abspath(os.path.join(HERE, '..', '..', '..', 'build', 'creative', f'loop_{round(BAR * bars)}s.wav'))


def one_pass_events(bars):
    """一輪的所有音：(訊號, 起點秒, 增益, 聲像)。只算一次、三輪都放同一份 ——
    music.py 的樂器帶隨機相位與槌擊雜訊，每輪各算一次會差一點點，接縫就會「喀」一聲。"""
    ev = []
    for b, ci in enumerate(prog(bars)):
        c = M.CHORDS[ci]
        bs = b * BAR
        # 和弦墊：整小節，前後略為重疊，換和弦不留空
        for f in c['pad']:
            pad = M.pad_note(M.NOTE[f], BAR + 0.5)
            ev.append((pad[:, 0], bs - 0.1, 0.05, -0.35))
            ev.append((pad[:, 1], bs - 0.1, 0.05, 0.35))
        # 低音：第一拍
        ev.append((M.bass_note(M.NOTE[c['bass']], BEAT * 2.2), bs, 0.16, 0.0))
        # 木琴分解和弦：八分音符，第一拍稍重
        for i, f in enumerate(c['arp']):
            vel = 0.36 if i % 4 == 0 else 0.24
            ev.append((M.marimba(M.NOTE[f], 0.9, vel), bs + i * BEAT / 2, 0.42, -0.2 + 0.4 * (i % 2)))
        # 輕的大鼓（第一拍）＋沙鈴（八分音符，反拍稍重）
        ev.append((M.kick(0.55), bs, 0.32, 0.0))
        for i in range(8):
            ev.append((M.shaker(0.5 if i % 2 else 0.3), bs + i * BEAT / 2, 0.09, 0.3))
        # 照片收進相簿的那一刻：App 自己的「收進相簿」音效
        ev.append((FILE_AWAY, bs + FILE_AT, M.SFX_GAIN['file_away'] * 0.85, 0.0))
    return ev


FILE_AWAY = M.load_sfx('file_away')


def main(bars=6):
    loop = BAR * bars
    n = int(round(loop * 3 * M.SR)) + M.SR
    buf = np.zeros((n, 2))
    events = one_pass_events(bars)
    for k in range(3):
        for sig, t, g, pan in events:
            M.place(buf, sig, k * loop + t, gain=g, pan=pan)
    ir = M.reverb_ir(1.6, 1.4)
    wet = M.convolve(buf, ir)
    mix = buf * 0.85 + wet * 0.22
    a = int(round(loop * M.SR))
    seg = mix[a:2 * a]
    # 手機喇叭放不出的超低頻濾掉（與預覽影片的配樂同一個處理），再把峰值壓在 −1 dBFS 以下
    for ch in range(2):
        seg[:, ch] = M.bandpass(seg[:, ch], 45, None)
    peak = np.abs(seg).max()
    seg = seg / peak * 10 ** (-1.5 / 20)
    rms = 20 * np.log10(np.sqrt((seg ** 2).mean()))
    # 比預覽影片的配樂再安靜一點（−20 dBFS 左右）：這裡是背景，不是主角
    target = -20.0
    if rms > target:
        seg = seg * 10 ** ((target - rms) / 20)
    M.write_wav(out_path(bars), seg)
    print(f'✓ {out_path(bars)}  {len(seg) / M.SR:.3f}s  rms {20 * np.log10(np.sqrt((seg ** 2).mean())):.1f} dBFS')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
