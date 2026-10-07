# -*- coding: utf-8 -*-
"""預覽影片的配樂：照時間軸合成一首原創曲（完全自有、沒有授權問題）。

    python music.py              # 四個版本全部產生 → remotion/public/music/<版本>.wav
    python music.py appstore     # 只產生一個

## 音色：跟 App 的操作音效同一台「紙與木」

App 的音效（`tool/gen_sfx.dart`）是木琴式的木質基音＋極短的紙質起音、C 大調五聲音階。
影片裡會在每個操作的瞬間疊上那些音效，所以配樂也用同一個調（C 大調）、同一種木質音色：
任何一個操作音疊在配樂上都不會不協和。

- 木琴（主音色）：正弦基頻＋約 4 倍的泛音（木琴的特徵）＋極短的槌擊雜訊，指數衰減。
- 鋪底：溫暖的和弦墊（去掉高頻的鋸齒波疊加），慢起音。
- 低音：正弦＋二三倍泛音（手機喇叭放不出基頻，泛音讓它聽得到）。
- 打擊：輕的大鼓、拍手、沙鈴。不用電子感的合成鼓組。

## 結構（照 `remotion/src/ad/timeline.json`）

- 開場（一小節）：只有和弦墊與往上爬的木琴、一點上升的空氣聲 —— 痛點的那兩秒是「懸著」的。
- 第一個功能出現的那一拍「進拍」：鼓、低音、木琴樂句一起進來。C – G – Am – F 一小節一個和弦。
  後半段多一條高音木琴的旋律，讓尾段不單調。
- 結尾卡：停鼓，木琴琶音落在 C 大三和弦上，自然收掉。

100 BPM（一拍 0.6 秒）—— 每段功能的長度都是整數拍，畫面切換永遠落在拍點上。
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TIMELINE = os.path.join(HERE, '..', 'remotion', 'src', 'ad', 'timeline.json')
OUT_DIR = os.path.join(HERE, '..', 'remotion', 'public', 'music')
SR = 44100
rng = np.random.default_rng(20261003)

# ── 音高 ─────────────────────────────────────────────────────────────
NOTE = {}
for octave in range(1, 8):
    for i, name in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']):
        NOTE[f'{name}{octave}'] = 440.0 * 2 ** ((octave - 4) + (i - 9) / 12)

# 一小節一個和弦：C – G – Am – F
CHORDS = [
    {'pad': ['C4', 'E4', 'G4'], 'bass': 'C2', 'arp': ['C5', 'G4', 'E5', 'G4', 'C5', 'D5', 'E5', 'G5'],
     'mel': ['E6', 'G6']},
    {'pad': ['B3', 'D4', 'G4'], 'bass': 'G2', 'arp': ['B4', 'G4', 'D5', 'G4', 'B4', 'C5', 'D5', 'G5'],
     'mel': ['D6', 'G6']},
    {'pad': ['C4', 'E4', 'A4'], 'bass': 'A2', 'arp': ['C5', 'A4', 'E5', 'A4', 'C5', 'D5', 'E5', 'A5'],
     'mel': ['C6', 'E6']},
    {'pad': ['A3', 'C4', 'F4'], 'bass': 'F2', 'arp': ['A4', 'F4', 'C5', 'F4', 'A4', 'C5', 'D5', 'A5'],
     'mel': ['A5', 'C6']},
]


# ── 小工具 ───────────────────────────────────────────────────────────
def bandpass(x, lo, hi):
    """FFT 帶通（一次性的短音用，不需要即時濾波器）。"""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    w = np.ones_like(f)
    if lo:
        w *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        w *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * w, n)


def ramp(n, ms):
    k = min(n, int(SR * ms / 1000))
    r = np.ones(n)
    if k > 0:
        r[:k] = np.linspace(0, 1, k)
    return r


def place(buf, sig, t, gain=1.0, pan=0.0):
    """把單聲道訊號放進立體聲緩衝區（等功率聲像）。"""
    i = int(round(t * SR))
    if i >= buf.shape[0] or i + len(sig) <= 0:
        return
    s0 = max(0, -i)
    sig = sig[s0:]
    i = max(0, i)
    n = min(len(sig), buf.shape[0] - i)
    a = (pan + 1) * np.pi / 4
    buf[i:i + n, 0] += sig[:n] * gain * np.cos(a)
    buf[i:i + n, 1] += sig[:n] * gain * np.sin(a)


# ── 樂器 ─────────────────────────────────────────────────────────────
def marimba(f, dur=0.9, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tau = float(np.clip(0.42 * (440 / f) ** 0.6, 0.09, 0.7))
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
         + 0.34 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / (tau * 0.28))
         + 0.10 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t / (tau * 0.1)))
    s *= ramp(n, 1.5)
    k = int(0.006 * SR)
    click = bandpass(rng.standard_normal(k), f * 2, f * 10) * np.exp(-np.arange(k) / (0.0015 * SR)) * 0.25
    s[:k] += click
    return s * vel


def glock(f, dur=1.2, vel=1.0):
    """鐘琴：非諧和泛音（2.76、5.40 倍），比木琴亮、尾巴長 —— 後半段的旋律用。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.55)
         + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.2)
         + 0.18 * np.sin(2 * np.pi * 5.40 * f * t) * np.exp(-t / 0.08))
    return s * ramp(n, 1) * vel


