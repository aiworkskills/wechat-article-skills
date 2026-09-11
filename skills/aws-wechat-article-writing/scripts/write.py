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
    python write.py draft <topic_card.md> --reference .aws-article/products/公众号AI运营助手/项目介绍.md
    （可重复 --reference，最多 5 个；须形如 .aws-article/products/<产品名>/<文件名>.md，
     直接挂在产品根；不接受 images/ 子目录下的图片说明文件）
    python write.py rewrite <article.md>               改写已有文章
    python write.py rewrite <article.md> --instruction "改成口语化"
    python write.py continue <article.md>              续写未完成的文章
    python write.py prompt draft <topic_card.md>       只输出提示词JSON(不调LLM)
    python write.py prompt rewrite <article.md> --instruction "..."
    python write.py check <draft.md>                  按产出配额量一遍稿子（摘要/加粗/金句/标签列表）
                                                       打印加粗串成的提要；有硬性项未达标时退出码 1
    python write.py strip-citations <draft.md> -o <article.md>
                                                       剥离 （资料路径：...） 引用标注（review skill 定稿前调用）
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

# 参考资料库：业务介绍 .md（直接挂在 .aws-article/products/<产品名>/ 根下）
# 全文注入，不设脚本内截断（API 超限请减少 --reference）
MAX_REFERENCE_FILES = 5
PRODUCTS_BASE_REL = Path(".aws-article") / "products"


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


def _load_article_yaml(draft_dir: Path) -> dict:
    """仅用于读取本篇已选预设（单元素列表）。"""
    art = (draft_dir / "article.yaml").resolve()
    if not art.is_file():
        return {}
    return _load_yaml_file(art)


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


def _load_structure_template(screening: dict, article_cfg: dict) -> str:
    """
    加载文章结构模板。
    预设选择仅读取本篇 article.yaml 的 default_structure（单元素列表）。
    未选择时回退内置结构模板。
    """
    default_name = _coerce_single_preset("default_structure", article_cfg.get("default_structure"))
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


def _load_closing_block(screening: dict, article_cfg: dict) -> str:
    """
    文末区块：预设选择仅读取本篇 article.yaml 的 default_closing_block。
    若本篇未选择预设，才使用合并上下文中的内联 closing_block。
    """
    default_name = _coerce_single_preset("default_closing_block", article_cfg.get("default_closing_block"))
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


# 密度词的定义。**这几个词是本套件自造的词汇，模型不认识。**
#
# 此前提示词只把 `image_density` 的值原样拼进去（「配图密度必须遵循：每节一图」），
# 等于丢一个自定义词让模型自己猜是什么意思。实测五篇真稿，每一篇产出的正文配图
# 标记数都少于 `##` 小节数——密度配的是每节一图，实际只出了两三个。
#
# 定义原本只写在 images skill 的 references/image-method.md 里，而那份文档是配图
# 阶段读的，写稿阶段根本读不到。两处必须保持同一套措辞。
_DENSITY_RULES = {
    "每节一图": "每个 `##` 小节各配一张，不多不少",
    "按需配图": "只在文字讲不清的地方配（流程、对比、数据），其余不配",
    "少图": "全篇只配 1–2 张最关键的",
    "多图": "每 2–3 个自然段配一张",
}


def _density_rule(density: str) -> str:
    """密度词对应的具体规则；自定义词返回空串（按字面理解）。"""
    return _DENSITY_RULES.get((density or "").strip(), "")


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


def _validate_reference_path(p: Path, repo_root: Path) -> Path:
    """
    校验 --reference 路径必须形如 `.aws-article/products/<产品名>/<文件名>.md`
    （直接挂在产品根，不在 images/ 子目录下；那里是图片说明 .md，不是业务介绍）。
    返回相对仓库根的 Path。
    """
    rp = p.resolve()
    try:
        rel = rp.relative_to(repo_root.resolve())
    except ValueError:
        _err(f"参考资料须在仓库根下：{p}")
    parts = rel.parts
    if (
        len(parts) != 4
        or parts[0] != ".aws-article"
        or parts[1] != "products"
        or not parts[2]
        or not parts[3].lower().endswith(".md")
    ):
        _err(
            "参考资料路径应形如 "
            ".aws-article/products/<产品名>/<文件名>.md（直接挂在产品根，不在 images/ 下）："
            f"{rel.as_posix()}"
        )
    if not rp.is_file():
        _err(f"参考资料文件不存在：{rp}")
    return rel


