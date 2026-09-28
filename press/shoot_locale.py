# -*- coding: utf-8 -*-
"""商店截圖：換一個語言，把七張畫板要用的 App 畫面一次拍完。

    python shoot_locale.py base          # 只做一次：關掉引導、存 App 資料快照
    python shoot_locale.py ja            # 拍日文（ko、en… 同理）
    python shoot_locale.py ja --only home,review   # 只重拍其中幾張

前提（見 LOCALIZE.md）：截圖專用模擬器 Pibook_Shots（emulator-5556）已開機、
已裝好不含開發者工具的 release 包、示範圖庫已推好（中文版那一輪的狀態）。

輸出：site/assets/shots/<語言>/ 底下的 home_hd / review_hd / review_rail_hd /
gallery_hd / similar_groups_hd / memory_hd / compress_hd。
縮圖特寫（gallery_badge_hd）與飛進相簿的小照片（review_fly_photo）沒有文字，各語言共用。

設計重點（每一條都是英文版那一輪踩過的）：
- 相簿名不能用 adb 打中日韓字 → 直接在裝置上把資料夾改名（UTF-8 腳本），再到 App 裡補圖示與順序。
- 「已整理」是 App 資料 → 每個語言開始前還原 base 快照，整理記號歸零。
- 影片移出再移回圖庫，加入時間會變成「現在」→ 回憶那兩支移回後用 is_pending 改回拍攝時間。
- 會捲動、會隨機的畫面（壓縮跑馬燈、回憶、相似清單）一律用像素／文字自動挑，不靠人看。
"""
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageStat

DEV = 'emulator-5556'
PKG = 'com.minobear.pibook'
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', 'assets', 'shots'))
TMP = os.path.join(HERE, '_shoot_tmp')
REF = os.path.join(HERE, 'shoot_ref')
ENV = dict(os.environ, MSYS_NO_PATHCONV='1')
CAM = '/sdcard/DCIM/Camera'
HOLD = '/sdcard/Movies/.hold'   # 有 .nomedia，放進去就從圖庫消失

# ── 示範圖庫的分組（檔名在 DCIM/Camera ↔ .hold 之間搬） ─────────────
EXTRA = ['IMG_20260923_203015.jpg', 'IMG_20260923_203522.jpg', 'IMG_20260923_204010.jpg']  # 巴哥犬那三張
BURSTS = [f'IMG_20260923_{t}.jpg' for t in
          ('210510', '210512', '210514', '211830', '211832', '211835', '212503', '212505', '212508')]
MEMV = ['VID_20230923_190510.mp4', 'VID_20240923_203048.mp4']        # 回憶頁那兩支
MEMV_TAKEN = {'VID_20230923_190510.mp4': 1695467110, 'VID_20240923_203048.mp4': 1727094648}
BIGV = ['VID_20260920_161045.mp4', 'VID_20260921_203512.mp4']        # 壓縮用的 4K
OTHERV = ['VID_20260919_211502.mp4', 'VID_20260921_102530.mp4']
ALL = EXTRA + BURSTS + MEMV + BIGV + OTHERV

# 每一張要看得到哪些檔（沒列到的就收進 .hold）
SCENE = {
    'home': OTHERV,
    'review': OTHERV + EXTRA,
    'gallery': OTHERV,
    'similar': OTHERV + BURSTS,
    'memory': MEMV,
    'compress': BIGV + OTHERV + MEMV,
}

# 八本相簿：順序＝相簿軌上的順序；圖示＝編輯頁「免費」區的座標
ALBUM_ICON_XY = [(457, 1406), (125, 1572), (125, 1406), (955, 1406),
                 (457, 1572), (291, 1572), (623, 1572), (789, 1406)]
ALBUMS = {
    'zh': ['家人', '旅行', '最愛', '狗狗', '生日', '美食', '花草', '貓咪'],
    'en': ['Family', 'Travel', 'Favourites', 'Dogs', 'Birthday', 'Food', 'Flowers', 'Cats'],
    'ja': ['家族', '旅行', 'お気に入り', '犬', '誕生日', 'ごはん', '花', '猫'],
    'ko': ['가족', '여행', '즐겨찾기', '강아지', '생일', '음식', '꽃', '고양이'],
    'zh-Hans': ['家人', '旅行', '最爱', '狗狗', '生日', '美食', '花草', '猫咪'],
}
LOCALE_TAG = {'zh': 'zh-Hant-TW', 'en': 'en-US', 'ja': 'ja-JP', 'ko': 'ko-KR', 'zh-Hans': 'zh-Hans-CN'}


