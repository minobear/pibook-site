# -*- coding: utf-8 -*-
"""商店預覽影片：每一段實機錄影的「起點」與「腳本」。

    python shoot.py prep              # 只做一次：相簿順序調好、存成 video2 快照
    python shoot.py review            # 整理那一輪：滑卡／歸檔／修圖／分享／壓縮 五段連著錄
    python shoot.py gallery           # 圖庫：縮圖上的記號 → 點一張 → 開始整理
    python shoot.py organised         # 已整理好的相簿：勾兩本 → 套用
    python shoot.py similar           # 相似照片：保留 → 全螢幕左右比對
    python shoot.py memory            # 回憶：往上滑、雙擊愛心

錄影本身與「慢動作 → 原速」的換算在 rec.py。分鏡要求在 ../DIRECTOR_SCRIPT.md。

前提（見 DIRECTOR_SCRIPT.md〈慢動作錄影〉）：Pibook_Shots 模擬器、錄影包
（PIBOOK_CAPTURE_DILATION=4）、繁中、示範圖庫、`today` 那 10 張已換成手機原圖大小。
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rec  # noqa: E402
from rec import tap, swipe, hold, double_tap, wait, motion  # noqa: E402,F401

sl = rec.sl
BIG = os.environ.get('PB_TODAY_DIR') or os.path.join(rec.ROOT, 'build', 'app_preview_big')   # 今天那 10 張的手機原圖版
CAM = '/sdcard/DCIM/Camera'

# 今天那一輪（新到舊＝牌堆順序）
TODAY = ['IMG_20260923_204010', 'IMG_20260923_203522', 'IMG_20260923_203015', 'IMG_20260923_194210',
         'IMG_20260923_180530', 'IMG_20260923_162040', 'IMG_20260923_141020', 'IMG_20260923_113015',
         'IMG_20260923_100550', 'IMG_20260923_084210']

# 相簿軌（整理頁底部）每一格的中心 x；y 固定。順序由 prep() 排好：家人 旅行 美食 最愛 狗狗 生日 …
RAIL_Y = 2203
RAIL_X = {'家人': 274, '旅行': 421, '美食': 568, '最愛': 715, '狗狗': 862}

# 整理卡右下角「展開」鈕與它的選單（修圖／分享／拷貝在上排）
CARD_MORE = (975, 1806)


def reset_media():
    """今天那 10 張回到「都在相機資料夾、內容是原圖」的狀態；壓縮產生的副本收起來。"""
    lines = [f'for f in /sdcard/Pictures/*/IMG_20260923_*.jpg; do [ -e "$f" ] && mv "$f" {CAM}/; done',
             f'mkdir -p {sl.HOLD}; touch {sl.HOLD}/.nomedia',
             f'for f in {CAM}/*_[0-9].jpg {CAM}/*_[0-9].mp4 /sdcard/Pictures/*/*_[0-9].jpg; do '
             f'[ -e "$f" ] && mv "$f" {sl.HOLD}/; done',
             # 連拍組只在相似照片那段放出來（它們也是 9/23 拍的，會混進「今天」那一輪）
             *[f'[ -e {CAM}/{f} ] && mv {CAM}/{f} {sl.HOLD}/' for f in sl.BURSTS],
             'true']
    sl.sh_script('\n'.join(lines) + '\n', 'reset_media.sh')
    # 修圖「覆寫」會改到檔案本身 —— 換回原圖（同路徑覆蓋，id 不變）
    default_big = os.path.join(rec.ROOT, 'build', 'app_preview_big')
    for n in TODAY:
        p = f'{CAM}/{n}.jpg'
        src = os.path.join(BIG, f'{n}.jpg')
        sl.adb('push', src.replace('\\', '/'), p)
        sec = int(n[17:19])
        # 換成別的內容的那幾張（v3.3 丟棄示範用的壞照片，PB_TODAY_DIR）修改時間錯開 2 秒：
        # 修改時間一樣的話，App 與系統相簿的縮圖快取（鑰匙＝id＋修改時間）會一直拿舊的那張出來
        dflt = os.path.join(default_big, f'{n}.jpg')
        if os.path.exists(dflt) and os.path.getsize(dflt) != os.path.getsize(src):
            sec = min(59, sec + 2)
        stamp = f'{n[4:12]}{n[13:17]}.{sec:02d}'
        sl.sh(f'touch -t {stamp} {p}')
    rows = sl.sh("content query --uri content://media/external/images/media --projection _id:_display_name "
                 "--where \"_display_name LIKE 'IMG_20260923%'\"")
    for line in rows.splitlines():
        if '_id=' in line:
            i = line.split('_id=')[1].split(',')[0]
            sl.sh(f'content update --uri content://media/external/images/media/{i} --bind is_pending:i:0')
    sl.rescan()


def reset_app(tag='video2'):
    rec.snapshot(tag, False)
    sl.root()
    # 修圖覆寫的備份與 journal 在 no_backup（不在快照裡）—— 一起清掉，否則選單會多出「還原成原照片」
    sl.sh(f'rm -rf /data/data/{sl.PKG}/no_backup/photo_edit')
    # App 的縮圖磁碟快取（getTemporaryDirectory()/pibook_thumbs）也清掉：示範照片換過內容時不會拿到舊縮圖
    sl.sh(f'rm -rf /data/data/{sl.PKG}/cache/pibook_thumbs')
    sl.root(False)
    rec.set_dilation()


def prep():
    """相簿軌排成 家人 旅行 美食 最愛 狗狗 …（今天那幾張要收的三本都在第一屏），存成 video2。"""
    reset_media()
    rec.snapshot('video', False)
    sl.restart_app(15)
    sl.open_today()
    sl.tap(116, RAIL_Y)
    time.sleep(5)
    rows = sl.sheet_rows()
    order = [n for n, _ in rows]
    if order.index('美食') != 2:
        sl.drag(rows[order.index('美食')][1], rows[2][1])
    sl.log('順序', [n for n, _ in sl.sheet_rows()])
    sl.sh('input keyevent 4')
    time.sleep(3)
    sl.sh('input keyevent 4')
    time.sleep(4)
    rec.snapshot('video2', True)


def open_today_settled():
    sl.restart_app(15)
    sl.open_today()
    time.sleep(6)          # 卡堆、縮圖軌、相簿軌都到齊、動畫停住再開錄


KEEP = (760, 1150, 140, 1190)          # 左滑＝保留
DISCARD = (540, 950, 560, 1950)        # 下滑＝丟棄


def keep(ms=240):
    return swipe(*KEEP, ms)


def discard(ms=260):
    return swipe(*DISCARD, ms)


def take(name, body, live, lead=0.5, tail=0.8):
    """live=False 時只跑手勢不錄（乾跑：量座標、確認狀態）。"""
    if live:
        return rec.record(name, body, lead=lead, tail=tail)
    script = rec.HEADER + '\n'.join(body) + '\n'
    sl.sh_script(script, f'dry_{name}.sh')
    return None


def review_session(live=True, only=None):
    """今天那一輪 10 張，五段連著錄（狀態一路接下去）。"""
    reset_media()
    reset_app()
    open_today_settled()
    want = lambda n: only is None or n in only  # noqa: E731

    # 暖機（不錄）：修圖的 shader、分享面板第一次開都要編譯／解碼，第一次開會停一格。
    # 在同一個行程裡先各開一次再關掉 —— 不會留下任何整理記號。
    warm = (tap(*CARD_MORE) + wait(0.6) + tap(525, 1483) + wait(2.0) + tap(84, 201) + wait(1.2)
            + tap(*CARD_MORE) + wait(0.6) + tap(718, 1483) + wait(2.0) + ['input keyevent 4'] + wait(1.2))
    take('warmup', warm, False)
    time.sleep(3)

    # R1 滑卡（v3.3，2026-10-07 使用者）：保留、保留、丟棄、丟棄 —— 兩張字卡各停一樣久；
    # 丟棄的那兩張要一眼就看得出是不好的照片（PB_TODAY_DIR=build/app_preview_big_v33：手震糊掉、口袋裡誤觸）。
    # 每一下放手的間隔都約 0.7 秒（剪的時候 1.17 倍速＝一拍一下）
    body = keep() + wait(0.45) + keep(230) + wait(0.45) + discard() + wait(0.45) + discard() + wait(0.6)
    take('r1_swipe', body, live and want('r1_swipe'))
    time.sleep(3)

    # R2 歸檔：奶茶 → 美食、健行自拍 → 旅行、溜滑梯的孩子 → 家人（自動換下一張）
    body = []
    for album in ('美食', '旅行', '家人'):
        body += tap(RAIL_X[album], RAIL_Y) + wait(0.95)
    take('r2_album', body, live and want('r2_album'))
    time.sleep(4)

    # R3 修圖：展開 → 修圖 → 自動 → 濾鏡「鮮明」→ 儲存 → 覆寫原照片
    body = (tap(*CARD_MORE) + wait(0.4) + tap(525, 1483) + wait(0.8) + tap(126, 1917) + wait(0.6)
            + tap(880, 2232) + wait(0.45) + tap(808, 2010) + wait(0.75) + tap(974, 201) + wait(0.4)
            + tap(733, 368) + wait(1.0))
    take('r3_edit', body, live and want('r3_edit'))
    time.sleep(5)

    # R4 分享：展開（覆寫過，選單多一列「還原成原照片」，分享往上移）→ 分享 → 版型左右滑三張
    body = tap(*CARD_MORE) + wait(0.45) + tap(718, 1368) + wait(1.1)
    for _ in range(3):
        body += swipe(820, 1100, 300, 1110, 260) + wait(0.6)
    take('r4_share', body, live and want('r4_share'), tail=0.6)
    time.sleep(3)
    sl.sh('input keyevent 4')
    time.sleep(5)

    # R5 收尾：最後三張保留 → 結尾頁 → 「壓縮」（照片飛進懸浮球）
    # 「壓縮」鈕的位置隨結尾頁改版會變（2026-10-07 多了「接著整理『昨天』」，從 y 1519 移到 1470）——
    # 量到的新位置可用 PB_COMPRESS_XY="x,y" 蓋過去（乾跑時 sl.dump() 印得出來）
    cx_, cy_ = (int(v) for v in os.environ.get('PB_COMPRESS_XY', '922,1470').split(','))
    body = keep() + wait(0.45) + keep(230) + wait(0.45) + keep() + wait(1.3) + tap(cx_, cy_) + wait(1.6)
    take('r5_compress', body, live and want('r5_compress'), tail=1.0)
    if not live:
        sl.log([(l, b) for l, b in sl.dump() if l.strip()])


def finish_round_without_compress():
    """（不錄）今天那一輪：照 R1／R2 的決定做完、剩下的保留，但不按壓縮 —— 壓縮的副本會出現在圖庫裡。"""
    body = (keep() + wait(0.5) + keep() + wait(0.5) + discard() + wait(0.5) + keep() + wait(0.5))
    for album in ('美食', '旅行', '家人'):
        body += tap(RAIL_X[album], RAIL_Y) + wait(1.0)
    body += keep() + wait(0.5) + keep() + wait(0.5) + keep() + wait(1.5)
    take('round', body, False)
    time.sleep(4)
    sl.tap(540, 2190)            # 結尾頁「先退出，晚點再刪」→ 首頁
    time.sleep(6)


GALLERY_TAP = (990, 1180)        # 圖庫裡要點開的那一張：9/21 大安森林公園的全家福（沒整理過）


def gallery_session(live=True):
    """圖庫：先停在縮圖上（後製推近、圈出「已整理」與「已加相簿」）→ 點開一張 → 開始整理。"""
    reset_media()
    reset_app()
    open_today_settled()
    finish_round_without_compress()
    sl.tap(340, 2297)            # 底部「圖庫」
    time.sleep(8)
    sl.dismiss_tips()
    time.sleep(4)
    if not live:
        import dev
        dev.snap('gallery_pick', 540)
        return
    # 暖機（不錄）：第一次進瀏覽、第一次長出整理介面都要建一大堆東西，會停一兩格。
    # 先走一遍再關掉（沒有滑卡＝不留任何記號），錄的是第二次。
    sl.tap(*GALLERY_TAP)
    time.sleep(10)
    sl.tap(696, 2203)
    time.sleep(10)
    sl.tap(84, 201)
    time.sleep(8)
    if not sl.find(lambda l, b: l.strip() == '選取'):
        sl.sh('input keyevent 4')
        time.sleep(6)
    time.sleep(4)
    # 第三輪：先停久一點（全景 → 推近 → 圈出標記 → 拉回，標籤要讀得完），再點開
    body = wait(3.4) + tap(*GALLERY_TAP) + wait(0.9) + tap(696, 2203) + wait(1.2)
    take('g_gallery', body, live, lead=0.2, tail=0.8)


def organised_session(live=True):
    """已整理的相簿：首頁「相簿」區 → 已整理的相簿 → 勾三本 → 套用 → 首頁那三本變成「已完成」。"""
    reset_media()
    reset_app()
    sl.restart_app(15)
    for _ in range(3):           # 捲到底：相簿區整個在畫面上（捲到底＝每次停的位置都一樣）
        sl.sh('input swipe 540 1900 540 700 1600')
        time.sleep(3)
    time.sleep(3)
    hit = sl.find(lambda l, b: '已整理的相簿' in l and b[1] > 900)
    if not hit:
        sl.log('找不到「已整理的相簿」入口')
        return
    x1, y1, x2, y2 = hit[1]
    body = (tap((x1 + x2) // 2, (y1 + y2) // 2) + wait(1.0) + tap(540, 666) + wait(0.35) + tap(540, 823)
            + wait(0.35) + tap(540, 981) + wait(0.6) + tap(540, 2082) + wait(1.6))
    take('o_organised', body, live, lead=0.4, tail=0.6)


# 回憶頁「影片」分頁的池子（順序是隨機的 —— 六支都好看，抽到哪支都行；暖機會先用掉兩支）：
# 煙火、生日女孩、101 夜景、狗狗隧道、黑貓、飛盤女孩
MEM_POOL = ['VID_20230926_203048.mp4', 'VID_20240924_190005.mp4', 'VID_20250925_201040.mp4',
            'VID_20250928_093012.mp4', 'VID_20260919_211502.mp4', 'VID_20260921_102530.mp4']
MEM_OUT = ['VID_20230923_190510.mp4', 'VID_20240923_203048.mp4', 'VID_20260920_161045.mp4',
           'VID_20260921_203512.mp4']
# 錄影用的輕量版（導演腳本 P7）：1080p、6 Mbps、**真 30fps** —— 原片有三支是 25fps，放進 30fps 的成片
# 每 6 格就重複一格；改成加速 1.2 倍（不補幀，每一格都是原片的真畫面）。產生方式見 DIRECTOR_SCRIPT.md。
VIDEOS = os.path.join(rec.ROOT, 'build', 'app_preview_videos')
LIGHT = {f: os.path.join(VIDEOS, f) for f in MEM_POOL}


def memory_pool():
    lines = [f'mkdir -p {sl.HOLD}; touch {sl.HOLD}/.nomedia']
    for f in MEM_POOL:
        lines.append(f'[ -e {sl.HOLD}/{f} ] && mv {sl.HOLD}/{f} {CAM}/')
    for f in MEM_OUT:
        lines.append(f'[ -e {CAM}/{f} ] && mv {CAM}/{f} {sl.HOLD}/')
    lines.append('true')
    sl.sh_script('\n'.join(lines) + '\n', 'mem_pool.sh')
    for name, src in LIGHT.items():
        sl.adb('push', src.replace('\\', '/'), f'{CAM}/{name}')
    sl.rescan()
    # 影片的「幾年前」看加入時間：搬進搬出會變成「現在」→ 改回拍攝時間（is_pending 1 → 改 → 0）
    rows = sl.sh('content query --uri content://media/external/video/media --projection _id:_display_name:datetaken')
    for m in __import__('re').finditer(r'_id=(\d+), _display_name=(\S+), datetaken=(\d+)', rows):
        vid, name, taken = m.group(1), m.group(2), int(m.group(3)) // 1000
        u = f'content://media/external/video/media/{vid}'
        sl.sh(f'content update --uri {u} --bind is_pending:i:1')
        sl.sh(f'content update --uri {u} --bind date_added:l:{taken}')
        sl.sh(f'content update --uri {u} --bind is_pending:i:0')
    sl.log(sl.sh('content query --uri content://media/external/video/media --projection _display_name:date_added:_size'))


def memory_session(live=True):
    """回憶：影片分頁 → 停一下 → 往上滑 → 雙擊愛心 → 再往上滑。"""
    reset_media()
    reset_app()
    memory_pool()
    sl.restart_app(15)
    sl.tap(540, 2297)            # 底部「回憶」
    time.sleep(8)
    sl.tap(440, 208)             # 上方「影片」
    time.sleep(8)
    sl.dismiss_tips()
    time.sleep(4)
    # 第二支影片會跳「附近」的引導氣泡（擋住雙擊與上滑）—— 先滑一次讓它出來、關掉
    for _ in range(2):
        sl.sh('input swipe 540 1750 540 600 1600')
        time.sleep(8)
        sl.dismiss_tips()
        time.sleep(3)
    time.sleep(4)
    if not live:
        import dev
        dev.snap('memory_pick', 540)
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:20])
        return
    body = (wait(1.1) + swipe(540, 1750, 540, 600, 230) + wait(1.25) + double_tap(540, 1100) + wait(1.0)
            + swipe(540, 1750, 540, 600, 230) + wait(1.2))
    take('m_memory', body, live, lead=0.3, tail=0.6)


def hook_session(live=True):
    """開場：圖庫一路往下捲（還沒整理過的圖庫，什麼記號都沒有）。"""
    reset_media()
    reset_app()
    sl.restart_app(15)
    sl.tap(340, 2297)            # 底部「圖庫」
    time.sleep(8)
    sl.dismiss_tips()
    time.sleep(5)
    # 手指往上拖 1.3 秒、放手帶一點慣性：整段持續滑過。分好幾次滑的話，每次手指按下都會把捲動
    # 「接住」停一兩格；甩一下又太快（示範圖庫只有約百張，0.7 秒就到底）。
    # ⚠️ 也不能拖得太慢：長按的判定是真實時間 0.5 秒，慢動作下手指還沒移出觸控門檻（47px）
    # 就被當成長按（照片浮起來、清單不動）。
    body = wait(0.2) + swipe(540, 2060, 540, 330, 1300) + wait(1.2)
    take('h_scroll', body, live, lead=0.2, tail=0.4)


def similar_session(live=True):
    """相似照片：自動精選 → 全部（每組最美的打勾、其餘標成待刪）→ 點開一張 → 全螢幕左右滑比對。"""
    reset_media()
    reset_app()
    sl.scene('similar')
    sl.restart_app(40)           # 連拍組要等分析跑完
    for _ in range(4):
        sl.tap(739, 2297)        # 底部「工具」
        time.sleep(6)
        sl.tap(540, 980)         # 「相似照片」
        time.sleep(12)
        sl.dismiss_tips()
        if sl.find(lambda l, b: '6 組' in l):
            break
        sl.log('相似組還沒到齊，等一下再進')
        sl.sh('input keyevent 4')
        time.sleep(30)
    time.sleep(4)
    # 暖機（不錄）：第一次打開全螢幕比對頁要建畫面、解三張大圖，會停一格 —— 先開一次、取消（不改任何選擇）
    sl.tap(536, 800)
    time.sleep(10)
    sl.tap(110, 2145)            # 比對頁左下「取消」
    time.sleep(8)
    # 2026-10-03 第三輪：比對要「往左看一張、再往右看回來」（真人的來回比較），然後按下方的「保留」
    body = (wait(0.5) + tap(200, 2090) + wait(0.45) + tap(120, 1940) + wait(1.1) + tap(536, 800) + wait(0.75)
            + swipe(860, 1100, 220, 1100, 230) + wait(0.65) + swipe(220, 1100, 860, 1100, 230) + wait(0.55)
            + tap(613, 1993) + wait(1.0))
    if not live:
        take('s_similar', body, False)
        time.sleep(3)
        import dev
        dev.snap('similar_after', 540)
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:12])
        return
    take('s_similar', body, live, lead=0.3, tail=0.6)


def _center(hit):
    x1, y1, x2, y2 = hit[1]
    return (x1 + x2) // 2, (y1 + y2) // 2


def compress_done_session(live=True):
    """壓縮完成頁（v3，2026-10-06 使用者：「順手壓縮」之後要接到壓縮完成的成果頁）。

    先照原本那一輪（R1–R5，含修圖覆寫）全部做一次、按下「壓縮」—— 不錄，結尾頁的數字才會跟
    r5_compress 那段一模一樣；等背景壓縮跑完（懸浮球變成打勾），再錄「點懸浮球 → 成果頁長出來」。"""
    review_session(live=False)
    for _ in range(60):                       # 背景壓縮：5–10 張手機原圖，模擬器上約半分鐘到兩分鐘
        time.sleep(5)
        if sl.find(lambda l, b: '壓縮完成' in l):
            break
    else:
        sl.log('壓縮一直沒跑完')
        return
    # 跑完時懸浮球旁會冒「N 個原檔待決定」的提示（第一次還會往下輕推兩下）—— 等它自己收掉再錄
    time.sleep(16)
    hit = sl.find(lambda l, b: '壓縮完成' in l)
    bx, by = _center(hit)
    sl.log('懸浮球', hit)
    if not live:
        import dev
        dev.snap('done_before', 540)
        return
    body = wait(0.6) + tap(bx, by) + wait(3.6)
    take('r6_done', body, live, lead=0.3, tail=0.6)


def similar_done_session(live=True):
    """相似照片的成果頁（v3，2026-10-06 使用者：「比一比」之後要接到省下多少空間、數字在跳的那一頁）。

    先照 s_similar 的操作做一次（自動精選 → 全部 → 點開比對 → 保留，不錄），回到清單，
    再錄「清理 N 張 → 確認 → 成果頁數字從 0 跳到省下的空間」。
    錄影包裝在模擬器上有 MANAGE_MEDIA，移到回收桶不會跳 Android 系統的確認框（那一框不准入鏡：2.3.10）。"""
    reset_media()
    reset_app()
    sl.scene('similar')
    sl.restart_app(40)
    for _ in range(4):
        sl.tap(739, 2297)
        time.sleep(6)
        sl.tap(540, 980)
        time.sleep(12)
        sl.dismiss_tips()
        if sl.find(lambda l, b: '6 組' in l):
            break
        sl.log('相似組還沒到齊，等一下再進')
        sl.sh('input keyevent 4')
        time.sleep(30)
    time.sleep(4)
    sl.tap(536, 800)                          # 暖機：比對頁先開一次再取消
    time.sleep(10)
    sl.tap(110, 2145)
    time.sleep(8)
    body = (wait(0.5) + tap(200, 2090) + wait(0.45) + tap(120, 1940) + wait(1.1) + tap(536, 800) + wait(0.75)
            + swipe(860, 1100, 220, 1100, 230) + wait(0.65) + swipe(220, 1100, 860, 1100, 230) + wait(0.55)
            + tap(613, 1993) + wait(1.0))
    # 錄影時連 s_similar 一起重錄：連拍組換成手機原圖大小（bigify.py）之後，清單上的「佔用 N MB」要跟
    # 成果頁跳出來的數字是同一批檔案算的
    take('s_similar', body, live, lead=0.3, tail=0.6)
    time.sleep(4)
    hit = sl.find(lambda l, b: l.strip() == '套用')
    if hit:
        sl.tap(*_center(hit))
        time.sleep(6)
    clean = sl.find(lambda l, b: '清理' in l and '張' in l and b[1] > 1900)
    sl.log('清理鈕', clean)
    if not clean:
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:30])
        return
    cx, cy = _center(clean)
    if not live:
        sl.tap(cx, cy)
        time.sleep(5)
        import dev
        dev.snap('similar_sheet', 540)
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:30])
        return
    # 一支錄完：清理 → 確認單出來 → 「刪除 N 張」→ 成果頁（剪的時候確認單那一段剪掉，留「點清理」與成果頁）。
    # 確認單上那顆鈕的位置由乾跑量（--dry 會印出來），以 PB_DEL_XY="x,y" 傳進來。
    # 成果頁：數字 0.38 秒開始跳、1.48 秒落定、3.08 秒全部到位 —— 錄到 4 秒以上
    dx, dy = (int(v) for v in os.environ['PB_DEL_XY'].split(','))
    body = wait(0.5) + tap(cx, cy) + wait(1.2) + tap(dx, dy) + wait(4.4)
    take('s2_done', body, live, lead=0.3, tail=0.6)



BURST_BIG = os.path.join(rec.ROOT, 'build', 'app_preview_burst_big')


def push_big_bursts():
    """連拍組換成手機原圖大小（video/bigify.py 產生）。模擬器是唯讀開機（-read-only），
    推上去的檔關機就沒了 —— 每次開機後第一次錄相似照片都要再推一次（2026-10-07 漏過：清單只剩 8.0 MB）。
    推到 .hold（scene('similar') 會搬回相機資料夾），修改時間照檔名的拍攝時間。
    錄過成果頁之後也要再推一次（PB_PUSH_BURSTS=1）：清理會把連拍真的刪進回收桶。"""
    for f in sl.BURSTS:
        src = os.path.join(BURST_BIG, f)
        if not os.path.exists(src):
            sl.log('沒有大圖版', f)
            return
    sl.sh(f'mkdir -p {sl.HOLD}; touch {sl.HOLD}/.nomedia')
    # 錄過成果頁（清理 → 刪除）之後，那幾張是進了系統回收桶（同資料夾的 .trashed-…），不在 .hold —— 一起清掉
    sl.sh(f'rm -f {CAM}/.trashed-*IMG_20260923_21*')
    for f in sl.BURSTS:
        for d in (sl.HOLD, CAM):
            sl.sh(f'rm -f {d}/{f}')
        dst = f'{sl.HOLD}/{f}'
        sl.adb('push', os.path.join(BURST_BIG, f).replace('\\', '/'), dst)
        n = f[4:-4]
        sl.sh(f'touch -t {n[:8]}{n[9:13]}.{n[13:15]} {dst}')
    sl.rescan()



DENSE = os.path.join(rec.ROOT, 'build', 'app_preview_dense')


def push_dense():
    """開場「相簿爆滿」用：多塞 220 張進相機資料夾（示範照片鏡像＋重新取景、色調微調，日期分散在 3–9 月，
    EXIF 拍攝時間跟檔名一致）。2026-10-07 使用者：原本的示範圖庫只有約百張，往下滑到 8 月以後每個月只剩幾張、
    一大片空格，看起來一點都不「爆滿」。只在錄開場時放（唯讀開機，關機就沒了）。"""
    files = sorted(f for f in os.listdir(DENSE) if f.endswith('.jpg'))
    sl.sh('rm -rf /sdcard/DCIM/_dense')
    sl.adb('push', DENSE.replace('\\', '/'), '/sdcard/DCIM/_dense')
    lines = [f'mv /sdcard/DCIM/_dense/{f} {CAM}/{f} && touch -t {f[4:12]}{f[13:17]}.{f[17:19]} {CAM}/{f}'
             for f in files]
    lines.append('rmdir /sdcard/DCIM/_dense; true')
    sl.sh_script('\n'.join(lines) + '\n', 'dense.sh')
    sl.rescan()


def hook2_session(live=True):
    """開場 v3.1：爆滿的圖庫一路往下捲（push_dense 之後，每個月都排滿）。
    手勢同 hook_session（拖 1.3 秒、放手帶慣性）；之後多等一點，讓慣性自己停下來 —— 嘆氣的表情在那時候出現。
    錄的時候 PB_K=8（24 倍時 1.3 秒的拖曳在真實時間裡太慢，手指還沒移出觸控門檻就被當成長按，清單一動也不動），
    還原時用 rec.retime('h_dense', speed=0.6)。"""
    reset_media()
    reset_app()
    push_dense()
    sl.restart_app(40)           # 220 張新照片要先進索引
    sl.tap(340, 2297)            # 底部「圖庫」
    time.sleep(20)
    sl.dismiss_tips()
    time.sleep(8)
    body = wait(0.2) + swipe(540, 2060, 540, 330, 1300) + wait(2.6)
    take('h_dense', body, live, lead=0.2, tail=0.4)

def _open_similar_settled():
    """相似照片頁：示範圖庫的 6 組都分析好、引導收掉、比對頁暖機過（第一次開要建畫面、解三張大圖會停一格）。"""
    if os.environ.get('PB_PUSH_BURSTS'):
        push_big_bursts()
    reset_media()
    reset_app()
    sl.scene('similar')
    sl.restart_app(40)
    for _ in range(4):
        sl.tap(739, 2297)                     # 底部「工具」
        time.sleep(6)
        sl.tap(540, 980)                      # 「相似照片」
        time.sleep(12)
        sl.dismiss_tips()
        if sl.find(lambda l, b: '6 組' in l):
            break
        sl.log('相似組還沒到齊，等一下再進')
        sl.sh('input keyevent 4')
        time.sleep(30)
    else:
        # 2026-10-07 踩過：上一輪錄成果頁把照片真的刪進回收桶，只剩 3 組 —— 照錄下去整段都是錯的
        raise RuntimeError('相似照片不是 6 組（上一輪的清理把照片刪掉了？重開模擬器再錄）')
    time.sleep(4)
    sl.tap(536, 800)
    time.sleep(10)
    if not sl.find(lambda l, b: '相似照片 第' in l):
        # 比對頁沒開起來時，「取消」那個位置是清單上的「自動精選」—— 按下去會開選單，整段錄壞
        raise RuntimeError('暖機時比對頁沒開起來')
    sl.tap(110, 2145)                         # 比對頁左下「取消」
    time.sleep(8)


def similar3_session(live=True):
    """相似照片 v3.1（2026-10-07 使用者）：

    - 先讓人看懂「相似的照片會被排成一組一組」：清單停著讓人看（不按自動精選）。
    - 點開一組的第一張 → 比對頁，**每一張都親手標**：保留（App 標星號的那張）→ 刪除 → 刪除。
      App 按下去就跳到下一張、鈕的顏色看不到，唯一的回饋是縮圖軌上的小角標 —— 影片裡把角標圈出來
      （storyboard 的 callouts，tone＝保留／刪除；使用者 2026-10-07 選了「只在影片裡加強調」）。
    - 標完直接切到成果頁（數字在跳）。成果頁一起重錄：慶祝卡改版過。

    座標由乾跑量（PB_G1 第一組第一張、PB_DISCARD／PB_KEEP 比對頁兩顆鈕，"x,y"）。"""
    _open_similar_settled()
    g1 = tuple(int(v) for v in os.environ.get('PB_G1', '203,793').split(','))
    dis = tuple(int(v) for v in os.environ.get('PB_DISCARD', '466,1993').split(','))
    kp = tuple(int(v) for v in os.environ.get('PB_KEEP', '613,1993').split(','))
    if not live:
        import dev
        dev.snap('s3_list', 540)
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:40])
        sl.tap(*g1)
        time.sleep(8)
        dev.snap('s3_compare', 540)
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:40])
        sl.tap(110, 2145)
        return
    # v3.3（2026-10-07 使用者）：點開之後先往左看一張、再往右看回來（讓人看得出可以這樣滑著比），
    # 再標：第一張（App 標星號的那張）保留 → App 自己跳到下一張 → 丟棄 → 跳到第三張 → 丟棄。
    # 每一下之間都約 0.7 秒（剪的時候 1.17 倍速＝一拍一下）；開頭清單多停一點，留給「一組一組」的聚焦
    left = (860, 1100, 220, 1100, 230)
    right = (220, 1100, 860, 1100, 230)
    body = (wait(2.2) + tap(*g1) + wait(0.47) + swipe(*left) + wait(0.47) + swipe(*right) + wait(0.7)
            + tap(*kp) + wait(0.7) + tap(*dis) + wait(0.7) + tap(*dis) + wait(1.2))
    if os.environ.get('PB_ONLY_DONE'):
        # 只重錄成果頁（慶祝卡又改版）：比對那幾下照做、不錄 —— 第一組的標記要跟比對那支一樣
        take('s3_similar', body, False)
    else:
        take('s3_similar', body, live, lead=0.3, tail=0.6)
    if os.environ.get('PB_SKIP_DONE'):
        return
    time.sleep(4)
    # 不錄：存起來回清單 → 其餘幾組用自動精選標好（成果頁的數字＝整個相似照片清掉的量）→ 清理 → 確認單
    hit = sl.find(lambda l, b: l.strip() == '套用')
    if hit:
        sl.tap(*_center(hit))
        time.sleep(6)
    sl.tap(200, 2090)                         # 自動精選
    time.sleep(1.5)
    sl.tap(120, 1940)                         # 「全部」
    time.sleep(5)
    clean = sl.find(lambda l, b: '清理' in l and '張' in l and b[1] > 1900)
    sl.log('清理鈕', clean)
    if not clean:
        sl.log([(l, b) for l, b in sl.dump() if l.strip()][:30])
        return
    sl.tap(*_center(clean))
    time.sleep(5)
    dx, dy = (int(v) for v in os.environ['PB_DEL_XY'].split(','))
    # 成果頁：數字從 0 跳上去、彩帶、分享卡（改版後的）滑進來 —— 錄 6 秒
    body = wait(0.5) + tap(dx, dy) + wait(6.0)
    take('s3_done', body, live, lead=0.3, tail=0.6)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1]
    if cmd == 'compress_done':
        compress_done_session(live='--dry' not in sys.argv)
    elif cmd == 'similar_done':
        similar_done_session(live='--dry' not in sys.argv)
    elif cmd == 'similar3':
        similar3_session(live='--dry' not in sys.argv)
    elif cmd == 'hook2':
        hook2_session(live='--dry' not in sys.argv)
    if cmd == 'prep':
        prep()
    elif cmd == 'review':
        review_session(live='--dry' not in sys.argv,
                       only=sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None)
    elif cmd == 'gallery':
        gallery_session(live='--dry' not in sys.argv)
    elif cmd == 'organised':
        organised_session(live='--dry' not in sys.argv)
    elif cmd == 'memory':
        memory_session(live='--dry' not in sys.argv)
    elif cmd == 'hook':
        hook_session(live='--dry' not in sys.argv)
    elif cmd == 'similar':
        similar_session(live='--dry' not in sys.argv)
    elif cmd == 'reset':
        reset_media()
        reset_app()
