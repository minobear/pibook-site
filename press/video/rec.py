# -*- coding: utf-8 -*-
"""商店預覽影片的「慢動作錄影」：錄得到的每一格都是 App 真的畫出來的。

為什麼要這樣錄（2026-10-02）
────────────────────────────
模擬器上 App 每秒只畫得出約 20–24 張不同的畫面，舊版素材的掉幀就是這樣來的
（不是錄影工具的問題 —— 主機端錄 60 fps，其中四成是重複格）。
所以改成：裝一顆帶 `PIBOOK_CAPTURE_DILATION=4` 的錄影包（動畫、手勢速度、影片播放
一起慢 4 倍，見 `lib/core/config/capture_time_dilation.dart`），手勢也照 4 倍慢做，
錄完把時間軸壓回 1/4。每秒 24 張 × 4 ＝ 每秒 96 張真畫面，取 30 fps 時每一格都獨立。

流程
────
1. 錄：主機端 `adb emu screenrecord`（不吃模擬器裡的 CPU，比 guest 的 screenrecord 快）。
   錄影本身用 24fps 就夠（慢 8 倍時，成片每一格對應 0.27 秒真實時間）；開 60fps 時編碼器會跟不上、
   自己漏格（回憶頁的影片就是這樣出現停格的）。
   同時在裝置上跑手勢腳本；腳本每個動作前後都記一筆時間（裝置時鐘）。
2. 對時：裝置時鐘 ↔ 主機時鐘量一次差；錄影起點的延遲用「第一個動作造成的第一個畫面變化」
   校正（導演腳本 §3 的作法）。
3. 還原：`setpts=PTS/4` → `fps=30`，輸出 H.264（crf 12）。
4. 驗：逐格比對，動作期間不准有任何一格跟前一格一樣（=掉幀）。

用法（被 shoot.py 呼叫；也可以單獨跑）
  python rec.py check <clip.mp4>          # 掉幀檢查
"""
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import shoot_locale as sl  # noqa: E402

# 慢動作倍率。錄影包啟動時讀 /data/data/<pkg>/files/capture_dilation（set_dilation 寫的），
# 所以這裡跟 App 端永遠是同一個數。4 吸收不掉模擬器偶發 0.13–0.27 秒的停頓 → 用 8。
K = int(os.environ.get('PB_K', '8'))
FPS = 30
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
RAW = os.path.join(ROOT, 'build', 'app_preview_raw')
_RC = os.path.join(HERE, '..', 'remotion', 'node_modules', '@remotion', 'compositor-win32-x64-msvc')
FFPROBE = os.path.join(_RC, 'ffprobe.exe')
# Remotion 附的 ffmpeg 沒有 libx264；編碼用 imageio-ffmpeg 帶的完整版
try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = os.path.join(_RC, 'ffmpeg.exe')
DEV_LOG = '/data/local/tmp/ev.log'
# 成片只留 App 畫面：裁掉頂端狀態列（含主機端錄影才看得到的鏡頭開孔黑點）與底部手勢列。
# 跟商店截圖同一個規格（2026-09-23 起兩個商店都不畫任何系統列），iOS／Play 共用同一份素材。
CROP = (0, 100, 1080, 2360)

# 裝置上的腳本開頭：ev <標籤> 會在記錄檔寫一行「標籤 奈秒」
HEADER = f'''rm -f {DEV_LOG}
ev() {{ echo "$1 $(date +%s%N)" >> {DEV_LOG}; }}
'''


def slow(sec):
    """自然時間 → 錄影時要等的真實時間。"""
    return round(sec * K, 3)


# ── 手勢（全部是「自然時間」，內部乘上 K）──────────────────────────
# 每個動作在記錄檔留兩行：「B <序號> <種類> 座標…」與「E <序號> <種類>」，
# 之後換算成成片時間軸上的觸控指示（Remotion 畫）。
_seq = [0]


def _wrap(kind, args, cmd):
    _seq[0] += 1
    i = _seq[0]
    a = ' '.join(str(v) for v in args)
    return [f'ev "B {i} {kind} {a}"'] + cmd + [f'ev "E {i} {kind}"']


def tap(x, y):
    return _wrap('tap', (x, y), [f'input tap {x} {y}'])


