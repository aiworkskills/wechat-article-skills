#!/usr/bin/env python3
"""
用户供图准备工具：
- 确保本篇 imgs/ 目录存在
- 基于 imgs/ 下的图片文件生成 img_analysis.md 模板
- 强制“推荐用途：封面”只能有一个

用法：
  python user_image_prepare.py drafts/20260402-slug
  python user_image_prepare.py drafts/20260402-slug --cover 02-taomi.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


def _list_images(imgs_dir: Path) -> list[Path]:
    files = [p for p in sorted(imgs_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return files


def _build_analysis_md(files: list[Path], cover_name: str | None) -> str:
    if not files:
        return "# 图片分析（img_analysis）\n\n> imgs/ 下暂无图片，请先上传后重跑。\n"

    if cover_name:
        matched = [p for p in files if p.name == cover_name]
        if not matched:
            _err(f"--cover 指定的文件不存在于 imgs/：{cover_name}")
        cover = matched[0]
    else:
        cover = files[0]

    lines = [
        "# 图片分析（img_analysis）",
        "",
        "> 说明：`推荐用途` 中“封面”只能出现一次；其余图片请标注“正文”。",
        "",
    ]
    for p in files:
        use = "封面" if p.name == cover.name else "正文"
        lines.extend(
            [
                f"## {p.name}",
                f"- 文件名：{p.name}",
                "- 图片内容：待补充（请描述画面主体、动作、场景）",
                "- 建议章节：待补充（例如：选米 / 淘米 / 浸泡 / 煮饭）",
                f"- 推荐用途：{use}",
                "- 图注建议：待补充",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="为用户上传图片生成 img_analysis.md 模板")
    parser.add_argument("article_dir", help="本篇目录，例如 drafts/20260402-slug")
    parser.add_argument("--cover", help="指定封面文件名（必须位于 imgs/）")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 img_analysis.md")
    args = parser.parse_args()

    article_dir = Path(args.article_dir).resolve()
    if not article_dir.exists():
        _err(f"文章目录不存在：{article_dir}")

    imgs_dir = article_dir / "imgs"
    imgs_dir.mkdir(parents=True, exist_ok=True)
    _info(f"已确保目录存在：{imgs_dir}")

    analysis_path = article_dir / "img_analysis.md"
    if analysis_path.exists() and not args.overwrite:
        _err(f"img_analysis.md 已存在：{analysis_path}（如需覆盖请加 --overwrite）")

    files = _list_images(imgs_dir)
    content = _build_analysis_md(files, args.cover)
    analysis_path.write_text(content, encoding="utf-8")
    _ok(f"已写入：{analysis_path}")
    _info("请补充“图片内容/建议章节/图注建议”，并确保推荐用途里“封面”仅 1 处。")


if __name__ == "__main__":
    main()

