"""生成笔锋 / 飞白 / 波浪类的 SVG 路径，给标题装饰层（h2-deco）用。

## 为什么要有这个脚本

组件模板里最终存的是一串 `d="M2 5.6 L9.8 4.1 …"`。手写这种字符串有两个问题：
调不动（想让笔锋粗一点得重算几十个坐标），也看不懂（三个月后没人知道那串数是什么）。
这里把「笔画」参数化：给一条粗细包络，脚本算出上下两条边围成的闭合路径。

    python3 brush_svg.py taper --peak 4.5 --end 0.3
    python3 brush_svg.py dry --peak 6.8 --tail       # 尾部渐散的飞白
    python3 brush_svg.py --list                      # 看全部预设

## 为什么是「闭合形状」不是「一根线」

`stroke` 画出来的线是等宽的，两端永远齐平——那是机器的线。笔锋要两端收尖、中段饱满，
只能把上下两条边分开走再围成闭合区域用 `fill` 填。这也是笔锋看着比正弦波高级的原因：
正弦波是机器的规整，笔锋暗示了一只手和一支笔。

## 点数取多少

实测在 375px 宽下渲染：n=48 到 n=12 肉眼看不出差别，n=8 才开始能看到折角。
所以默认 n=14、小数 1 位——约 330 B，比 n=48 小数 2 位的 1270 B 小四倍。
这些路径要跟着每一篇文章发出去，一篇六个标题就是六份，省下来的是实打实的。

## 飞白别拿白色盖

早先的做法是先画一整笔，再用白色线条盖出几道缺口。那在浅色底上就露馅了——
看着是划伤不是飞白。正确做法是把整笔切成几段，段与段之间是真的空（见 `dry`）。
"""

from __future__ import annotations

import argparse
import math
import random
import sys

WIDTH = 343          # 375px 屏减去容器左右各 16px


def _edges(y0, env, n, wobble, seed, x0, x1, prec, width):
    """算上下两条边。env(t) 给出该处笔画粗细，t ∈ [0,1]。"""
    r = random.Random(seed)
    fmt = f"%.{prec}f %.{prec}f"
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        h = max(0.1, env(t))
        w = (r.random() - 0.5) * wobble
        x = width * (x0 + (x1 - x0) * t)
        top.append(fmt % (x, y0 - h / 2 + w))
        bot.append(fmt % (x, y0 + h / 2 + w))
    return "M" + " L".join(top) + " L" + " L".join(reversed(bot)) + " Z"


def taper(y0=6.0, peak=4.5, end=0.3, n=14, wobble=0.0, seed=1,
          x0=0.0, x1=1.0, prec=1, width=WIDTH, curve=0.0):
    """两端收尖的一笔。curve>0 时基线本身走一条缓弧。"""
    env = lambda t: end + (peak - end) * math.sin(math.pi * t)
    if not curve:
        return _edges(y0, env, n, wobble, seed, x0, x1, prec, width)
    fmt = f"%.{prec}f %.{prec}f"
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        base = y0 + curve * (math.sin(math.pi * t) - 0.5)
        h = max(0.1, env(t))
        x = width * (x0 + (x1 - x0) * t)
        top.append(fmt % (x, base - h / 2))
        bot.append(fmt % (x, base + h / 2))
    return "M" + " L".join(top) + " L" + " L".join(reversed(bot)) + " Z"


def wedge(y0=7.0, head=7.5, tail=0.6, **kw):
    """起笔重收笔轻。反过来（起轻收重）在中文里读着别扭——像写错了往回描。"""
    kw.setdefault("n", 14)
    return _edges(y0, lambda t: head + (tail - head) * t,
                  kw.pop("n"), kw.pop("wobble", 0.0), kw.pop("seed", 1),
                  kw.pop("x0", 0.0), kw.pop("x1", 1.0),
                  kw.pop("prec", 1), kw.pop("width", WIDTH))


