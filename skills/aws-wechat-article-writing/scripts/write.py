#!/usr/bin/env python3
"""
公众号文章写作工具

调用第三方 LLM API（OpenAI 兼容格式）生成公众号文章。
支持 DeepSeek、OpenAI、Claude（兼容端点）、智谱、通义千问等。

凭证和模型配置从 config.yaml 读取。

用法：
    python write.py draft <topic_card.md>              按选题卡片写初稿
    python write.py draft <topic_card.md> -o out.md    指定输出路径
    python write.py rewrite <article.md>               改写已有文章
    python write.py rewrite <article.md> --instruction "改成口语化"
    python write.py continue <article.md>              续写未完成的文章
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

def _err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"✅ {msg}")


def _info(msg: str):
    print(f"ℹ️  {msg}")


# ── 配置读取 ─────────────────────────────────────────────────

def _load_config() -> dict:
    import yaml
    candidates = [
        Path(".aws-article/config.yaml"),
        Path.home() / ".aws-article" / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    _err(
        "未找到 config.yaml\n"
        "  项目级: .aws-article/config.yaml\n"
        "  用户级: ~/.aws-article/config.yaml"
    )


def _get_model_config(cfg: dict) -> dict:
    """从 config 中提取模型配置。"""
    mc = cfg.get("writing_model", {})

    base_url = mc.get("base_url", "")
    model = mc.get("model", "")
    api_key = mc.get("api_key", "")

    if not base_url or not api_key or not model:
        _err(
            "config.yaml 中 writing_model 配置不完整，需要三个必填项：\n"
            "  writing_model:\n"
            "    base_url: https://api.deepseek.com  # 任何 OpenAI 兼容端点\n"
            "    api_key: 你的APIKey\n"
            "    model: deepseek-chat                 # 模型名"
        )

    return {
        "base_url": base_url.rstrip("/"),
        "model": model,
        "api_key": api_key,
        "temperature": mc.get("temperature", 0.7),
        "max_tokens": mc.get("max_tokens", 4000),
    }


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


def _load_structure_template() -> str:
    """加载文章结构模板。"""
    script_dir = Path(__file__).parent.parent
    template_path = script_dir / "references" / "structure-template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


# ── LLM 调用 ────────────────────────────────────────────────

def call_llm(model_cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """调用 OpenAI 兼容的 Chat Completions API。"""
    url = f"{model_cfg['base_url']}/v1/chat/completions"
    body = {
        "model": model_cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": model_cfg["temperature"],
        "max_tokens": model_cfg["max_tokens"],
    }

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_cfg['api_key']}",
        },
    )

    _info(f"调用模型: {model_cfg['model']} @ {model_cfg['base_url']}")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(f"API 调用失败 ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        _err(f"网络错误: {e.reason}")

    choices = result.get("choices", [])
    if not choices:
        _err(f"API 返回无内容: {result}")

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


# ── 写作模式 ─────────────────────────────────────────────────

def build_system_prompt(cfg: dict, writing_spec: str, structure_template: str) -> str:
    """构建系统 prompt，融合配置 + 写作规范 + 结构模板。"""
    parts = ["你是一位资深的微信公众号内容创作者。请按以下要求写文章。\n"]

    parts.append("## 基本要求\n")
    parts.append(f"- 语气调性：{cfg.get('tone', '轻松')}")
    parts.append(f"- 文章风格：{cfg.get('article_style', '口语化')}")
    parts.append(f"- 段落偏好：{cfg.get('paragraph_preference', '短段为主')}")
    parts.append(f"- 小标题密度：{cfg.get('heading_density', '每节必有小标题')}")

    forbidden = cfg.get("forbidden_words", [])
    if forbidden:
        parts.append(f"- 禁用词：{', '.join(forbidden)}")

    closing = cfg.get("closing_block", "")
    if closing:
        parts.append(f"- 文末引导语：{closing}")

    attribution = cfg.get("original_attribution", "")
    if attribution:
        parts.append(f"- 原创标注：{attribution}")

    if writing_spec:
        parts.append(f"\n## 用户写作规范\n\n{writing_spec}")

    if structure_template:
        parts.append(f"\n## 文章结构参考\n\n{structure_template}")

    parts.append("\n## 输出要求\n")
    parts.append("- 输出完整的 Markdown 格式文章")
    parts.append("- 包含：标题（# 开头）、摘要（> 引用块，80-150字）、正文（## 小标题分节）、结尾、文末区块")
    parts.append("- 开头 2-3 句必须吸睛")
    parts.append("- 段落短小，适合手机阅读")
    parts.append("- 不要输出任何解释性文字，只输出文章本身")

    parts.append("\n## 配图标记\n")
    parts.append("在需要配图的位置插入标记，格式：`![类型：描述](placeholder)`")
    parts.append("类型包括：封面、信息图、氛围、流程图、对比、实证")
    parts.append("- 封面标记放在标题之前")
    parts.append("- 描述要写清画面内容和意图")
    parts.append("- 信息图需包含具体数据点或维度")
    parts.append("- 实证类注明需用户提供")

    return "\n".join(parts)


def draft(topic_card: str, cfg: dict, model_cfg: dict,
          writing_spec: str, structure_template: str) -> str:
    """按选题卡片写初稿。"""
    system_prompt = build_system_prompt(cfg, writing_spec, structure_template)
    user_prompt = f"请根据以下选题卡片，写一篇完整的微信公众号文章：\n\n{topic_card}"
    return call_llm(model_cfg, system_prompt, user_prompt)


def rewrite(article: str, instruction: str, cfg: dict, model_cfg: dict,
            writing_spec: str, structure_template: str) -> str:
    """改写已有文章。"""
    system_prompt = build_system_prompt(cfg, writing_spec, structure_template)
    user_prompt = f"请改写以下文章"
    if instruction:
        user_prompt += f"，改写要求：{instruction}"
    user_prompt += f"\n\n---\n\n{article}"
    return call_llm(model_cfg, system_prompt, user_prompt)


def continue_writing(article: str, cfg: dict, model_cfg: dict,
                     writing_spec: str, structure_template: str) -> str:
    """续写未完成的文章。"""
    system_prompt = build_system_prompt(cfg, writing_spec, structure_template)
    user_prompt = (
        "以下是一篇未完成的微信公众号文章，请从断点处继续写完，"
        "保持风格和结构一致：\n\n"
        f"{article}"
    )
    return call_llm(model_cfg, system_prompt, user_prompt)


# ── CLI ──────────────────────────────────────────────────────

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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")
    input_text = input_path.read_text(encoding="utf-8")

    cfg = _load_config()
    model_cfg = _get_model_config(cfg)
    writing_spec = _load_writing_spec()
    structure_template = _load_structure_template()

    if args.command == "draft":
        result = draft(input_text, cfg, model_cfg, writing_spec, structure_template)
    elif args.command == "rewrite":
        result = rewrite(input_text, args.instruction, cfg, model_cfg,
                         writing_spec, structure_template)
    elif args.command == "continue":
        result = continue_writing(input_text, cfg, model_cfg,
                                  writing_spec, structure_template)
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
