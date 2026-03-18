#!/usr/bin/env python3
"""
图片生成工具

调用 OpenAI 兼容的图片生成 API（DALL-E、Flux、SD 等）。
跟 write.py 一样，使用任何 OpenAI 兼容端点，用户自行配置。

凭证从 config.yaml 的 image_model 读取。

用法：
    python image-gen.py generate <prompt.md> -o output.png
    python image-gen.py generate <prompt.md> --size 1024x576 --quality hd
    python image-gen.py batch <prompts_dir/> -o imgs/
    python image-gen.py test                                    测试 API 连通性
"""

import argparse
import base64
import json
import sys
import time
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


# ── 配置 ─────────────────────────────────────────────────────

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
    _err("未找到 config.yaml")


def _get_model_config(cfg: dict) -> dict:
    mc = cfg.get("image_model", {})
    base_url = mc.get("base_url", "")
    api_key = mc.get("api_key", "")
    model = mc.get("model", "")

    if not base_url or not api_key or not model:
        _err(
            "config.yaml 中 image_model 配置不完整：\n"
            "  image_model:\n"
            "    base_url: https://api.openai.com   # 任何 OpenAI 兼容端点\n"
            "    api_key: 你的APIKey\n"
            "    model: dall-e-3                     # 模型名"
        )
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": model,
        "default_size": mc.get("default_size", "1024x1024"),
        "default_quality": mc.get("default_quality", "standard"),
    }


# ── 图片生成 ─────────────────────────────────────────────────

ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "2.35:1": "1792x1024",
    "4:3": "1024x768",
    "3:4": "768x1024",
}


def generate_image(model_cfg: dict, prompt: str, size: str = None,
                   quality: str = None) -> bytes:
    """调用 OpenAI 兼容的 images/generations API。"""
    url = f"{model_cfg['base_url']}/v1/images/generations"
    body = {
        "model": model_cfg["model"],
        "prompt": prompt,
        "n": 1,
        "size": size or model_cfg["default_size"],
        "quality": quality or model_cfg["default_quality"],
        "response_format": "b64_json",
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
    _info(f"尺寸: {body['size']} | 质量: {body['quality']}")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(f"API 调用失败 ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        _err(f"网络错误: {e.reason}")

    items = result.get("data", [])
    if not items:
        _err(f"API 返回无图片: {result}")

    b64 = items[0].get("b64_json", "")
    if not b64:
        img_url = items[0].get("url", "")
        if img_url:
            _info("下载图片...")
            with urllib.request.urlopen(img_url, timeout=60) as r:
                return r.read()
        _err("API 未返回图片数据")

    return base64.b64decode(b64)


def _read_prompt_file(path: Path) -> tuple[str, dict]:
    """读取 prompt 文件，支持 YAML frontmatter。"""
    text = path.read_text(encoding="utf-8")

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            import yaml
            meta = yaml.safe_load(parts[1]) or {}
            prompt = parts[2].strip()
            return prompt, meta

    return text.strip(), {}


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="图片生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_gen = sub.add_parser("generate", help="从 prompt 文件生成单张图片")
    p_gen.add_argument("prompt_file", help="prompt 文件路径（.md，可含 YAML frontmatter）")
    p_gen.add_argument("-o", "--output", help="输出路径（默认同名 .png）")
    p_gen.add_argument("--size", help="尺寸（如 1024x1024）或比例（如 16:9）")
    p_gen.add_argument("--quality", help="质量（standard/hd）")

    p_batch = sub.add_parser("batch", help="批量生成（读取目录下所有 prompt 文件）")
    p_batch.add_argument("prompts_dir", help="prompt 文件目录")
    p_batch.add_argument("-o", "--output-dir", help="输出目录（默认同目录）")
    p_batch.add_argument("--size", help="统一尺寸")
    p_batch.add_argument("--quality", help="统一质量")

    p_test = sub.add_parser("test", help="测试 API 连通性")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    cfg = _load_config()
    model_cfg = _get_model_config(cfg)

    if args.command == "test":
        _info("测试 API 连通性...")
        try:
            img_data = generate_image(model_cfg, "A simple blue circle on white background",
                                       size="1024x1024", quality="standard")
            _ok(f"API 连通正常，收到 {len(img_data)} 字节图片数据")
        except SystemExit:
            pass
        return

    if args.command == "generate":
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            _err(f"文件不存在: {prompt_path}")

        prompt, meta = _read_prompt_file(prompt_path)

        size = args.size or meta.get("size") or meta.get("aspect")
        if size and size in ASPECT_TO_SIZE:
            size = ASPECT_TO_SIZE[size]
        quality = args.quality or meta.get("quality")

        img_data = generate_image(model_cfg, prompt, size=size, quality=quality)

        output_path = Path(args.output) if args.output else prompt_path.with_suffix(".png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_data)
        _ok(f"已保存: {output_path} ({len(img_data)} 字节)")

    elif args.command == "batch":
        prompts_dir = Path(args.prompts_dir)
        if not prompts_dir.exists():
            _err(f"目录不存在: {prompts_dir}")

        output_dir = Path(args.output_dir) if args.output_dir else prompts_dir.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        prompt_files = sorted(prompts_dir.glob("*.md"))
        if not prompt_files:
            _err(f"目录下无 .md 文件: {prompts_dir}")

        _info(f"找到 {len(prompt_files)} 个 prompt 文件")
        for i, pf in enumerate(prompt_files, 1):
            _info(f"[{i}/{len(prompt_files)}] {pf.name}")
            prompt, meta = _read_prompt_file(pf)

            size = args.size or meta.get("size") or meta.get("aspect")
            if size and size in ASPECT_TO_SIZE:
                size = ASPECT_TO_SIZE[size]
            quality = args.quality or meta.get("quality")

            img_data = generate_image(model_cfg, prompt, size=size, quality=quality)
            out_path = output_dir / pf.with_suffix(".png").name
            out_path.write_bytes(img_data)
            _ok(f"  → {out_path}")

            if i < len(prompt_files):
                time.sleep(1)

        _ok(f"批量生成完成：{len(prompt_files)} 张")


if __name__ == "__main__":
    main()
