#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

所有主题均为 YAML 文件，按优先级查找：
1. .aws-article/presets/formatting/<主题名>.yaml（用户自定义）
2. skill 内置 references/presets/themes/<主题名>.yaml

用法：
    python format.py <article.md>                      主题：仅读取本篇 article.yaml 的 default_format_preset（须为 YAML 列表），否则 default
    python format.py <article.md> --theme grace         显式指定主题（覆盖配置）
    python format.py <article.md> --theme my-brand      使用自定义主题
    python format.py <article.md> --color "#0F4C81"     覆盖主色
    python format.py <article.md> --font-size 16px
    python format.py --list-themes                       列出可用主题
    python format.py --export-theme default > my.yaml     导出主题 YAML（含默认变量/样式）作为自定义起点
    python format.py <article.md> --no-preformat         跳过中英文加空格 / 引号替换等预格式化
"""

from __future__ import annotations

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

# 版式组件：markdown 里用 :::name[参数] … ::: 调用，渲染成设计过的 HTML 结构。
# 为什么需要它：微信只认内联样式，没有伪元素，所以「标题前的角标」「引用块的大引号」
# 这类装饰没法靠 CSS 变出来，必须真的插元素。而主题只能给标签配样式，表达不了结构。
BUILTIN_COMPONENTS_DIR = SKILL_DIR / "references" / "components"
USER_COMPONENTS_DIR = Path(".aws-article/presets/components")
COMPONENT_SEARCH_DIRS = [USER_COMPONENTS_DIR, BUILTIN_COMPONENTS_DIR]

DEFAULT_VARIABLES = {
    "primary-color": "#0F4C81",
    # 下面四个由 primary-color 派生，见 _derive_palette；这里的值只是没主题时的兜底
    "primary-fill": "#0F4C81",
    "primary-ink": "#0F4C81",
    "bg-accent-soft": "#F7F9FB",
    "bg-accent-color": "#F0F4F8",
    "highlight-pen": "#C6D6E6",
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


def _export_theme(name: str) -> None:
    """导出主题为完整 YAML（合并默认变量与样式，{变量} 引用保持原样）；仅向 stdout 输出 YAML。"""
    path = _find_theme_file(name)
    if not path:
        available = ", ".join(t["name"] for t in _list_themes())
        _err(f"主题 '{name}' 不存在。可用主题：{available}")
    theme = _load_theme_file(path)
    data = {
        "name": theme.get("name", name),
        "description": theme.get("description", ""),
        "variables": {**DEFAULT_VARIABLES, **(theme.get("variables") or {})},
        "styles": {**DEFAULT_STYLES, **(theme.get("styles") or {})},
    }
    sys.stdout.write(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000))


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
    cfg_path = Path(".aws-article/config.yaml")
    if not cfg_path.is_file():
        # 静默跳过是最坏的失败方式：退出码 0、HTML 照出，只是名片/小程序等嵌入元素
        # 和主题设置全都没生效，肉眼要比对两份产物才看得出来。
        print(f"[WARN] 未在当前工作目录下找到 .aws-article/config.yaml（当前目录：{Path.cwd()}），"
              f"本次不套用全局配置（嵌入元素、图注等按默认处理）。"
              f"如非本意，请在仓库根下重跑。", file=sys.stderr)
    cfg = _safe_yaml_dict(cfg_path)
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


def _load_article_context(draft_dir: Path) -> dict:
    """仅加载本篇 article.yaml（用于本篇已选预设读取）。"""
    return _safe_yaml_dict(draft_dir / "article.yaml")


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

    # 整套配色由一个强调色派生。--color 换了强调色时，主题里写死的那几个派生色就过期了，
    # 必须一并重算——否则会出现「块底换了颜色、文字色还是旧的」这种半换不换的状态。
    pinned = set((theme.get("variables") or {}).keys())
    if overrides and overrides.get("primary-color"):
        pinned -= set(_DERIVED_COLORS)
    variables.update({k: v for k, v in _derive_palette(variables["primary-color"]).items()
                      if k not in pinned})

    resolved = {}
    for key, val in variables.items():
        resolved[key] = _resolve_vars(str(val), variables)

    styles = {**DEFAULT_STYLES}
    styles.update(theme.get("styles", {}))
    for key, val in styles.items():
        resolved[key] = _resolve_vars(str(val), resolved)

    # 主题没写 variables 时（网站导出的主题都是这样），从它自己的样式里反推组件用色，
    # 否则版式组件会全部落到 DEFAULT_VARIABLES 的兜底蓝，16 套主题的小标题一个色。
    # 放在 styles 解析之后：反推要读已经解析好的 strong / a / blockquote。
    if not overrides or not overrides.get("primary-color"):
        inferred = _infer_theme_vars(theme, resolved)
        if inferred.get("primary-color") and inferred["primary-color"] != resolved["primary-color"]:
            # 反推出了别的强调色，派生色要跟着重算，否则文字色仍停在兜底蓝上。
            # 但反推自己给出的值优先：那是主题作者实际写在 styles 里的颜色（比如引用块的
            # 底色），比我们按比例算出来的更能代表这套主题的本意。
            for k, v in _derive_palette(inferred["primary-color"]).items():
                if k not in pinned and k not in inferred:
                    inferred[k] = v
        resolved.update(inferred)

    # --font-size 覆盖：主题 p / li 若硬编码了字号（未用 {font-size} 变量），也一并替换
    if overrides and overrides.get("font-size"):
        fs = str(overrides["font-size"])
        for key in ("p", "li"):
            if resolved.get(key):
                resolved[key] = re.sub(r"font-size:\s*[^;]+;?", f"font-size:{fs};", resolved[key])

    return resolved


# ── Markdown 预格式化 ─────────────────────────────────────────

# 预格式化时需原样保留的片段（按顺序匹配；先匹配到的片段内部不再被后续规则触碰）
_PREFORMAT_PROTECT_PATTERNS = (
    re.compile(r"^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$", re.M | re.S),  # 围栏代码块
    re.compile(r"`[^`\n]+`"),                                            # 行内代码
    re.compile(r"\]\([^)\s]+(?:\s+\"[^\"]*\")?\)"),                       # 链接 / 图片目标 ](url)
    re.compile(r"\{embed:\w+:[^}\n]+\}"),                                 # 嵌入占位
    re.compile(r"<[A-Za-z/][^>\n]*>"),                                    # 原生 HTML 标签
    re.compile(r"https?://[^\s<>()\"']+"),                                # 裸 URL
)
_PREFORMAT_TOKEN_RE = re.compile("\x00(\\d+)\x00")


def _preformat_markdown(text: str) -> str:
    """预格式化 Markdown：修复中文排版常见问题。

    围栏代码块、行内代码、链接/图片目标、{embed:...}、原生 HTML 标签与裸 URL 会被原样保留，
    避免中英文加空格或引号替换改坏图片路径与示例代码。
    """
    protected: list[str] = []

    def _stash(m: re.Match) -> str:
        protected.append(m.group(0))
        return f"\x00{len(protected) - 1}\x00"

    for pattern in _PREFORMAT_PROTECT_PATTERNS:
        text = pattern.sub(_stash, text)

    # 中英文之间加空格
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fff])", r"\1 \2", text)

    # 中文与数字之间加空格
    text = re.sub(r"([\u4e00-\u9fff])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([\u4e00-\u9fff])", r"\1 \2", text)

    # ASCII 引号 → 中文引号（仅同一行内配对，避免跨段误配）
    text = re.sub(r'"([^"\n]*?)"', r"「\1」", text)

    # 连续多个空行 → 最多两个
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 修复加粗标记中的空格问题（清理 **..** 配对内侧空格，不动外侧）
    text = re.sub(r"\*\* *(.+?) *\*\*", r"**\1**", text)

    # 还原受保护片段
    text = _PREFORMAT_TOKEN_RE.sub(lambda m: protected[int(m.group(1))], text)

    return text


# ── Markdown → HTML ──────────────────────────────────────────

# config.yaml 的 caption_style。原先这个字段谁也没读，图注是「alt 里有全角冒号就切一刀」
# 写死的行为——用户在配置台选「无图注」照样出图注，选「关键图有」也毫无区别。
CAPTION_ALWAYS = "有图注"
CAPTION_NEVER = "无图注"
CAPTION_KEY_ONLY = "关键图有"

# 「关键图有」按图位判定：信息位的图是拿来解释内容的，图注补充说明有意义；
# 节奏位（概念隐喻/场景还原/金句卡片）本来就不承载信息，图注只是重复一遍。
# 形态名就写在 alt 的全角冒号之前（`![流程步骤：…]`），不必另存元数据。
INFO_SLOT_FORMS = frozenset({"流程步骤", "结构分层", "数据图表", "对比两栏", "清单要点"})


def _want_caption(alt: str, caption_style: str) -> bool:
    """按 caption_style 决定这张图要不要图注。alt 形如 `形态：给生图模型的画面指令`。

    调用点已经保证了「作者显式写了 title」才会进来，这里只做 caption_style 的过滤。

    早先这里有一条 `"：" not in alt → False`：那是图注还从 alt 切出来的年代留下的，
    当时没有冒号确实无图注可出。图注改成由 markdown 的 title 参数显式指定之后，这条
    就变成了「作者明明写了图注，却因为 alt 里没冒号被静默丢掉」——两处的判据对不上。
    """
    style = (caption_style or "").strip() or CAPTION_ALWAYS
    if style == CAPTION_NEVER:
        return False
    if style == CAPTION_KEY_ONLY:
        # 「关键图有」是用户主动收窄的设置。认不出图位就说明它不是已知的信息位，
        # 这时候出图注等于替用户放宽他刚设的限制——宁可不出。
        return alt.split("：", 1)[0].strip() in INFO_SLOT_FORMS if "：" in alt else False
    return True               # 有图注，以及无法识别的取值都按默认走


def _load_components(skeleton: str = "") -> dict:
    """加载版式组件；同名时后加载的覆盖先加载的。

    查找顺序：内置基础版 → 内置的骨架专属版 → 用户自定义。

    为什么要有「骨架专属版」：组件此前是全局资产，一个 steps.yaml 全部主题共用，
    只有颜色不同。而导语、金句卡、步骤、数字块这些恰恰是一篇文章里视觉重量最集中
    的地方——它们全都一样，主题之间就只剩色相的差别。骨架要成立，装饰语言必须能
    按骨架整套替换，不只是换几个数字。
    """
    dirs = [BUILTIN_COMPONENTS_DIR]
    if skeleton:
        dirs.append(BUILTIN_COMPONENTS_DIR / skeleton)
        dirs.append(USER_COMPONENTS_DIR / skeleton)
    dirs.append(USER_COMPONENTS_DIR)
    out: dict[str, dict] = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")):
            spec = _safe_yaml_dict(f)
            name = str(spec.get("name") or f.stem).strip()
            if name and spec.get("template"):
                out[name] = spec
    return out


# 组件模板里可用的占位符 → 从当前主题取值，保证组件与主题不脱节
_COMPONENT_VARS = (
    # primary-ink 必须排在 primary-color 前面：替换是逐个字符串 replace，
    # "primary-color" 不是 "primary-ink" 的前缀所以其实不冲突，但把它放前面能
    # 少一次「以后新增 primary-color-xxx 时被前缀吃掉」的隐患。
    "primary-ink", "primary-fill", "primary-color", "bg-accent-soft",
    "bg-accent-color", "highlight-pen",
    "text-color", "text-light",
    "text-muted", "border-color", "link-color", "font-size", "line-height",
)


def _relative_luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(h[0:2]) + 0.7152 * ch(h[2:4]) + 0.0722 * ch(h[4:6])


def _contrast_on_white(hexcolor: str) -> float:
    return 1.05 / (_relative_luminance(hexcolor) + 0.05)


def _darken_to_readable(hexcolor: str, target: float = 4.5) -> str:
    """把强调色压深到在白底上够读，色相不变。

    为什么需要两个强调色：同一个颜色既要当大面积块底（h2 的实心色块、steps 的编号圈），
    又要当正文级文字（h3、链接、行内代码），而这两件事对明度的要求是反的。薄荷绿
    #17A398 压白字的对比是 3.12——当块底够用，当 17px 的文字就低于可读线了。
    所以面积用品牌色本身，文字用这里压深的版本。四套（暖橙、马卡龙粉、薄荷绿、莫兰迪）
    实测都卡在 3.1~3.9，不分开就只能改色相，那等于把主题的身份也改了。
    """
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) < 6:
        return hexcolor
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    for _ in range(40):
        if _contrast_on_white("#%02X%02X%02X" % (r, g, b)) >= target:
            break
        r, g, b = (max(0, round(c * 0.94)) for c in (r, g, b))
    return "#%02X%02X%02X" % (r, g, b)


# 由强调色派生、不需要用户填的颜色。用户换强调色时它们必须一起重算。
_DERIVED_COLORS = ("primary-fill", "primary-ink", "bg-accent-soft",
                   "bg-accent-color", "highlight-pen")


def _normalize_hex(value: str) -> str | None:
    """`#1a6db5` / `1A6DB5` / `#abc` 都收下，统一成 `#RRGGBB`；认不出返回 None。"""
    h = str(value or "").strip().lstrip("#")
    if len(h) == 3 and all(c in "0123456789abcdefABCDEF" for c in h):
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        return None
    return "#" + h.upper()


def _mix_to_white(hexcolor: str, ratio: float) -> str:
    r, g, b = (int(hexcolor.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: round(c + (255 - c) * ratio)
    return "#%02X%02X%02X" % (f(r), f(g), f(b))


def _contrast_with_white(hexcolor: str) -> float:
    """白字压在这个颜色上的对比度。"""
    return 1.05 / (_relative_luminance(hexcolor) + 0.05)


def _derive_palette(accent: str) -> dict:
    """从用户选的一个强调色派生出整套用色。

    强调色有三种角色，对明度的要求各不相同，混成一个变量必然出事：

        primary-color  纯装饰面积（色条、底线、竖条）——上面没有文字，用户的原色，不动
        primary-fill   白字压在上面的实心块——白字对比须 ≥3.0
        primary-ink    文字压白底（h3、链接、行内代码）——须 ≥4.5

    实测：明黄 #FFD400 当块底时白字对比只有 1.36，糊得看不见；而它当一根色条完全没问题。

    为什么只让用户选一个：整套配色本来就只有一个自由度。此前 16 套主题里有 14 套，
    所有用色都能从强调色算出来——把一个连续参数固化成 16 个离散选项，本身就是设计错误。

    护栏只管可读性，不管审美——审美是用户的品牌，不该被我们改：

    - **面积色**：白字要压在它上面（h2 色块、导语出血块），对比度不足 3.0 就压深。
      太浅的品牌色（明黄、浅粉）直接当块底会让白字糊掉。
    - **文字色**：h3、链接、行内代码是正文级文字，压白底要够 4.5。同一个颜色没法既当
      大面积块底又当正文级文字——这两件事对明度的要求是反的。
    - 浅底与高亮笔按固定比例混白，不需要判断。
    """
    accent = _normalize_hex(accent) or DEFAULT_VARIABLES["primary-color"]
    # 白字要压上去的实心块才需要压深。纯装饰的色条、底线上面没有文字，
    # 压深它等于平白改掉用户的品牌色——多数品牌色（蓝红紫绿）本来就够，两者相同。
    fill = accent if _contrast_with_white(accent) >= 3.0 else _darken_to_readable(accent, target=3.0)
    return {
        "primary-fill": fill,                         # 白字压在上面的实心块
        "primary-ink": _darken_to_readable(accent),   # 文字压白底：h3、链接、行内代码
        # 浅底分两档：大面积底（导语、数字块这种整块的）要比小卡片更淡，
        # 否则一块 400px 高的浅色域会跟正文抢注意力。只有一档时两者只能共用一个值。
        "bg-accent-soft": _mix_to_white(accent, 0.96),    # 大面积底
        "bg-accent-color": _mix_to_white(accent, 0.92),   # 卡片底
        "highlight-pen": _mix_to_white(accent, 0.74),     # strong 的高亮笔
    }


def _is_accent(hexcolor: str) -> bool:
    """这个颜色能不能当强调色用——即它是不是「有颜色」。

    反推强调色时不能见 color: 就取。有些主题的 strong 是纯黑加粗（黑白骨架 + 单一
    强调色的写法里很常见），取到黑，组件就会整块变黑，强调色反而丢了。
    判据是饱和度：最大与最小通道差 24 以上才算有颜色；同时排除太浅的（当不了前景）。
    """
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) < 6:
        return False
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (max(r, g, b) - min(r, g, b)) >= 24 and (r + g + b) / 3 <= 210


def _infer_theme_vars(theme: dict, styles: dict) -> dict:
    """主题没写 variables 时，从它自己的样式里反推组件要用的颜色。

    网站导出的主题（`.aws` 包里的 formatting/*.yaml）只有字面色的 styles，**没有
    variables 块**——导出格式就不带变量表。而组件模板用 {primary-color} 取色，
    结果 16 套网站主题的组件全部落到 DEFAULT_VARIABLES 的兜底蓝 #0F4C81，
    「所有小标题都是蓝的」。

    反推顺序按「最能代表这套主题强调色」排：strong 是行内强调、a 是链接、h3 次之。
    取每条样式里第一个 color: 值。
    """
    if (theme.get("variables") or {}).get("primary-color"):
        return {}
    out = {}
    for key in ("strong", "em", "a", "h3", "h2", "code"):
        m = re.search(r"(?<!-)\bcolor\s*:\s*(#[0-9A-Fa-f]{3,8})", str(styles.get(key) or ""))
        if m and _is_accent(m.group(1)):
            out["primary-color"] = m.group(1)
            break
    # 浅底色：从 blockquote / highlight 的 background 里取
    for key in ("blockquote", "highlight", "code"):
        m = re.search(r"background(?:-color)?\s*:\s*(#[0-9A-Fa-f]{3,8})", str(styles.get(key) or ""))
        if m:
            out["bg-accent-color"] = m.group(1)
            break
    return out


def _sub_theme_vars(html: str, styles: dict) -> str:
    """把模板里的 {primary-color} 等占位符换成当前主题的值。

    行模板（row_template）必须和外层模板一样走这一步——行是先渲染再塞进 {content} 的，
    只替换外层会让行里的占位符原样漏到产出里。
    """
    for var in _COMPONENT_VARS:
        html = html.replace("{" + var + "}", str(styles.get(var, "")))
    return html


def _cjk_numeral(n: int) -> str:
    """1 → 一，11 → 十一。给 `{nz}` 用。

    只做 1~99：组件里的行数超过十几条本身就该拆，没必要为三位数写通用算法。
    超出范围退回阿拉伯数字，宁可难看也不要打出「一百二十三」把一格撑爆。
    """
    if not 1 <= n <= 99:
        return str(n)
    d = "〇一二三四五六七八九"
    if n < 10:
        return d[n]
    tens, ones = divmod(n, 10)
    return ("十" if tens == 1 else d[tens] + "十") + (d[ones] if ones else "")


def _render_component(spec: dict, arg: str, body_lines: list[str], styles: dict) -> str:
    """把一个 :::块 渲染成 HTML。arg 是方括号里的参数，body_lines 是块内正文。"""
    body_kind = str(spec.get("body") or "free").strip()
    if body_kind == "rows":
        # 每行一条，按分隔符切列，逐行套 row_template。列不足时补空串，
        # 多余的列丢弃——宁可少显示，也不要因为作者多打一个分隔符就整块渲染失败。
        delim = str(spec.get("row_delimiter") or "|")
        row_tpl = _sub_theme_vars(str(spec.get("row_template") or ""), styles)
        ncol = int(spec.get("row_columns") or 0)
        row_map = spec.get("row_map") or {}
        row_map_default = spec.get("row_map_default") or {}
        rows_html = []
        idx = 0
        for ln in body_lines:
            if not ln.strip():
                continue
            idx += 1
            cells = [c.strip() for c in ln.split(delim)]
            # 枚举列漏写的兜底。checklist 的第一列是状态（done/todo/warn），作者很容易
            # 直接写事项忘了状态——那样事项会被塞进 18px 宽的状态格，一个字一行整块塌掉。
            # 判据是「这一列有 row_map 却填了表外的值，且总列数不够」：几乎只可能是漏写，
            # 于是右移一格、该列取默认符号。宁可猜一次，也不要给用户一坨废墟。
            for i, dft in row_map_default.items():
                pos = int(str(i).lstrip("c") or 0)
                if (ncol and len(cells) < ncol and pos < len(cells)
                        and cells[pos] not in (row_map.get(str(i)) or {})):
                    cells.insert(pos, str(dft))
            if ncol:
                cells = (cells + [""] * ncol)[:ncol]
            row = (row_tpl.replace("{n}", str(idx))
                          .replace("{n2}", "%02d" % idx)
                          .replace("{nz}", _cjk_numeral(idx)))
            for i, cell in enumerate(cells):
                # row_map：把某一列的取值映射成符号/短语（如 done → ✓）。
                # 没有它的话，枚举列只能把 "done" 原样打进去——18px 宽的状态列会截成 "don"。
                mapped = (row_map.get("c%d" % i) or {}).get(cell)
                # 映射值也要走变量替换——枚举列的符号常常是内联 SVG 图标，
                # 里面的描边色要跟着主题走；不替换的话图标会带着 {primary-color} 字面量。
                row = row.replace("{c%d}" % i,
                                  _sub_theme_vars(str(mapped), styles) if mapped is not None
                                  else _inline_format(cell, styles))
            row = re.sub(r"\{c\d+\}", "", row)      # 未用到的列位清掉
            rows_html.append(row.strip())
        content = "\n".join(rows_html)
    elif body_kind == "single":
        content = _inline_format(" ".join(x.strip() for x in body_lines if x.strip()), styles)
    else:                                           # free：空行分段
        paras, buf = [], []
        for ln in body_lines:
            if ln.strip():
                buf.append(ln.strip())
            elif buf:
                paras.append(" ".join(buf)); buf = []
        if buf:
            paras.append(" ".join(buf))
        # 多段时用真正的段落间距，不能只 <br />——那样两段挤在一起没有气口。
        # 单段时不包 <section>，免得给只有一句话的组件平白多一层。
        if len(paras) > 1:
            content = "".join(
                f'<section style="margin:0 0 {"0.9em" if i < len(paras) - 1 else "0"};">'
                f'{_inline_format(x, styles)}</section>'
                for i, x in enumerate(paras))
        else:
            content = "".join(_inline_format(x, styles) for x in paras)

    html = _sub_theme_vars(str(spec["template"]), styles)
    html = html.replace("{arg}", html_mod.escape(arg))
    # {arg0} {arg1} …：把方括号参数切开，供「左标题 / 右标题」这类双栏组件用。
    # 斜杠和竖线都认：竖线是行分隔符，作者在参数里顺手也写竖线是常事，
    # 只认斜杠的话右栏标题会整个空掉——而空标题在并排结构里格外显眼。
    parts = [x.strip() for x in re.split(r"\s*[/|]\s*", arg)]
    for i in range(max(len(parts), 4)):
        html = html.replace("{arg%d}" % i, html_mod.escape(parts[i]) if i < len(parts) else "")
    html = html.replace("{content}", content)
    return html.strip()


def _md_to_html(md_text: str, styles: dict, skip_first_h1: bool = True,
                caption_style: str = CAPTION_ALWAYS,
                components: dict | None = None) -> str:
    """Markdown → 带 inline style 的 HTML。

    skip_first_h1=True 时正文不包含文章标题（第一个 h1 跳过，由公众号后台单独填）；
    closing.md 等附加片段应传 False，否则其首个 h1 会被误当作文章标题丢弃。
    """
    lines = md_text.strip().split("\n")
    html_parts = []
    in_list = None
    list_stack = []     # 嵌套列表标签栈：["ul", "ol", ...]
    list_depth = -1     # 当前嵌套深度（-1 = 不在列表中）
    in_blockquote = False
    in_code_block = False
    code_block_lines = []
    paragraph_lines = []
    first_h1_skipped = not skip_first_h1

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
        nonlocal in_list, list_depth
        while list_stack:
            html_parts.append(f"</{list_stack.pop()}>")
        list_depth = -1
        in_list = None

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html_parts.append("</blockquote>")
            in_blockquote = False

    for line_idx, line in enumerate(lines):
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
        # 版式组件：:::name[参数] … :::
        directive = re.match(r'^:::([A-Za-z0-9_-]+)(?:\[(.*)\])?\s*$', stripped)
        if directive and components:
            name, arg = directive.group(1), (directive.group(2) or "")
            spec = components.get(name)
            end = None
            for look in range(line_idx + 1, len(lines)):
                if lines[look].strip() == ":::":
                    end = look
                    break
            # highlight 是主题里定义的样式键，不是组件文件。16 套主题全都给它写了样式、
            # 门户预览也一直在渲染它，但此前**没有任何语法能产出它**——预览里那个提示框
            # 真实文章根本做不出来，和当初 formatDecorations 是同一类问题：预览承诺了
            # 交付不了的东西。这里给它接上 :::highlight（别名 :::note），沿用主题样式。
            # 真有骨架想给它做结构，放一个同名组件文件即可覆盖这条兜底。
            if not spec and name in ("highlight", "note") and end is not None:
                flush_paragraph()
                close_list()
                close_blockquote()
                body = [x.strip() for x in lines[line_idx + 1:end] if x.strip()]
                inner = "".join(
                    f'<section style="margin:0 0 {"0.8em" if i < len(body) - 1 else "0"};">'
                    f'{_inline_format(x, styles)}</section>'
                    for i, x in enumerate(body)) if len(body) > 1 else \
                    "".join(_inline_format(x, styles) for x in body)
                hl = styles.get("highlight") or styles.get("blockquote", "")
                html_parts.append(f'<section style="{hl}">{inner}</section>')
                for skip_i in range(line_idx + 1, end + 1):
                    lines[skip_i] = ""
                continue
            if spec and end is not None:
                flush_paragraph()
                close_list()
                close_blockquote()
                body = lines[line_idx + 1:end]
                html_parts.append(_render_component(spec, arg, body, styles))
                for skip_i in range(line_idx + 1, end + 1):
                    lines[skip_i] = ""
                continue
            # 组件不存在或没有闭合，按原文走，别把内容吞掉
            if not spec:
                print(f"[WARN] 未知版式组件 :::{name}，按普通文本输出。"
                      f"可用组件：{', '.join(sorted(components)) or '（无）'}", file=sys.stderr)
            elif end is None:
                print(f"[WARN] 组件 :::{name} 缺少结尾的 :::，按普通文本输出。", file=sys.stderr)

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

        # Markdown 表格
        if re.match(r'^\|.+\|$', stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            # 收集连续的表格行
            table_lines = [stripped]
            # 向前看后续行（通过索引）
            cur_idx = line_idx
            lookahead = cur_idx + 1
            while lookahead < len(lines):
                next_s = lines[lookahead].strip()
                if re.match(r'^\|.+\|$', next_s):
                    table_lines.append(next_s)
                    lookahead += 1
                else:
                    break
            # 跳过已消费的行（通过替换为空行，后续循环会跳过）
            for skip_i in range(cur_idx + 1, lookahead):
                lines[skip_i] = ""
            # 解析表格
            tbl_style = styles.get("table", "") or "width:100%; border-collapse:collapse; margin:1em 0; font-size:14px;"
            th_style = styles.get("th", "") or "background:#f5f5f5; padding:8px 14px; text-align:center; font-weight:bold;"
            td_style = styles.get("td", "") or "padding:8px 14px; border:1px solid #EEE; text-align:center;"
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                rows.append(cells)
            # 过滤分隔行（|---|---|）
            data_rows = [r for r in rows if not all(re.match(r'^:?-+:?$', c.strip()) for c in r)]
            if data_rows:
                table_html = f'<table style="{tbl_style}">'
                for ri, row in enumerate(data_rows):
                    table_html += "<tr>"
                    for cell in row:
                        tag = "th" if ri == 0 else "td"
                        st = th_style if ri == 0 else td_style
                        cell_text = _inline_format(cell, styles)
                        table_html += f'<{tag} style="{st}">{cell_text}</{tag}>'
                    table_html += "</tr>"
                table_html += "</table>"
                html_parts.append(table_html)
            continue

        # 第三个分组是 markdown 原生的 title 参数，用来放图注：
        #   ![信息图：画面指令给模型看](imgs/x.png "图注给读者看")
        img_match = re.match(r'^!\[(.*?)\]\(\s*(\S+?)(?:\s+["\u201c\u2018\'](.*?)["\u201d\u2019\'])?\s*\)$', stripped)
        if img_match:
            flush_paragraph()
            alt = img_match.group(1)
            src = img_match.group(2)
            caption_text = (img_match.group(3) or "").strip()

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
            # 图注只用显式写的 title 参数。alt 里冒号后那段是**给生图模型的画面指令**
            # （「开发者站在巨型 99.9 分数牌前，视线越过分数望向……」），拿它当图注等于
            # 把读者眼睛已经看见的东西复述一遍，零信息；图没生成出来时更会同一句话出现
            # 两次（一次破图 alt、一次图注）。没写 title 就不出图注——错的图注比没有更糟。
            if caption_text and _want_caption(alt, caption_style):
                caption = caption_text
                fc_style = styles.get("figcaption", "") or (
                    f'text-align:center; font-size:14px; '
                    f'color:{styles["text-muted"]}; margin-top:-0.8em; margin-bottom:1.5em;'
                )
                html_parts.append(
                    f'<p style="{fc_style}">'
                    f'{html_mod.escape(caption)}</p>'
                )
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{styles.get("blockquote", "")}">')
                in_blockquote = True
            quote_text = stripped[1:].strip()
            if not quote_text:
                # 引用块内的空行（单独一个 >）：保持引用块打开
                continue
            text = _inline_format(quote_text, styles)
            html_parts.append(
                f'<p style="margin:0.3em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</p>'
            )
            continue
        elif in_blockquote:
            close_blockquote()

        # 列表项检测（支持嵌套：通过缩进层级判断）
        ul_match = re.match(r'^( *)[-*]\s+', line)
        ol_match = re.match(r'^( *)\d+\.\s+', line)
        if ul_match or ol_match:
            flush_paragraph()
            close_blockquote()
            indent = len((ul_match or ol_match).group(1))
            # 缩进层级：每 2 个空格（或 1 个 tab）为一级
            level = indent // 2
            # 缩进跳级（如直接 4 空格）时只加深一层，避免产生空的嵌套容器
            if level > list_depth + 1:
                level = list_depth + 1
            list_type = "ul" if ul_match else "ol"

            ul_style = styles.get("ul", "") or f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
            ol_style = styles.get("ol", "") or f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
            li_style = styles.get("li", "") or (
                f'margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};'
            )

            # 需要更深的嵌套
            while level > list_depth:
                tag = list_type
                st = ul_style if tag == "ul" else ol_style
                # 子列表不需要外边距
                if list_depth >= 0:
                    st = re.sub(r'margin:[^;]+;?', '', st).strip()
                    if not st:
                        st = f'padding-left:1.5em; color:{styles["text-color"]};'
                html_parts.append(f'<{tag} style="{st}">')
                list_stack.append(tag)
                list_depth += 1

            # 需要回退到更浅的层级
            while level < list_depth:
                if list_stack:
                    html_parts.append(f'</{list_stack.pop()}>')
                list_depth -= 1

            # 同层级但列表类型变了
            if list_stack and list_stack[-1] != list_type:
                html_parts.append(f'</{list_stack.pop()}>')
                st = ul_style if list_type == "ul" else ol_style
                html_parts.append(f'<{list_type} style="{st}">')
                list_stack.append(list_type)

            # 第一层还没开始
            if not list_stack:
                st = ul_style if list_type == "ul" else ol_style
                html_parts.append(f'<{list_type} style="{st}">')
                list_stack.append(list_type)
                list_depth = 0

            if ul_match:
                raw_text = re.sub(r'^[-*]\s+', '', stripped).strip()
            else:
                raw_text = re.sub(r'^\d+\.\s+', '', stripped).strip()
            if not raw_text:
                continue
            text = _inline_format(raw_text, styles)
            html_parts.append(f'<li style="{li_style}">{text}</li>')
            in_list = list_type
            continue

        close_list()
        close_blockquote()
        paragraph_lines.append(stripped)

    flush_paragraph()
    close_list()
    close_blockquote()

    return "".join(html_parts)


def _inline_format(text: str, styles: dict) -> str:
    """行内格式：加粗、斜体、删除线、行内代码、链接。

    行内代码内容做 HTML 转义，且不参与加粗/斜体/链接等替换。
    """
    code_style = styles.get("code", "")
    if not code_style:
        code_style = (
            f'background:{styles.get("bg-light", "#F7F7F7")}; padding:2px 6px; '
            f'border-radius:3px; font-size:0.9em; color:{styles.get("primary-color", "#333")};'
        )
    code_spans: list[str] = []

    def _stash_code(m: re.Match) -> str:
        code_spans.append(
            f'<code style="{code_style}">{html_mod.escape(m.group(1))}</code>'
        )
        return f"\x00C{len(code_spans) - 1}\x00"

    text = re.sub(r'`([^`\n]+)`', _stash_code, text)

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
    # strikethrough ~~text~~
    del_style = styles.get("del", "") or "text-decoration:line-through; color:#999;"
    text = re.sub(r'~~(.+?)~~', rf'<del style="{del_style}">\1</del>', text)
    # link（排除行内图片语法 ![alt](src)）
    a_style = styles.get("a", "")
    if not a_style:
        a_style = f'color:{styles.get("link-color", "#576B95")}; text-decoration:none;'
    text = re.sub(
        r'(?<!!)\[(.+?)\]\((.+?)\)',
        rf'<a style="{a_style}" href="\2">\1</a>',
        text,
    )
    # 还原行内代码
    text = re.sub(r"\x00C(\d+)\x00", lambda m: code_spans[int(m.group(1))], text)
    return text


def _wrap_document(body_html: str, styles: dict) -> str:
    """包装为 HTML section。"""
    return (
        f'<section style="'
        f'font-family:{styles.get("font-family", "sans-serif")}; '
        f'font-size:{styles["font-size"]}; '
        f'line-height:{styles["line-height"]}; '
        f'color:{styles["text-color"]}; '
        # 行长（左右留白）必须由容器统一控制。此前是在 p 上打 padding:0 12px，
        # 标题、引用、表格都不跟随，于是标题比正文宽出 12px——一条一直没被发现的对齐 bug。
        f'padding:16px {styles.get("page-padding", "16px")}; text-align:left;'
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
        help="主题名；省略则仅读取本篇 article.yaml 的 default_format_preset，再无则 default",
    )
    parser.add_argument("--color", help="覆盖主色（如 #0F4C81）")
    parser.add_argument("--font-size", help="覆盖字号（如 16px）")
    parser.add_argument("-o", "--output", help="输出路径（默认同名 .html）")
    parser.add_argument("--no-preformat", action="store_true", help="跳过 Markdown 预格式化")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")
    parser.add_argument(
        "--export-theme",
        metavar="主题名",
        help="以 YAML 导出主题（合并默认变量与样式），可重定向到 .aws-article/presets/formatting/<名>.yaml 后修改",
    )

    args = parser.parse_args()

    if args.list_themes:
        print("可用主题：")
        for t in _list_themes():
            label = f" ({t['label']})" if t["label"] else ""
            desc = f" - {t['description']}" if t["description"] else ""
            print(f"  {t['name']}{label} [{t['source']}]{desc}")
        return

    if args.export_theme:
        _export_theme(args.export_theme)
        return

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    draft_dir = input_path.parent
    article_ctx = _load_article_context(draft_dir)

    if args.theme is None:
        preset = _coerce_single_preset("default_format_preset", article_ctx.get("default_format_preset"))
        theme_name = preset if preset else "default"
        if preset:
            _info(f"主题来自本篇 article.yaml 的 default_format_preset: {theme_name}")
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
    caption_style = str(_merge_format_context(draft_dir).get("caption_style") or CAPTION_ALWAYS)
    skeleton = str(theme.get("skeleton") or "").strip()
    components = _load_components(skeleton)
    if components:
        _info(f"已加载版式组件 {len(components)} 个"
              + (f"（骨架 {skeleton}）" if skeleton else "")
              + f": {', '.join(sorted(components))}")
    body_html = _md_to_html(md_text, styles, caption_style=caption_style, components=components)

    embeds = _resolve_embeds_config(draft_dir)
    if embeds:
        body_html = _resolve_embeds(body_html, embeds)
        _info("嵌入元素已替换（名片/小程序/小程序卡片/链接）")

    # 每篇专属文末：若同目录存在 closing.md，则将其转换为 HTML 并追加到文末
    closing_md_path = input_path.parent / "closing.md"
    if closing_md_path.exists():
        closing_md = closing_md_path.read_text(encoding="utf-8")
        # 不对 closing.md 进行预格式化，避免意外更改作者自定义的链接与排版
        closing_html = _md_to_html(closing_md, styles, skip_first_h1=False, caption_style=caption_style, components=components)
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
