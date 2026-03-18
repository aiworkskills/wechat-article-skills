#!/usr/bin/env python3
"""
微信公众号发布工具

支持通过微信公众号 API 完成：上传图片、创建草稿、发布、查询状态。

环境变量：
    WECHAT_APPID       公众号 AppID
    WECHAT_APPSECRET   公众号 AppSecret

用法：
    python publish.py token                           获取 access_token
    python publish.py upload-thumb <image_path>       上传封面图（永久素材）
    python publish.py upload-content-image <image>    上传正文图片
    python publish.py create-draft <article.yaml>     从 YAML 创建草稿
    python publish.py publish <media_id>              发布草稿
    python publish.py status <publish_id>             查询发布状态
    python publish.py full <article_dir>              一键全流程
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.weixin.qq.com/cgi-bin"


def _err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"✅ {msg}")


def _info(msg: str):
    print(f"ℹ️  {msg}")


# ── access_token ────────────────────────────────────────────

def get_access_token(appid: str, appsecret: str) -> str:
    """获取 access_token（有效期 2 小时）。"""
    url = (
        f"{API_BASE}/token?"
        f"grant_type=client_credential&appid={appid}&secret={appsecret}"
    )
    data = _api_get(url)
    if "access_token" not in data:
        _err(f"获取 access_token 失败: {data}")
    return data["access_token"]


# ── 上传图片 ────────────────────────────────────────────────

def upload_thumb(token: str, image_path: str) -> dict:
    """上传封面图为永久素材，返回 {media_id, url}。"""
    url = f"{API_BASE}/material/add_material?access_token={token}&type=image"
    data = _upload_file(url, image_path, field_name="media")
    if "media_id" not in data:
        _err(f"上传封面图失败: {data}")
    return {"media_id": data["media_id"], "url": data.get("url", "")}


def upload_content_image(token: str, image_path: str) -> str:
    """上传正文内图片，返回可在正文中使用的 URL。"""
    url = f"{API_BASE}/media/uploadimg?access_token={token}"
    data = _upload_file(url, image_path, field_name="media")
    if "url" not in data:
        _err(f"上传正文图片失败: {data}")
    return data["url"]


# ── 草稿 ────────────────────────────────────────────────────

def create_draft(token: str, articles: list[dict]) -> str:
    """创建草稿，返回 media_id。

    articles 中每个元素包含：
        title, content, thumb_media_id,
        author(可选), digest(可选),
        content_source_url(可选),
        need_open_comment(可选, 0/1),
        only_fans_can_comment(可选, 0/1)
    """
    url = f"{API_BASE}/draft/add?access_token={token}"
    body = {"articles": articles}
    data = _api_post_json(url, body)
    if "media_id" not in data:
        _err(f"创建草稿失败: {data}")
    return data["media_id"]


# ── 发布 ────────────────────────────────────────────────────

def publish_draft(token: str, media_id: str) -> str:
    """发布草稿（异步），返回 publish_id。"""
    url = f"{API_BASE}/freepublish/submit?access_token={token}"
    data = _api_post_json(url, {"media_id": media_id})
    if "publish_id" not in data:
        _err(f"提交发布失败: {data}")
    return data["publish_id"]


def get_publish_status(token: str, publish_id: str) -> dict:
    """查询发布状态。

    返回 publish_status:
        0=成功, 1=发布中, 2=原创失败, 3=常规失败,
        4=审核不通过, 5=已删除, 6=已封禁
    """
    url = f"{API_BASE}/freepublish/get?access_token={token}"
    return _api_post_json(url, {"publish_id": publish_id})


# ── 全流程 ──────────────────────────────────────────────────

def full_publish(token: str, article_dir: str, do_publish: bool = False):
    """一键全流程：读取文章目录 → 上传图片 → 创建草稿 → 可选发布。

    文章目录结构：
        article_dir/
        ├── article.yaml    文章元信息（title, author, digest 等）
        ├── content.html    排版后的正文 HTML
        ├── cover.jpg       封面图
        └── images/         正文内图片（可选）
            ├── img1.png
            └── img2.jpg
    """
    article_dir = Path(article_dir)

    meta_path = article_dir / "article.yaml"
    if not meta_path.exists():
        _err(f"未找到 {meta_path}")

    import yaml  # lazy import，仅全流程需要
    with open(meta_path, encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    content_path = article_dir / "content.html"
    if not content_path.exists():
        _err(f"未找到 {content_path}")
    content = content_path.read_text(encoding="utf-8")

    # 上传封面
    cover_path = _find_file(article_dir, ["cover.jpg", "cover.png", "cover.jpeg", "cover.webp"])
    if not cover_path:
        _err("未找到封面图（cover.jpg/png/jpeg/webp）")
    _info(f"上传封面图: {cover_path}")
    thumb = upload_thumb(token, str(cover_path))
    _ok(f"封面图上传成功: media_id={thumb['media_id']}")

    # 上传正文图片并替换路径
    images_dir = article_dir / "images"
    if images_dir.exists():
        for img_file in sorted(images_dir.iterdir()):
            if img_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                _info(f"上传正文图片: {img_file.name}")
                img_url = upload_content_image(token, str(img_file))
                content = content.replace(f"images/{img_file.name}", img_url)
                content = content.replace(img_file.name, img_url)
                _ok(f"  → {img_url}")

    # 构建草稿
    article = {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "digest": meta.get("digest", ""),
        "content": content,
        "thumb_media_id": thumb["media_id"],
        "content_source_url": meta.get("content_source_url", ""),
        "need_open_comment": meta.get("need_open_comment", 0),
        "only_fans_can_comment": meta.get("only_fans_can_comment", 0),
    }
    _info("创建草稿...")
    media_id = create_draft(token, [article])
    _ok(f"草稿创建成功: media_id={media_id}")

    # 可选发布
    if do_publish:
        _info("提交发布...")
        publish_id = publish_draft(token, media_id)
        _ok(f"发布任务已提交: publish_id={publish_id}")
        _info("等待发布结果（异步，轮询中）...")
        _poll_publish_status(token, publish_id)
    else:
        _info("草稿已创建，未发布。如需发布：")
        print(f"  python publish.py publish {media_id}")

    return media_id


def _poll_publish_status(token: str, publish_id: str, max_wait: int = 60):
    """轮询发布状态，最多等待 max_wait 秒。"""
    status_map = {
        0: "✅ 发布成功",
        1: "⏳ 发布中",
        2: "❌ 原创失败",
        3: "❌ 常规失败",
        4: "❌ 平台审核不通过",
        5: "❌ 已删除",
        6: "❌ 已封禁",
    }
    start = time.time()
    while time.time() - start < max_wait:
        result = get_publish_status(token, publish_id)
        status = result.get("publish_status", -1)
        print(f"  状态: {status_map.get(status, f'未知({status})')}")
        if status != 1:
            return result
        time.sleep(3)
    _info(f"已等待 {max_wait}s，发布仍在进行中。可稍后查询：")
    print(f"  python publish.py status {publish_id}")


# ── HTTP 工具 ───────────────────────────────────────────────

def _api_get(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _api_post_json(url: str, body: dict) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _upload_file(url: str, file_path: str, field_name: str = "media") -> dict:
    """multipart/form-data 文件上传（纯标准库实现）。"""
    boundary = f"----WechatPublish{int(time.time() * 1000)}"
    file_path = Path(file_path)
    if not file_path.exists():
        _err(f"文件不存在: {file_path}")

    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    file_data = file_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; '
        f'filename="{file_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _find_file(directory: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        p = directory / name
        if p.exists():
            return p
    return None


# ── CLI ─────────────────────────────────────────────────────

def _get_credentials() -> tuple[str, str]:
    appid = os.environ.get("WECHAT_APPID", "")
    appsecret = os.environ.get("WECHAT_APPSECRET", "")
    if not appid or not appsecret:
        _err(
            "请设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET\n"
            "  export WECHAT_APPID=your_appid\n"
            "  export WECHAT_APPSECRET=your_appsecret"
        )
    return appid, appsecret


def _get_token() -> str:
    appid, appsecret = _get_credentials()
    return get_access_token(appid, appsecret)


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    sub.add_parser("token", help="获取 access_token")

    p_thumb = sub.add_parser("upload-thumb", help="上传封面图（永久素材）")
    p_thumb.add_argument("image", help="图片路径")

    p_img = sub.add_parser("upload-content-image", help="上传正文图片")
    p_img.add_argument("image", help="图片路径")

    p_draft = sub.add_parser("create-draft", help="从 YAML 创建草稿")
    p_draft.add_argument("article_yaml", help="article.yaml 路径")

    p_pub = sub.add_parser("publish", help="发布草稿")
    p_pub.add_argument("media_id", help="草稿 media_id")

    p_status = sub.add_parser("status", help="查询发布状态")
    p_status.add_argument("publish_id", help="发布任务 publish_id")

    p_full = sub.add_parser("full", help="一键全流程")
    p_full.add_argument("article_dir", help="文章目录路径")
    p_full.add_argument("--publish", action="store_true", help="创建草稿后立即发布")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "token":
        token = _get_token()
        _ok(f"access_token: {token[:20]}...")
        print(token)

    elif args.command == "upload-thumb":
        token = _get_token()
        result = upload_thumb(token, args.image)
        _ok(f"media_id: {result['media_id']}")
        _ok(f"url: {result['url']}")

    elif args.command == "upload-content-image":
        token = _get_token()
        url = upload_content_image(token, args.image)
        _ok(f"url: {url}")

    elif args.command == "create-draft":
        token = _get_token()
        import yaml
        with open(args.article_yaml, encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        articles = meta.get("articles", [meta])
        media_id = create_draft(token, articles)
        _ok(f"草稿 media_id: {media_id}")

    elif args.command == "publish":
        token = _get_token()
        publish_id = publish_draft(token, args.media_id)
        _ok(f"publish_id: {publish_id}")
        _poll_publish_status(token, publish_id)

    elif args.command == "status":
        token = _get_token()
        result = get_publish_status(token, args.publish_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "full":
        token = _get_token()
        full_publish(token, args.article_dir, do_publish=args.publish)


if __name__ == "__main__":
    main()