# 版式组件的 `:::` 语法**不再写进提示词**（原 build_components_block，2026-09-07 移除）。
#
# 链路定为「markdown 语法 → 按语法输出 → 渲染器排版」：写手只产出标准 markdown，
# 识别结构是排版层的事。让写手同时掌握标准 markdown 和一套私有语法，就是耦合——
# 而且那套语法只有本套件认得，稿子换个工具就废了。
#
# 排版侧仍然认 `:::`（存量草稿、用户手写时可用），只是不再主动教。markdown 表达得了的
# 都走标准写法：有序列表、两列表格、任务列表、`>` 引用、`##`、首段。markdown 表达不了的
# （stat 的大数字对、layers 的层级图）目前就不产出——这是这个取舍明确付出的代价。


def build_reference_library_block(raw_paths: list[str], cwd: Path) -> str:
    """读取业务资料库 .md，拼成系统提示「参考资料库」正文。"""
    if not raw_paths:
        return ""
    if len(raw_paths) > MAX_REFERENCE_FILES:
        _err(f"--reference 最多 {MAX_REFERENCE_FILES} 个路径，当前 {len(raw_paths)} 个")
    repo_root = cwd.resolve()
    chunks: list[str] = []
    for i, raw in enumerate(raw_paths, 1):
        p = Path(raw.strip())
        if not p.is_absolute():
            p = (cwd / p).resolve()
        else:
            p = p.resolve()
        rel = _validate_reference_path(p, repo_root)
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as e:
            _err(f"无法读取参考资料: {p}：{e}")
        chunks.append(f"### {i}\n\n{text}\n\n资料路径：`{rel.as_posix()}`\n")
    return "\n".join(chunks)


# ── 写作模式 ─────────────────────────────────────────────────

