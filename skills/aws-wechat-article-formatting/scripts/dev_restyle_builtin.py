"""把内置 7 套主题换成和网站 16 套同一套装饰词汇。dev 工具，不参与运行时。

## 为什么单独有这一份

`references/presets/themes/` 下这 7 套是**用户没导入预设包时的兜底**——下载完 skill
第一次跑 format.py 用的就是它们。网站那 16 套换了词汇之后，这 7 套还停在旧词汇上，
落差比不改还难看。而且 `杂志` 整套建立在 `'Songti SC','Noto Serif CJK SC'` 上，
那些中文字体名在手机微信里实测完全无效（见 references/wechat-html-constraints.md），
等于这套主题的核心特征一直没生效过。

装饰词汇的三条规则（和网站那边一致）：

    1. 不画 1px 边框做分隔——用留白，或者整块浅底
    2. 圆角只取 0 或 12~16px——2~6px 是最没态度的一档
    3. 装饰用「面积」不用「线」

h2 分三型（N 底线 / S 色块 / W 色条），7 套各配一种形态，保留各自原有的主色。

## 和网站那份脚本的关系

两边各有一份生成器，规则相同、数据不同。没有做成共享模块——跨仓库共享一个
生成器要么把 skills 变成 website 的依赖、要么反过来，为了七套兜底主题不值得。
改规则时两边都要改，这一点写在这里提醒。

用法：

    python3 skills/aws-wechat-article-formatting/scripts/dev_restyle_builtin.py --write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

THEMES_DIR = Path(__file__).parent.parent / "references" / "presets" / "themes"

MUTED = "#8A8F98"
RULE = "#EFF0F2"
CODE_BG_DARK = "#141519"
MONO = "Menlo, Consolas, monospace"
SERIF = "Georgia, serif"

# name → (型, 主色, 墨色, 形态, 西文字形, 正文额外)
#   形态：N 型是底线宽度、S 型是圆角、W 型是色条位置；("inline"|"block", 值, 对齐)
PLAN = {
    "default":  ("N", "#1A6DB5", "#111318", ("block",  "3px", "left"),   None,  {}),
    "grace":    ("S", "#664D9D", "#14161A", ("block",  "20px", "center"), None,  {"letter-spacing": "1.2px"}),
    "modern":   ("S", "#EF7060", "#14161A", ("inline", "14px", "left"),  None,  {}),
    "simple":   ("W", "#18181B", "#111318", ("inline", "top4", "left"),  None,  {"padding": "0 12px", "letter-spacing": "0.8px"}),
    "克制":      ("W", "#07A87C", "#1F1C19", ("inline", "bottom4", "left"), None, {"padding": "0 12px", "letter-spacing": "0.6px"}),
    "工程笔记":   ("N", "#2F6FEB", "#111318", ("inline", "6px", "left"),   MONO,  {"letter-spacing": "0.3px"}),
    "杂志":      ("N", "#1A1A1A", "#111318", ("block",  "2px", "center"), SERIF, {"text-align": "justify", "letter-spacing": "0.3px"}),
}


def _lum(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(h[0:2]) + 0.7152 * ch(h[2:4]) + 0.0722 * ch(h[4:6])


def darken_to_readable(hexcolor: str, target: float = 4.5) -> str:
    """强调色的「能当文字用」版本：色相不变，压深到白底上够读。

    面积（色块、色条、底线）用原色，文字（h3、链接、行内代码）用这个。同一个颜色
    没法同时满足两者——暖橙系的 #EF7060 压白底只有 2.9，当块底够，当 17px 文字不够。
    """
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    for _ in range(40):
        if 1.05 / (_lum("#%02X%02X%02X" % (r, g, b)) + 0.05) >= target:
            break
        r, g, b = (max(0, round(c * 0.94)) for c in (r, g, b))
    return "#%02X%02X%02X" % (r, g, b)


def mix(hexcolor: str, ratio: float) -> str:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: round(c + (255 - c) * ratio)
    return "#%02X%02X%02X" % (f(r), f(g), f(b))


def build(kind, accent, ink, shape, latin, extra) -> dict:
    tint = mix(accent, 0.92)
    hl = mix(accent, 0.74)
    aink = darken_to_readable(accent)
    disp, val, align = shape
    box = "display:inline-block; " if disp == "inline" else ""
    mid = f"text-align:{align}; " if align != "left" else ""

    if kind == "N":
        h2 = (f"{box}{mid}font-size:22px; font-weight:800; color:{ink}; line-height:1.4; "
              f"letter-spacing:-0.3px; margin:56px 0 20px; padding-bottom:12px; "
              f"border-bottom:{val} solid {accent};")
        h3 = f"font-size:17px; font-weight:800; color:{aink}; line-height:1.6; letter-spacing:0.5px; margin:40px 0 12px;"
    elif kind == "S":
        h2 = (f"{box}{mid}font-size:19px; font-weight:700; color:#FFFFFF; line-height:1.45; "
              f"margin:52px 0 20px; padding:13px 18px; background:{accent}; border-radius:{val};")
        h3 = f"font-size:17px; font-weight:700; color:{aink}; line-height:1.6; margin:38px 0 12px;"
    else:
        side, px = ("bottom", "4px") if val == "bottom4" else ("top", "4px")
        pad = f"padding-{'top' if side == 'top' else 'bottom'}:14px"
        h2 = (f"display:inline-block; font-size:22px; font-weight:800; color:{ink}; line-height:1.4; "
              f"letter-spacing:-0.3px; margin:56px 0 20px; {pad}; border-{side}:{px} solid {accent};")
        h3 = f"font-size:17px; font-weight:800; color:{aink}; line-height:1.6; letter-spacing:0.5px; margin:40px 0 12px;"

    body = {"font-size": "16px", "line-height": "1.95", "color": ink,
            "margin": "0 0 28px", "font-weight": "400"}
    body.update(extra)
    if latin:
        body["font-family"] = latin
    p = "; ".join(f"{k}:{v}" for k, v in body.items()) + ";"
    li = p.replace("margin:0 0 28px", "margin:0 0 10px").replace("line-height:1.95", "line-height:1.9")

    styles = {
        "h1": f"font-size:26px; font-weight:800; color:{ink}; line-height:1.35; letter-spacing:-0.5px; margin:0 0 32px;",
        "h2": h2,
        "h3": h3,
        "h4": f"font-size:15px; font-weight:700; color:{ink}; line-height:1.6; margin:28px 0 10px;",
        "p": p,
        "strong": f"color:{ink}; font-weight:700; background:linear-gradient(transparent 62%, {hl} 62%);",
        "em": f"font-style:normal; color:{aink}; font-weight:600;",
        "a": f"color:{aink}; text-decoration:none; font-weight:500;",
        "blockquote": (f"color:{ink}; font-size:16.5px; line-height:1.8; font-weight:500; "
                       f"padding:2px 0 2px 18px; margin:0 0 30px; border-left:3px solid #D6D9DE;"
                       + (f" font-family:{latin};" if latin else "")),
        "ul": "margin:0 0 28px; padding-left:20px; list-style:disc;",
        "ol": "margin:0 0 28px; padding-left:20px; list-style:decimal;",
        "li": li,
        "hr": f"border:none; height:4px; width:36px; background:{accent}; display:block; margin:56px auto;",
        "img": "display:block; max-width:100%; height:auto; margin:8px auto 10px; border-radius:12px;",
        "figcaption": f"text-align:center; font-size:13px; line-height:1.7; color:{MUTED}; margin:10px 0 32px;",
        "code": f"font-family:{MONO}; font-size:14px; color:{aink}; background:{tint}; border-radius:5px; padding:1px 6px;",
        "pre": (f"background:{CODE_BG_DARK}; color:#E6E8EB; font-family:{MONO}; font-size:13px; "
                f"line-height:1.8; padding:20px 18px; margin:0 0 30px; border-radius:14px; overflow-x:auto;"),
        "highlight": f"background:{tint}; color:{ink}; font-size:16px; line-height:1.9; padding:22px 20px; margin:0 0 30px; border-radius:16px;",
        "table": "width:100%; border-collapse:collapse; font-size:14.5px; margin:0 0 30px; font-variant-numeric:tabular-nums;",
        "th": (f"color:{MUTED}; font-size:12.5px; font-weight:700; letter-spacing:1px; text-align:left; "
               f"padding:10px 12px; border-bottom:2px solid {accent}; font-variant-numeric:tabular-nums;"),
        "td": (f"color:{ink}; font-size:14.5px; line-height:1.7; padding:13px 12px; "
               f"border-bottom:1px solid {RULE}; font-variant-numeric:tabular-nums;"
               + (f" font-family:{latin};" if latin else "")),
        "del": f"text-decoration:line-through; color:{MUTED};",
        "u": f"text-decoration:none; border-bottom:2px solid {accent}; padding-bottom:1px;",
    }
    variables = {"primary-color": accent, "primary-ink": aink, "bg-accent-color": tint,
                 "text-color": ink, "text-muted": MUTED}
    return {"variables": variables, "styles": styles}


def main(write: bool) -> int:
    print(f"{'主题':8} {'型':>3} {'主色':>9} {'文字色':>9}  形态")
    for name, (kind, accent, ink, shape, latin, extra) in PLAN.items():
        path = THEMES_DIR / f"{name}.yaml"
        if not path.exists():
            print(f"[ERROR] 缺 {path}")
            return 1
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        built = build(kind, accent, ink, shape, latin, extra)
        tag = "等宽" if latin == MONO else ("衬线" if latin == SERIF else "默认西文")
        print(f"  {name:7} {kind:>3} {accent:>9} {built['variables']['primary-ink']:>9}  "
              f"{shape[0]}/{shape[1]}/{shape[2]}、{tag}")
        if write:
            out = {"name": old.get("name") or name,
                   "description": old.get("description", ""),
                   **built}
            path.write_text(
                yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=10000),
                encoding="utf-8")

    if write:
        print(f"\n已写回 {THEMES_DIR}")
    else:
        print("\n未写盘（加 --write 生效）")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    sys.exit(main(ap.parse_args().write))