def swipe(x1, y1, x2, y2, ms):
    real = int(ms * K)
    return _wrap('swipe', (x1, y1, x2, y2), [f'input swipe {x1} {y1} {x2} {y2} {real}'])


def hold(x, y, ms):
    """長按。注意：長按的判定是真實時間的 Timer（約 500ms 真實時間就成立），
    慢動作下等於 125ms —— 成片裡看起來是「按一下就跳選單」。指示圈會畫完整的按住過程。"""
    real = int(ms * K)
    return _wrap('hold', (x, y), [f'input swipe {x} {y} {x} {y} {real}'])


def double_tap(x, y):
    # 雙擊的判定窗是真實時間（300ms）—— 兩下之間不能放慢
    return _wrap('dtap', (x, y), [f'input tap {x} {y} &', 'sleep 0.12', f'input tap {x} {y}', 'wait'])


def wait(sec):
    return [f'sleep {slow(sec)}']


def motion(points, hold_end=0.0):
    """自訂軌跡的拖曳：points 是 [(x, y), …]。input motionevent 每一筆都要開一次行程
    （約 0.1–0.3 秒），所以只適合慢的、不需要精準速度的拖曳（例如拖到一半停住）。"""
    cmd = [f'input motionevent DOWN {points[0][0]} {points[0][1]}']
    cmd += [f'input motionevent MOVE {x} {y}' for x, y in points[1:]]
    if hold_end:
        cmd.append(f'sleep {slow(hold_end)}')
    cmd.append(f'input motionevent UP {points[-1][0]} {points[-1][1]}')
    flat = [v for p in (points[0], points[-1]) for v in p]
    return _wrap('drag', flat, cmd)


# ── 錄影 ─────────────────────────────────────────────────────────────
def _host_dev_offset():
    """裝置時鐘 − 主機時鐘（秒）。取三次裡來回最短的那一次。"""
    best = None
    for _ in range(5):
        t0 = time.time()
        d = int(sl.sh('date +%s%N').strip()) / 1e9
        t1 = time.time()
        if best is None or t1 - t0 < best[0]:
            best = (t1 - t0, d - (t0 + t1) / 2)
    return best[1]


