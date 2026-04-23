#!/usr/bin/env python3
"""
将用户上传的图片复制到素材库 `.aws-article/assets/stock/images/`，
按中文主文件名保存；重名时自动使用 原名2、原名3… 后缀（扩展名前）。

运行前若缺少 `.aws-article`（仅含 `.git` 的仓库根也会识别）则创建；素材目录不存在则一并创建。

与图片同主文件名、扩展名为 `.md` 的说明文件一并生成，固定两行标签（全角冒号）：
  **图片路径**：`相对仓库根路径`
  **图片描述**：…
（可用 --content 传入描述正文；路径由脚本写入。）

用法（在仓库根执行）：
  python skills/aws-wechat-article-assets/scripts/stock_image_ingest.py path/to/a.png --stem 淘米
  python skills/aws-wechat-article-assets/scripts/stock_image_ingest.py a.png --stem 淘米 --content "双手在盆中淘米，水清米白。"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

INVALID_NAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def _err(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _find_repo_root(start: Path) -> Path:
    """仓库根 = `--repo` 参数指向的目录（默认当前工作目录）。

    不再向上遍历父目录；若传入路径不是预期的仓库根（需要存在 `.aws-article` 或 `.git`），
    直接报错退出，避免对非预期目录进行读写。
    """
    cur = start.resolve()
    if not cur.is_dir():
        _err(f"指定的仓库根不是目录：{cur}")
    if (cur / ".aws-article").is_dir() or (cur / ".git").is_dir():
        return cur
    _err(
        f"{cur} 不像仓库根（未检测到 .aws-article 或 .git 目录）。\n"
        "请传入 --repo 指向真正的仓库根，或在仓库根下运行。"
    )


def _ensure_aws_article_dir(repo: Path) -> None:
    (repo / ".aws-article").mkdir(parents=True, exist_ok=True)


def _sanitize_stem(stem: str) -> str:
    s = (stem or "").strip()
    s = INVALID_NAME_CHARS.sub("", s)
    s = s.strip(" .")
    if not s:
        s = "未命名素材"
    return s[:120]


def _unique_dest_paths(dest_dir: Path, stem: str, ext: str) -> tuple[Path, str]:
    """返回 (图片路径, 实际主文件名不含扩展名)。重名时 淘米 → 淘米2 → 淘米3…"""
    ext = ext if ext.startswith(".") else f".{ext}"
    ext = ext.lower()
    base = _sanitize_stem(stem)
    names = [base] + [f"{base}{i}" for i in range(2, 10001)]
    for name in names:
        img = dest_dir / f"{name}{ext}"
        md = dest_dir / f"{name}.md"
        if not img.exists() and not md.exists():
            return img, name
    _err("无法分配唯一文件名（重试次数过多）。")


def main() -> None:
    parser = argparse.ArgumentParser(description="用户图片入库：中文名 + 同主文件名 .md（图片描述）")
    parser.add_argument("source", help="源图片路径")
    parser.add_argument("--stem", required=True, help="中文主文件名（不含扩展名），由分析内容决定")
    parser.add_argument(
        "--content",
        default="",
        help="写入同名 .md 的正文（纯中文图片描述）；默认写入一行占位提示，由智能体读图后替换",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="仓库根目录（默认当前目录）",
    )
    args = parser.parse_args()

    src = Path(args.source).resolve()
    if not src.is_file():
        _err(f"源文件不存在: {src}")

    suffix = src.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        _err(f"不支持的图片扩展名: {suffix}（允许 png/jpg/jpeg/webp/gif）")

    repo = _find_repo_root(Path(args.repo))
    _ensure_aws_article_dir(repo)
    dest_dir = repo / ".aws-article" / "assets" / "stock" / "images"
    dest_dir.mkdir(parents=True, exist_ok=True)

    img_path, final_stem = _unique_dest_paths(dest_dir, args.stem, suffix)
    shutil.copy2(src, img_path)

    rel_posix = img_path.relative_to(repo).as_posix()
    md_path = dest_dir / f"{final_stem}.md"
    path_line = f"**图片路径**：`{rel_posix}`\n\n"
    if (args.content or "").strip():
        body = path_line + "**图片描述**：" + (args.content or "").strip() + "\n"
    else:
        body = path_line + "**图片描述**：请根据图片补全（客观描述画面内容即可）。\n"
    md_path.write_text(body, encoding="utf-8")

    _ok(f"图片: {img_path}")
    _ok(f"图片描述: {md_path}")


if __name__ == "__main__":
    main()
