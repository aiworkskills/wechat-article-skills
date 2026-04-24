#!/usr/bin/env python3
"""
将用户上传的图片复制到业务配图库 `.aws-article/products/{产品名}/images/`，
按中文主文件名保存；重名时自动使用 原名2、原名3… 后缀（扩展名前）。

`products/{产品名}/` 是用户业务的资料库根；本脚本仅写入其 `images/` 子目录
（业务介绍 .md 直挂产品根，由 AI 用 Write 工具落库，不走本脚本）。

运行前若缺少 `.aws-article`（仅含 `.git` 的仓库根也会识别）则创建；
产品目录与 `images/` 子目录不存在时一并创建。

与图片同主文件名、扩展名为 `.md` 的说明文件一并生成，固定两行标签（全角冒号）：
  **图片路径**：`相对仓库根路径`
  **图片描述**：…
（可用 --content 传入描述正文；路径由脚本写入。）

用法（在仓库根执行）：
  python skills/aws-wechat-article-assets/scripts/product_image_ingest.py path/to/a.png \
    --product 公众号AI运营助手 --stem 配置首页
  python skills/aws-wechat-article-assets/scripts/product_image_ingest.py a.png \
    --product 公众号AI运营助手 --stem 配置首页 --content "aiworkskills.cn 配置平台首页。"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

INVALID_NAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')
PRODUCTS_BASE_REL = Path(".aws-article") / "products"


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


def _sanitize_name(name: str, fallback: str) -> str:
    s = (name or "").strip()
    s = INVALID_NAME_CHARS.sub("", s)
    s = s.strip(" .")
    if not s:
        s = fallback
    return s[:120]


def _unique_dest_paths(dest_dir: Path, stem: str, ext: str) -> tuple[Path, str]:
    """返回 (图片路径, 实际主文件名不含扩展名)。重名时 配置首页 → 配置首页2 → …"""
    ext = ext if ext.startswith(".") else f".{ext}"
    ext = ext.lower()
    base = _sanitize_name(stem, "未命名素材")
    names = [base] + [f"{base}{i}" for i in range(2, 10001)]
    for name in names:
        img = dest_dir / f"{name}{ext}"
        md = dest_dir / f"{name}.md"
        if not img.exists() and not md.exists():
            return img, name
    _err("无法分配唯一文件名（重试次数过多）。")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="业务图入库：写到 .aws-article/products/{产品名}/images/，含同名 .md（图片描述）"
    )
    parser.add_argument("source", help="源图片路径")
    parser.add_argument(
        "--product",
        required=True,
        help="产品名（业务资料库根目录名，如「公众号AI运营助手」）；不存在时自动创建",
    )
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

    product = _sanitize_name(args.product, "")
    if not product:
        _err("--product 不能为空（清洗后为空字符串）")

    repo = _find_repo_root(Path(args.repo))
    _ensure_aws_article_dir(repo)
    dest_dir = repo / PRODUCTS_BASE_REL / product / "images"
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
