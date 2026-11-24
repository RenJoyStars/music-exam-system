# -*- coding: utf-8 -*-
"""生成简谱 SVG（可隐藏拍号），供题库 spec 字段直接 innerHTML。"""

def spec_svg(bars, key='1=G', show_time=None, width_hint=420):
    F, BASE = 21, 62
    adv = lambda u: 23 if u >= 4 else (25 if u == 2 else 31)
    x = 56 if show_time else 46
    out = []
    for bi, bar in enumerate(bars):
        i = 0
        while i < len(bar):
            ch, unit = bar[i]
            if ch == '-':
                out.append(f'<text x="{x}" y="{BASE}" text-anchor="middle">-</text>')
            else:
                out.append(f'<text x="{x}" y="{BASE}" text-anchor="middle">{ch}</text>')
            if unit > 1:
                j = i
                sx = x
                while j + 1 < len(bar) and bar[j + 1][1] == unit:
                    j += 1
                ex = sx + sum(adv(n[1]) for n in bar[i:j + 1]) - adv(unit) + 10
                out.append(f'<line x1="{sx-9}" y1="{BASE+6}" x2="{ex}" y2="{BASE+6}" stroke="#1E2A38" stroke-width="1.3"/>')
                if unit == 4:
                    out.append(f'<line x1="{sx-9}" y1="{BASE+11}" x2="{ex}" y2="{BASE+11}" stroke="#1E2A38" stroke-width="1.3"/>')
            x += adv(unit)
            i += 1
        x += 14
        last = bi == len(bars) - 1
        out.append(f'<line x1="{x}" y1="{BASE-27}" x2="{x}" y2="{BASE+9}" stroke="#1E2A38" stroke-width="{2 if last else 1.2}"/>')
        if last:
            out.append(f'<line x1="{x+5}" y1="{BASE-27}" x2="{x+5}" y2="{BASE+9}" stroke="#1E2A38" stroke-width="2"/>')
        x += 20
    W = int(x + 8)
    head = f'<text x="4" y="40" font-size="15" font-family="-apple-system,PingFang SC,sans-serif">{key}</text>'
    if show_time:
        n, d = show_time.split('/')
        head += (f'<text x="44" y="24" text-anchor="middle" font-size="15">{n}</text>'
                 f'<text x="44" y="42" text-anchor="middle" font-size="15">{d}</text>'
                 f'<line x1="37" y1="28" x2="51" y2="28" stroke="#1E2A38"/>')
    return (f'<svg class="spec" viewBox="0 0 {W} 96" width="{W}" height="96" '
            f'xmlns="http://www.w3.org/2000/svg"><g font-family="Songti SC,SimSun,serif" '
            f'fill="#1E2A38" font-size="{F}">{head}{"".join(out)}</g></svg>')
