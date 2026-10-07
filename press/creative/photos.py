#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""創意素材用的照片：從示範圖庫的快取（build/store_demo_cache，Pexels 授權）挑出來、
縮成長邊 1600 px，放到 build/creative/photos/。

跟商店截圖、預覽影片是同一批照片 —— 使用者在標題圖看到的那隻巴哥犬，
往下滑到截圖裡還是同一隻，整頁講的是同一個人的相簿。
⛔ 素材不得有裸露（使用者 2026-08-30 規定），示範圖庫挑選時已排除。
⚠️ 招牌上有字的照片不挑（標題圖面向五個語言的使用者）。
"""
from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / 'build' / 'store_demo_cache'
OUT = REPO / 'build' / 'creative' / 'photos'

# 名稱 → 示範圖庫快取裡的 Pexels 編號。名稱只是給版面腳本好讀。
PHOTOS = {
    'pug': 'photos/16652400',
    'fireworks_a': 'photos/1317364',
    'fireworks_b': 'photos/19720556',
    'fireworks_c': 'photos/27068360',
    'fireworks_d': 'photos/949592',
    'cat_orange_face': 'photos/29020872',
    'cat_orange_sofa': 'photos/34345889',
    'cat_tabby': 'photos/34360871',
    'cat_orange_warm': 'photos/3693769',
    'cat_sleep': 'photos/116835',
    'bday_a': 'photos/23495684',
    'bday_b': 'photos/23495685',
    'bday_c': 'photos/7336935',
    'bday_d': 'photos/7336949',
    'bday_e': 'photos/7336963',
    'couple_park': 'photos/11947714',
    'couple_lying': 'photos/20424752',
    'couple_picnic': 'photos/4127427',
    'friends_row': 'photos/13335936',
    'friends_laugh': 'photos/36713424',
    'selfie_a': 'burst/36713387',
    'selfie_b': 'burst/36729906',
    'selfie_c': 'burst/36764839',
    'travel_a': 'photos/4881005',
    'travel_b': 'photos/4881126',
    'travel_c': 'photos/4881140',
    'girl_jump': 'photos/5275834',
    'boy_slide': 'photos/8535889',
    'family_floor': 'photos/3912425',
    'dad_kid': 'photos/4617316',
    'grandpa_a': 'photos/8297498',
    'grandpa_b': 'photos/8298421',
    'picnic_mom': 'photos/5119589',
    'picnic_a': 'photos/7669128',
    'picnic_b': 'photos/7669177',
    'shrimp': 'photos/132263',
    'salad': 'photos/20693276',
    'croissant': 'photos/34052564',
    'dish': 'photos/36627096',
    'brunch': 'photos/5865690',
    'boba_pair': 'photos/12940112',
    'boba_cheers': 'photos/14267667',
    'boba_hand': 'photos/6412836',
    'latte_a': 'photos/31139336',
    'latte_b': 'photos/39537967',
    'latte_c': 'photos/6747870',
    'taipei_night': 'photos/11720365',
    'taipei_101': 'photos/16705976',
    'sunset_city': 'photos/13232354',
    'sunset_101': 'photos/16642634',
    'mountain_a': 'photos/34533758',
    'mountain_b': 'photos/35689607',
    'flowers_a': 'photos/37796899',
    'flowers_b': 'photos/37796901',
    'dog_walk': 'photos/31240501',
    'dog_autumn': 'photos/34470228',
    'dinner_a': 'photos/3937644',
    'women_cafe': 'photos/8794812',
    'couple_city': 'photos/8889026',
    'kids_swing': 'photos/8535898',
    'friends_couch': 'photos/7114420',
    'forest_walk': 'photos/5506093',
    'dinner_b': 'photos/3937667',
    'women_park': 'photos/33867307',
    'friends_selfie': 'photos/7973102',
    'family_living': 'photos/8054853',
    'grandma_kid': 'photos/8297670',
    'hikers': 'photos/8532284',
    'girl_eating': 'photos/36161182',
    'friends_eat': 'photos/36005727',
    'couple_b': 'photos/8889021',
    'picnic_c': 'photos/7669136',
}


def prep(long_edge=1600):
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, rel in PHOTOS.items():
        dst = OUT / f'{name}.jpg'
        src = CACHE / f'{rel}.jpg'
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
            im.thumbnail((long_edge, long_edge), Image.LANCZOS)
            im.save(dst, quality=90, optimize=True)
        with Image.open(dst) as im:
            sizes[name] = im.size
    return sizes


if __name__ == '__main__':
    s = prep()
    print(len(s), 'photos →', OUT)
