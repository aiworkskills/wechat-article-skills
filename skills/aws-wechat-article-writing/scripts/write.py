#!/usr/bin/env python3
"""
公众号文章写作工具

调用第三方 LLM API（OpenAI 兼容格式）生成公众号文章。
支持 DeepSeek、OpenAI、Claude（兼容端点）、智谱、通义千问等。

写作模型（可选）：`writing_model`（base_url / model；provider / temperature / max_tokens 可选）写在
**`.aws-article/config.yaml`**，**`WRITING_MODEL_API_KEY`** 写在仓库根 **`aws.env`**。
未配置时 draft/rewrite/continue 以退出码 2 退出；可改用 prompt 子命令获取提示词，由 Agent 代写。

文风、预设名、`closing_block` 等：合并 **`.aws-article/config.yaml`（顶层，不含 writing_model/image_model）** 与本篇 **`article.yaml`**（本篇覆盖同名字段）。
结构/文末预设 **`.md`** 仍从 **`.aws-article/presets/`**（及用户目录）解析。
**`default_structure` / `default_closing_block`** 须为 **YAML 列表**：`[]` 表示未选默认；`[名]` 单元素即用；**多元素为候选池**，须先在本篇 **`article.yaml`** 同键写成**单元素列表** `[名]` 后再运行本脚本（勿使用字符串标量）。

退出码: 0=成功  1=硬错误  2=写作模型未配置(仅draft/rewrite/continue)

用法：
    python write.py draft <topic_card.md>              按选题卡片写初稿
    python write.py draft <topic_card.md> -o out.md    指定输出路径
    python write.py rewrite <article.md>               改写已有文章
    python write.py rewrite <article.md> --instruction "改成口语化"
    python write.py continue <article.md>              续写未完成的文章
    python write.py prompt draft <topic_card.md>       只输出提示词JSON(不调LLM)
    python write.py prompt rewrite <article.md> --instruction "..."
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


def _coerce_single_preset(field_label: str, raw) -> str:
    """
    将 YAML 中的预设字段规范为单一预设名（与 presets 下文件主名一致）。
    仅接受 list/tuple：`[]` → 空；`[x]` → x；多项 → 候选池须本篇收敛为单元素列表。
    """
    if raw is None:
        return ""
    if isinstance(raw, str):
        _err(
            f"{field_label} 须为 YAML 列表（例如 [] 或 [预设名]），勿使用字符串。"
            f" 当前为字符串，请改为列表形式。"
        )
    if isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw if x is not None and str(x).strip()]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        _err(
            f"{field_label} 含多个候选 {items!r}：请先按主题在本篇 article.yaml 中写入同名字段，"
            f"且值为仅含**一项**的列表（例如 [\"{items[0]}\"]），再运行 write.py。"
        )
    _err(f"{field_label} 须为 YAML 列表（[] 或 [预设名]），当前类型：{type(raw).__name__}")


# ── 配置读取 ─────────────────────────────────────────────────

_CONFIG_SKIP_TOP = frozenset({"writing_model", "image_model"})


def _resolve_env_path() -> Path:
    return Path("aws.env")


def _parse_dotenv(content: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


def _load_env_map() -> dict[str, str]:
    p = _resolve_env_path()
    if not p.is_file():
        return {}
    try:
        return _parse_dotenv(p.read_text(encoding="utf-8"))
    except OSError:
        return {}


def _load_config_yaml() -> dict | None:
    p = Path(".aws-article/config.yaml")
    if not p.is_file():
        return None
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except OSError as e:
        _err(f"无法读取 .aws-article/config.yaml：{e}")
    except yaml.YAMLError as e:
        _err(f".aws-article/config.yaml 解析失败：{e}")
    if data is None:
        return {}
    if not isinstance(data, dict):
        _err(".aws-article/config.yaml 须为 YAML 键值对象")
    return data


def _writing_context_from_config(cfg: dict) -> dict:
    """顶层键注入写作 prompt；排除 writing_model / image_model 避免嵌套污染。"""
    return {k: v for k, v in cfg.items() if k not in _CONFIG_SKIP_TOP}


def _model_config_from_config_and_env(cfg: dict | None, env: dict[str, str]) -> dict | None:
    if not isinstance(cfg, dict):
        return None
    wm = cfg.get("writing_model")
    if not isinstance(wm, dict):
        return None
    base_url = (wm.get("base_url") or "").strip()
    model = (wm.get("model") or "").strip()
    api_key = (env.get("WRITING_MODEL_API_KEY") or "").strip()
    if not base_url or not api_key or not model:
        return None
    temp_raw = wm.get("temperature", env.get("WRITING_MODEL_TEMPERATURE", "0.7"))
    max_raw = wm.get("max_tokens", env.get("WRITING_MODEL_MAX_TOKENS", "4000"))
    try:
        temperature = float(str(temp_raw).strip())
    except (ValueError, TypeError):
        temperature = 0.7
    try:
        max_tokens = int(str(max_raw).strip())
    except (ValueError, TypeError):
        max_tokens = 4000
    provider = (wm.get("provider") or "").strip().lower()
    return {
        "base_url": base_url.rstrip("/"),
        "model": model,
        "api_key": api_key,
        "provider": provider,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _aws_root() -> Path:
    """用于定位 presets：优先仓库 .aws-article，否则 ~/.aws-article。"""
    local = Path(".aws-article")
    if local.is_dir():
        return local.resolve()
    return (Path.home() / ".aws-article").resolve()


def _load_yaml_file(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as e:
        _err(f"无法读取 {path}：{e}")
    except yaml.YAMLError as e:
        _err(f"{path.name} 解析失败（{path}）：{e}")
    if not isinstance(data, dict):
        _err(f"{path.name} 须为 YAML 键值对象：{path}")
    return data


def _load_writing_context(draft_dir: Path) -> dict:
    """合并：.aws-article/config.yaml（顶层）→ 本篇 article.yaml。"""
    merged: dict = {}
    cfg = _load_config_yaml()
    if cfg:
        merged.update(_writing_context_from_config(cfg))
        _info("已加载仓库配置: .aws-article/config.yaml")

    art = (draft_dir / "article.yaml").resolve()
    if art.is_file():
        merged.update(_load_yaml_file(art))
        _info(f"已加载本篇: {art}")

    if not merged:
        _err(
            "未找到写作约束：请配置 .aws-article/config.yaml，"
            "或在本篇目录创建 article.yaml。"
        )
    return merged


def _resolve_model_config() -> dict | None:
    """Return model config dict, or None if not configured."""
    env_map = _load_env_map()
    cfg = _load_config_yaml()
    m = _model_config_from_config_and_env(cfg, env_map)
    if m:
        _info(f"写作模型已解析（API Key 等来自 {_resolve_env_path().name}）")
        return m
    return None


def _load_writing_spec() -> str:
    """加载用户自定义写作规范。"""
    candidates = [
        Path(".aws-article/writing-spec.md"),
        Path.home() / ".aws-article" / "writing-spec.md",
    ]
    for p in candidates:
        if p.exists():
            _info(f"加载写作规范: {p}")
            return p.read_text(encoding="utf-8")
    return ""


def _preset_dirs(cfg_base: Path) -> list[Path]:
    """与 format.py 一致：先项目 .aws-article，再用户 ~/.aws-article。"""
    home_aws = Path.home() / ".aws-article"
    return [cfg_base / "presets", home_aws / "presets"]


def _find_preset_file(preset_dirs: list[Path], subdir: str, name: str, exts: list[str]) -> Path | None:
    for root in preset_dirs:
        d = root / subdir
        if not d.exists():
            continue
        for ext in exts:
            p = d / f"{name}{ext}"
            if p.exists():
                return p
    return None


def _load_structure_template(screening: dict) -> str:
    """加载文章结构模板。合并上下文中 default_structure 非空时从 presets/structures 加载。"""
    default_name = _coerce_single_preset("default_structure", screening.get("default_structure"))
    if default_name:
        preset_dirs = _preset_dirs(_aws_root())
        found = _find_preset_file(preset_dirs, "structures", default_name, [".md"])
        if found:
            _info(f"加载结构预设: {found}")
            return found.read_text(encoding="utf-8")
        _err(
            f"default_structure 指向的预设文件不存在：{default_name}\n"
            "  请在 .aws-article/presets/structures/ 下创建对应 .md 文件，或运行 bash scripts/init-presets.sh 后复制示例并改名。"
        )
    script_dir = Path(__file__).parent.parent
    template_path = script_dir / "references" / "structure-template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def _load_closing_block(screening: dict) -> str:
    """文末区块：预设文件优先于 screening 内联 closing_block。"""
    default_name = _coerce_single_preset("default_closing_block", screening.get("default_closing_block"))
    if default_name:
        preset_dirs = _preset_dirs(_aws_root())
        found = _find_preset_file(preset_dirs, "closing-blocks", default_name, [".md"])
        if found:
            _info(f"加载文末区块预设: {found}")
            return found.read_text(encoding="utf-8")
    return (screening.get("closing_block") or "").strip()


# ── LLM 调用 ────────────────────────────────────────────────

def _detect_api_type(model_cfg: dict) -> str:
    """
    协议识别优先级：
    1) 显式 provider（若配置）
    2) 根据 base_url 路径特征自动识别（未命中则须显式 provider）
    """
    p = (model_cfg.get("provider") or "").strip().lower()
    allowed = {"openai", "volcengine", "qwen", "gemini"}
    if p:
        if p not in allowed:
            _err(f"未识别的 writing_model.provider: {p}，请使用 openai | volcengine | qwen | gemini")
            raise RuntimeError("invalid writing provider")
        return p

    base_url = (model_cfg.get("base_url") or "").strip().lower()

    # Gemini 自动识别：须为完整端点（:generateContent 在 URL 中，不在 model 字段）
    if "/v1beta/models/" in base_url and ":generatecontent" in base_url:
        return "gemini"
    if "dashscope.aliyuncs.com" in base_url and "/compatible-mode/v1/chat/completions" in base_url:
        return "qwen"
    if "volces.com" in base_url and "ark." in base_url and "/api/v3/chat/completions" in base_url:
        return "volcengine"
    if "/v1/chat/completions" in base_url:
        return "openai"

    _err(
        "无法从 writing_model.base_url / model 自动识别协议类型。"
        "请在 .aws-article/config.yaml 显式填写 writing_model.provider（openai | volcengine | qwen | gemini），"
        "或者填写可识别的完整 writing_model.base_url。"
    )
    raise RuntimeError("undetected writing provider")


def _post_json(url: str, body: dict, api_key: str, timeout: int = 300) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "aws-article-writer/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(f"API 调用失败 ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        _err(f"网络错误: {e.reason}")


def _call_openai_like(model_cfg: dict, system_prompt: str, user_prompt: str, api_type: str) -> str:
    """base_url：网关根（自动拼路径）或已含 .../chat/completions 的完整端点。"""
    b = model_cfg["base_url"].rstrip("/")
    bl = b.lower()
    if api_type == "volcengine":
        url = b if "/api/v3/chat/completions" in bl else f"{b}/api/v3/chat/completions"
    elif api_type == "qwen":
        url = (
            b
            if "/compatible-mode/v1/chat/completions" in bl
            else f"{b}/compatible-mode/v1/chat/completions"
        )
    elif api_type == "openai":
        url = b if "/v1/chat/completions" in bl else f"{b}/v1/chat/completions"
    else:
        _err(f"未支持的 OpenAI 兼容协议: {api_type}")
        raise RuntimeError("unsupported openai-like api type")

    body = {
        "model": model_cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": model_cfg["temperature"],
        "max_tokens": model_cfg["max_tokens"],
        "stream": False,
    }
    _info(f"调用模型: {model_cfg['model']} @ {url} ({api_type})")
    result = _post_json(url, body, model_cfg["api_key"])

    # 兼容 apimart 等网关：响应可能包裹在 {"code":200,"data":{...}} 中
    if "data" in result and isinstance(result["data"], dict) and "choices" in result["data"]:
        result = result["data"]

    choices = result.get("choices", [])
    if not choices:
        _err(f"API 返回无内容（顶层键: {list(result.keys())}）: {json.dumps(result, ensure_ascii=False)[:500]}")
    content = choices[0].get("message", {}).get("content", "")

    usage = result.get("usage", {})
    if usage:
        _info(
            f"Token 用量: "
            f"输入 {usage.get('prompt_tokens', '?')} + "
            f"输出 {usage.get('completion_tokens', '?')} = "
            f"总计 {usage.get('total_tokens', '?')}"
        )
    return content


def _call_gemini(model_cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """base_url：完整 ...:generateContent 端点，或网关根（如 https://yunwu.ai）。"""
    b = model_cfg["base_url"].rstrip("/")
    model = (model_cfg["model"] or "").strip()
    bl = b.lower()
    if ":generatecontent" in bl:
        url = b
    else:
        url = f"{b}/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }],
        "generationConfig": {
            "temperature": model_cfg["temperature"],
            "maxOutputTokens": model_cfg["max_tokens"],
        },
    }
    _info(f"调用模型: {model_cfg['model']} @ {url} (gemini)")
    result = _post_json(url, body, model_cfg["api_key"])
    candidates = result.get("candidates", [])
    if not candidates:
        _err(f"API 返回无内容: {result}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    if not text:
        _err(f"API 返回无文本内容: {result}")
    return text


def call_llm(model_cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """根据 provider 调用对应的文本生成接口。"""
    api_type = _detect_api_type(model_cfg)
    if api_type in {"openai", "volcengine", "qwen"}:
        return _call_openai_like(model_cfg, system_prompt, user_prompt, api_type)
    if api_type == "gemini":
        return _call_gemini(model_cfg, system_prompt, user_prompt)
    _err(f"未识别的协议类型: {api_type}。请检查 writing_model.provider/base_url/model 配置。")
    raise RuntimeError("invalid writing api type")


def _image_density_value(screening: dict) -> str:
    """默认每节一图。"""
    return (screening.get("image_density") or "").strip() or "每节一图"


def _resolve_image_source(screening: dict) -> str:
    """图片来源：generated | user（默认 generated）。"""
    src = (screening.get("image_source") or "").strip().lower()
    if src in {"generated", "user"}:
        return src
    return "generated"


def _load_img_analysis(draft_dir: Path) -> str:
    p = (draft_dir / "img_analysis.md").resolve()
    if not p.is_file():
        return ""
    try:
        text = p.read_text(encoding="utf-8").strip()
    except OSError as e:
        _err(f"无法读取 img_analysis.md：{e}")
    return text


def _extract_recommended_cover_count(img_analysis: str) -> int:
    if not img_analysis:
        return 0
    # 兼容“推荐用途：封面”及“推荐用途: 封面”
    return len(re.findall(r"推荐用途\s*[:：]\s*封面", img_analysis))


def _extract_image_filenames(img_analysis: str) -> list[str]:
    if not img_analysis:
        return []
    # 允许形式：文件名：xxx.png 或 “- xxx.png：”
    names: list[str] = []
    for m in re.finditer(r"文件名\s*[:：]\s*([^\s]+?\.(?:png|jpg|jpeg|webp|gif))", img_analysis, flags=re.I):
        names.append(m.group(1))
    for m in re.finditer(r"^\s*[-*]?\s*([^\s:：]+?\.(?:png|jpg|jpeg|webp|gif))\s*[:：]", img_analysis, flags=re.I | re.M):
        names.append(m.group(1))
    # 去重并保序
    uniq: list[str] = []
    seen = set()
    for n in names:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


# ── 写作模式 ─────────────────────────────────────────────────

def build_system_prompt(
    screening: dict,
    writing_spec: str,
    structure_template: str,
    closing_block: str = "",
    image_source: str = "generated",
    img_analysis: str = "",
) -> str:
    """构建系统 prompt：config/本篇合并约束 + 写作规范 + 结构模板。closing_block 已解析（预设 > 内联）。"""
    parts = ["你是一位资深的微信公众号内容创作者。请按以下要求写文章。\n"]

    parts.append("## 基本要求\n")
    article_category = (screening.get("article_category") or screening.get("article_style") or "").strip()
    if article_category:
        parts.append(f"- 账号/领域：{article_category}")
    target_reader = (screening.get("target_reader") or "").strip()
    if target_reader:
        parts.append(f"- 目标读者：{target_reader}")
    topic_direction = (screening.get("topic_direction") or "").strip()
    if topic_direction:
        parts.append(f"- 选题方向或禁区：{topic_direction}")
    parts.append(f"- 语气调性：{screening.get('tone', '轻松')}")
    parts.append(f"- 文章风格：{screening.get('writing_style', '口语化')}")
    parts.append(f"- 段落偏好：{screening.get('paragraph_preference', '短段为主')}")
    parts.append(f"- 小标题密度：{screening.get('heading_density', '每节必有小标题')}")
    title_max = screening.get("title_max_length")
    if title_max is not None:
        parts.append(f"- 文章标题字数不超过：{title_max}")
    summary_length = (screening.get("summary_length") or "").strip()
    if summary_length:
        parts.append(f"- 摘要字数范围：{summary_length}")
    target_word_count = (screening.get("target_word_count") or "").strip()
    if target_word_count:
        parts.append(f"- 文章目标字数：{target_word_count}")

    forbidden = screening.get("forbidden_words", [])
    if isinstance(forbidden, list) and forbidden:
        parts.append(f"- 禁用词：{', '.join(str(x) for x in forbidden)}")

    if closing_block:
        parts.append(f"- 文末必须包含以下区块：\n{closing_block}")

    attribution = screening.get("original_attribution", "")
    if attribution:
        parts.append(f"- 原创标注：{attribution}")

    if writing_spec:
        parts.append(f"\n## 用户写作规范\n\n{writing_spec}")

    if structure_template:
        parts.append(f"\n## 文章结构参考\n\n{structure_template}")

    parts.append(
        "\n## 输出要求\n"
        "- 输出完整的 Markdown 格式文章\n"
        "- 包含：标题（# 开头）、摘要（> 引用块，80-128字）、正文（## 小标题分节）、结尾、文末区块\n"
        "- 开头 2-3 句必须吸睛\n"
        "- 段落短小，适合手机阅读\n"
        "- 不要输出任何解释性文字，只输出文章本身"
    )
    if image_source == "user" and img_analysis:
        image_files = _extract_image_filenames(img_analysis)
        parts.append(
            "\n## 用户供图模式（硬性）\n"
            "- 本篇图片由用户提供，必须直接使用现有图片，不得再输出 placeholder\n"
            "- 封面只能出现 1 张，且必须放在标题之前\n"
            "- 正文按图片分析内容匹配到对应章节；图片语法：`![类型名：画面内容](imgs/文件名)`\n"
            "  冒号前只能是：封面、信息图、氛围、流程图、对比、实证之一；"
            "禁止在方括号内写字面「类型」二字；冒号后为简短画面概括（如「淘米」「小孩钓鱼」），"
            "- 若某图不适配正文可不使用，但不得虚构不存在的文件名\n"
        )
        if image_files:
            parts.append("- 可用图片文件： " + ", ".join(image_files))
    else:
        density = _image_density_value(screening)
        parts.append(
            "\n## 配图标记（硬性）\n"
            f"- 配图密度必须遵循：{density}（未配置时默认每节一图）\n"
            "- 正文配图数量需尽量满足该密度规则\n"
            "- 格式：`![类型名：画面内容](placeholder)`。全角冒号 `：` 分隔两段\n"
            "  冒号前只能是：封面、信息图、氛围、流程图、对比、实证之一；"
            "  冒号后为画面内容的简短概括即可（如「淘米」「小孩钓鱼」「窗前喝水」），"
            "  也可略写细；禁止只用「配图」「示意图」等敷衍词\n"
            "- 必须用图片语法 ![]()，不能写成 []()（少写 ! 会在排版时变成链接）\n"
            "- 每个配图标记独占一行，前后留空行，不要与正文同一行\n"
            "- 封面标记放在标题之前\n"
            "- 信息图冒号后需包含具体数据点或维度（若本篇用到信息图）\n"
            "- 实证类注明需用户提供"
        )

    return "\n".join(parts)


def draft(
    topic_card: str,
    screening: dict,
    model_cfg: dict,
    writing_spec: str,
    structure_template: str,
    closing_block: str = "",
    image_source: str = "generated",
    img_analysis: str = "",
) -> str:
    """按选题卡片写初稿。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
    )
    user_prompt = f"请根据以下选题卡片，写一篇完整的微信公众号文章：\n\n{topic_card}"
    if image_source == "user" and img_analysis:
        user_prompt += f"\n\n以下是用户上传图片的分析记录，需据此组织章节并使用对应图片：\n\n{img_analysis}"
    return call_llm(model_cfg, system_prompt, user_prompt)


def rewrite(
    article: str,
    instruction: str,
    screening: dict,
    model_cfg: dict,
    writing_spec: str,
    structure_template: str,
    closing_block: str = "",
    image_source: str = "generated",
    img_analysis: str = "",
) -> str:
    """改写已有文章。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
    )
    user_prompt = f"请改写以下文章"
    if instruction:
        user_prompt += f"，改写要求：{instruction}"
    user_prompt += f"\n\n---\n\n{article}"
    if image_source == "user" and img_analysis:
        user_prompt += f"\n\n附：用户图片分析记录（改写时保持图片映射关系）：\n\n{img_analysis}"
    return call_llm(model_cfg, system_prompt, user_prompt)


def continue_writing(
    article: str,
    screening: dict,
    model_cfg: dict,
    writing_spec: str,
    structure_template: str,
    closing_block: str = "",
    image_source: str = "generated",
    img_analysis: str = "",
) -> str:
    """续写未完成的文章。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
    )
    user_prompt = (
        "以下是一篇未完成的微信公众号文章，请从断点处继续写完，"
        "保持风格和结构一致：\n\n"
        f"{article}"
    )
    if image_source == "user" and img_analysis:
        user_prompt += f"\n\n附：用户图片分析记录（续写时保持图片映射关系）：\n\n{img_analysis}"
    return call_llm(model_cfg, system_prompt, user_prompt)


# ── CLI ──────────────────────────────────────────────────────

def _build_prompts(mode, input_text, screening, writing_spec,
                   structure_template, closing_block, image_source,
                   img_analysis, instruction=""):
    """Build system_prompt + user_prompt without calling LLM."""
    system_prompt = build_system_prompt(
        screening, writing_spec, structure_template, closing_block,
        image_source=image_source, img_analysis=img_analysis,
    )
    if mode == "draft":
        user_prompt = f"请根据以下选题卡片，写一篇完整的微信公众号文章：\n\n{input_text}"
        if image_source == "user" and img_analysis:
            user_prompt += f"\n\n以下是用户上传图片的分析记录，需据此组织章节并使用对应图片：\n\n{img_analysis}"
    elif mode == "rewrite":
        user_prompt = "请改写以下文章"
        if instruction:
            user_prompt += f"，改写要求：{instruction}"
        user_prompt += f"\n\n---\n\n{input_text}"
        if image_source == "user" and img_analysis:
            user_prompt += f"\n\n附：用户图片分析记录（改写时保持图片映射关系）：\n\n{img_analysis}"
    elif mode == "continue":
        user_prompt = (
            "以下是一篇未完成的微信公众号文章，请从断点处继续写完，"
            "保持风格和结构一致：\n\n"
            f"{input_text}"
        )
        if image_source == "user" and img_analysis:
            user_prompt += f"\n\n附：用户图片分析记录（续写时保持图片映射关系）：\n\n{img_analysis}"
    else:
        _err(f"未知写作模式: {mode}")
        raise RuntimeError("unknown mode")
    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def main():
    parser = argparse.ArgumentParser(
        description="公众号文章写作工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_draft = sub.add_parser("draft", help="按选题卡片写初稿")
    p_draft.add_argument("input", help="选题卡片文件路径（.md）")
    p_draft.add_argument("-o", "--output", help="输出路径（默认输出到终端）")

    p_rewrite = sub.add_parser("rewrite", help="改写已有文章")
    p_rewrite.add_argument("input", help="文章文件路径（.md）")
    p_rewrite.add_argument("--instruction", default="", help="改写要求")
    p_rewrite.add_argument("-o", "--output", help="输出路径")

    p_continue = sub.add_parser("continue", help="续写未完成的文章")
    p_continue.add_argument("input", help="文章文件路径（.md）")
    p_continue.add_argument("-o", "--output", help="输出路径")

    p_prompt = sub.add_parser("prompt", help="只输出写作提示词 JSON（不调用 LLM）")
    p_prompt.add_argument("mode", choices=["draft", "rewrite", "continue"], help="写作模式")
    p_prompt.add_argument("input", help="输入文件路径")
    p_prompt.add_argument("--instruction", default="", help="改写要求（仅 rewrite）")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # prompt subcommand: build prompts only, no model config needed
    if args.command == "prompt":
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            _err(f"文件不存在: {input_path}")
        input_text = input_path.read_text(encoding="utf-8")
        draft_dir = input_path.parent
        screening = _load_writing_context(draft_dir)
        writing_spec = _load_writing_spec()
        structure_template = _load_structure_template(screening)
        closing_block = _load_closing_block(screening)
        image_source = _resolve_image_source(screening)
        img_analysis = _load_img_analysis(draft_dir)
        if image_source == "user" and not img_analysis:
            _err(
                "当前 image_source=user，但未找到本篇 img_analysis.md。"
                "请先生成并补全 img_analysis.md，再执行。"
            )
        if image_source == "user" and img_analysis:
            cover_count = _extract_recommended_cover_count(img_analysis)
            if cover_count != 1:
                _err(f"img_analysis.md 中“推荐用途：封面”必须且只能有 1 处，当前为 {cover_count} 处。")
        prompts = _build_prompts(
            args.mode, input_text, screening, writing_spec,
            structure_template, closing_block, image_source, img_analysis,
            instruction=getattr(args, "instruction", ""),
        )
        print(json.dumps(prompts, ensure_ascii=False))
        sys.exit(0)

    # draft / rewrite / continue: need model config
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")
    input_text = input_path.read_text(encoding="utf-8")

    draft_dir = input_path.parent
    screening = _load_writing_context(draft_dir)
    model_cfg = _resolve_model_config()
    if model_cfg is None:
        print(
            "[NO_MODEL] 写作模型未配置（writing_model 或 WRITING_MODEL_API_KEY 缺失）。"
            "请使用 write.py prompt 获取提示词后由 Agent 代写。",
            file=sys.stderr,
        )
        sys.exit(2)
    writing_spec = _load_writing_spec()
    structure_template = _load_structure_template(screening)
    closing_block = _load_closing_block(screening)

    image_source = _resolve_image_source(screening)
    img_analysis = _load_img_analysis(draft_dir)
    if image_source == "user":
        if not img_analysis:
            _err(
                "当前 image_source=user，但未找到本篇 img_analysis.md。"
                "请先执行：python skills/aws-wechat-article-images/scripts/user_image_prepare.py <article_dir> "
                "生成模板并补全分析，再执行写稿。"
            )
        cover_count = _extract_recommended_cover_count(img_analysis)
        if cover_count != 1:
            _err(f"img_analysis.md 中“推荐用途：封面”必须且只能有 1 处，当前为 {cover_count} 处。")
        _info("检测到用户供图模式：将直接使用现有图片写稿（封面仅 1 张）")

    if args.command == "draft":
        result = draft(
            input_text,
            screening,
            model_cfg,
            writing_spec,
            structure_template,
            closing_block,
            image_source=image_source,
            img_analysis=img_analysis,
        )
    elif args.command == "rewrite":
        result = rewrite(
            input_text,
            args.instruction,
            screening,
            model_cfg,
            writing_spec,
            structure_template,
            closing_block,
            image_source=image_source,
            img_analysis=img_analysis,
        )
    elif args.command == "continue":
        result = continue_writing(
            input_text,
            screening,
            model_cfg,
            writing_spec,
            structure_template,
            closing_block,
            image_source=image_source,
            img_analysis=img_analysis,
        )
    else:
        parser.print_help()
        sys.exit(0)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        _ok(f"已保存到: {out_path}")
    else:
        print("\n" + result)


if __name__ == "__main__":
    main()
