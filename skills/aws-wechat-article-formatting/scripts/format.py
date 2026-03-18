#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

所有主题均为 YAML 文件，按优先级查找：
1. .aws-article/presets/formatting/<主题名>.yaml（用户自定义）
2. skill 内置 references/presets/themes/<主题名>.yaml

用法：
    python format.py <article.md>                      使用默认主题
    python format.py <article.md> --theme grace         指定主题
    python format.py <article.md> --theme my-brand      使用自定义主题
    python format.py <article.md> --color "#0F4C81"     覆盖主色
    python format.py <article.md> --font-size 16px
    python format.py --list-themes                       列出可用主题
"""

import argparse
import html as html_mod
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
BUILTIN_THEMES_DIR = SKILL_DIR / "references" / "presets" / "themes"

USER_THEMES_DIRS = [
    Path(".aws-article/presets/formatting"),
    Path.home() / ".aws-article" / "presets" / "formatting",
]

THEME_SEARCH_DIRS = USER_THEMES_DIRS + [BUILTIN_THEMES_DIR]

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

DEFAULT_STYLES = {
    "h1": "text-align:center; font-size:22px; font-weight:bold; margin-bottom:24px;",
    "h2": "font-size:18px; font-weight:bold; margin-top:2em; margin-bottom:1em;",
    "h3": "font-size:16px; font-weight:bold; margin-top:1.5em; margin-bottom:0.8em;",
    "blockquote": "border-left:3px solid #DDD; padding:8px 16px; margin:1em 0;",
    "hr": "border:none; border-top:1px solid #EEE; margin:2em 0;",
    "strong-color": "#333333",
}


def _err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"✅ {msg}")


def _info(msg: str):
    print(f"ℹ️  {msg}")


# ── 主题加载 ─────────────────────────────────────────────────

def _find_theme_file(name: str) -> Path | None:
    """按优先级查找主题文件。"""
    for d in THEME_SEARCH_DIRS:
        for ext in (".yaml", ".yml"):
            path = d / f"{name}{ext}"
            if path.exists():
                return path
    return None


def _load_theme_file(path: Path) -> dict:
    """加载单个主题 YAML 文件。"""
    import yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _load_theme(name: str) -> dict:
    """按优先级加载主题。"""
    path = _find_theme_file(name)
    if not path:
        available = ", ".join(t["name"] for t in _list_themes())
        _err(
            f"主题 '{name}' 不存在。\n"
            f"可用主题：{available}\n"
            f"创建自定义主题：在 .aws-article/presets/formatting/ 下新建 {name}.yaml"
        )
    _info(f"加载主题: {path}")
    return _load_theme_file(path)


def _list_themes() -> list[dict]:
    """列出所有可用主题（用户自定义优先，同名去重）。"""
    themes = []
    seen = set()

    for d in THEME_SEARCH_DIRS:
        if not d.exists():
            continue
        is_builtin = (d == BUILTIN_THEMES_DIR)
        for f in sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")):
            name = f.stem
            if name in seen:
                continue
            seen.add(name)
            data = _load_theme_file(f)
            source = "内置" if is_builtin else "自定义"
            if not is_builtin and (BUILTIN_THEMES_DIR / f"{name}.yaml").exists():
                source = "自定义(覆盖内置)"
            themes.append({
                "name": name,
                "label": data.get("name", ""),
                "description": data.get("description", ""),
                "source": source,
            })
    return themes


# ── 样式构建 ─────────────────────────────────────────────────

def _resolve_vars(template: str, variables: dict) -> str:
    """替换 {variable} 占位符。"""
    result = template
    for _ in range(3):
        for key, val in variables.items():
            result = result.replace(f"{{{key}}}", str(val))
    return result


def _build_styles(theme: dict, overrides: dict = None) -> dict:
    """从主题文件构建完整样式字典。"""
    variables = {**DEFAULT_VARIABLES}
    variables.update(theme.get("variables", {}))
    if overrides:
        variables.update(overrides)

    resolved = {}
    for key, val in variables.items():
        resolved[key] = _resolve_vars(str(val), variables)

    styles = {**DEFAULT_STYLES}
    styles.update(theme.get("styles", {}))
    for key, val in styles.items():
        resolved[key] = _resolve_vars(str(val), resolved)

    return resolved


# ── Markdown 预格式化 ─────────────────────────────────────────

def _preformat_markdown(text: str) -> str:
    """预格式化 Markdown：修复中文排版常见问题。"""

    # 中英文之间加空格
    text = re.sub(r'([\u4e00-\u9fff])([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z0-9])([\u4e00-\u9fff])', r'\1 \2', text)

    # 中文与数字之间加空格
    text = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([\u4e00-\u9fff])', r'\1 \2', text)

    # ASCII 引号 → 中文引号（简单启发式）
    text = re.sub(r'"([^"]*?)"', r'「\1」', text)

    # 连续多个空行 → 最多两个
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 修复加粗标记中的空格问题（** 内侧不应有空格）
    text = re.sub(r'\*\*\s+', '**', text)
    text = re.sub(r'\s+\*\*', '**', text)

    return text


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
            alt = img_match.group(1)
            src = img_match.group(2)

            # 封面图不进正文 HTML（通过 API 单独上传）
            if alt.startswith("封面"):
                continue

            alt_escaped = html_mod.escape(alt)
            html_parts.append(
                f'<p style="text-align:center; margin:1.5em 0;">'
                f'<img src="{src}" alt="{alt_escaped}" style="max-width:100%; border-radius:4px;" />'
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
    """行内格式：加粗、斜体、行内代码、链接。"""
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
    parser.add_argument("--no-preformat", action="store_true", help="跳过 Markdown 预格式化")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")

    args = parser.parse_args()

    if args.list_themes:
        print("可用主题：")
        for t in _list_themes():
            label = f" ({t['label']})" if t["label"] else ""
            desc = f" - {t['description']}" if t["description"] else ""
            print(f"  {t['name']}{label} [{t['source']}]{desc}")
        return

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    md_text = input_path.read_text(encoding="utf-8")

    if not args.no_preformat:
        md_text = _preformat_markdown(md_text)
        _info("Markdown 预格式化完成（中英文间距、引号、空行）")

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
