"""扫描渲染产物里所有「文字压在某个背景上」的组合，检查对比度。

必须追踪嵌套：组件模板里背景常在外层 section、文字在内层，只比对同一个 style 属性
里的前景/背景会整片漏掉——明黄那一版的导语白字压在原色上完全没被发现。
"""
import re
from html.parser import HTMLParser


def _lum(hexc):
    h = hexc.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(h[0:2]) + 0.7152 * ch(h[2:4]) + 0.0722 * ch(h[4:6])


def ratio(fg, bg):
    a, b = _lum(fg), _lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


_BG = re.compile(r"background(?:-color)?:\s*(#[0-9A-Fa-f]{3,6})(?![0-9A-Fa-f])")
_FG = re.compile(r"(?<!-)\bcolor:\s*(#[0-9A-Fa-f]{3,6}(?![0-9A-Fa-f])|rgba\(\s*255\s*,\s*255\s*,\s*255[^)]*\))")


class _Scan(HTMLParser):
    """维护一个背景栈，任何带文字色的元素都拿它和最近的祖先背景比。"""

    def __init__(self):
        super().__init__()
        self.bg = ["#FFFFFF"]
        self.fg = ["#111111"]
        self.stack = []
        self.pairs = []

    def handle_starttag(self, tag, attrs):
        style = dict(attrs).get("style", "") or ""
        b = _BG.search(style)
        f = _FG.search(style)
        bg = b.group(1) if b else self.bg[-1]
        fg = f.group(1) if f else self.fg[-1]
        if fg.startswith("rgba"):
            fg = "#FFFFFF"
        self.bg.append(bg)
        self.fg.append(fg)
        self.stack.append(tag)
        self._cur = (fg, bg, tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop(); self.bg.pop(); self.fg.pop()

    def handle_data(self, data):
        if data.strip():
            self.pairs.append((self.fg[-1], self.bg[-1], self.stack[-1] if self.stack else "?",
                               data.strip()[:18]))


def violations(html, threshold=3.0):
    s = _Scan()
    s.feed(html)
    out = []
    for fg, bg, tag, text in s.pairs:
        try:
            r = ratio(fg, bg)
        except Exception:
            continue
        if r < threshold:
            out.append((fg, bg, round(r, 2), tag, text))
    return out
