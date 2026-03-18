#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

支持主题切换，主题按优先级查找：
1. .aws-article/presets/formatting/<主题名>.css
2. skill 内置 references/presets/themes/<主题名>.css

用法：
    python format.py <article.md>                      使用默认主题
    python format.py <article.md> --theme grace         指定主题
    python format.py <article.md> --theme grace -o out.html
    python format.py <article.md> --color "#0F4C81"     自定义主色
    python format.py <article.md> --font-size 16px
    python format.py --list-themes                       列出可用主题
"""

import argparse
import html
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
BUILTIN_THEMES_DIR = SKILL_DIR / "references" / "presets" / "themes"


def _err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"✅ {msg}")


def _info(msg: str):
    print(f"ℹ️  {msg}")


# ── 主题 ─────────────────────────────────────────────────────

DEFAULT_VARS = {
    "primary-color": "#0F4C81",
    "text-color": "#333333",
    "text-light": "#666666",
    "text-muted": "#999999",
    "bg-light": "#F7F7F7",
    "border-color": "#EEEEEE",
    "link-color": "#576B95",
    "font-size": "16px",
    "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "line-height": "1.8",
    "paragraph-spacing": "1.5em",
}

THEMES = {
    "default": {
        "primary-color": "#0F4C81",
        "h1-style": "text-align:center; font-size:22px; font-weight:bold; border-bottom:1px solid {primary-color}; padding-bottom:12px; margin-bottom:24px;",
        "h2-style": "font-size:18px; font-weight:bold; border-left:3px solid {primary-color}; padding-left:10px; margin-top:2em; margin-bottom:1em;",
        "h3-style": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
        "blockquote-style": "border-left:3px solid {primary-color}; background:{bg-light}; padding:12px 16px; margin:1em 0; color:{text-light};",
        "hr-style": "border:none; border-top:1px dashed #CCCCCC; width:60%; margin:2em auto;",
        "strong-color": "{primary-color}",
    },
    "grace": {
        "primary-color": "#92617E",
        "h1-style": "text-align:center; font-size:22px; font-weight:bold; text-shadow:1px 1px 2px rgba(0,0,0,0.1); margin-bottom:24px;",
        "h2-style": "font-size:18px; font-weight:bold; background:{primary-color}; color:#FFFFFF; padding:6px 14px; border-radius:6px; margin-top:2em; margin-bottom:1em; display:inline-block;",
        "h3-style": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
        "blockquote-style": "border-left:none; background:{bg-light}; padding:16px 20px; border-radius:8px; margin:1em 0; color:{text-light};",
        "hr-style": "border:none; border-top:1px solid #E8E0E4; width:50%; margin:2em auto;",
        "strong-color": "{primary-color}",
    },
    "modern": {
        "primary-color": "#D97757",
        "h1-style": "text-align:center; font-size:24px; font-weight:bold; margin-bottom:28px;",
        "h2-style": "font-size:18px; font-weight:bold; background:{primary-color}; color:#FFFFFF; padding:8px 20px; border-radius:20px; margin-top:2em; margin-bottom:1em; display:inline-block;",
        "h3-style": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
        "blockquote-style": "border-left:4px solid {primary-color}; background:#FFF8F5; padding:14px 18px; border-radius:0 8px 8px 0; margin:1em 0; color:{text-light};",
        "hr-style": "border:none; border-top:2px solid {primary-color}; width:40%; margin:2em auto; opacity:0.3;",
        "strong-color": "{primary-color}",
    },
    "simple": {
        "primary-color": "#333333",
        "h1-style": "font-size:22px; font-weight:bold; margin-bottom:24px;",
        "h2-style": "font-size:18px; font-weight:bold; margin-top:2em; margin-bottom:1em; padding-bottom:6px; border-bottom:1px solid {border-color};",
        "h3-style": "font-size:16px; font-weight:bold; margin-top:1.5em; margin-bottom:0.8em;",
        "blockquote-style": "border-left:3px solid #DDDDDD; padding:8px 16px; margin:1em 0; color:{text-muted};",
        "hr-style": "border:none; border-top:1px solid #EEEEEE; margin:2em 0;",
        "strong-color": "#000000",
    },
}


def _resolve_vars(template: str, variables: dict) -> str:
    """替换模板中的 {variable} 占位符。"""
    result = template
    for _ in range(3):
        for key, val in variables.items():
            result = result.replace(f"{{{key}}}", val)
    return result


def _build_styles(theme_name: str, overrides: dict = None) -> dict:
    """构建完整的样式字典。"""
    theme = THEMES.get(theme_name, THEMES["default"])
    variables = {**DEFAULT_VARS, **theme, **(overrides or {})}

    resolved = {}
    for key, val in variables.items():
        resolved[key] = _resolve_vars(val, variables)
    return resolved


# ── Markdown → HTML ──────────────────────────────────────────

def _md_to_html(md_text: str, styles: dict) -> str:
    """简易 Markdown → 带 inline style 的 HTML 转换。"""

    lines = md_text.strip().split("\n")
    html_parts = []
    in_list = None
    in_blockquote = False
    paragraph_lines = []

    def flush_paragraph():
        if paragraph_lines:
            text = " ".join(paragraph_lines)
            text = _inline_format(text, styles)
            html_parts.append(
                f'<p style="margin:0 0 {styles["paragraph-spacing"]} 0; '
                f'font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]}; '
                f'color:{styles["text-color"]};">{text}</p>'
            )
            paragraph_lines.clear()

    def close_list():
        nonlocal in_list
        if in_list:
            html_parts.append(f"</{in_list}>")
            in_list = None

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html_parts.append("</blockquote>")
            in_blockquote = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            close_list()
            close_blockquote()
            continue

        # headings
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            close_blockquote()
            level = len(heading_match.group(1))
            text = _inline_format(heading_match.group(2), styles)
            tag = f"h{level}"
            style_key = f"h{level}-style"
            style = styles.get(style_key, "")
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            continue

        # hr
        if re.match(r'^---+$', stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            html_parts.append(f'<hr style="{styles.get("hr-style", "")}" />')
            continue

        # image placeholder (preserve for images skill)
        img_match = re.match(r'^!\[(.+?)\]\((.+?)\)$', stripped)
        if img_match:
            flush_paragraph()
            alt = html.escape(img_match.group(1))
            src = img_match.group(2)
            html_parts.append(
                f'<p style="text-align:center; margin:1.5em 0;">'
                f'<img src="{src}" alt="{alt}" style="max-width:100%; border-radius:4px;" />'
                f'</p>'
            )
            if "：" in alt:
                caption = alt.split("：", 1)[1]
                html_parts.append(
                    f'<p style="text-align:center; font-size:14px; '
                    f'color:{styles["text-muted"]}; margin-top:-0.8em; margin-bottom:1.5em;">'
                    f'{html.escape(caption)}</p>'
                )
            continue

        # blockquote
        if stripped.startswith("> "):
            flush_paragraph()
            close_list()
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{styles.get("blockquote-style", "")}">')
                in_blockquote = True
            text = _inline_format(stripped[2:], styles)
            html_parts.append(
                f'<p style="margin:0.3em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</p>'
            )
            continue
        elif in_blockquote:
            close_blockquote()

        # unordered list
        if re.match(r'^[-*]\s+', stripped):
            flush_paragraph()
            if in_list != "ul":
                close_list()
                html_parts.append(
                    f'<ul style="margin:0.8em 0; padding-left:1.5em; '
                    f'color:{styles["text-color"]};">'
                )
                in_list = "ul"
            text = _inline_format(re.sub(r'^[-*]\s+', '', stripped), styles)
            html_parts.append(
                f'<li style="margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</li>'
            )
            continue

        # ordered list
        ol_match = re.match(r'^\d+\.\s+', stripped)
        if ol_match:
            flush_paragraph()
            if in_list != "ol":
                close_list()
                html_parts.append(
                    f'<ol style="margin:0.8em 0; padding-left:1.5em; '
                    f'color:{styles["text-color"]};">'
                )
                in_list = "ol"
            text = _inline_format(re.sub(r'^\d+\.\s+', '', stripped), styles)
            html_parts.append(
                f'<li style="margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</li>'
            )
            continue

        # regular paragraph
        close_list()
        close_blockquote()
        paragraph_lines.append(stripped)

    flush_paragraph()
    close_list()
    close_blockquote()

    return "\n".join(html_parts)


def _inline_format(text: str, styles: dict) -> str:
    """处理行内格式：加粗、斜体、行内代码、链接。"""
    strong_color = styles.get("strong-color", styles["primary-color"])
    text = re.sub(
        r'\*\*(.+?)\*\*',
        rf'<strong style="color:{strong_color}; font-weight:bold;">\1</strong>',
        text,
    )
    text = re.sub(
        r'\*(.+?)\*',
        r'<em>\1</em>',
        text,
    )
    text = re.sub(
        r'`(.+?)`',
        rf'<code style="background:{styles["bg-light"]}; padding:2px 6px; '
        rf'border-radius:3px; font-size:0.9em; color:{styles["primary-color"]};">\1</code>',
        text,
    )
    text = re.sub(
        r'\[(.+?)\]\((.+?)\)',
        rf'<a style="color:{styles["link-color"]}; text-decoration:none;" href="\2">\1</a>',
        text,
    )
    return text


# ── 输出 ─────────────────────────────────────────────────────

def _wrap_document(body_html: str, styles: dict) -> str:
    """包装为完整的 HTML 文档。"""
    return (
        f'<section style="'
        f'font-family:{styles["font-family"]}; '
        f'font-size:{styles["font-size"]}; '
        f'line-height:{styles["line-height"]}; '
        f'color:{styles["text-color"]}; '
        f'padding:16px; '
        f'text-align:left;'
        f'">\n'
        f'{body_html}\n'
        f'</section>'
    )


# ── 主题发现 ─────────────────────────────────────────────────

def _list_themes() -> list[str]:
    """列出所有可用主题。"""
    themes = list(THEMES.keys())

    user_dir = Path(".aws-article/presets/formatting")
    if user_dir.exists():
        for f in user_dir.glob("*.css"):
            name = f.stem
            if name not in themes:
                themes.append(name)
    return sorted(themes)


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="公众号文章排版工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", nargs="?", help="Markdown 文件路径")
    parser.add_argument("--theme", default="default", help="主题名（default/grace/modern/simple）")
    parser.add_argument("--color", help="自定义主色（如 #0F4C81）")
    parser.add_argument("--font-size", help="字号（如 16px）")
    parser.add_argument("-o", "--output", help="输出路径（默认同名 .html）")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")

    args = parser.parse_args()

    if args.list_themes:
        print("可用主题：")
        for t in _list_themes():
            marker = " (内置)" if t in THEMES else " (自定义)"
            print(f"  {t}{marker}")
        return

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    md_text = input_path.read_text(encoding="utf-8")

    overrides = {}
    if args.color:
        overrides["primary-color"] = args.color
    if args.font_size:
        overrides["font-size"] = args.font_size

    _info(f"主题: {args.theme}")
    styles = _build_styles(args.theme, overrides)
    body_html = _md_to_html(md_text, styles)
    full_html = _wrap_document(body_html, styles)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    _ok(f"已保存: {output_path}")


if __name__ == "__main__":
    main()