# ── adb 與 UI ────────────────────────────────────────────────────────
def adb(*a, out=True, binary=False):
    r = subprocess.run(['adb', '-s', DEV, *a], capture_output=True, env=ENV)
    if binary:
        return r.stdout
    return r.stdout.decode('utf-8', 'replace') if out else None


def sh(cmd):
    return adb('shell', cmd)


def sh_script(body, name='s.sh'):
    """推一支 UTF-8 腳本到裝置上跑 —— 中日韓檔名、連續手勢都走這條。"""
    p = os.path.join(TMP, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)
    adb('push', p, f'/data/local/tmp/{name}')
    return sh(f'sh /data/local/tmp/{name}')


def tap(x, y):
    sh(f'input tap {x} {y}')


def screencap(name):
    data = adb('exec-out', 'screencap', '-p', binary=True)
    p = os.path.join(TMP, name)
    with open(p, 'wb') as f:
        f.write(data)
    return p


def dump():
    for _ in range(6):
        o = adb('exec-out', 'uiautomator', 'dump', '/dev/tty')
        m = re.search(r'(<\?xml.*</hierarchy>)', o, re.S)
        if m:
            nodes = []
            for n in ET.fromstring(m.group(1)).iter('node'):
                b = list(map(int, re.findall(r'\d+', n.get('bounds', ''))))
                label = (n.get('text') or '') + (n.get('content-desc') or '')
                if len(b) == 4:
                    nodes.append((label, tuple(b)))
            return nodes
        time.sleep(1.5)
    return []


def find(pred):
    for label, b in dump():
        if pred(label, b):
            return label, b
    return None


