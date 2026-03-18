#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

支持主题切换，主题按优先级查找：
1. .aws-article/presets/formatting/<主题名>.yaml（用户自定义）
2. 脚本内置主题

用户自定义主题：创建 YAML 文件放入 .aws-article/presets/formatting/ 即可使用。

用法：
    python format.py <article.md>                      使用默认主题
    python format.py <article.md> --theme grace         指定主题
    python format.py <article.md> --theme my-brand      使用自定义主题
    python format.py <article.md> --color "#0F4C81"     覆盖主色
    python format.py <article.md> --font-size 16px
    python format.py --list-themes                       列出可用主题
    python format.py --export-theme default              导出内置主题为 YAML（方便基于此自定义）
"""

import argparse
import html as html_mod
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent

USER_THEMES_DIRS = [
    Path(".aws-article/presets/formatting"),
    Path.home() / ".aws-article" / "presets" / "formatting",
]


def _err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"✅ {msg}")


def _info(msg: str):
    print(f"ℹ️  {msg}")


# ── 主题定义 ─────────────────────────────────────────────────

DEFAULT_VARIABLES = {
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

BUILTIN_THEMES = {
    "default": {
        "name": "经典蓝",
        "description": "左边框小标题，底部分割线大标题，适合科技、干货、通用",
        "variables": {
            "primary-color": "#0F4C81",
        },
        "styles": {
            "h1": "text-align:center; font-size:22px; font-weight:bold; border-bottom:1px solid {primary-color}; padding-bottom:12px; margin-bottom:24px;",
            "h2": "font-size:18px; font-weight:bold; border-left:3px solid {primary-color}; padding-left:10px; margin-top:2em; margin-bottom:1em;",
            "h3": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
            "blockquote": "border-left:3px solid {primary-color}; background:{bg-light}; padding:12px 16px; margin:1em 0; color:{text-light};",
            "hr": "border:none; border-top:1px dashed #CCCCCC; width:60%; margin:2em auto;",
            "strong-color": "{primary-color}",
        },
    },
    "grace": {
        "name": "优雅紫",
        "description": "圆角色块小标题，文字阴影，适合文艺、生活方式",
        "variables": {
            "primary-color": "#92617E",
        },
        "styles": {
            "h1": "text-align:center; font-size:22px; font-weight:bold; text-shadow:1px 1px 2px rgba(0,0,0,0.1); margin-bottom:24px;",
            "h2": "font-size:18px; font-weight:bold; background:{primary-color}; color:#FFFFFF; padding:6px 14px; border-radius:6px; margin-top:2em; margin-bottom:1em; display:inline-block;",
            "h3": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
            "blockquote": "border-left:none; background:{bg-light}; padding:16px 20px; border-radius:8px; margin:1em 0; color:{text-light};",
            "hr": "border:none; border-top:1px solid #E8E0E4; width:50%; margin:2em auto;",
            "strong-color": "{primary-color}",
        },
    },
    "modern": {
        "name": "暖橙",
        "description": "胶囊圆角小标题，宽松行高，适合现代感、品牌",
        "variables": {
            "primary-color": "#D97757",
        },
        "styles": {
            "h1": "text-align:center; font-size:24px; font-weight:bold; margin-bottom:28px;",
            "h2": "font-size:18px; font-weight:bold; background:{primary-color}; color:#FFFFFF; padding:8px 20px; border-radius:20px; margin-top:2em; margin-bottom:1em; display:inline-block;",
            "h3": "font-size:16px; font-weight:bold; color:{primary-color}; margin-top:1.5em; margin-bottom:0.8em;",
            "blockquote": "border-left:4px solid {primary-color}; background:#FFF8F5; padding:14px 18px; border-radius:0 8px 8px 0; margin:1em 0; color:{text-light};",
            "hr": "border:none; border-top:2px solid {primary-color}; width:40%; margin:2em auto; opacity:0.3;",
            "strong-color": "{primary-color}",
        },
    },
    "simple": {
        "name": "极简黑",
        "description": "底线小标题，最少装饰，适合极简主义、学术",
        "variables": {
            "primary-color": "#333333",
        },
        "styles": {
            "h1": "font-size:22px; font-weight:bold; margin-bottom:24px;",
            "h2": "font-size:18px; font-weight:bold; margin-top:2em; margin-bottom:1em; padding-bottom:6px; border-bottom:1px solid {border-color};",
            "h3": "font-size:16px; font-weight:bold; margin-top:1.5em; margin-bottom:0.8em;",
            "blockquote": "border-left:3px solid #DDDDDD; padding:8px 16px; margin:1em 0; color:{text-muted};",
            "hr": "border:none; border-top:1px solid #EEEEEE; margin:2em 0;",
            "strong-color": "#000000",
        },
    },
}


# ── 主题加载 ─────────────────────────────────────────────────

def _load_user_theme(name: str) -> dict | None:
    """从用户目录加载自定义主题。"""
    import yaml

    for d in USER_THEMES_DIRS:
        path = d / f"{name}.yaml"
        if path.exists():
            _info(f"加载用户主题: {path}")
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        yml_path = d / f"{name}.yml"
        if yml_path.exists():
            _info(f"加载用户主题: {yml_path}")
            with open(yml_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return None


def _load_theme(name: str) -> dict:
    """按优先级加载主题：用户自定义 > 内置。"""
    user_theme = _load_user_theme(name)
    if user_theme:
        return user_theme

    if name in BUILTIN_THEMES:
        return BUILTIN_THEMES[name]

    _err(
        f"主题 '{name}' 不存在。\n"
        f"可用主题：{', '.join(_list_themes())}\n"
        f"或在 .aws-article/presets/formatting/ 下创建 {name}.yaml"
    )


def _resolve_vars(template: str, variables: dict) -> str:
    """替换模板中的 {variable} 占位符。"""
    result = template
    for _ in range(3):
        for key, val in variables.items():
            result = result.replace(f"{{{key}}}", str(val))
    return result


def _build_styles(theme: dict, overrides: dict = None) -> dict:
    """从主题定义构建完整的样式字典。"""
    variables = {**DEFAULT_VARIABLES}
    variables.update(theme.get("variables", {}))
    if overrides:
        variables.update(overrides)

    resolved = {}
    for key, val in variables.items():
        resolved[key] = _resolve_vars(str(val), variables)

    styles = theme.get("styles", BUILTIN_THEMES["default"]["styles"])
    for key, val in styles.items():
        resolved[key] = _resolve_vars(str(val), resolved)

    return resolved


# ── 主题发现 ─────────────────────────────────────────────────

def _list_themes() -> list[dict]:
    """列出所有可用主题。"""
    themes = []

    for name, t in BUILTIN_THEMES.items():
        themes.append({"name": name, "label": t.get("name", ""), "source": "内置"})

    seen = {t["name"] for t in themes}
    for d in USER_THEMES_DIRS:
        if d.exists():
            for f in sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")):
                name = f.stem
                if name not in seen:
                    import yaml
                    with open(f, encoding="utf-8") as fh:
                        data = yaml.safe_load(fh) or {}
                    themes.append({
                        "name": name,
                        "label": data.get("name", ""),
                        "source": "自定义",
                    })
                    seen.add(name)
                else:
                    for t in themes:
                        if t["name"] == name:
                            t["source"] = "自定义(覆盖内置)"
    return themes


def _export_theme(name: str) -> str:
    """将内置主题导出为 YAML 格式。"""
    import yaml

    if name not in BUILTIN_THEMES:
        _err(f"内置主题 '{name}' 不存在，可导出：{', '.join(BUILTIN_THEMES.keys())}")

    theme = BUILTIN_THEMES[name]
    full = {
        "name": theme.get("name", name),
        "description": theme.get("description", ""),
        "variables": {**DEFAULT_VARIABLES, **theme.get("variables", {})},
        "styles": theme.get("styles", {}),
    }
    return yaml.dump(full, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ── Markdown → HTML ──────────────────────────────────────────

def _md_to_html(md_text: str, styles: dict) -> str:
    """Markdown → 带 inline style 的 HTML。"""

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

        heading_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            close_blockquote()
            level = len(heading_match.group(1))
            text = _inline_format(heading_match.group(2), styles)
            tag = f"h{level}"
            style = styles.get(tag, "")
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            continue

        if re.match(r'^---+$', stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            html_parts.append(f'<hr style="{styles.get("hr", "")}" />')
            continue

        img_match = re.match(r'^!\[(.+?)\]\((.+?)\)$', stripped)
        if img_match:
            flush_paragraph()
            alt = html_mod.escape(img_match.group(1))
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
                    f'{html_mod.escape(caption)}</p>'
                )
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            close_list()
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{styles.get("blockquote", "")}">')
                in_blockquote = True
            text = _inline_format(stripped[2:], styles)
            html_parts.append(
                f'<p style="margin:0.3em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</p>'
            )
            continue
        elif in_blockquote:
            close_blockquote()

        if re.match(r'^[-*]\s+', stripped):
            flush_paragraph()
            if in_list != "ul":
                close_list()
                html_parts.append(
                    f'<ul style="margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};">'
                )
                in_list = "ul"
            text = _inline_format(re.sub(r'^[-*]\s+', '', stripped), styles)
            html_parts.append(
                f'<li style="margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</li>'
            )
            continue

        ol_match = re.match(r'^\d+\.\s+', stripped)
        if ol_match:
            flush_paragraph()
            if in_list != "ol":
                close_list()
                html_parts.append(
                    f'<ol style="margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};">'
                )
                in_list = "ol"
            text = _inline_format(re.sub(r'^\d+\.\s+', '', stripped), styles)
            html_parts.append(
                f'<li style="margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</li>'
            )
            continue

        close_list()
        close_blockquote()
        paragraph_lines.append(stripped)

    flush_paragraph()
    close_list()
    close_blockquote()

    return "\n".join(html_parts)


def _inline_format(text: str, styles: dict) -> str:
    """处理行内格式：加粗、斜体、行内代码、链接。"""
    strong_color = styles.get("strong-color", styles.get("primary-color", "#333"))
    text = re.sub(
        r'\*\*(.+?)\*\*',
        rf'<strong style="color:{strong_color}; font-weight:bold;">\1</strong>',
        text,
    )
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(
        r'`(.+?)`',
        rf'<code style="background:{styles.get("bg-light", "#F7F7F7")}; padding:2px 6px; '
        rf'border-radius:3px; font-size:0.9em; color:{styles.get("primary-color", "#333")};">\1</code>',
        text,
    )
    text = re.sub(
        r'\[(.+?)\]\((.+?)\)',
        rf'<a style="color:{styles.get("link-color", "#576B95")}; text-decoration:none;" href="\2">\1</a>',
        text,
    )
    return text


def _wrap_document(body_html: str, styles: dict) -> str:
    """包装为 HTML section。"""
    return (
        f'<section style="'
        f'font-family:{styles.get("font-family", "sans-serif")}; '
        f'font-size:{styles["font-size"]}; '
        f'line-height:{styles["line-height"]}; '
        f'color:{styles["text-color"]}; '
        f'padding:16px; text-align:left;'
        f'">\n{body_html}\n</section>'
    )


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="公众号文章排版工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", nargs="?", help="Markdown 文件路径")
    parser.add_argument("--theme", default="default", help="主题名")
    parser.add_argument("--color", help="覆盖主色（如 #0F4C81）")
    parser.add_argument("--font-size", help="覆盖字号（如 16px）")
    parser.add_argument("-o", "--output", help="输出路径（默认同名 .html）")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")
    parser.add_argument("--export-theme", metavar="NAME", help="导出内置主题为 YAML")

    args = parser.parse_args()

    if args.list_themes:
        print("可用主题：")
        for t in _list_themes():
            label = f" ({t['label']})" if t["label"] else ""
            print(f"  {t['name']}{label} [{t['source']}]")
        return

    if args.export_theme:
        print(_export_theme(args.export_theme))
        return

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    md_text = input_path.read_text(encoding="utf-8")

    theme = _load_theme(args.theme)

    overrides = {}
    if args.color:
        overrides["primary-color"] = args.color
    if args.font_size:
        overrides["font-size"] = args.font_size

    _info(f"主题: {args.theme}")
    styles = _build_styles(theme, overrides)
    body_html = _md_to_html(md_text, styles)
    full_html = _wrap_document(body_html, styles)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    _ok(f"已保存: {output_path}")


if __name__ == "__main__":
    main()