def record(name, body, lead=0.6, tail=1.2):
    os.makedirs(RAW, exist_ok=True)
    webm = os.path.join(RAW, f'{name}.webm')
    if os.path.exists(webm):
        os.remove(webm)
    script = HEADER + 'ev "start"\n' + '\n'.join(wait(lead) + body + wait(tail)) + '\nev "end"\n'
    p = os.path.join(sl.TMP, f'rec_{name}.sh')
    os.makedirs(sl.TMP, exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(script)
    sl.adb('push', p, f'/data/local/tmp/rec_{name}.sh')
    offset = _host_dev_offset()
    win = webm.replace('\\', '/')     # 模擬器主控台會把反斜線當跳脫字元
    sl.adb('emu', 'screenrecord', 'start', '--fps', os.environ.get('PB_CAP_FPS', '24'), '--bit-rate', '25M', '--time-limit', '180', win)
    host_start = time.time()
    sl.sh(f'sh /data/local/tmp/rec_{name}.sh')
    sl.adb('emu', 'screenrecord', 'stop')
    for _ in range(40):                      # 編碼器把檔案寫完需要一點時間
        time.sleep(0.5)
        if os.path.exists(webm) and os.path.getsize(webm) > 0:
            s1 = os.path.getsize(webm)
            time.sleep(1.0)
            if os.path.getsize(webm) == s1:
                break
    events = []
    for line in sl.sh(f'cat {DEV_LOG}').splitlines():
        m = re.match(r'(.*) (\d{15,})$', line.strip())
        if m:
            # 錄影檔時間軸上的秒數（未校正錄影起點延遲）
            events.append((m.group(1), int(m.group(2)) / 1e9 - offset - host_start))
    meta = {'name': name, 'k': K, 'events': events}
    with open(os.path.join(RAW, f'{name}.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    sl.log('錄好', name, f'{os.path.getsize(webm) / 1e6:.1f} MB', f'{len(events)} 筆事件')
    return meta


# ── 還原成原速 ───────────────────────────────────────────────────────
def _gray_frames(path, w=108, h=240, vsync='passthrough'):
    p = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f'scale={w}:{h}', '-vsync', vsync,
                        '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8)
    return a.reshape(-1, h, w).astype(np.int16)


def _pts(path):
    out = subprocess.run([FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    return [float(x.strip(',')) for x in out.split() if x.strip(',') and x.strip(',') != 'N/A']


def first_change_after(path, t_raw, roi=None, thr=0.8):
    """錄影檔裡 t_raw 秒之後第一個「畫面開始變」的時間（原始時間軸）。"""
    f = _gray_frames(path)
    ts = _pts(path)
    n = min(len(f), len(ts))
    for i in range(1, n):
        if ts[i] < t_raw:
            continue
        a, b = f[i - 1], f[i]
        if roi:
            x0, y0, x1, y1 = roi
            a = a[int(y0 * 240):int(y1 * 240), int(x0 * 108):int(x1 * 108)]
            b = b[int(y0 * 240):int(y1 * 240), int(x0 * 108):int(x1 * 108)]
        if np.abs(a - b).mean() > thr:
            return ts[i]
    return None


def retime(name, calib_id=None, calib_roi=None, calib_thr=0.8, speed=1.0):
    """慢動作 → 原速 30fps。事件時間換算到成片時間軸並校正錄影起點延遲。

    speed < 1：成片要比真實操作慢（例如開場的捲動要撐久一點）。直接從慢動作原檔取格，
    不是把 30fps 成片放慢（那樣會重複格）。"""
    webm = os.path.join(RAW, f'{name}.webm')
    meta = json.load(open(os.path.join(RAW, f'{name}.json'), encoding='utf-8'))
    ts = _pts(webm)
    t0 = ts[0] if ts else 0.0
    # 起點延遲（錄影檔時間軸與裝置時鐘之間的常數差）：每個動作之後「第一個畫面變化」都量一次，
    # 取最小的那個 —— App 有時反應得慢（模擬器忙的時候），只看第一個動作會把整批指示圈拖晚。
    # 點擊的反應在 E（指令送出、返回）之後；滑動在 B 之後約 0.25 秒開始動。
    lag = 0.0
    acts = _actions(meta['events'])
    if calib_id is not None:
        acts = [a for a in acts if a['id'] == calib_id]
    lags = []
    for a in acts[:6]:
        ch = first_change_after(webm, a['b'] - 0.3, calib_roi, calib_thr)
        if ch is None:
            continue
        expect = a['e'] + 0.03 if a['kind'] in ('tap', 'dtap') else a['b'] + 0.25
        if ch - expect < 3.0:
            lags.append(ch - expect)
    if lags:
        lag = max(-0.3, min(lags))
    out = os.path.join(RAW, f'{name}.mp4')
    subprocess.run([FF, '-y', '-v', 'error', '-i', webm, '-vf',
                    f'setpts=(PTS-STARTPTS)/{K * speed},fps={FPS},crop={CROP[2] - CROP[0]}:{CROP[3] - CROP[1]}:{CROP[0]}:{CROP[1]}', '-an', '-c:v', 'libx264', '-preset', 'slow',
                    '-crf', '12', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], check=True)
    # 事件 → 成片時間（秒）
    conv = []
    for l, t in meta['events']:
        conv.append((l, round((t + lag - t0) / (K * speed), 4)))
    meta['out_events'] = conv
    meta['lag'] = lag
    with open(os.path.join(RAW, f'{name}.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    sl.log('還原', name, f'起點延遲 {lag:.3f}s')
    return out


def _actions(events):
    """把 B／E 兩行配成一個動作：{id, kind, args, b, e}（錄影檔時間軸，秒）。"""
    acts = {}
    for l, t in events:
        parts = l.split(' ')
        if parts[0] == 'B':
            acts[parts[1]] = {'id': int(parts[1]), 'kind': parts[2], 'args': [int(v) for v in parts[3:]], 'b': t}
        elif parts[0] == 'E' and parts[1] in acts:
            acts[parts[1]]['e'] = t
    return [a for a in acts.values() if 'e' in a]


def taps_out(name):
    """成片時間軸上的觸控清單（給 Remotion 畫觸控指示）。"""
    meta = json.load(open(os.path.join(RAW, f'{name}.json'), encoding='utf-8'))
    out = []
    for a in _actions(meta['out_events']):
        out.append({'kind': a['kind'], 'args': a['args'], 'b': round(a['b'], 3), 'e': round(a['e'], 3)})
    return out


# ── 掉幀檢查 ─────────────────────────────────────────────────────────
def check(path, still=0.15, move=3.0, report=True):
    """回傳動作期間的重複格（掉幀）清單：[(格號, 秒)]。

    判準：前後兩格都在明顯地動（差異 > move），中間這一格卻跟前一格幾乎一樣（< still）
    —— 也就是「動、停、動」。真正的靜止（使用者停下來看）不算；動畫收尾時次像素級的
    緩慢移動（差異 < 3）偶爾會有一格沒變，肉眼看不出來，也不算。"""
    f = _gray_frames(path, vsync='cfr')
    d = np.array([np.abs(f[i] - f[i - 1]).mean() for i in range(1, len(f))])
    bad = []
    for i in range(1, len(d) - 1):
        if d[i] < still and d[i - 1] > move and d[i + 1] > move:
            bad.append((i + 1, round((i + 1) / FPS, 2)))
    if report:
        moving = int((d > move).sum())
        print(f'{os.path.basename(path)}: {len(f)} 格，動作中 {moving} 格，掉幀 {len(bad)} 格', bad[:12])
    return bad


def flashes(path):
    """閃黑：某一格突然整片變暗、前後兩格都正常（模擬器上原生影片元件開始移動的那一格）。"""
    f = _gray_frames(path, vsync='cfr')
    m = np.array([fr[40:200, 10:98].mean() for fr in f])
    return [i for i in range(1, len(m) - 1) if m[i] < 12 and m[i - 1] > 30 and m[i + 1] > 30]


def fix_flashes(name):
    """把閃黑的那一格換成前一格（等於動作晚一格開始，不會變成停格）。"""
    out = os.path.join(RAW, f'{name}.mp4')
    bad = flashes(out)
    if not bad:
        return []
    tmp = out.replace('.mp4', '_fx.mp4')
    # freezeframes 要兩路輸入（第二路提供替換用的格）：[0] 分成 n+1 路，一格一格串下去
    n = len(bad)
    parts = [f'[0:v]split={n + 1}' + ''.join(f'[s{k}]' for k in range(n + 1))]
    cur = 's0'
    for k, i in enumerate(bad):
        parts.append(f'[{cur}][s{k + 1}]freezeframes=first={i}:last={i}:replace={i - 1}[f{k}]')
        cur = f'f{k}'
    subprocess.run([FF, '-y', '-v', 'error', '-i', out, '-filter_complex', ';'.join(parts), '-map', f'[{cur}]',
                    '-an', '-c:v', 'libx264', '-preset', 'slow',
                    '-crf', '12', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, out)
    sl.log('閃黑換成前一格', name, bad)
    return bad




def fill_scroll_drop(name, idx, band, dx):
    """掉幀（「動、停、動」裡停住的那一格）補成「前一格的那一條帶子往左平移 dx」。
    給整條橫向捲動的東西用（壓縮成果頁的前後對比列）：帶子以外不動，邊緣 18px 混回原圖。
    ⚠️ 不要拿 ffmpeg minterpolate 補：重複紋理的捲動列它會配錯對應點，補出來那一格整條糊掉（r6_done 試過）。
    dx＝前後兩格位移的一半（用 check 的那一格前後做互相關量出來）。"""
    out = os.path.join(RAW, f'{name}.mp4')
    w, h = _size(out)
    fs = w * h * 3
    y0, y1 = band
    tmp = out.replace('.mp4', '_fx.mp4')
    dec = subprocess.Popen([FF, '-v', 'error', '-i', out, '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                            '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    frames, n, prev = {}, 0, None
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        if n == idx + 1:
            # 拿到後一格才補得出停住的那一格
            a, b_ = frames[idx - 1], fr
            f = a.copy()
            f[y0:y1, :w - dx] = a[y0:y1, dx:]
            f[y0:y1, w - dx:] = b_[y0:y1, w - 2 * dx:w - dx]
            bl = 18
            for k in range(bl):
                al = (k + 1) / (bl + 1)
                for y in (y0 + k, y1 - 1 - k):
                    f[y] = (a[y].astype(float) * (1 - al) + f[y].astype(float) * al).astype(np.uint8)
            enc.stdin.write(f.tobytes())
        if n == idx - 1:
            frames[n] = fr.copy()
        if n != idx:
            enc.stdin.write(buf)
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    os.replace(tmp, out)
    sl.log('掉幀補一格（平移）', name, idx, band, dx)

def _size(path):
    r = subprocess.run([FF, '-i', path], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    m = re.search(r'Video:.*?, (\d{2,5})x(\d{2,5})', r)
    return int(m.group(1)), int(m.group(2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1] == 'check':
        for p in sys.argv[2:]:
            check(p)
            print('  閃黑', flashes(p))


def set_dilation():
    """把倍率寫進 App 的 files 資料夾（快照還原會換掉整個 files，所以每次還原之後都要寫）。"""
    sl.root()
    d = f'/data/data/{sl.PKG}/files'
    uid = sl.sh(f'stat -c %u /data/data/{sl.PKG}').strip()
    sl.sh(f'mkdir -p {d} && echo {K} > {d}/capture_dilation && chown {uid}:{uid} {d} {d}/capture_dilation '
          f'&& restorecon -R {d}')
    sl.root(False)


# ── App 資料快照（每一段開錄前回到同一個起點）────────────────────────
def snapshot(tag, save):
    """跟 shoot_locale.snapshot 一樣，只是檔名可以指定（不動截圖那份 base）。"""
    sl.root()
    sl.sh(f'am force-stop {sl.PKG}')
    d = f'/data/data/{sl.PKG}'
    tar = f'/data/local/tmp/pibook_{tag}.tar'
    if save:
        sl.sh(f'cd {d} && tar -cf {tar} app_flutter shared_prefs files 2>/dev/null')
    else:
        uid = sl.sh(f'stat -c %u {d}').strip()
        sl.sh(f'cd {d} && rm -rf app_flutter shared_prefs files && tar -xf {tar} '
              f'&& chown -R {uid}:{uid} app_flutter shared_prefs files && restorecon -R {d}')
    sl.root(False)


# ── 交給 Remotion ───────────────────────────────────────────────────
REMOTION = os.path.join(HERE, '..', 'remotion')


def export(names):
    """成片素材複製到 remotion/public/clips/v2/，觸控清單與長度寫進 src/ad/clips.ts。"""
    import shutil
    dst_dir = os.path.join(REMOTION, 'public', 'clips', 'v2')
    os.makedirs(dst_dir, exist_ok=True)
    ts_path = os.path.join(REMOTION, 'src', 'ad', 'clips.ts')
    # 既有的保留（一次只重錄幾段時，其他段不動）
    existing = {}
    if os.path.exists(ts_path):
        txt = open(ts_path, encoding='utf-8').read()
        m = re.search(r'CLIPS_JSON = (\{.*\});', txt, re.S)
        if m:
            existing = json.loads(m.group(1))
    for n in names:
        src = os.path.join(RAW, f'{n}.mp4')
        shutil.copy2(src, os.path.join(dst_dir, f'{n}.mp4'))
        nframes = len(_pts(src))
        existing[n] = {'file': f'clips/v2/{n}.mp4', 'duration': round(nframes / FPS, 3), 'touches': taps_out(n)}
    body = json.dumps(existing, ensure_ascii=False, indent=1)
    with open(ts_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// 由 site/press/video/rec.py export() 產生 —— 不要手改。\n'
                '// 每段實機錄影：檔案、長度（秒）、錄影時記下的手勢（素材時間軸上的秒數）。\n'
                "import type { Touch } from './Phone';\n\n"
                'export type ClipInfo = { file: string; duration: number; touches: Touch[] };\n\n'
                f'const CLIPS_JSON = {body};\n\n'
                'export const CLIPS = CLIPS_JSON as Record<string, ClipInfo>;\n')
    sl.log('匯出', names)
