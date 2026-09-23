# -*- coding: utf-8 -*-
"""乾跑：讀出每張卡片的相簿軌實際版位並照名字點，把座標記下來。
   之後可以用固定座標的裝置端腳本重放（快、節奏可控），不必在錄影中途 dump。"""
import re, subprocess, sys, time, json, os
SP = os.path.dirname(os.path.abspath(__file__))

def sh(a, t=60): return subprocess.run(["adb"]+a, capture_output=True, timeout=t)
def dump():
    sh(["shell","uiautomator","dump","/data/local/tmp/ui.xml"])
    return sh(["exec-out","cat","/data/local/tmp/ui.xml"]).stdout.decode("utf-8","replace")
def nodes(x):
    r=[]
    for m in re.finditer(r"<node[^>]*>", x):
        t=re.search(r'text="([^"]*)"',m.group(0)); c=re.search(r'content-desc="([^"]*)"',m.group(0))
        b=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',m.group(0))
        lab=(t.group(1) if t else "") or (c.group(1) if c else "")
        if lab.strip() and b:
            x1,y1,x2,y2=map(int,b.groups()); r.append((lab.strip(),(x1+x2)//2,(y1+y2)//2))
    return r

plan = json.loads(sys.argv[1])
coords=[]
for name in plan:
    xml = dump()
    strip = [(l,cx,cy) for l,cx,cy in nodes(xml) if 1980 <= cy <= 2120]
    print("strip:", [(l,cx) for l,cx,cy in strip])
    hit = [ (cx,cy) for l,cx,cy in strip if l==name ]
    if not hit:
        print("MISS", name); coords.append(None); continue
    x, y = hit[0][0], hit[0][1]-100
    coords.append((x,y))
    print("tap %s -> (%d,%d)" % (name,x,y))
    sh(["shell","input","tap",str(x),str(y)])
    time.sleep(1.8)
open(os.path.join(SP,"album_coords.json"),"w").write(json.dumps(coords))
print(json.dumps(coords))