def tap_text(*needles):
    hit = find(lambda l, b: any(n in l for n in needles))
    if hit:
        x1, y1, x2, y2 = hit[1]
        tap((x1 + x2) // 2, (y1 + y2) // 2)
    return hit


# 各語言的引導按鈕字（新語言要加上它自己的「略過／知道了」）
DISMISS = ['Skip', 'Got it', 'Explore on my own', 'スキップ', 'わかりました', '건너뛰기', '알겠어요',
           '跳過', '知道了', '自己逛逛', '跳过']


def dismiss_tips():
    for _ in range(3):
        hit = find(lambda l, b: l.strip() in DISMISS or l.strip().split('\n')[-1] in DISMISS)
        if not hit:
            return
        x1, y1, x2, y2 = hit[1]
        if x2 - x1 >= 1000 and y2 - y1 >= 2000:   # 整片蓋住的教學（回憶頁）：按鈕在畫面中央偏下
            tap(540, 1474)
        else:
            tap((x1 + x2) // 2, (y1 + y2) // 2)
        time.sleep(2)


def wait_for(pred, limit=40):
    t = time.time()
    while time.time() - t < limit:
        if find(pred):
            return True
        time.sleep(2)
    return False


def open_today():
    """首頁「今天」那張卡 → 整理頁；等到相簿軌出現才算數。"""
    for _ in range(3):
        wait_for(lambda l, b: b[0] == 54 and 480 < b[1] < 560)   # 首頁那張卡載好了
        dismiss_tips()
        tap(540, 740)
        if wait_for(lambda l, b: b[0] == 53 and b[1] > 2080, 15):
            time.sleep(2)
            dismiss_tips()
            return True
        restart_app()
    log('進不了整理頁')
    return False


def crop_save(src, dst, box=(0, 100, 1080, 2360)):
    im = Image.open(src).convert('RGB')
    im = im.crop(box)
    if dst.endswith('.png'):
        im.save(dst)
    else:
        im.save(dst, quality=92)


def log(*a):
    print(*a, flush=True)


# ── 裝置狀態 ─────────────────────────────────────────────────────────
def root(on=True):
    adb('root' if on else 'unroot')
    time.sleep(2.5)
    adb('wait-for-device')


def set_date(s):
    root()
    sh("service call alarm 3 s16 Asia/Taipei")
    sh(f"date -s '{s}'")
    root(False)


def set_locale(loc):
    # Android 13 起每個 App 可以有自己的語言，會蓋過系統語言 —— 先清掉，一律跟系統走
    # （2026-09-24：Pibook 被設成了 zh-Hant，切簡中時拍出來全是繁體）
    sh(f'cmd locale set-app-locales {PKG} --locales ""')
    root()
    sh(f'setprop persist.sys.locale {LOCALE_TAG[loc]}')
    sh('stop; start')
    time.sleep(15)
    wait_boot()
    root(False)


def wait_boot(limit=240):
    t = time.time()
    while sh('getprop sys.boot_completed').strip() != '1':
        if time.time() - t > limit:
            raise SystemExit('模擬器沒有回來 —— 可能整個掛了，重開 Pibook_Shots 再跑')
        time.sleep(3)
    time.sleep(5)


def restart_app(wait=12):
    sh(f'am force-stop {PKG}')
    sh(f'monkey -p {PKG} -c android.intent.category.LAUNCHER 1')
    time.sleep(wait)


def rescan():
    sh('content call --uri content://media/ --method scan_volume --arg external_primary')
    time.sleep(6)


def scene(name):
    """照 SCENE 把檔案搬到位，回憶影片搬回來要把加入時間改回拍攝時間。"""
    want = set(SCENE[name])
    lines = [f'mkdir -p {HOLD}; touch {HOLD}/.nomedia']
    for f in ALL:
        if f in want:
            lines.append(f'[ -e {HOLD}/{f} ] && mv {HOLD}/{f} {CAM}/')
        else:
            lines.append(f'[ -e {CAM}/{f} ] && mv {CAM}/{f} {HOLD}/')
    # 壓縮產生的副本（…_1.jpg、…_2.mp4）一律收起來
    # 可能落在 Camera，也可能落在原檔所在的相簿資料夾
    lines.append(f'for f in {CAM}/*_[0-9].jpg {CAM}/*_[0-9].mp4 /sdcard/Pictures/*/*_[0-9].jpg '
                 f'/sdcard/Pictures/*/*_[0-9].mp4; do [ -e "$f" ] && mv "$f" {HOLD}/; done')
    lines.append('true')
    sh_script('\n'.join(lines) + '\n', 'scene.sh')
    rescan()
    if any(v in want for v in MEMV):
        fix_video_dates()


def fix_video_dates():
    rows = sh('content query --uri content://media/external/video/media --projection _id:_display_name')
    for m in re.finditer(r'_id=(\d+), _display_name=(\S+)', rows):
        vid, name = m.group(1), m.group(2)
        if name in MEMV_TAKEN:
            u = f'content://media/external/video/media/{vid}'
            sh(f'content update --uri {u} --bind is_pending:i:1')
            sh(f'content update --uri {u} --bind date_added:l:{MEMV_TAKEN[name]}')
            sh(f'content update --uri {u} --bind is_pending:i:0')


def snapshot(save):
    """App 資料快照：整理記號、引導看過了沒、各種偏好都在這裡。"""
    root()
    sh(f'am force-stop {PKG}')
    d = f'/data/data/{PKG}'
    if save:
        sh(f'cd {d} && tar -cf /data/local/tmp/pibook_base.tar app_flutter shared_prefs files 2>/dev/null')
    else:
        uid = sh(f'stat -c %u {d}').strip()
        sh(f'cd {d} && rm -rf app_flutter shared_prefs files && tar -xf /data/local/tmp/pibook_base.tar '
           f'&& chown -R {uid}:{uid} app_flutter shared_prefs files && restorecon -R {d}')
    root(False)


# ── 相簿：改名（裝置上直接改資料夾）→ App 裡補圖示與順序 ───────────
def rename_albums(loc):
    cur = sh('ls /sdcard/Pictures').split()
    body = []
    for names in ALBUMS.values():
        for i, n in enumerate(names):
            if n in cur and n != ALBUMS[loc][i]:
                dst = f'/sdcard/Pictures/{ALBUMS[loc][i]}'
                # 目標名稱若已有同名空資料夾，mv 會把整本搬「進去」而不是改名 —— 先拿掉
                body.append(f'rmdir "{dst}" 2>/dev/null; mv "/sdcard/Pictures/{n}" "{dst}"')
    if body:
        sh_script('\n'.join(body) + '\n', 'ren.sh')
        rescan()


def sheet_rows(with_toggle=False):
    """相簿清單的每一列：[(名字, 中心 y, 右邊顯示開關的字)]，由上到下。
    拖曳後清單還在動，uiautomator 讀不到 —— 讀到空的就等一下再讀。"""
    for _ in range(4):
        nodes = dump()
        rows = []
        for label, (x1, y1, x2, y2) in nodes:
            if x1 == 0 and x2 == 1080 and y1 > 1100 and y2 - y1 > 100 and '\n' in label:
                cy = (y1 + y2) // 2
                tog = next((l for l, bb in nodes if bb[0] >= 860 and bb[1] <= cy <= bb[3]), '')
                rows.append((cy, label.split('\n')[0], tog))
        if rows:
            rows.sort()
            return [(n, y, t) for y, n, t in rows] if with_toggle else [(n, y) for y, n, t in rows]
        time.sleep(2.5)
    return []


def unhide_all():
    """被藏起來的相簿，開關上的字跟其他列不一樣 —— 點那幾顆（不必知道是哪個語言）。"""
    rows = sheet_rows(True)
    labels = [t for _, _, t in rows]
    if not labels:
        return
    common = max(set(labels), key=labels.count)
    for n, y, t in rows:
        if t != common:
            tap(949, y)
            time.sleep(1.5)
            log('打開被藏起來的相簿', n)


def drag(y1, y2, x=300):
    body = [f'input motionevent DOWN {x} {y1}', 'sleep 0.8']
    body += [f'input motionevent MOVE {x} {y1 + (y2 - y1) * k // 12}' for k in range(1, 13)]
    body += ['sleep 0.4', f'input motionevent UP {x} {y2}']
    sh_script('\n'.join(body) + '\n', 'drag.sh')
    time.sleep(2.5)


def rail_item(name):
    """相簿軌上那一格的中心；看不到就左右捲一下再找。"""
    sh('input swipe 250 2203 1000 2203 200')     # 先捲回最左邊
    time.sleep(1)
    for sweep in (None, (700, 350), (700, 350), (700, 350), (700, 350)):
        if sweep:
            sh(f'input swipe {sweep[0]} 2203 {sweep[1]} 2203 300')
            time.sleep(1.2)
        hit = find(lambda l, b: l == name and b[1] > 2000)
        if hit:
            x1, y1, x2, y2 = hit[1]
            return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def fix_albums(loc):
    names = ALBUMS[loc]
    open_today()
    # 順序：「更多」清單裡長按拖曳，一次把一本搬到正確位置
    tap(116, 2203)
    time.sleep(3)
    tap(838, 846)                  # 排序 → 第一項「自訂順序」（不是自訂的話拖了也不會留下來）
    time.sleep(1.5)
    tap(733, 998)
    time.sleep(2)
    unhide_all()
    for target in range(len(names)):
        rows = sheet_rows()
        order = [n for n, _ in rows]
        if names[target] not in order:
            log('清單裡找不到', names[target], order)
            continue
        cur = order.index(names[target])
        if cur != target:
            drag(rows[cur][1], rows[target][1])
    log('順序', [n for n, _ in sheet_rows()])
    sh('input keyevent 4')
    time.sleep(2)
    # 圖示：相簿軌上長按 → 選單第一項（編輯相簿）→ 點圖示 → 儲存
    for k, n in enumerate(names):
        xy = rail_item(n)
        if not xy:
            log('相簿軌上找不到', n)
            continue
        sh(f'input swipe {xy[0]} {xy[1]} {xy[0]} {xy[1]} 900')
        time.sleep(2)
        head = find(lambda l, b: l == n and b[3] < 2000)
        if not head:
            log('沒有跳出選單', n)
            sh('input keyevent 4')
            continue
        below = sorted((b[1], b) for l, b in dump() if l and b[1] >= head[1][3] - 10 and b[0] < 700)
        x1, y1, x2, y2 = below[0][1]
        tap((x1 + x2) // 2, (y1 + y2) // 2)
        time.sleep(2.2)
        if not find(lambda l, b: 1300 < b[1] and b[3] < 1500 and b[0] < 200):
            log('編輯頁沒開', n, below[0])
        tap(*ALBUM_ICON_XY[k])
        time.sleep(0.8)
        save = find(lambda l, b: b[0] > 800 and b[1] > 2100 and b[3] < 2350)
        tap(*(((save[1][0] + save[1][2]) // 2, (save[1][1] + save[1][3]) // 2) if save else (938, 2243)))
        time.sleep(2.5)
    sh('input swipe 200 2203 900 2203 300')
    time.sleep(1)
    sh('input keyevent 4')
    time.sleep(2)


# ── 各畫面 ───────────────────────────────────────────────────────────
def out(loc, name):
    d = os.path.join(SHOTS, loc)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def shoot_home(loc):
    scene('home')
    restart_app()
    dismiss_tips()
    crop_save(screencap('home.png'), out(loc, 'home_hd.jpg'))


def shoot_review(loc):
    scene('review')
    restart_app()
    open_today()
    p = screencap('review_static.png')
    Image.open(p).convert('RGB').crop((32, 2090, 1048, 2318)).save(out(loc, 'review_rail_hd.png'))
    body = ['input motionevent DOWN 760 1150']
    body += [f'input motionevent MOVE {x} {1150 + (760 - x) // 20}' for x in range(740, 450, -20)]
    body += ['sleep 1.2', 'screencap -p /data/local/tmp/mid.png']
    body += [f'input motionevent MOVE {x} 1150' for x in (560, 660, 760)]
    body += ['input motionevent UP 760 1150']
    sh_script('\n'.join(body) + '\n', 'mid.sh')
    adb('pull', '/data/local/tmp/mid.png', os.path.join(TMP, 'review_mid.png'))
    crop_save(os.path.join(TMP, 'review_mid.png'), out(loc, 'review_hd.jpg'))
    sh('input keyevent 4')
    time.sleep(2)


def shoot_gallery(loc):
    scene('gallery')
    restart_app()
    # 今天那 7 張先整理掉（左滑保留），圖庫縮圖才會有「已整理」的點
    open_today()
    for _ in range(7):
        sh('input swipe 760 1150 150 1180 220')
        time.sleep(1.6)
    time.sleep(3)
    restart_app()
    tap(340, 2297)                 # 底部第二顆：圖庫
    time.sleep(7)
    dismiss_tips()
    crop_save(screencap('gallery.png'), out(loc, 'gallery_hd.jpg'))


def group_tops():
    """每一組標頭列的 top。有的語言標頭是獨立節點（42–1038、高約 89），有的整組合成一個節點
    （32–1049），那種的標頭在節點頂端往下 27px。"""
    tops = []
    for l, b in dump():
        if b[0] == 42 and b[2] == 1038 and 80 <= b[3] - b[1] <= 95:
            tops.append(b[1])
        elif b[0] == 32 and b[2] == 1049 and b[3] - b[1] > 300:
            tops.append(b[1] + 27)
    return sorted(tops)


def shoot_similar(loc):
    scene('similar')
    restart_app(20)                # 連拍組要等分析跑完
    tap(739, 2297)                 # 底部第四顆：工具
    time.sleep(4)
    tap(540, 980)                  # 工具頁最上面那張「相似照片」
    time.sleep(8)
    dismiss_tips()
    tap(383, 352)                  # 相似程度：最寬鬆那一檔
    time.sleep(5)
    wait_for(lambda l, b: b[0] in (32, 42) and b[1] > 450, 30)
    for _ in range(4):
        tops = group_tops()
        if not tops:
            break
        top = tops[0]
        if 555 <= top <= 559:
            break
        d = abs(top - 557) + 37    # 手指要先走過約 37px 的觸控門檻才開始捲
        sign = -1 if top > 557 else 1
        steps = [1500 + sign * d * k // 6 for k in range(1, 7)]
        sh_script('input motionevent DOWN 540 1500\n' +
                  ''.join(f'input motionevent MOVE 540 {y}\n' for y in steps) +
                  f'sleep 0.6\ninput motionevent UP 540 {steps[-1]}\n', 'nudge.sh')
        time.sleep(1.5)
    top = group_tops()[0]
    title = find(lambda l, b: b[1] < 300 and re.search(r'\d+', l) and b[0] > 150)
    n = re.search(r'(\d+)', title[0]).group(1) if title else '?'
    with open(out(loc, 'meta.txt'), 'w', encoding='utf-8') as f:
        f.write(f'similar_groups={n}\n')
    log('相似第一組 top', top, '組數', n)
    crop_save(screencap('similar.png'), out(loc, 'similar_groups_hd.jpg'), (0, top - 43, 1080, top - 43 + 1514))
    sh('input keyevent 4')
    time.sleep(2)


def shoot_memory(loc):
    scene('memory')
    restart_app()
    tap(540, 2297)                 # 底部中間：回憶
    time.sleep(5)
    tap(440, 208)                  # 上方「影片」分頁
    time.sleep(5)
    dismiss_tips()
    for _ in range(4):
        if find(lambda l, b: '2023/09/23' in l):
            break
        sh('input swipe 540 1700 540 500 250')
        time.sleep(4)
    body = ['input motionevent DOWN 470 1850']
    body += [f'input motionevent MOVE 470 {y}' for y in range(1800, 1240, -50)]
    body += ['sleep 1.4', 'screencap -p /data/local/tmp/vm.png']
    body += [f'input motionevent MOVE 470 {y}' for y in (1400, 1600, 1850)]
    body += ['input motionevent UP 470 1850']
    sh_script('\n'.join(body) + '\n', 'vm.sh')
    adb('pull', '/data/local/tmp/vm.png', os.path.join(TMP, 'memory.png'))
    crop_save(os.path.join(TMP, 'memory.png'), out(loc, 'memory_hd.jpg'))


def compressed_count():
    return len(re.findall(r'_\d\.(?:jpg|mp4)', sh(f'ls {CAM}')))


def shoot_compress(loc, day):
    scene('compress')
    set_date(f'2026-09-{day} 10:00:00')   # 每天的免費額度：換一天就重來
    restart_app()
    tap(739, 2297)                 # 底部第四顆：工具
    time.sleep(5)
    tap(540, 1824)                 # 影片壓縮那張卡
    time.sleep(6)
    tap(316, 614); time.sleep(1)   # 最大的兩支（清單依大小排）
    tap(660, 614); time.sleep(1)
    tap(626, 2088); time.sleep(3)  # 下一步：畫質
    tap(540, 2090); time.sleep(3)  # 壓縮
    tap(739, 1324); time.sleep(6)  # 確認框「開始」
    tap(84, 210); time.sleep(3)    # 縮成懸浮球
    tap(410, 202); time.sleep(5)   # 切到照片
    for y in (590, 902):
        for x in (244, 502, 760, 1016):
            tap(x, y); time.sleep(0.7)
    for x in (244, 502):
        tap(x, 1212); time.sleep(0.7)
    tap(626, 2088); time.sleep(3)  # 下一步：目標大小
    tap(540, 2088); time.sleep(3)  # 加入壓縮佇列
    base = compressed_count()
    for _ in range(90):
        time.sleep(10)
        if compressed_count() - base >= 12:
            break
    time.sleep(8)
    tap(974, 1382)                 # 懸浮球 → 成果頁
    time.sleep(5)
    sh_script('for i in $(seq 1 24); do screencap -p /data/local/tmp/cb_$i.png; sleep 0.5; done\n', 'burst.sh')
    ref = Image.open(os.path.join(REF, 'compress_strip.png')).convert('L')
    best = None
    for i in range(1, 25):
        p = os.path.join(TMP, f'cb_{i}.png')
        adb('pull', f'/data/local/tmp/cb_{i}.png', p)
        strip = Image.open(p).convert('L').crop((0, 1340, 1080, 1680))
        score = ImageStat.Stat(ImageChops.difference(strip, ref)).mean[0]
        if best is None or score < best[0]:
            best = (score, p)
    log('跑馬燈最接近參考的那一格', round(best[0], 1))
    crop_save(best[1], out(loc, 'compress_hd.jpg'))
    tap(288, 2226); time.sleep(4)  # 保留原檔
    sh('input keyevent 4')


STEPS = ['home', 'review', 'gallery', 'similar', 'memory', 'compress']


def run_locale(loc, only):
    os.makedirs(TMP, exist_ok=True)
    day = {'en': 24, 'ja': 25, 'ko': 26, 'zh-Hans': 27}.get(loc, 28)
    snapshot(save=False)
    set_date('2026-09-23 21:00:00')
    set_locale(loc)
    rename_albums(loc)
    if 'albums' in only or not only:
        # 目前那張照片在哪幾本相簿，清單就會把那幾本釘在最上面 ——
        # 所以排順序時要讓「不在任何相簿」的巴哥犬當第一張
        scene('review')
        restart_app(15)
        fix_albums(loc)
    for s in STEPS:
        if only and s not in only:
            continue
        log('▶', s)
        if s == 'compress':
            shoot_compress(loc, day)
        else:
            globals()[f'shoot_{s}'](loc)
    set_date('2026-09-23 21:00:00')
    log('完成', loc)


def base():
    """只做一次：目前的 App 狀態（引導都看過了、沒有整理記號）存成快照。"""
    os.makedirs(TMP, exist_ok=True)
    snapshot(save=True)
    log('已存 base 快照')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1]
    only = []
    if '--only' in sys.argv:
        only = sys.argv[sys.argv.index('--only') + 1].split(',')
    if cmd == 'base':
        base()
    else:
        run_locale(cmd, only)