def build_system_prompt(
    screening: dict,
    writing_spec: str,
    structure_template: str,
    closing_block: str = "",
    image_source: str = "generated",
    img_analysis: str = "",
    reference_library_block: str = "",
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
    summary_length = str(screening.get("summary_length") or "").strip()
    if summary_length:
        parts.append(f"- 摘要字数范围：{summary_length}")
    target_word_count = str(screening.get("target_word_count") or "").strip()
    if target_word_count:
        parts.append(f"- 文章目标字数：{target_word_count}")

    forbidden = screening.get("forbidden_words", [])
    if isinstance(forbidden, list) and forbidden:
        parts.append(f"- 禁用词：{', '.join(str(x) for x in forbidden)}")

    if closing_block:
        parts.append(f"- 文末必须包含以下区块：\n{closing_block}")

    attribution = screening.get("original_attribution", "")
    if attribution:
        parts.append(f"- 原创标注（发布时的元数据，仅作背景信息，**不要写进正文或当作署名/电头**）：{attribution}")

    if writing_spec:
        parts.append(f"\n## 用户写作规范\n\n{writing_spec}")

    if structure_template:
        parts.append(
            "\n## 文章结构参考\n"
            "（以下为**写作指引**。其中方括号元标签【开头】【主体】【结尾】【金句节奏】【情绪节奏】【篇幅分配】等，"
            "以及「互动引导」「互动收尾」之类的说明，**只供你组织行文，严禁原样作为文章里的小标题或标签输出**。"
            "互动收尾要自然融入结尾段落的句子里，**不得**写成「互动话题」「互动时间」「话题互动」「互动引导」这类标题或加粗标签。）\n\n"
            f"{structure_template}"
        )

    ref_block = (reference_library_block or "").strip()
    if ref_block:
        parts.append(
            "\n## 参考资料库\n"
            "以下为仓库内说明文档全文或节选，**可作事实与术语依据**。\n"
            "**引用标注（硬性）**：若某句或某段**实际依据**了某条资料，须在该句/段**结束之后**立刻写出标注；"
            "标注**整段**必须用**一对中文全角括号**（ ）包起来，中间为「资料路径：」+ **反引号**内的仓库相对路径，"
            "路径须与下文中对应条目 **`资料路径：`** 后的字符串**完全一致**。\n"
            "**正确示例**：（资料路径：`.aws-article/products/<产品名>/某介绍.md`）\n"
            + ref_block
        )

    out_lines = [
        "\n## 输出要求\n",
        "- 输出完整的 Markdown 格式文章\n",
        "- 包含：标题（# 开头）、摘要（> 引用块，80-128字）、正文（## 小标题分节）、结尾、文末区块\n",
        "- 文章必须**直接以 `#` 标题开头**；标题前后严禁出现「作者署名／发自某地／记者／媒体名报道」之类的新闻电头（如「马斯 发自 北京」「XX 发自 凹非寺」「量子位报道」「本报记者」）。作者与原创标注属发布时的元数据，不写进正文\n",
        "- 开头 2-3 句必须吸睛\n",
        "- 段落短小，适合手机阅读\n",
        "- 严禁把结构指引中的元标签（如【开头】【结尾】等）或「互动话题／互动时间／互动引导」之类字样当作正文标题或加粗标签输出；要做互动收尾就直接写成自然句子（如一句抛给读者的开放式提问），不加任何标签\n",
        "- 不要输出任何解释性文字，只输出文章本身\n",
        # 链路是「markdown 语法 → 按语法输出 → 渲染器排版」。写错的标记不会报错——
        # 渲染照常完成，读者会在正文里直接看见 `__加粗__` `###### 六级` `[^1]` 这些符号。
        # 实测模型最常写错的就是下划线强调、裸 URL、Setext 标题这三样，所以逐条点名。
        "\n### Markdown 语法（硬性）\n",
        # markdown 语法是系统不变量，不是用户偏好——用户不会写、也不该知道要写。
        # 所以它只能来自代码侧，不能指望 .aws-article/writing-spec.md 提及。
        # 这一节无条件拼在最后，并显式声明优先级：上面的用户写作规范若与之冲突，
        # 以本节为准。否则用户随手写一句「强调用 __双下划线__」就能把整条链路带歪。\n"
        "以下几条是**格式规范**，与上文任何风格约定冲突时以本节为准"
        "（风格由上文决定，标记写法由本节决定）：\n",
        "- 加粗只用 `**加粗**`，斜体只用 `*斜体*`。**不要**用 `__加粗__` 或 `_斜体_`\n",
        "- 小标题只用 `## ` `### `（井号后有空格）。**不要**用 `====` / `----` 下划线式标题\n",
        "- 链接必须写成 `[锚文本](https://…)`。**不要**在正文里留裸 URL\n",
        "- 无序列表用 `- `，有序列表用 `1. `。有序列表只在**真有先后**时用；"
        "并列的几项用 `- `，否则等于替读者断言了一个不存在的顺序\n",
        "- 代码块用三个反引号围栏。**不要**用四个空格缩进当代码块\n",
        "- 表格必须带分隔行 `|---|---|`\n",
        "- 需要一个明显转场时用独占一行的 `---`（上下各留空行）——排版会把它换成本模版的分隔装饰\n",
        "- **不要**输出任何 HTML 标签（`<br>` `<div>` 等），排版由渲染器负责\n",
        "- **不要**使用 `:::` 之类的自定义块语法，写标准 markdown 即可\n",
        # 下面三条管的不是「怎么写」而是「写多少」。语法规则模型都照做，但没有配额
        # 就一处都不产出——真稿实测：金句卡 0/10 篇，正文段落内的加粗 0/5 篇
        # （写出来的加粗全在列表标签里），读者在手机上一屏扫过去没有任何落点。
        "\n**以下是产出配额，不是可选项：**\n",
        # 摘要在「输出要求」里已经写过一次，但那是一串并列项里的一条，实测三篇连着漏。
        # 挪进配额区重申——这一区的几条（配图数、金句数）是实测唯一被稳定执行的。
        # 漏掉的代价不显眼却确定：第一个 `##` 之前没有 `>`，导语版式就整篇不出现。
        "- **正文开头必须有摘要**：紧跟标题写一段 `> ` 引用块（80-128 字）。"
        "它是正文的一部分，要写进文章里，**不是**只填到别处的摘要字段——"
        "第一个 `##` 之前没有 `>`，排版的导语样式就整篇不会出现。\n",
        # 实测七篇（含改动前的三篇）导语与 article.yaml 的 digest 逐字相同。
        # digest 显示在列表页和分享卡片上，读者点进来第一段又原样读一遍。
        # 两者的读者处境不同：一个要决定点不点，一个已经点进来了。
        "  **这段导语不要和摘要字段写成同一句话。** 摘要字段是给还没点进来的人看的，"
        "负责说清「为什么值得点」；正文导语是给已经点进来的人看的，负责交代"
        "「这篇讲什么、按什么顺序讲」。两处逐字重复，读者等于同一段话读了两遍\n",
        # 密度早就达标了（实测四篇平均每 2.1 段一处），但读者仍然觉得「没有重点」。
        # 因为加粗的全是 9-11 字的抽象概括短句（「成果来自工程能力的扩张」），平均 7.9 字、
        # 只有 28% 在 6 字以内、含数字的仅 4%——正文里 9 个数字只有 2 个被加粗。
        # 把整句的意思复述一遍再加粗，读者扫到它等于把这段又读一次，不构成落点。
        # 所以这条规则管的是**加粗什么**，不再只管多久一次。
        # 加粗的用途是让读者从密密麻麻的正文里一眼抓住关键信息，所以验收标准是
        # 「只读加粗能不能串成一份提要」。两个失败方向都见过：
        # 复述整句（9-11 字的抽象概括，扫到它等于把这段重读一遍），
        # 和只留裸数字（`**88%**` 单独拎出来看不出是什么的 88%）。
        # 两个极端都踩过：先是 9-11 字复述整句（扫到它等于把这段重读一遍），
        # 收紧到「2-8 字」之后又滑到另一头——实测 48 处加粗平均 3.6 字、94% 在 4 字
        # 以内，全是「透明度」「瓶颈」「采用」这类裸名词，串起来是个词云不是提要。
        # 所以给的是目标区间而不是上限，并且直接点名裸名词不合格。
        "- 正文**每 2-3 段至少有一处 `**加粗**`**，一段里最多两处，"
        "**每处 5-8 个字最好**（少于 5 字多半是裸名词，多于 8 字多半是复述整句；"
        "数字和英文整串算一个字，`**省 88% Token**` 是 3 个字不是 11 个）。\n",
        "  **验收标准：把全文的加粗单独抽出来连起来读，应该像一份能看懂的提要。**"
        "串不起来就是挑错了。\n",
        "  所以加粗的必须能**独立成立**——单独读它就知道你想说什么："
        "数字连着它的意思（`**省 88% Token**`，不是光一个 `**88%**`）；"
        "术语连着它的定性（`**按问题找证据**`，不是光一个 `**证据**`）；"
        "判断连着它的对象（`**打断不等于撤销**`）。"
        "文中的关键数字要尽量覆盖到——那是最有效的落点。\n",
        "  **裸名词不合格**：「透明度」「瓶颈」「一致性」「采用」这种单独读看不出你想说什么，"
        "读者扫到它得回原句才懂，等于没有落点\n",
        "  **禁止**加粗对整句的概括或改写（「**成果来自工程能力的扩张**」这种），"
        "**禁止**每段都加在首句同一位置。排版会按模版给加粗上重点色、荧光底或底纹，"
        "位置和长度都要有变化，否则整篇看下去是均匀的纹理，不是重点\n",
        # 实测四篇「完整自然段」风格的深度分析文，列表项 0 个，li-label 因此从不触发。
        # 问题不是该不该用列表——而是三四个并列的条件被塞进一个长段落，读者只能顺读，
        # 没法跳读也没法对照。段落偏好管的是叙述段的长短，不该把枚举也压成散文。
        "- 本篇但凡出现**三项以上的并列**（并列的条件、选项、判断、对照项），"
        "就写成 `- **标签**：说明` 的列表，不要压进一个长段落。"
        "排版会把标签在视觉上提出来；即使段落偏好要求「完整自然段」，"
        "那管的是叙述段，枚举仍然用列表\n",
        "- 全文**恰好写一处**金句：最值得截图转发的那一句，写成 `> 金句。 —— 出处` —— "
        "带破折号出处的引用会排成金句卡。写两处以上，卡片就退化成装饰条，一处都不会被转；"
        "不写出处就是普通引用",
    ]
    if ref_block:
        out_lines.append(
            "- **参考资料引用格式（硬性）**：凡依据参考资料处，句末或段末须为「（资料路径：`…`）」；"
            "一对中文括号**不可省略**；反引号内路径须与「参考资料库」中某条 **`资料路径：`** 后路径**完全一致**"
        )
    parts.append("".join(out_lines))
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
        rule = _density_rule(density)
        parts.append(
            "\n## 配图标记（硬性）\n"
            f"- 配图密度：**{density}**"
            + (f" —— 就是说：{rule}\n" if rule else "（未配置时默认每节一图）\n")
            + "- 这是**硬配额不是参考值**：数量对不上就是没写完，写完后请自己数一遍\n"
            "- 格式：`![类型名：画面内容](placeholder)`。全角冒号 `：` 分隔两段\n"
            "- **图注单独写**，放在括号内路径之后的引号里："
            "`![信息图：画面内容](placeholder \"这里是图注\")`。\n"
            "  冒号后的「画面内容」是**给生图模型的画面指令**，不会显示给读者；"
            "图注是**给读者看的**，两者用途不同，不要互相复制。\n"
            "- **绝大多数图不需要图注**。图注要补充画面之外的信息（数据出处、一句判断、"
            "反常识的细节），不要复述读者眼睛已经看见的东西——"
            "「开发者站在巨型 99.9 分数牌前望向远方」这种就是废话图注。写不出有信息量的"
            "图注就不写第三个参数。\n"
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
    reference_library_block: str = "",
) -> str:
    """按选题卡片写初稿。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
        reference_library_block=reference_library_block,
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
    reference_library_block: str = "",
) -> str:
    """改写已有文章。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
        reference_library_block=reference_library_block,
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
    reference_library_block: str = "",
) -> str:
    """续写未完成的文章。"""
    system_prompt = build_system_prompt(
        screening,
        writing_spec,
        structure_template,
        closing_block,
        image_source=image_source,
        img_analysis=img_analysis,
        reference_library_block=reference_library_block,
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

_CITATION_PATTERN = re.compile(r"（资料路径[:：]\s*`[^`]+?`）")


def _strip_citations(text: str) -> str:
    """剥离正文中所有 （资料路径：`...`） 引用标注，并清理行尾空白与多余空行。"""
    cleaned = _CITATION_PATTERN.sub("", text)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if text.endswith("\n") and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned


_CJK = r"一-鿿　-〿＀-￯"


def _emph_units(s: str) -> int:
    """加粗的「长度」按显示单位算：一个汉字 1 个，一串连续的数字/英文也算 1 个。

    按字符数会误伤中英混排。`省 88% Token` 是理想的加粗——数字连着它的意思——
    但 len() 数出来是 11，会被当成「复述整句」拦下来，而它恰恰是我们要的样子。
    """
    return len(re.findall(rf"[{_CJK}]", s)) + len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.%]*", s))


