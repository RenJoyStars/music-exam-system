# -*- coding: utf-8 -*-
"""从五章复习课件提取音频：按 PPT 里设的裁剪起点 p14:trim st（毫秒）开始截 60 秒。
命名 s{册}p{PPT页}.mp3。没有设裁剪的页从 0 开始。"""
import os, subprocess, zipfile, re, json
from pptx import Presentation

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'web', 'media', 'audio')
WPS = '/Users/joyren/Library/Containers/com.kingsoft.wpsoffice.mac/Data/Library/Application Support/Kingsoft/WPS Cloud Files/userdata/qing/filecache/251627508'
SRC = {
  1: os.path.join(WPS, '2026 初三 新教材复习 第一章《精神·信仰·力量·情感》 .pptx'),
  2: os.path.join(WPS, '2026 初三 新教材复习 第二章《华夏之声·文化根脉》.pptx'),
  3: os.path.join(WPS, '2026 初三 新教材复习 第三章《真善美的深情呼唤》.pptx'),
  4: os.path.join(WPS, '2026 初三 新教材复习 第四章《多姿多彩的乐音世界》.pptx'),
}
RANGE = {1: (2, 32), 2: (2, 31), 3: (2, 25), 4: (2, 19)}
os.makedirs(OUT, exist_ok=True)

def trims_of(path):
    """返回 {页码: (st秒, end秒)}"""
    z = zipfile.ZipFile(path)
    out = {}
    for name in z.namelist():
        m = re.match(r'ppt/slides/slide(\d+)\.xml$', name)
        if not m: continue
        x = z.read(name).decode('utf-8', 'ignore')
        t = re.search(r'<p14:trim[^/]*?st="([\d.]+)"(?:[^/]*?end="([\d.]+)")?', x)
        if t:
            st = float(t.group(1)) / 1000.0
            en = float(t.group(2)) / 1000.0 if t.group(2) else None
            out[int(m.group(1))] = (st, en)
    return out

def media_part(slide):
    for rel in slide.part.rels.values():
        if rel.reltype.split('/')[-1] in ('video', 'audio', 'media') and not rel.is_external:
            try:
                return rel.target_part
            except Exception:
                continue
    return None

rows = []
for ch, path in SRC.items():
    if not os.path.exists(path):
        print('缺文件', ch); continue
    trims = trims_of(path)
    prs = Presentation(path)
    a, b = RANGE[ch]
    print(f'第{ch}章：{len(trims)} 页设了裁剪')
    for i, slide in enumerate(prs.slides, 1):
        if not (a <= i <= b): continue
        part = media_part(slide)
        if part is None:
            print(f'  s{ch}p{i:02d} 无媒体'); continue
        ext = os.path.splitext(str(part.partname))[1].lower()
        tmp = f'/tmp/_x{ext}'
        with open(tmp, 'wb') as f:
            f.write(part.blob)
        total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                     '-of', 'default=nw=1:nk=1', tmp],
                                    capture_output=True, text=True).stdout.strip() or 0)
        st, en = trims.get(i, (0.0, None))
        if st >= total - 1: st = max(0.0, total - 60)
        dur = 60.0
        if en is not None and en > st: dur = min(60.0, en - st)
        out = os.path.join(OUT, f's{ch}p{i:02d}.mp3')
        cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', f'{st:.3f}', '-i', tmp,
               '-t', f'{dur:.2f}', '-vn', '-ac', '1', '-ar', '22050', '-b:a', '48k',
               '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', out]
        r = subprocess.run(cmd)
        if r.returncode == 0 and os.path.exists(out):
            rows.append({'f': os.path.basename(out), 'ch': ch, 'page': i,
                         'st': round(st, 2), 'total': round(total, 1),
                         'kb': os.path.getsize(out)//1024})
            print(f'  s{ch}p{i:02d} 从 {st:6.1f}s 起（原片 {total:.0f}s） {os.path.getsize(out)//1024}KB')
        else:
            print(f'  s{ch}p{i:02d} 失败')
json.dump(rows, open(os.path.join(BASE, 'tools', 'audio_index.json'), 'w'), ensure_ascii=False, indent=1)
print('完成', len(rows), '条')
