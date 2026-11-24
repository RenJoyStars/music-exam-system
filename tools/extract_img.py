# -*- coding: utf-8 -*-
"""提取课件附录页的乐器图片（透明底 PNG）。按白名单页码取，跳过分类/对比页。"""
import os, json, io
from pptx import Presentation
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'web', 'media', 'img')
WPS = '/Users/joyren/Library/Containers/com.kingsoft.wpsoffice.mac/Data/Library/Application Support/Kingsoft/WPS Cloud Files/userdata/qing/filecache/251627508'
CH2 = os.path.join(WPS, '2026 初三 新教材复习 第二章《华夏之声·文化根脉》.pptx')
CH4 = os.path.join(WPS, '2026 初三 新教材复习 第四章《多姿多彩的乐音世界》.pptx')

MZ = [47,48,49,50,51,52, 54,55,56,57,58,59,60, 62,63,64,65,66,67, 69,70,71,72,73,74,75,76,77,78,79,80,81]
XY = [31,32,33,34,36, 38,39,40,41, 43,44,45,46, 48,49,50,51,52,53]
os.makedirs(OUT, exist_ok=True)
idx = []

def grab(path, pages, prefix):
    prs = Presentation(path)
    n = 0
    for i, s in enumerate(prs.slides, 1):
        if i not in pages: continue
        title = ''
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                t = sh.text_frame.text.strip().split('\n')[0]
                if '｜' in t: t = t.split('｜')[0]
                t = t.strip().replace('　','')
                if t and '湘珺' not in t and '乐器' not in t:
                    title = t; break
        pic = None
        for sh in s.shapes:
            try: im = sh.image
            except Exception: continue
            if pic is None or sh.width > pic[1].width:
                pic = (im, sh)
        if not pic:
            print(f'  p{i} 无图'); continue
        im, sh = pic
        n += 1
        name = f'{prefix}{n:02d}.png'
        open(os.path.join(OUT, name), 'wb').write(im.blob)
        img = Image.open(io.BytesIO(im.blob))
        idx.append({'f': name, 'name': title, 'page': i, 'w': img.size[0], 'h': img.size[1]})
        print(f'  {name} {title:6s} p{i} {img.size[0]}x{img.size[1]}')

grab(CH2, MZ, 'mz')
grab(CH4, XY, 'xy')
json.dump(idx, open(os.path.join(BASE, 'tools', 'img_index.json'), 'w'), ensure_ascii=False, indent=1)
print('完成', len(idx), '张')