def _is_bare_noun(s: str) -> bool:
    """短的纯中文词 —— 「透明度」「瓶颈」「商业模式」这种单独读看不出想说什么的。

    含数字或英文的不算（`省 88% Token` 自带信息）；长一点的中文短语也不算
    （`按问题找证据` 能独立成立）。只拦「纯中文且 ≤4 字」这一类。
    """
    return not re.search(r"[A-Za-z0-9]", s) and len(re.findall(rf"[{_CJK}]", s)) <= 4


def check_output(text: str) -> tuple[list[str], list[str], str]:
    """对着产出配额量一遍稿子，返回 (不合格项, 提醒项, 加粗串成的提要)。

    自检此前是一张表，靠人肉数——实测漏得很稳定：连着三篇没写摘要、四篇一个列表
    都没有、加粗密度够了但全是复述整句。这些都是能直接数出来的，不该靠眼睛。

    加粗那一项尤其需要机器量：数量达标不等于有重点。判据是「只读加粗能不能串成
    一份提要」，这里把提要打印出来，让人一眼看出串不串得起来。
    """
    lines = text.splitlines()
    bad: list[str] = []
    warn: list[str] = []

    first_h2 = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    if not any(l.strip().startswith(">") for l in lines[:first_h2]):
        bad.append("第一个 `##` 之前没有 `>` 摘要 —— 导语版式整篇不会出现")

    body = [l for l in lines
            if l.strip() and not l.startswith(("#", "!", ">", "-", "|", "```"))]
    bolds = [m for l in body for m in re.findall(r"\*\*([^*\n]+)\*\*", l)]
    paras = len(body)
    need = max(1, paras // 3)
    if len(bolds) < need:
        bad.append(f"正文 {paras} 段只有 {len(bolds)} 处加粗，至少要 {need} 处（每 2-3 段一处）")

    # 两头都要拦。只拦长的那次，模型转头去写 2-4 字的裸名词，48 处平均 3.6 字，
    # 机械指标全绿而串起来是个词云——工具报了假绿灯，比不报还糟。
    long_ones = [b for b in bolds if _emph_units(b) > 8]
    if long_ones:
        warn.append(f"{len(long_ones)} 处加粗偏长，多半是把整句复述了一遍："
                    + "、".join(f"「{b}」" for b in long_ones[:3]))

    bare = [b for b in bolds if _is_bare_noun(b)]
    if bolds and len(bare) > len(bolds) * 0.5:
        warn.append(f"{len(bare)}/{len(bolds)} 处加粗是短的纯中文词，多半是裸名词——"
                    f"单独读看不出想说什么，读者得回原句才懂："
                    + "、".join(f"「{b}」" for b in bare[:3]))

    nums_in_text = len(re.findall(r"\d+(?:\.\d+)?\s*(?:%|倍|美元|分|万|亿|个百分点)",
                                  "\n".join(body)))
    nums_bolded = len([b for b in bolds if re.search(r"\d", b)])
    if nums_in_text and nums_bolded * 2 < nums_in_text:
        warn.append(f"正文有 {nums_in_text} 个关键数字，只有 {nums_bolded} 个被加粗 —— "
                    f"数字是最有效的落点")

    if bolds:
        heads = sum(1 for l in body for m in re.finditer(r"\*\*[^*\n]+\*\*", l)
                    if m.start() < len(re.split(r"[。！？]", l)[0]))
        if heads > len(bolds) * 0.6:
            warn.append(f"{heads}/{len(bolds)} 处加粗都落在段落首句，位置要有变化")

    quotes = " ".join(l.strip()[1:].strip() for l in lines[first_h2:]
                      if l.strip().startswith(">"))
    n_card = len(re.findall(r"(?:——|—|--)\s*[^\s—][^—]{0,24}(?:\s|$)", quotes))
    if n_card == 0:
        bad.append("没有带出处的金句（`> 金句。 —— 出处`）—— 少一块可截图转发的内容")
    elif n_card > 1:
        warn.append(f"有 {n_card} 处带出处的引用，金句卡应恰好一处，多了就退化成装饰条")

    if not any(re.match(r"^\s*[-*+]\s+\*\*", l) for l in lines):
        warn.append("全文没有 `- **标签**：说明` 列表 —— 若文中有三项以上并列，"
                    "压在长段落里读者没法跳读")

    return bad, warn, " / ".join(bolds)


def _build_prompts(mode, input_text, screening, writing_spec,
                   structure_template, closing_block, image_source,
                   img_analysis, instruction="", reference_library_block=""):
    """Build system_prompt + user_prompt without calling LLM."""
    system_prompt = build_system_prompt(
        screening, writing_spec, structure_template, closing_block,
        image_source=image_source, img_analysis=img_analysis,
        reference_library_block=reference_library_block,
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

    ref_help = (
        "参考资料 Markdown 路径；须形如 "
        f"{PRODUCTS_BASE_REL.as_posix()}/<产品名>/<文件名>.md（直接挂在产品根，不在 images/ 下）；"
        f"可重复，最多 {MAX_REFERENCE_FILES} 个"
    )

    p_draft = sub.add_parser("draft", help="按选题卡片写初稿")
    p_draft.add_argument("input", help="选题卡片文件路径（.md）")
    p_draft.add_argument("-o", "--output", help="输出路径（默认输出到终端）")
    p_draft.add_argument("--reference", action="append", metavar="PATH", help=ref_help)

    p_rewrite = sub.add_parser("rewrite", help="改写已有文章")
    p_rewrite.add_argument("input", help="文章文件路径（.md）")
    p_rewrite.add_argument("--instruction", default="", help="改写要求")
    p_rewrite.add_argument("-o", "--output", help="输出路径")
    p_rewrite.add_argument("--reference", action="append", metavar="PATH", help=ref_help)

    p_continue = sub.add_parser("continue", help="续写未完成的文章")
    p_continue.add_argument("input", help="文章文件路径（.md）")
    p_continue.add_argument("-o", "--output", help="输出路径")
    p_continue.add_argument("--reference", action="append", metavar="PATH", help=ref_help)

    p_prompt = sub.add_parser("prompt", help="只输出写作提示词 JSON（不调用 LLM）")
    p_prompt.add_argument("mode", choices=["draft", "rewrite", "continue"], help="写作模式")
    p_prompt.add_argument("input", help="输入文件路径")
    p_prompt.add_argument("--instruction", default="", help="改写要求（仅 rewrite）")
    p_prompt.add_argument("--reference", action="append", metavar="PATH", help=ref_help)

    p_check = sub.add_parser(
        "check",
        help="对着产出配额量一遍稿子（摘要/加粗/金句/标签列表），不调 LLM",
    )
    p_check.add_argument("input", help="稿件路径（draft.md 或 article.md）")

    p_strip = sub.add_parser(
        "strip-citations",
        help="剥离正文 （资料路径：...） 引用标注（review skill 定稿前调用）",
    )
    p_strip.add_argument("input", help="含引用标注的 Markdown 路径（如 draft.md）")
    p_strip.add_argument("-o", "--output", help="输出路径（默认输出到终端）")

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
        article_cfg = _load_article_yaml(draft_dir)
        screening = _load_writing_context(draft_dir)
        writing_spec = _load_writing_spec()
        structure_template = _load_structure_template(screening, article_cfg)
        closing_block = _load_closing_block(screening, article_cfg)
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
        refs = getattr(args, "reference", None) or []
        ref_block = build_reference_library_block(refs, Path.cwd()) if refs else ""
        if ref_block:
            _info(f"已将 {len(refs)} 个参考资料文件注入 system_prompt（--reference）")
        prompts = _build_prompts(
            args.mode, input_text, screening, writing_spec,
            structure_template, closing_block, image_source, img_analysis,
            instruction=getattr(args, "instruction", ""),
            reference_library_block=ref_block,
        )
        print(json.dumps(prompts, ensure_ascii=False))
        sys.exit(0)

    # check subcommand: pure local measurement, no LLM / no config
    if args.command == "check":
        p = Path(args.input)
        if not p.is_file():
            _err(f"文件不存在: {p}")
        bad, warn, digest = check_output(p.read_text(encoding="utf-8"))
        if digest:
            print("加粗串起来是这样（读得通才算挑对了）：")
            print(f"  {digest}\n")
        for b in bad:
            print(f"[FAIL] {b}")
        for w in warn:
            print(f"[WARN] {w}")
        if not bad and not warn:
            _ok("产出配额全部达标")
        elif not bad:
            _ok(f"硬性项达标，另有 {len(warn)} 条提醒")
        sys.exit(1 if bad else 0)

    # strip-citations subcommand: pure local text rewrite, no LLM / no config
    if args.command == "strip-citations":
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            _err(f"文件不存在: {input_path}")
        text = input_path.read_text(encoding="utf-8")
        n_stripped = len(_CITATION_PATTERN.findall(text))
        cleaned = _strip_citations(text)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(cleaned, encoding="utf-8")
            _ok(f"已剥离 {n_stripped} 处引用标注，保存到: {out_path}")
        else:
            _info(f"已剥离 {n_stripped} 处引用标注（输出到 stdout）")
            sys.stdout.write(cleaned)
        sys.exit(0)

    # draft / rewrite / continue: need model config
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")
    input_text = input_path.read_text(encoding="utf-8")

    draft_dir = input_path.parent
    article_cfg = _load_article_yaml(draft_dir)
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
    structure_template = _load_structure_template(screening, article_cfg)
    closing_block = _load_closing_block(screening, article_cfg)

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

    refs = getattr(args, "reference", None) or []
    ref_block = build_reference_library_block(refs, Path.cwd()) if refs else ""
    if ref_block:
        _info(f"已将 {len(refs)} 个参考资料文件注入系统提示（--reference）")

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
            reference_library_block=ref_block,
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
            reference_library_block=ref_block,
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
            reference_library_block=ref_block,
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