def dry(y0=7.0, peak=6.5, end=0.4, gaps=None, tail=False,
        wobble=0.5, seed=3, n=10, prec=1, width=WIDTH):
    """飞白：切成几段，段间是真的空。tail=True 时缺口向尾部越来越密——
    读起来就是笔走到末尾墨用尽了，这一版里最像真飞白的就是它。"""
    if gaps is None:
        gaps = ([(.62, .645), (.74, .775), (.85, .895), (.94, .965)] if tail
                else [(.33, .38), (.63, .665)])
    env = ((lambda t: end + (peak - end) * (1 - t)) if tail
           else (lambda t: end + (peak - end) * math.sin(math.pi * t)))
    segs, x = [], 0.0
    for a, b in gaps:
        if a > x:
            segs.append((x, a))
        x = b
    if x < 1:
        segs.append((x, 1.0))
    return " ".join(
        _edges(y0, lambda t, s=s: env(s[0] + (s[1] - s[0]) * t),
               n, wobble, seed + i, s[0], s[1], prec, width)
        for i, s in enumerate(segs))


def sine(y0=6.0, amp=2.0, period=26.0, n=None, prec=1, width=WIDTH):
    """正弦波。列在这里是为了完整，但实测它在中文标题下读着廉价——
    低振幅像拼写检查的红线，高振幅幼稚。要用先渲出来自己看一眼。"""
    n = n or int(width / 3)
    fmt = f"%.{prec}f %.{prec}f"
    return "M" + " L".join(
        fmt % (width * i / n, y0 + amp * math.sin(2 * math.pi * (width * i / n) / period))
        for i in range(n + 1))


PRESETS = {
    "细笔锋":       lambda: ("path", taper(6, 4.5, 0.3), 12),
    "粗笔锋":       lambda: ("path", taper(8, 9.0, 0.4), 16),
    "起笔重":       lambda: ("path", wedge(7, 7.5, 0.6), 15),
    "毛笔抖":       lambda: ("path", taper(8, 5.0, 0.5, wobble=1.6, seed=11, n=22), 16),
    "飞白":         lambda: ("path", dry(7), 15),
    "飞白渐散":     lambda: ("path", dry(7, tail=True), 15),
    "半幅笔锋":     lambda: ("path", taper(7, 6.0, 0.35, x1=0.58), 14),
    "缓弧笔锋":     lambda: ("path", taper(9, 5.5, 0.35, curve=2.4), 18),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("preset", nargs="?", help="预设名；省略时用 --list 看全部")
    ap.add_argument("--list", action="store_true", help="列出全部预设并输出一页对照 HTML")
    ap.add_argument("--color", default="{primary-ink}", help="填充色，默认留主题变量")
    ap.add_argument("--out", help="把对照页写到这个路径")
    a = ap.parse_args()

    if a.list or not a.preset:
        rows = []
        for name, make in PRESETS.items():
            _, d, h = make()
            body = f'<path d="{d}" fill="{a.color}"/>'
            print(f"{name:10} 高 {h:2}px  {len(body):5} B")
            rows.append((name, h, body.replace(a.color, "#14508C")))
        if a.out:
            html = ('<!doctype html><meta charset="utf-8">'
                    '<body style="margin:0;padding:12px;background:#e9e9ea;">'
                    + "".join(
                        f'<div style="margin-bottom:10px;width:375px;background:#fff;padding:12px 16px;">'
                        f'<div style="font:600 11px/1.8 -apple-system;color:#888;">{n}</div>'
                        f'<div style="font-size:22px;font-weight:800;color:#111318;">决定读完率的其实是三个数</div>'
                        f'<svg width="{WIDTH}" height="{h}" viewBox="0 0 {WIDTH} {h}" '
                        f'style="display:block;margin-top:7px;">{b}</svg></div>'
                        for n, h, b in rows) + "</body>")
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n对照页 → {a.out}")
        return 0

    if a.preset not in PRESETS:
        print(f"没有预设 {a.preset!r}。可用：{'、'.join(PRESETS)}", file=sys.stderr)
        return 1
    _, d, h = PRESETS[a.preset]()
    print(f'<svg width="{WIDTH}" height="{h}" viewBox="0 0 {WIDTH} {h}" '
          f'style="display:block;"><path d="{d}" fill="{a.color}"/></svg>')
    return 0


if __name__ == "__main__":
    sys.exit(main())
