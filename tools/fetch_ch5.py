# -*- coding: utf-8 -*-
"""从湖南文艺出版社数字教材平台，按曲名搜索并下载第五章 22 首的音频，转 60 秒 / 48k。"""
from playwright.sync_api import sync_playwright
import os, json, urllib.parse, urllib.request, subprocess, sys, time

EXE = '/Users/joyren/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(BASE, 'tools', 'hnwy_state.json')
OUT = os.path.join(BASE, 'web', 'media', 'audio')
os.makedirs(OUT, exist_ok=True)

TRACKS = [
 (2, '山丹丹花开红艳艳', '七上'), (3, '幸福在哪里', '七上'), (4, '乡间的小路', '七上'),
 (5, '洗衣歌', '七上'), (6, '十五的月亮', '七下'), (7, '弯弯的月亮', '七下'),
 (8, '在银色的月光下', '七下'), (9, '彩云追月', '七下'), (10, '三沙谣', '八上'),
 (11, '渔家姑娘在海边', '八上'), (12, '军港之夜', '八上'), (13, '大海啊，故乡', '八上'),
 (14, '滚滚长江东逝水', '八下'), (15, '好汉歌', '八下'), (16, '葬花吟', '八下'),
 (17, '敢问路在何方', '八下'), (18, '迎来春色换人间', '九上'), (19, '东方之珠', '九上'),
 (20, '孤独的牧羊人', '九上'), (21, '卡门序曲', '九上'), (22, '天鹅湖', '九上'),
 (23, '斯卡博罗集市', '九上'),
]
ONLY = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None

def pick(items, title, book):
    """只挑数字教材-音频、非伴奏、册名匹配的那条，优先范唱。"""
    cands = []
    for it in items:
        t = it['text']
        if '【音频】' not in t or '[数字教材-音频]' not in t: continue
        if '伴奏' in t: continue
        if title not in t: continue
        score = 0
        if book in t: score += 5
        if '范唱' in t: score += 3
        if '听赏' in t: score += 2
        cands.append((score, it))
    cands.sort(key=lambda x: -x[0])
    return cands[0][1] if cands else None

log = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    ctx = b.new_context(storage_state=STATE, viewport={'width': 1400, 'height': 900})
    pg = ctx.new_page()
    for page, title, book in TRACKS:
        if ONLY and page not in ONLY: continue
        out = os.path.join(OUT, f's5p{page:02d}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 50000:
            print(f's5p{page:02d} 已存在，跳过', flush=True); continue
        pg.goto('https://www.hnwymusic.com/web/index/search?searchContent=' + urllib.parse.quote(title),
                wait_until='domcontentloaded', timeout=40000)
        pg.wait_for_timeout(1800)
        items = pg.evaluate("""()=>Array.from(document.querySelectorAll('li[fid]')).map(li=>({
            fid:li.getAttribute('fid'), text:li.innerText.replace(/\\n/g,' | ')}))""")
        hit = pick(items, title, book)
        if not hit:
            print(f's5p{page:02d} 《{title}》未找到匹配音频（{len(items)} 条结果）', flush=True)
            log.append({'page': page, 'title': title, 'ok': False}); continue
        r = pg.evaluate("""async (fid)=>{
            const res=await fetch('/web/resource/download-info?fileId='+fid,{method:'POST'});
            return await res.text();
        }""", hit['fid'])
        d = json.loads(r)
        url = (d.get('data') or {}).get('fileContent') or ''
        if not url.startswith('http'):
            print(f's5p{page:02d} 无 fileContent: {r[:120]}', flush=True)
            log.append({'page': page, 'title': title, 'ok': False}); continue
        tmp = '/tmp/_ch5' + os.path.splitext(url)[1]
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, 'wb') as f:
            f.write(resp.read())
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-t', '60', '-vn',
                        '-ac', '1', '-ar', '22050', '-b:a', '48k',
                        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', out], check=True)
        size = os.path.getsize(out) // 1024
        print(f's5p{page:02d} 《{title}》 OK {size}KB  ← {hit["text"][:48]}', flush=True)
        log.append({'page': page, 'title': title, 'fid': hit['fid'], 'url': url, 'kb': size, 'ok': True})
json.dump(log, open(os.path.join(BASE, 'tools', 'ch5_index.json'), 'w'), ensure_ascii=False, indent=1)
print('完成', sum(1 for x in log if x['ok']), '/', len(log), flush=True)