def hat():
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 7000, 14000) * np.exp(-t / 0.018)


def pad_note(f, dur, detune_cents=7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch, dc in ((0, -detune_cents), (1, detune_cents)):
        ff = f * 2 ** (dc / 1200)
        s = np.zeros(n)
        k = 1
        while ff * k < 6000:
            s += np.sin(2 * np.pi * ff * k * t + rng.uniform(0, 6.28)) / k * np.exp(-k * ff / 2200)
            k += 1
        out[:, ch] = s
    env = np.minimum(1, t / 0.28) * np.minimum(1, (dur - t) / 0.45).clip(0, 1)
    return out * env[:, None]


def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.22 * np.sin(2 * np.pi * 3 * f * t)
    env = ramp(n, 4) * (0.55 + 0.45 * np.exp(-t / 0.12)) * np.minimum(1, (dur - t) / 0.05).clip(0, 1)
    return np.tanh(1.4 * s * env) * 0.8


def kick(vel=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 50 + 75 * np.exp(-t / 0.032)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.2)
    s += np.sin(2 * ph) * 0.35 * np.exp(-t / 0.06)       # 手機喇叭聽得到的那一層
    k = int(0.004 * SR)
    s[:k] += bandpass(rng.standard_normal(k), 1500, 6000) * 0.25
    return s * vel


def clap(vel=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = bandpass(rng.standard_normal(n), 1000, 9000)
    env = np.zeros(n)
    for d in (0, 0.009, 0.019):
        env += (t >= d) * np.exp(-np.maximum(t - d, 0) / 0.012) * 0.6
    env += (t >= 0.024) * np.exp(-np.maximum(t - 0.024, 0) / 0.09)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.25
    return (noise * env * 0.5 + body) * vel


def shaker(vel=1.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    s = bandpass(rng.standard_normal(n), 4500, 10000)
    env = np.minimum(1, t / 0.008) * np.exp(-t / 0.03)
    return s * env * vel


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    seg = int(0.05 * SR)
    noise = rng.standard_normal(n)
    for i in range(0, n, seg):          # 分段帶通，中心頻率往上爬
        c = 600 * (8 ** (i / n))
        s[i:i + seg] = bandpass(noise[i:i + seg + 0], c * 0.6, c * 1.6)[:len(s[i:i + seg])]
    env = (t / dur) ** 2.2
    return s * env


def impact():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (45 + 30 * np.exp(-t / 0.08)) * t) * np.exp(-t / 0.35)
    air = bandpass(rng.standard_normal(n), 3000, 12000) * np.exp(-t / 0.5) * 0.18
    return boom * 0.7 + air


def thud():
    """開場「儲存空間塞滿」的那一下：比進拍的撞擊更悶、更短（不是警報聲）。"""
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (52 + 40 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.18)
    knock = bandpass(rng.standard_normal(n), 180, 900) * np.exp(-t / 0.04) * 0.35
    return boom * 0.8 + knock


def breath(dur=0.75):
    """嘆氣：一口吐出來的氣（帶通雜訊，起得快、慢慢收；音高略往下走）。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    seg = int(0.03 * SR)
    for i in range(0, n, seg):
        c = 1400 * (0.55 ** (i / n))
        out[i:i + seg] = bandpass(noise[i:i + seg], c * 0.5, c * 1.8)[:len(out[i:i + seg])]
    env = np.minimum(1, t / 0.06) * np.exp(-t / (dur * 0.38))
    return out * env


def whoosh(dur=2.6):
    """小飛機飛過：輕的風聲，音高先升後降；聲像由左到右（回傳立體聲）。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    mono = np.zeros(n)
    seg = int(0.03 * SR)
    for i in range(0, n, seg):
        x = i / n
        c = 900 + 1800 * np.sin(np.pi * x)
        mono[i:i + seg] = bandpass(noise[i:i + seg], c * 0.6, c * 1.5)[:len(mono[i:i + seg])]
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    mono *= env
    pan = np.clip(t / dur, 0, 1) * 1.6 - 0.8
    left = mono * np.sqrt((1 - pan) / 2)
    right = mono * np.sqrt((1 + pan) / 2)
    return np.stack([left, right], axis=1)


SYNTH = {'thud': (thud, 0.55), 'breath': (breath, 0.5), 'whoosh': (whoosh, 0.32)}


def reverb_ir(dur=1.5, t60=1.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for ch in range(2):
        x = rng.standard_normal(n) * np.exp(-6.9 * t / t60)
        ir[:, ch] = bandpass(x, 200, 6000)
    ir[:int(0.012 * SR)] = 0                      # 預延遲
    return ir / np.sqrt((ir ** 2).sum(axis=0)).max()


def convolve(x, ir):
    n = len(x) + len(ir) - 1
    m = 1 << (n - 1).bit_length()
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch], m) * np.fft.rfft(ir[:, ch], m), m)[:n]
    return out[:len(x)]


