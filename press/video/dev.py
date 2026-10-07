# -*- coding: utf-8 -*-
"""小工具：截一張縮小的圖給人看、列出畫面上的節點。錄影腳本開發時用。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.stdout.reconfigure(encoding='utf-8')
import shoot_locale as sl
from PIL import Image

SCRATCH = os.environ.get('PB_SCRATCH', sl.TMP)

def snap(name='s', w=360):
    p = sl.screencap(name + '.png')
    im = Image.open(p).convert('RGB')
    out = os.path.join(SCRATCH, name + '_small.jpg')
    im.resize((w, int(im.height * w / im.width))).save(out, quality=80)
    print(out)

def nodes(filt=''):
    for l, b in sl.dump():
        if l.strip() and filt in l:
            print(b, l.replace('\n', ' | ')[:80])

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'snap':
        snap(*(sys.argv[2:3] or ['s']))
    elif cmd == 'nodes':
        nodes(*(sys.argv[2:3] or ['']))
    elif cmd == 'tap':
        sl.tap(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == 'sh':
        print(sl.sh(sys.argv[2]))
