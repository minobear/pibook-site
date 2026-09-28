# -*- coding: utf-8 -*-
"""從中文畫板（press/0X_*.html）產生其他語言的畫板（press/<語言>/0X_*.html）。

    python make_boards.py ja ko

版面、座標、動線全部沿用中文版，這支只做三件事：
1. 換字（TEXT 表：中文原句 → 該語言），資源路徑改指 assets/shots/<語言>/
2. 換字型（日文用 JP 字形；韓文標題也用黑體，見 CLAUDE.md〈字型〉）
3. 「已整理」標籤翻出來很長的語言（LABEL_ABOVE），改放到特寫卡上方（放左邊會超出畫面）

新增語言：在 TEXT 加一份、在 FONTS 加字型，跑 shoot_locale.py 拍素材，再跑這支與 render.sh。
⚠️ 相似照片的組數從 assets/shots/<語言>/meta.txt 讀（shoot_locale.py 拍的時候記下的）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', 'assets', 'shots'))

FONTS = {
    'ja': ('Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;700',
           '"Noto Sans JP", sans-serif', '"Noto Serif JP", serif'),
    'ko': ('Noto+Sans+KR:wght@400;500;700;800',
           '"Noto Sans KR", sans-serif', '"Noto Sans KR", sans-serif'),
    'en': (None, None, None),
    'zh-Hans': ('Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@500;700',
                '"Noto Sans SC", sans-serif', '"Noto Serif SC", serif'),
}

# 中文原句 → 各語言。{n} ＝ 相似照片的組數。
TEXT = {
    'ja': {
        '<span class="wm">拍簿<small>PIBOOK</small></span>': '<span class="wm">Pibook</span>',
        '盡情拍、放心錄<br>整理與回憶靠拍簿': '思いきり撮って、<br>整理は Pibook に',
        '整理、挑最佳、省空間<br>全部在你的手機上完成': '整理も、ベスト選びも、容量の節約も<br>すべてスマホの中で',
        '>整理</div>': '>整理</div>',
        '滑一下<br>就整理好一張': 'スワイプ一回で、<br>一枚が片づく',
        '左滑保留、下滑丟進待刪除<br>想歸類？點一下相簿就收好': '左で残す、下で削除予定へ<br>アルバムをタップで仕分け',
        '>相似照片</div>': '>似ている写真</div>',
        '相似照片<br>自動幫你找出來': '似ている写真を<br>自動で見つけます',
        '相像的自動排成一組<br>留哪幾張由你決定': '連写も撮り直しもまとめて表示<br>どれを残すかは自分で選べます',
        '挑最佳 · 共 6 組': 'ベストを自動選択 · {n} 組',
        '>圖庫</div>': '>ギャラリー</div>',
        '整理過的、收進相簿的<br>一眼就看得到': '整理済みもアルバムも<br>ひと目でわかる',
        '左上角的點是整理狀態<br>右上角的數字是相簿數': '左上の点は整理済みのしるし<br>右上の数字は入っているアルバム数',
        '        已整理\n': '        整理済み\n',
        '        已加相簿\n': '        アルバムに追加済み\n',
        '>回憶</div>': '>思い出</div>',
        '像滑短影音一樣<br>回味那些日子': 'ショート動画のように<br>見返す',
        '隨機回味你的照片和影片<br>每一段都帶你回到當時': '写真と動画がランダムに戻ってくる<br>あの日にもう一度',
        '        回到 3 年前\n': '        3年前へ\n',
        '>往上滑，隨機下一段</div>': '>上にスワイプで次へ</div>',
        '>照片與影片壓縮</div>': '>写真と動画の圧縮</div>',
        '照片、影片<br>都能瘦身': '写真も動画も<br>すっきり軽く',
        '一次省下 823.9 MB<br>畫質與空間兼顧': '一度に 823.9 MB を節約<br>画質と容量をバランスよく',
        '>隱私</div>': '>プライバシー</div>',
        '你的照片<br>不離開你的手機': '写真は<br>スマホの外に出ません',
        '相似比對、臉部偵測與品質評分<br>全部在裝置上完成': '類似判定・顔検出・品質評価は<br>すべて端末の中で実行',
        '伺服器上沒有你的任何照片<small>所有影像分析都在這台裝置上執行</small>':
            'サーバーに写真は一枚もありません<small>画像の分析はすべてこの端末で実行</small>',
        '臉部偵測不建立身分資料<small>只判斷清不清楚，不辨識是誰</small>':
            '顔検出で個人を特定しません<small>見ているのは鮮明さだけ</small>',
        '不登入也能完整使用<small>雲端只備份整理進度，不碰照片</small>':
            'ログインなしですべて使えます<small>クラウドに残すのは整理の進み具合だけ</small>',
        '拍簿 Pibook</div>': 'Pibook</div>',
    },
    'ko': {
        '<span class="wm">拍簿<small>PIBOOK</small></span>': '<span class="wm">Pibook</span>',
        '盡情拍、放心錄<br>整理與回憶靠拍簿': '마음껏 찍고,<br>정리는 Pibook이',
        '整理、挑最佳、省空間<br>全部在你的手機上完成': '정리, 베스트 고르기, 용량 확보<br>모두 휴대폰 안에서',
        '>整理</div>': '>정리</div>',
        '滑一下<br>就整理好一張': '한 번 밀면<br>한 장이 정리돼요',
        '左滑保留、下滑丟進待刪除<br>想歸類？點一下相簿就收好': '왼쪽은 남기기, 아래는 삭제 예정<br>앨범을 누르면 바로 분류돼요',
        '>相似照片</div>': '>비슷한 사진</div>',
        '相似照片<br>自動幫你找出來': '비슷한 사진을<br>알아서 찾아요',
        '相像的自動排成一組<br>留哪幾張由你決定': '연사와 다시 찍은 사진을 한데 모아요<br>남길 사진은 직접 고르세요',
        '挑最佳 · 共 6 組': '베스트 자동 선택 · {n}묶음',
        '>圖庫</div>': '>갤러리</div>',
        '整理過的、收進相簿的<br>一眼就看得到': '정리 여부도, 앨범도<br>한눈에 보여요',
        '左上角的點是整理狀態<br>右上角的數字是相簿數': '왼쪽 위 점은 정리 상태<br>오른쪽 위 숫자는 앨범 수',
        '        已整理\n': '        정리함\n',
        '        已加相簿\n': '        앨범에 추가됨\n',
        '>回憶</div>': '>추억</div>',
        '像滑短影音一樣<br>回味那些日子': '숏폼처럼<br>다시 보기',
        '隨機回味你的照片和影片<br>每一段都帶你回到當時': '사진과 동영상이 무작위로 돌아와요<br>그때 그 순간으로',
        '        回到 3 年前\n': '        3년 전으로\n',
        '>往上滑，隨機下一段</div>': '>위로 밀면 다음 추억</div>',
        '>照片與影片壓縮</div>': '>사진·동영상 압축</div>',
        '照片、影片<br>都能瘦身': '사진도 동영상도<br>가볍게',
        '一次省下 823.9 MB<br>畫質與空間兼顧': '한 번에 823.9 MB 절약<br>화질과 용량의 균형',
        '>隱私</div>': '>개인정보</div>',
        '你的照片<br>不離開你的手機': '사진은 휴대폰 밖으로<br>나가지 않아요',
        '相似比對、臉部偵測與品質評分<br>全部在裝置上完成': '비슷한 사진 판별, 얼굴 감지, 품질 평가<br>모두 기기 안에서 처리해요',
        '伺服器上沒有你的任何照片<small>所有影像分析都在這台裝置上執行</small>':
            '서버에 사진을 저장하지 않아요<small>모든 이미지 분석은 이 기기에서</small>',
        '臉部偵測不建立身分資料<small>只判斷清不清楚，不辨識是誰</small>':
            '얼굴 감지로 신원을 만들지 않아요<small>선명한지만 보고, 누구인지는 몰라요</small>',
        '不登入也能完整使用<small>雲端只備份整理進度，不碰照片</small>':
            '로그인 없이 모든 기능을 써요<small>클라우드엔 정리 진행 상황만 백업</small>',
        '拍簿 Pibook</div>': 'Pibook</div>',
    },
    'zh-Hans': {
        '盡情拍、放心錄<br>整理與回憶靠拍簿': '尽情拍、放心录<br>整理与回忆靠拍簿',
        '整理、挑最佳、省空間<br>全部在你的手機上完成': '整理、挑最佳、省空间<br>全部在你的手机上完成',
        '滑一下<br>就整理好一張': '划一下<br>就整理好一张',
        '左滑保留、下滑丟進待刪除<br>想歸類？點一下相簿就收好': '左滑保留、下滑丢进待删除<br>想归类？点一下相册就收好',
        '相似照片<br>自動幫你找出來': '相似照片<br>自动帮你找出来',
        '相像的自動排成一組<br>留哪幾張由你決定': '相像的自动排成一组<br>留哪几张由你决定',
        '挑最佳 · 共 6 組': '挑最佳 · 共 {n} 组',
        '>圖庫</div>': '>图库</div>',
        '整理過的、收進相簿的<br>一眼就看得到': '整理过的、收进相册的<br>一眼就看得到',
        '左上角的點是整理狀態<br>右上角的數字是相簿數': '左上角的点是整理状态<br>右上角的数字是相册数',
        '        已加相簿\n': '        已加相册\n',
        '>回憶</div>': '>回忆</div>',
        '像滑短影音一樣<br>回味那些日子': '像刷短视频一样<br>回味那些日子',
        '隨機回味你的照片和影片<br>每一段都帶你回到當時': '随机回味你的照片和视频<br>每一段都带你回到当时',
        '>往上滑，隨機下一段</div>': '>往上滑，随机下一段</div>',
        '>照片與影片壓縮</div>': '>照片与视频压缩</div>',
        '照片、影片<br>都能瘦身': '照片、视频<br>都能瘦身',
        '一次省下 823.9 MB<br>畫質與空間兼顧': '一次省下 823.9 MB<br>画质与空间兼顾',
        '>隱私</div>': '>隐私</div>',
        '你的照片<br>不離開你的手機': '你的照片<br>不离开你的手机',
        '相似比對、臉部偵測與品質評分<br>全部在裝置上完成': '相似比对、人脸检测与质量评分<br>全部在设备上完成',
        '伺服器上沒有你的任何照片<small>所有影像分析都在這台裝置上執行</small>':
            '服务器上没有你的任何照片<small>所有图像分析都在这台设备上执行</small>',
        '臉部偵測不建立身分資料<small>只判斷清不清楚，不辨識是誰</small>':
            '人脸检测不建立身份资料<small>只判断清不清楚，不识别是谁</small>',
        '不登入也能完整使用<small>雲端只備份整理進度，不碰照片</small>':
            '不登录也能完整使用<small>云端只备份整理进度，不碰照片</small>',
    },
}

# 「已整理」標籤太長、放特寫卡左邊會超出畫面的語言，改放到特寫卡上方（英文版量過的座標）
LABEL_ABOVE = {'en'}
GALLERY_LABEL_ABOVE = [
    ('<line x1="87" y1="230.5" x2="109" y2="230.5"', '<line x1="130.5" y1="180" x2="130.5" y2="211"'),
    ('style="right:calc(100% - 84px);top:211px;z-index:6"',
     'style="left:130.5px;top:138px;transform:translateX(-50%);z-index:6"'),
]
SHOT_FILES = ['home_hd.jpg', 'review_hd.jpg', 'review_rail_hd.png', 'gallery_hd.jpg',
              'similar_groups_hd.jpg', 'memory_hd.jpg', 'compress_hd.jpg']


def build(loc):
    meta = {}
    mp = os.path.join(SHOTS, loc, 'meta.txt')
    if os.path.exists(mp):
        for line in open(mp, encoding='utf-8'):
            k, _, v = line.strip().partition('=')
            meta[k] = v
    font_link, sans, serif = FONTS[loc]
    os.makedirs(os.path.join(HERE, loc), exist_ok=True)
    for fn in sorted(os.listdir(HERE)):
        if not (fn[:2].isdigit() and fn.endswith('.html')):
            continue
        s = open(os.path.join(HERE, fn), encoding='utf-8').read()
        s = s.replace('<html lang="zh-Hant">', f'<html lang="{loc}">')
        s = s.replace('="../assets/', '="../../assets/')
        s = s.replace('href="press.css"', 'href="../press.css"').replace('src="press.js"', 'src="../press.js"')
        for f in SHOT_FILES:
            s = s.replace(f'shots/{f}', f'shots/{loc}/{f}')
        for a, b in TEXT[loc].items():
            if a in s:
                s = s.replace(a, b.replace('{n}', meta.get('similar_groups', '?')))
        if fn.startswith('04_') and loc in LABEL_ABOVE:
            for a, b in GALLERY_LABEL_ABOVE:
                s = s.replace(a, b)
        if font_link:
            s = s.replace('family=Noto+Sans+TC', f'family={font_link}&family=Noto+Sans+TC')
            s = s.replace('</head>', f'<style>:root{{--pb-sans:{sans};--pb-serif:{serif}}}</style>\n</head>')
        leftover = [ln.strip() for ln in s.splitlines()
                    if any('一' <= c <= '鿿' for c in ln) and 'alt=' not in ln
                    and '<title>' not in ln and '<!--' not in ln and loc not in ('ja', 'zh-Hans')]
        open(os.path.join(HERE, loc, fn), 'w', encoding='utf-8').write(s)
        if leftover:
            print(loc, fn, '還有中文沒換：', leftover[:3])
    print('ok', loc)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for loc in sys.argv[1:]:
        build(loc)