# ── 編曲 ─────────────────────────────────────────────────────────────
def render(segments, bpm, seg_defs=None):
    beat = 60 / bpm
    bar = beat * 4
    step = beat / 4                                  # 十六分音符
    total = sum(d for _, d, *rest in segments)
    t_drop = segments[0][1]                          # 開場結束＝進拍
    t_end = total - segments[-1][1]                  # 結尾卡開始
    n = int((total + 0.05) * SR)
    dry = np.zeros((n, 2))       # 不進殘響
    wet = np.zeros((n, 2))       # 進殘響
    pad = np.zeros((n, 2))       # 會被大鼓壓（側鏈）
    bass = np.zeros((n, 2))
    duck = np.ones(n)

    # 開場：F 和弦墊（懸著）→ 木琴往上爬到進拍
    intro_pad = sum(pad_note(NOTE[x], t_drop + 0.4) for x in ['A3', 'C4', 'F4'])
    place(pad, intro_pad[:, 0] * 0.07, 0.0, pan=-0.3)
    place(pad, intro_pad[:, 1] * 0.07, 0.0, pan=0.3)
    climb = ['G4', 'A4', 'C5', 'D5', 'E5', 'G5', 'A5', 'C6']
    for i, x in enumerate(climb):
        tt = t_drop - beat * 2 + i * (beat * 2 / len(climb))
        place(wet, marimba(NOTE[x], 0.6, 0.18 + 0.05 * i), tt, pan=-0.25 + 0.07 * i)
    place(dry, riser(t_drop) * 0.05, 0.0, pan=0.0)

    # 進拍：輕的撞擊
    place(dry, impact() * 0.32, t_drop)

    # 主段：C – G – Am – F
    n_bars = int(np.ceil((t_end - t_drop) / bar - 1e-6))
    for b in range(n_bars):
        t_bar = t_drop + b * bar
        ch = CHORDS[b % 4]
        second_half = b >= 4
        bar_len = min(bar, t_end - t_bar)
        # 和弦墊
        pn = sum(pad_note(NOTE[x], bar_len + 0.5) for x in ch['pad'])
        place(pad, pn[:, 0] * 0.065, t_bar, pan=-0.4)
        place(pad, pn[:, 1] * 0.065, t_bar, pan=0.4)
        for s in range(16):
            t = t_bar + s * step
            if t >= t_end - 1e-6:
                break
            hum = rng.uniform(-0.004, 0.004)
            # 大鼓：1、3 拍，加一個 3 拍前的十六分
            if s in (0, 8):
                place(dry, kick(1.0), t, gain=0.5)
                k = int(0.3 * SR)
                i0 = int(t * SR)
                curve = 1 - 0.38 * np.exp(-np.arange(k) / (0.09 * SR))
                duck[i0:i0 + k] = np.minimum(duck[i0:i0 + k], curve[:len(duck[i0:i0 + k])])
            if s == 7 and b % 2 == 1:
                place(dry, kick(0.55), t, gain=0.5)
            # 拍手：2、4 拍
            if s in (4, 12):
                c = clap(1.0)
                place(dry, c, t + hum, gain=0.34)
                place(wet, c, t + hum, gain=0.10)
            # 沙鈴：十六分，反拍重
            v = 0.55 if s % 2 else 0.28
            place(dry, shaker(v), t + hum + (0.012 if s % 2 else 0), gain=0.3, pan=0.45)
            if s % 4 == 2:                                       # 閉合銅鈸：八分反拍
                place(dry, hat(), t + hum, gain=0.16, pan=-0.35)
            # 低音：1 拍、2 拍的反拍、3 拍
            if s in (0, 6, 8, 14):
                d = {0: beat * 1.4, 6: beat * 0.45, 8: beat * 1.4, 14: beat * 0.45}[s]
                place(bass, bass_note(NOTE[ch['bass']], d), t, gain=0.30)
            # 木琴樂句：八分音符的琶音，留兩個空位喘氣
            if s % 2 == 0 and (s // 2) not in (3, 7):
                x = ch['arp'][s // 2]
                vel = 0.9 if s in (0, 8) else 0.65
                vel *= rng.uniform(0.9, 1.05)
                m = marimba(NOTE[x], 0.8, vel)
                place(dry, m, t + hum, gain=0.24, pan=-0.2 if (s // 2) % 2 else 0.2)
                place(wet, m, t + hum, gain=0.09)
            # 後半段：高音木琴的旋律（1 拍與 3 拍）
            if second_half and s in (0, 8):
                x = ch['mel'][0 if s == 0 else 1]
                m = glock(NOTE[x], 1.4, 0.8)
                place(dry, m, t, gain=0.12, pan=0.35)
                place(wet, m, t, gain=0.11)

    # 結尾卡：停鼓，木琴琶音落在 C 大三和弦上
    for i, x in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']):
        m = marimba(NOTE[x], 2.2, 0.85)
        place(dry, m, t_end + i * 0.045, gain=0.16, pan=-0.3 + 0.15 * i)
        place(wet, m, t_end + i * 0.045, gain=0.12)
    end_pad = sum(pad_note(NOTE[x], total - t_end + 0.3) for x in ['C4', 'E4', 'G4', 'C5'])
    place(pad, end_pad[:, 0] * 0.12, t_end, pan=-0.4)
    place(pad, end_pad[:, 1] * 0.12, t_end, pan=0.4)
    place(bass, bass_note(NOTE['C2'], total - t_end), t_end, gain=0.26)
    place(dry, impact() * 0.22, t_end)

    mix = dry + (pad + bass) * duck[:, None]
    # 高通 45Hz：手機喇叭放不出來的超低頻只會吃掉響度（正規化時算進去，聽到的反而變小聲）
    for ch in range(2):
        mix[:, ch] = bandpass(mix[:, ch], 45, None)
    mix += convolve(wet + pad * 0.35, reverb_ir()) * 0.32
    # 收尾淡出、開頭不爆
    t = np.arange(n) / SR
    fade = np.minimum(1, t / 0.02) * np.clip((total - t) / 0.7, 0, 1)
    mix *= fade[:, None]
    mix -= mix.mean(axis=0)
    music_only = mix
    # 操作音效：配樂先對齊響度，音效以固定比例疊上去，再一起限幅
    body = mix[int(t_drop * SR):int(t_end * SR)]
    mix = mix * (10 ** (-17 / 20) / np.sqrt((body ** 2).mean()))
    if seg_defs is not None:
        mix = mix + sfx_track(segments, seg_defs, n) * 0.5
    # 響度：主段 RMS 對齊 -17 dBFS（動態廣告常見的響度，留空間給操作音效），峰值軟限幅在 -1 dBFS
    body = mix[int(t_drop * SR):int(t_end * SR)]
    rms = np.sqrt((body ** 2).mean())
    mix *= 10 ** (-17 / 20) / rms
    ceil = 10 ** (-1 / 20)
    mix = np.tanh(mix / ceil) * ceil
    return mix, {'total': total, 't_drop': t_drop, 't_end': t_end}


# ── 15 秒短版的專屬編曲（2026-10-07 使用者：「15 秒短版的音樂能不能整個重作、搭配更適合它的版本」）──
# 30 秒版是「C–G–Am–F 循環＋木琴琶音」的從容律動；短版只有四小節主段，循環還沒繞完一圈就結束，聽起來像被剪斷。
# 所以短版寫成一首「有頭有尾的四小節」：
#   開場（一小節）：A 小調的低墊＋時鐘似的木琴八分音（壓力）＋上升的空氣聲；最後半拍抽空、進拍。
#   第 1 小節（滑卡）C、第 2 小節（滑卡收尾→歸檔）Am：四拍大鼓＋2、4 拍手＋切分低音，鐘琴一小節一句的主題。
#   第 3 小節（滑掉最後一張→按壓縮）F→G：拍手變八分往上堆、上升的空氣聲 ——「要來了」。
#   第 4 小節（省回來了）C：落拍一下鈸、主題往上走 —— 整支片子的高點放在成果頁。
#   結尾：停鼓，F→C 的木琴琶音收在 C 大和弦（Amen 終止），小飛機的風聲照舊。
AD15_BARS = [
    # 和弦墊、每一拍的低音根音、鐘琴主題（十六分格位置, 音）
    {'pad': ['C4', 'E4', 'G4'], 'bass': ['C2'] * 4,
     'mel': [(0, 'G5'), (3, 'E5'), (6, 'G5'), (8, 'C6'), (14, 'D6')]},
    {'pad': ['C4', 'E4', 'A4'], 'bass': ['A1'] * 4,
     'mel': [(0, 'A5'), (3, 'E5'), (6, 'A5'), (8, 'C6'), (14, 'B5')]},
    {'pad': ['A3', 'C4', 'F4'], 'pad2': ['B3', 'D4', 'G4'], 'bass': ['F2', 'F2', 'G2', 'G2'],
     'mel': [(0, 'A5'), (3, 'F5'), (6, 'A5'), (8, 'B5'), (11, 'G5'), (14, 'D6')]},
    {'pad': ['C4', 'E4', 'G4', 'C5'], 'bass': ['C2'] * 4,
     'mel': [(0, 'E6'), (3, 'D6'), (6, 'C6'), (8, 'G6'), (12, 'E6')]},
]


def crash():
    n = int(1.8 * SR)
    t = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 3500, 13000) * np.exp(-t / 0.55) * np.minimum(1, t / 0.003)


def render_ad15(segments, bpm, seg_defs=None):
    beat = 60 / bpm
    bar = beat * 4
    step = beat / 4
    total = sum(d for _, d, *rest in segments)
    t_drop = segments[0][1]
    t_end = total - segments[-1][1]
    n = int((total + 0.05) * SR)
    dry = np.zeros((n, 2))
    wet = np.zeros((n, 2))
    pad = np.zeros((n, 2))
    bass = np.zeros((n, 2))
    duck = np.ones(n)

    # 開場：A 小調低墊（有點悶、有點煩）＋時鐘似的木琴八分音，越來越亮；最後半拍抽空
    pre = t_drop - beat * 0.5
    intro = sum(pad_note(NOTE[x], pre + 0.3) for x in ['A3', 'C4', 'E4'])
    place(pad, intro[:, 0] * 0.06, 0.0, pan=-0.3)
    place(pad, intro[:, 1] * 0.06, 0.0, pan=0.3)
    place(bass, bass_note(NOTE['A1'], pre), 0.0, gain=0.16)
    ticks = int(round(pre / (beat / 2)))
    for i in range(ticks):
        x = 'E5' if i % 2 == 0 else 'A4'
        place(dry, marimba(NOTE[x], 0.25, 0.35 + 0.05 * i), i * beat / 2, gain=0.16,
              pan=-0.25 if i % 2 else 0.25)
    place(dry, riser(pre) * 0.06, 0.0)

    # 進拍
    place(dry, impact() * 0.34, t_drop)
    place(dry, crash() * 0.10, t_drop, pan=-0.2)

    n_bars = int(np.ceil((t_end - t_drop) / bar - 1e-6))
    for b in range(n_bars):
        t_bar = t_drop + b * bar
        spec = AD15_BARS[min(b, len(AD15_BARS) - 1)]
        build = b == n_bars - 2          # 倒數第二小節：往上堆
        lift = b == n_bars - 1           # 最後一小節：高點
        bar_len = min(bar, t_end - t_bar)
        if 'pad2' in spec:
            for k, key in enumerate(('pad', 'pad2')):
                pn = sum(pad_note(NOTE[x], bar_len / 2 + 0.4) for x in spec[key])
                place(pad, pn[:, 0] * 0.06, t_bar + k * bar / 2, pan=-0.4)
                place(pad, pn[:, 1] * 0.06, t_bar + k * bar / 2, pan=0.4)
        else:
            pn = sum(pad_note(NOTE[x], bar_len + 0.4) for x in spec['pad'])
            g = 0.075 if lift else 0.06
            place(pad, pn[:, 0] * g, t_bar, pan=-0.4)
            place(pad, pn[:, 1] * g, t_bar, pan=0.4)
        if lift:
            place(dry, crash() * 0.12, t_bar, pan=0.2)
            place(dry, impact() * 0.16, t_bar)
        for s in range(16):
            t = t_bar + s * step
            if t >= t_end - 1e-6:
                break
            hum = rng.uniform(-0.003, 0.003)
            # 大鼓：四拍（短版要一下子就有力）
            if s % 4 == 0:
                place(dry, kick(1.0), t, gain=0.5)
                k = int(0.26 * SR)
                i0 = int(t * SR)
                curve = 1 - 0.42 * np.exp(-np.arange(k) / (0.08 * SR))
                duck[i0:i0 + k] = np.minimum(duck[i0:i0 + k], curve[:len(duck[i0:i0 + k])])
            # 拍手：2、4 拍；往上堆的那一小節後半變八分、越來越大聲
            if s in (4, 12) or (build and s >= 8 and s % 2 == 0):
                v = 1.0 if s in (4, 12) else 0.55 + 0.1 * (s - 8) / 2
                c = clap(v)
                place(dry, c, t + hum, gain=0.32)
                place(wet, c, t + hum, gain=0.10)
            # 沙鈴十六分、閉合銅鈸八分反拍
            place(dry, shaker(0.5 if s % 2 else 0.25), t + hum, gain=0.28, pan=0.45)
            if s % 4 == 2:
                place(dry, hat(), t + hum, gain=0.18, pan=-0.35)
            # 切分低音（3-3-2）：每半小節第 0、3、6 格，第 3 格跳高八度
            if s % 8 in (0, 3, 6):
                root = spec['bass'][s // 4]
                d = beat * (0.7 if s % 8 != 6 else 0.45)
                f = NOTE[root] * (2 if s % 8 == 3 else 1)
                place(bass, bass_note(f, d), t, gain=0.30)
        # 鐘琴主題：一小節一句；木琴同音低八度疊在下面，讓旋律有木頭的厚度
        for pos, x in spec['mel']:
            t = t_bar + pos * step
            if t >= t_end - 1e-6:
                continue
            m = glock(NOTE[x], 1.2, 0.85 if pos in (0, 8) else 0.65)
            place(dry, m, t, gain=0.15 if lift else 0.12, pan=0.3)
            place(wet, m, t, gain=0.12)
            place(dry, marimba(NOTE[x] / 2, 0.5, 0.7), t, gain=0.12, pan=-0.2)
        # 往上堆的那一小節：上升的空氣聲收在下一小節的拍點
        if build:
            place(dry, riser(bar) * 0.07, t_bar)

    # 結尾：停鼓，F → C（Amen 終止），木琴琶音
    for i, x in enumerate(['A4', 'C5', 'F5']):
        m = marimba(NOTE[x], 1.2, 0.7)
        place(dry, m, t_end + i * 0.05, gain=0.14, pan=-0.2 + 0.2 * i)
        place(wet, m, t_end + i * 0.05, gain=0.10)
    f_pad = sum(pad_note(NOTE[x], beat * 2 + 0.4) for x in ['A3', 'C4', 'F4'])
    place(pad, f_pad[:, 0] * 0.09, t_end, pan=-0.4)
    place(pad, f_pad[:, 1] * 0.09, t_end, pan=0.4)
    place(bass, bass_note(NOTE['F2'], beat * 2), t_end, gain=0.24)
    t_c = t_end + beat * 2
    for i, x in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']):
        m = marimba(NOTE[x], 2.0, 0.85)
        place(dry, m, t_c + i * 0.045, gain=0.16, pan=-0.3 + 0.15 * i)
        place(wet, m, t_c + i * 0.045, gain=0.12)
    place(dry, glock(NOTE['G6'], 1.8, 0.6), t_c + 0.25, gain=0.08, pan=0.35)
    c_pad = sum(pad_note(NOTE[x], total - t_c + 0.3) for x in ['C4', 'E4', 'G4', 'C5'])
    place(pad, c_pad[:, 0] * 0.11, t_c, pan=-0.4)
    place(pad, c_pad[:, 1] * 0.11, t_c, pan=0.4)
    place(bass, bass_note(NOTE['C2'], total - t_c), t_c, gain=0.24)
    place(dry, impact() * 0.18, t_end)

    mix = dry + (pad + bass) * duck[:, None]
    for ch in range(2):
        mix[:, ch] = bandpass(mix[:, ch], 45, None)
    mix += convolve(wet + pad * 0.35, reverb_ir()) * 0.30
    t = np.arange(n) / SR
    fade = np.minimum(1, t / 0.02) * np.clip((total - t) / 0.7, 0, 1)
    mix *= fade[:, None]
    mix -= mix.mean(axis=0)
    body = mix[int(t_drop * SR):int(t_end * SR)]
    mix = mix * (10 ** (-17 / 20) / np.sqrt((body ** 2).mean()))
    if seg_defs is not None:
        mix = mix + sfx_track(segments, seg_defs, n) * 0.5
    body = mix[int(t_drop * SR):int(t_end * SR)]
    mix *= 10 ** (-17 / 20) / np.sqrt((body ** 2).mean())
    ceil = 10 ** (-1 / 20)
    mix = np.tanh(mix / ceil) * ceil
    return mix, {'total': total, 't_drop': t_drop, 't_end': t_end}


# ── 操作音效：App 自己的音效（assets/sfx），放在每個手勢「生效」的那一刻 ──────────
SFX_DIR = os.path.join(HERE, '..', '..', '..', 'assets', 'sfx')
CLIPS_TS = os.path.join(HERE, '..', 'remotion', 'src', 'ad', 'clips.ts')
SFX_GAIN = {'keep': 0.55, 'discard': 0.55, 'file_away': 0.5, 'favorite': 0.55, 'tap': 0.4,
            'celebrate': 0.5, 'range_complete': 0.42}


def load_sfx(name):
    with wave.open(os.path.join(SFX_DIR, f'{name}.wav')) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(axis=1)
    return x


def sfx_for(seg_key, touch):
    """這個手勢在 App 裡會發出哪個音（跟 App 的行為一致：保留／丟棄／收進相簿／收藏／點擊）。"""
    kind, a = touch['kind'], touch['args']
    if kind == 'swipe' and seg_key in ('swipe', 'compress'):
        if a[2] < a[0] - 300:
            return 'keep'
        if a[3] > a[1] + 500:
            return 'discard'
        return None
    if kind == 'tap':
        if seg_key == 'similar3':
            # 相似照片比對頁：右邊那顆是保留、左邊那顆是丟棄（App 按下去的聲音也是這兩個）
            if a[1] > 1900:
                return 'keep' if a[0] > 540 else 'discard'
            return 'tap'
        return 'file_away' if seg_key == 'album' else 'tap'
    if kind == 'dtap':
        return 'favorite'
    return None


def sfx_track(segments, seg_defs, n):
    import re
    txt = open(CLIPS_TS, encoding='utf-8').read()
    clips = json.loads(re.search(r'CLIPS_JSON = (\{.*\});', txt, re.S).group(1))
    out = np.zeros((n, 2))
    cache = {}
    t0 = 0.0
    for entry in segments:
        key, dur = entry[0], entry[1]
        d = dict(seg_defs.get(key, {}))
        d.update(entry[2] if len(entry) > 2 else {})
        info = clips.get(d.get('clip', ''))
        if info:
            for tc in info['touches']:
                name = sfx_for(key, tc)
                if not name:
                    continue
                local = (tc['e'] - d['from']) / d['rate']
                if 0 <= local < dur - 0.05:
                    cache.setdefault(name, load_sfx(name))
                    place(out, cache[name], t0 + local, gain=SFX_GAIN[name])
        # 影片自己加的音（開場塞滿的悶響、嘆氣、小飛機飛過）：時間寫段內秒數
        for name, tl in d.get('fx', []):
            fn, g = SYNTH[name]
            sig = fn()
            if sig.ndim == 1:
                place(out, sig, t0 + tl, gain=g)
            else:
                i0 = int((t0 + tl) * SR)
                m = min(len(sig), n - i0)
                if m > 0:
                    out[i0:i0 + m] += sig[:m] * g
        # 不是手勢的音：成果頁打開、數字落定（App 自己在那一刻也會出聲）。時間寫素材時間軸上的秒數
        for name, tc in d.get('cues', []):
            local = (tc - d.get('from', 0)) / d.get('rate', 1)
            if 0 <= local < dur - 0.05:
                cache.setdefault(name, load_sfx(name))
                place(out, cache[name], t0 + local, gain=SFX_GAIN[name])
        t0 += dur
    return out


def write_wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    tl = json.load(open(TIMELINE, encoding='utf-8'))
    names = sys.argv[1:] or list(tl['variants'])
    for name in names:
        segs = tl['variants'][name]
        fn = render_ad15 if name == 'ad15' else render
        mix, info = fn(segs, tl['bpm'], tl.get('segments'))
        path = os.path.join(OUT_DIR, f'{name}.wav')
        write_wav(path, mix)
        peak = 20 * np.log10(np.abs(mix).max())
        rms = 20 * np.log10(np.sqrt((mix ** 2).mean()))
        print(f"{name}: {info['total']:.1f}s（進拍 {info['t_drop']:.1f}s、結尾 {info['t_end']:.1f}s）"
              f" 峰值 {peak:.1f} dBFS、整體 RMS {rms:.1f} dBFS → {os.path.relpath(path)}")


if __name__ == '__main__':
    main()
