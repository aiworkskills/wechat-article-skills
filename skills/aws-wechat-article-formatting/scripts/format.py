#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

所有主题均为 YAML 文件，按优先级查找：
1. .aws-article/presets/formatting/<主题名>.yaml（用户自定义）
2. skill 内置 references/presets/themes/<主题名>.yaml

用法：
    python format.py <article.md>                      主题：合并配置中 default_format_preset（须为 YAML 列表），否则 default；多候选须本篇改为单元素列表
    python format.py <article.md> --theme grace         显式指定主题（覆盖配置）
    python format.py <article.md> --theme my-brand      使用自定义主题
    python format.py <article.md> --color "#0F4C81"     覆盖主色
    python format.py <article.md> --font-size 16px
    python format.py --list-themes                       列出可用主题
"""

import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             

import yaml

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
    "bg-accent-color": "#F0F4F8",
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
    "h4": "",
    "p": "",
    "strong": "",
    "em": "",
    "a": "",
    "blockquote": "border-left:3px solid #DDD; padding:8px 16px; margin:1em 0;",
    "ul": "",
    "ol": "",
    "li": "",
    "hr": "border:none; border-top:1px solid #EEE; margin:2em 0;",
    "img": "",
    "figcaption": "",
    "code": "",
    "pre": "",
    "strong-color": "#333333",
}


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


def _coerce_single_preset(field_label: str, raw) -> str:
    """default_format_preset：仅 YAML 列表；[] 空；[名] 单主题；多项须本篇改为单元素列表。"""
    if raw is None:
        return ""
    if isinstance(raw, str):
        _err(
            f"{field_label} 须为 YAML 列表（例如 [] 或 [主题名]），勿使用字符串。"
            f" 当前为字符串，请改为列表形式。"
        )
    if isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw if x is not None and str(x).strip()]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        _err(
            f"{field_label} 含多个候选 {items!r}：请先在本篇 article.yaml 中写入同名字段，"
            f"且值为仅含**一项**的列表，再运行 format.py。"
        )
    _err(f"{field_label} 须为 YAML 列表，当前类型：{type(raw).__name__}")


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


# ── 本篇 + 仓库 config（主题默认名、embeds）────────────────────

_CONFIG_SKIP = frozenset({"writing_model", "image_model"})


def _safe_yaml_dict(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _deep_merge_dict(base: dict, override: dict) -> dict:
    """递归合并字典；override 中非 dict 值整键覆盖（含 list）。"""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def _merge_format_context(draft_dir: Path) -> dict:
    """
    合并：.aws-article/config.yaml（顶层，不含 writing_model/image_model）
    → 本篇 article.yaml（同键本篇覆盖）。
    仅 embeds.related_articles 与全局深度合并；名片/小程序等仍以全局 embeds 为准，本篇 article.yaml 的其它 embeds 子键不参与覆盖。
    """
    merged: dict = {}
    cfg = _safe_yaml_dict(Path(".aws-article/config.yaml"))
    for k, v in cfg.items():
        if k not in _CONFIG_SKIP:
            merged[k] = v
    art = _safe_yaml_dict(draft_dir / "article.yaml")
    art_emb = art.get("embeds")
    if isinstance(art_emb, dict) and "related_articles" in art_emb:
        ge = merged.get("embeds")
        if not isinstance(ge, dict):
            merged["embeds"] = {}
            ge = merged["embeds"]
        ra = art_emb["related_articles"]
        if isinstance(ra, dict):
            br = ge.get("related_articles")
            if isinstance(br, dict):
                ge["related_articles"] = _deep_merge_dict(br, ra)
            else:
                ge["related_articles"] = dict(ra)
    for k, v in art.items():
        if k == "embeds":
            continue
        merged[k] = v
    return merged


# ── 嵌入元素 ─────────────────────────────────────────────────

def _resolve_embeds_config(draft_dir: Path) -> dict:
    """embeds：来自合并后的 config + 本篇（见 _merge_format_context）。"""
    ctx = _merge_format_context(draft_dir)
    emb = ctx.get("embeds")
    if isinstance(emb, dict) and emb:
        _info("嵌入元素配置来自 config.yaml / 本篇 YAML 合并")
        return emb
    return {}


def _xml_attr(value: object) -> str:
    """属性值转义，用于双引号属性。"""
    return html_mod.escape(str(value or ""), quote=True)


def _resolve_embeds(html_text: str, embeds: dict) -> str:
    """替换 {embed:type:name} 标记为对应 HTML。"""
    def _normalize_embed_name(name: str) -> str:
        # Preformat may insert spaces between CJK and ASCII.
        # Normalize all whitespace for robust key matching.
        return re.sub(r"\s+", "", str(name or ""))

    profiles = {}
    for p in embeds.get("profiles", []):
        if not isinstance(p, dict):
            continue
        seen_keys = set()
        for raw in (p.get("name"), p.get("nickname")):
            nk = _normalize_embed_name(raw or "")
            if nk and nk not in seen_keys:
                seen_keys.add(nk)
                profiles[nk] = p
    miniprograms = {}
    for m in embeds.get("miniprograms", []):
        if not isinstance(m, dict):
            continue
        seen_keys = set()
        for raw in (m.get("name"), m.get("title")):
            nk = _normalize_embed_name(raw or "")
            if nk and nk not in seen_keys:
                seen_keys.add(nk)
                miniprograms[nk] = m
    miniprogram_cards = {}
    for m in embeds.get("miniprogram_cards", []):
        if not isinstance(m, dict):
            continue
        seen_keys = set()
        for raw in (m.get("name"), m.get("title")):
            nk = _normalize_embed_name(raw or "")
            if nk and nk not in seen_keys:
                seen_keys.add(nk)
                miniprogram_cards[nk] = m

    def _render_mp_common_miniprogram_card(m: dict, embed_name: str) -> str:
        """微信编辑器拉取的 mp-common-miniprogram 卡片（与 insertminiprogram 一致）。"""
        appid = (m.get("appid") or "").strip()
        path = (m.get("path") or "pages/index/index").strip()
        mp_nick = (
            m.get("miniprogram_nickname")
            or m.get("nickname")
            or m.get("title")
            or embed_name
        )
        mp_nick = str(mp_nick).strip()
        card_title = (m.get("card_title") or m.get("title") or embed_name).strip()
        avatar = (m.get("avatar") or m.get("miniprogram_avatar") or "").strip()
        imageurl = (
            (m.get("imageurl") or m.get("image") or m.get("card_image") or "").strip()
        )
        applink = (m.get("applink") or "").strip()
        servicetype = str(m.get("servicetype") or m.get("service_type") or "0").strip()
        missing = []
        if not appid:
            missing.append("appid")
        if not avatar:
            missing.append("avatar")
        if not imageurl:
            missing.append("imageurl")
        if not applink:
            missing.append("applink")
        if missing:
            return f"<!-- mp-common-miniprogram 缺少: {', '.join(missing)} -->"

        parts = [
            '<section nodeleaf=""><mp-common-miniprogram ',
            'class="js_uneditable custom_select_card mp_miniprogram_iframe" ',
            'data-pluginname="insertminiprogram" ',
            f'data-miniprogram-path="{_xml_attr(path)}" ',
            f'data-miniprogram-nickname="{_xml_attr(mp_nick)}" ',
            f'data-miniprogram-avatar="{_xml_attr(avatar)}" ',
            f'data-miniprogram-title="{_xml_attr(card_title)}" ',
            f'data-miniprogram-imageurl="{_xml_attr(imageurl)}" ',
            'data-miniprogram-type="card" ',
            f'data-miniprogram-servicetype="{_xml_attr(servicetype)}" ',
            f'data-miniprogram-appid="{_xml_attr(appid)}" ',
            f'data-miniprogram-applink="{_xml_attr(applink)}" ',
        ]
        back = (m.get("imageurlback") or m.get("image_url_back") or "").strip()
        if back:
            back_enc = quote(back, safe="") if back.startswith("http") else back
            parts.append(f'data-miniprogram-imageurlback="{_xml_attr(back_enc)}" ')
        crop = m.get("cropperinfo")
        if crop is not None and str(crop).strip() != "":
            if isinstance(crop, dict):
                crop_str = json.dumps(crop, ensure_ascii=False, separators=(",", ":"))
            else:
                crop_str = str(crop).strip()
            parts.append(
                f'data-miniprogram-cropperinfo="{_xml_attr(quote(crop_str, safe=""))}" '
            )
        parts.append("></mp-common-miniprogram></section>")
        parts.append(
            '<p style="margin:0 0 1.5em 0;font-size:16px;line-height:1.8;color:#333333;">'
            '<span leaf=""><br /></span></p>'
        )
        return "".join(parts)

    def _render_related_link(link_item: dict, fallback_name: str) -> str:
        """渲染微信正文普通超链接（仅依赖 name + url）。"""
        url = str(link_item.get("url") or "").strip()
        if not url:
            return f"<!-- 链接缺少 url: {fallback_name} -->"
        # 与后台常见永久链形态一致，避免仅 http 触发校验问题
        if url.startswith("http://mp.weixin.qq.com"):
            url = "https://" + url[len("http://") :]
        text_value = str(link_item.get("name") or "").strip() or fallback_name
        visible_text = text_value
        return (
            '<span leaf=""><a class="normal_text_link" target="_blank" style="" '
            f'href="{_xml_attr(url)}" textvalue="{_xml_attr(text_value)}" '
            'data-itemshowtype="0" linktype="text" data-linktype="2">'
            f"{html_mod.escape(visible_text)}</a></span>"
        )

    def _replace_embed(match):
        embed_type = match.group(1)
        embed_name = match.group(2)
        norm_name = _normalize_embed_name(embed_name)

        if embed_type == "profile":
            p = profiles.get(norm_name)
            if p:
                # 新形态：mp-common-profile（与草稿箱拉取一致），需 id + headimg
                pid = (p.get("profile_id") or p.get("id") or "").strip()
                headimg = (p.get("headimg") or "").strip()
                nickname = (p.get("nickname") or p.get("name") or "").strip()
                signature = (p.get("signature") or "").strip()
                service_type = str(p.get("service_type", "2")).strip()
                if pid and headimg:
                    return (
                        '<mp-common-profile class="custom_select_card mp_profile_iframe" '
                        'data-pluginname="mp-common-profile" '
                        f'data-nickname="{_xml_attr(nickname)}" data-from="0" '
                        f'data-headimg="{_xml_attr(headimg)}" '
                        f'data-signature="{_xml_attr(signature)}" '
                        f'data-id="{_xml_attr(pid)}" '
                        f'data-service_type="{_xml_attr(service_type)}">'
                        "</mp-common-profile>"
                    )
                # 旧形态：仅 alias（gh_ 开头）
                alias = (p.get("alias") or "").strip()
                if alias:
                    return (
                        '<mpprofile class="js_uneditable custom_select_card mp_profile_iframe" '
                        f'data-pluginname="mpprofile" data-alias="{_xml_attr(alias)}" '
                        'data-from="0"></mpprofile>'
                    )
            return f"<!-- 未找到公众号名片配置: {embed_name} -->"

        if embed_type == "miniprogram":
            m = miniprograms.get(norm_name)
            if m:
                appid = (m.get("appid") or "").strip()
                path = (m.get("path") or "pages/index/index").strip()
                title = (m.get("title") or embed_name).strip()
                applink = (m.get("applink") or "").strip()
                # 文字链：默认 title 同时作链接文案与 data-miniprogram-nickname；可另设 link_text / miniprogram_nickname
                link_text = (m.get("link_text") or title or embed_name).strip()
                mp_nick = (
                    m.get("miniprogram_nickname")
                    or m.get("nickname")
                    or title
                    or link_text
                ).strip()
                servicetype = str(m.get("servicetype") or m.get("service_type") or "0").strip()
                # 新形态：文字跳转小程序（与编辑器拉取一致），需 applink
                if applink:
                    # 不外包 <p>：{embed:...} 所在行会被 _md_to_html 包成一段
                    return (
                        f'<span leaf=""><a class="weapp_text_link js_weapp_entry" '
                        f'style="font-size: 17px;" data-miniprogram-type="text" '
                        f'data-miniprogram-appid="{_xml_attr(appid)}" '
                        f'data-miniprogram-path="{_xml_attr(path)}" '
                        f'data-miniprogram-nickname="{_xml_attr(mp_nick)}" '
                        f'data-miniprogram-servicetype="{_xml_attr(servicetype)}" '
                        f'data-miniprogram-applink="{_xml_attr(applink)}">'
                        f"{html_mod.escape(link_text)}</a></span>"
                        '<span leaf=""><br /></span>'
                    )
                # 旧形态：mp-miniprogram 卡片
                image = (m.get("image") or "").strip()
                return (
                    f'<mp-miniprogram '
                    f'data-miniprogram-appid="{_xml_attr(appid)}" '
                    f'data-miniprogram-path="{_xml_attr(path)}" '
                    f'data-miniprogram-title="{_xml_attr(title)}" '
                    f'data-miniprogram-imageurl="{_xml_attr(image)}">'
                    f"</mp-miniprogram>"
                )
            return f"<!-- 未找到小程序配置: {embed_name} -->"

        if embed_type == "miniprogram_card":
            m = miniprogram_cards.get(norm_name)
            if m:
                return _render_mp_common_miniprogram_card(m, embed_name)
            return f"<!-- 未找到小程序卡片配置: {embed_name} -->"

        if embed_type == "link":
            manual = embeds.get("related_articles", {}).get("manual", [])
            for lnk in manual:
                if not isinstance(lnk, dict):
                    continue
                if _normalize_embed_name(lnk.get("name", "")) == norm_name:
                    return _render_related_link(lnk, embed_name)
            return f'<!-- 未找到链接配置: {embed_name} -->'

        return match.group(0)

    return re.sub(r'\{embed:(\w+):(.+?)\}', _replace_embed, html_text)


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
    """Markdown → 带 inline style 的 HTML。正文不包含文章标题（第一个 h1 跳过，由公众号后台单独填）。"""
    lines = md_text.strip().split("\n")
    html_parts = []
    in_list = None
    in_blockquote = False
    in_code_block = False
    code_block_lines = []
    paragraph_lines = []
    first_h1_skipped = False

    def _p_style():
        """段落样式：主题提供则直接用，否则用变量拼接。"""
        theme_p = styles.get("p", "")
        if theme_p:
            return theme_p
        return (
            f'margin:0 0 {styles["paragraph-spacing"]} 0; '
            f'font-size:{styles["font-size"]}; '
            f'line-height:{styles["line-height"]}; '
            f'color:{styles["text-color"]};'
        )

    def flush_paragraph():
        if paragraph_lines:
            text = " ".join(paragraph_lines)
            text = _inline_format(text, styles)
            html_parts.append(f'<p style="{_p_style()}">{text}</p>')
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

        # 围栏代码块（``` ... ```）
        if stripped.startswith("```"):
            if not in_code_block:
                flush_paragraph()
                close_list()
                close_blockquote()
                in_code_block = True
                code_block_lines = []
                continue
            else:
                pre_style = styles.get("pre", "") or (
                    "background:#f5f5f5; padding:16px; border-radius:4px; "
                    "font-size:13px; line-height:1.8; overflow-x:auto; color:#333;"
                )
                code_text = html_mod.escape("\n".join(code_block_lines))
                html_parts.append(
                    f'<pre style="{pre_style}"><code>{code_text}</code></pre>'
                )
                in_code_block = False
                code_block_lines = []
                continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            close_blockquote()
            continue

        # 单独成段：避免多个 {embed:...} 被 join 进同一段 <p>（微信 API 易报 invalid content）
        if re.fullmatch(r"\{embed:\w+:.+\}", stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            html_parts.append(f'<p style="{_p_style()}">{stripped}</p>')
            continue

        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            close_blockquote()
            level = len(heading_match.group(1))
            # 跳过第一个 h1（文章标题），公众号后台单独填写标题，正文不再重复
            if level == 1 and not first_h1_skipped:
                first_h1_skipped = True
                continue
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
            if ("封面" in alt) or alt.startswith("cover"):
                continue

            alt_escaped = html_mod.escape(alt)
            img_style = styles.get("img", "") or "max-width:100%; border-radius:4px;"
            html_parts.append(
                f'<p style="text-align:center; margin:1.5em 0;">'
                f'<img src="{src}" alt="{alt_escaped}" style="{img_style}" />'
                f'</p>'
            )
            if "：" in alt:
                caption = alt.split("：", 1)[1]
                fc_style = styles.get("figcaption", "") or (
                    f'text-align:center; font-size:14px; '
                    f'color:{styles["text-muted"]}; margin-top:-0.8em; margin-bottom:1.5em;'
                )
                html_parts.append(
                    f'<p style="{fc_style}">'
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
                ul_style = styles.get("ul", "") or f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
                html_parts.append(f'<ul style="{ul_style}">')
                in_list = "ul"
            raw_text = re.sub(r'^[-*]\s+', '', stripped).strip()
            if not raw_text:
                continue
            text = _inline_format(raw_text, styles)
            li_style = styles.get("li", "") or (
                f'margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};'
            )
            html_parts.append(f'<li style="{li_style}">{text}</li>')
            continue

        ol_match = re.match(r'^\d+\.\s+', stripped)
        if ol_match:
            flush_paragraph()
            if in_list != "ol":
                close_list()
                ol_style = styles.get("ol", "") or f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
                html_parts.append(f'<ol style="{ol_style}">')
                in_list = "ol"
            raw_text = re.sub(r'^\d+\.\s+', '', stripped).strip()
            if not raw_text:
                continue
            text = _inline_format(raw_text, styles)
            li_style = styles.get("li", "") or (
                f'margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};'
            )
            html_parts.append(f'<li style="{li_style}">{text}</li>')
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
    # strong
    strong_style = styles.get("strong", "")
    if not strong_style:
        strong_color = styles.get("strong-color", styles.get("primary-color", "#333"))
        strong_style = f"color:{strong_color}; font-weight:bold;"
    text = re.sub(
        r'\*\*(.+?)\*\*',
        rf'<strong style="{strong_style}">\1</strong>',
        text,
    )
    # em
    em_style = styles.get("em", "")
    if em_style:
        text = re.sub(r'\*(.+?)\*', rf'<em style="{em_style}">\1</em>', text)
    else:
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # inline code
    code_style = styles.get("code", "")
    if not code_style:
        code_style = (
            f'background:{styles.get("bg-light", "#F7F7F7")}; padding:2px 6px; '
            f'border-radius:3px; font-size:0.9em; color:{styles.get("primary-color", "#333")};'
        )
    text = re.sub(
        r'`(.+?)`',
        rf'<code style="{code_style}">\1</code>',
        text,
    )
    # link
    a_style = styles.get("a", "")
    if not a_style:
        a_style = f'color:{styles.get("link-color", "#576B95")}; text-decoration:none;'
    text = re.sub(
        r'\[(.+?)\]\((.+?)\)',
        rf'<a style="{a_style}" href="\2">\1</a>',
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
    parser.add_argument(
        "--theme",
        default=None,
        help="主题名；省略则用 config.yaml+本篇 YAML 合并后的 default_format_preset，再无则 default",
    )
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

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    draft_dir = input_path.parent
    fmt_ctx = _merge_format_context(draft_dir)

    if args.theme is None:
        preset = _coerce_single_preset("default_format_preset", fmt_ctx.get("default_format_preset"))
        theme_name = preset if preset else "default"
        if preset:
            _info(f"主题来自合并配置 default_format_preset: {theme_name}")
    else:
        theme_name = args.theme

    md_text = input_path.read_text(encoding="utf-8")

    if not args.no_preformat:
        md_text = _preformat_markdown(md_text)
        _info("Markdown 预格式化完成（中英文间距、引号、空行）")

    theme = _load_theme(theme_name)

    overrides = {}
    if args.color:
        overrides["primary-color"] = args.color
    if args.font_size:
        overrides["font-size"] = args.font_size

    _info(f"主题: {theme_name}")
    styles = _build_styles(theme, overrides)
    body_html = _md_to_html(md_text, styles)

    embeds = _resolve_embeds_config(draft_dir)
    if embeds:
        body_html = _resolve_embeds(body_html, embeds)
        _info("嵌入元素已替换（名片/小程序/小程序卡片/链接）")

    # 每篇专属文末：若同目录存在 closing.md，则将其转换为 HTML 并追加到文末
    closing_md_path = input_path.parent / "closing.md"
    if closing_md_path.exists():
        closing_md = closing_md_path.read_text(encoding="utf-8")
        # 不对 closing.md 进行预格式化，避免意外更改作者自定义的链接与排版
        closing_html = _md_to_html(closing_md, styles)
        # 以段落分隔以避免直接黏连
        body_html = f"{body_html}\n\n<div style=\"margin-top:1.5em\"></div>\n{closing_html}"
        _info(f"已追加文末区块: {closing_md_path}")

    full_html = _wrap_document(body_html, styles)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    _ok(f"已保存: {output_path}")


if __name__ == "__main__":
    main()
