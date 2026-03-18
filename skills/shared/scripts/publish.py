#!/usr/bin/env python3
"""
微信公众号发布工具

支持通过微信公众号 API 完成：上传图片、创建草稿、发布、查询状态。

凭证从 config.yaml 读取（wechat_appid / wechat_appsecret 字段）。
配置查找顺序：项目 .aws-article/config.yaml → 用户 ~/.aws-article/config.yaml

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
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_API_BASE = "https://api.weixin.qq.com/cgi-bin"
API_BASE = DEFAULT_API_BASE  # 运行时从 config 覆盖


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


# ── 图片压缩 ────────────────────────────────────────────────

def _compress_image(image_path: str, max_bytes: int, for_content: bool = False) -> str:
    """压缩图片到指定大小以内，返回压缩后的路径（可能是临时文件）。

    封面/永久素材：max 10MB
    正文图片：max 1MB
    """
    path = Path(image_path)
    size = path.stat().st_size
    if size <= max_bytes:
        return image_path

    _info(f"图片 {path.name} ({size/1024:.0f}KB) 超过限制 ({max_bytes/1024:.0f}KB)，压缩中...")

    try:
        from PIL import Image
    except ImportError:
        _info("未安装 Pillow，跳过压缩（pip install Pillow）")
        return image_path

    img = Image.open(path)
    if img.mode == "RGBA":
        img = img.convert("RGB")

    compressed_path = path.parent / f"{path.stem}_compressed.jpg"

    quality = 85
    while quality >= 20:
        img.save(compressed_path, "JPEG", quality=quality, optimize=True)
        if compressed_path.stat().st_size <= max_bytes:
            new_size = compressed_path.stat().st_size
            _ok(f"压缩完成: {new_size/1024:.0f}KB (quality={quality})")
            return str(compressed_path)
        quality -= 10

    max_dim = 1920 if not for_content else 1080
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img.save(compressed_path, "JPEG", quality=60, optimize=True)
    new_size = compressed_path.stat().st_size
    _ok(f"压缩+缩放完成: {new_size/1024:.0f}KB")
    return str(compressed_path)


THUMB_MAX_BYTES = 10 * 1024 * 1024    # 封面 10MB
CONTENT_MAX_BYTES = 1 * 1024 * 1024   # 正文 1MB


# ── 上传图片 ────────────────────────────────────────────────

def upload_thumb(token: str, image_path: str) -> dict:
    """上传封面图为永久素材，返回 {media_id, url}。自动压缩到 10MB 以内。"""
    image_path = _compress_image(image_path, THUMB_MAX_BYTES)
    url = f"{API_BASE}/material/add_material?access_token={token}&type=image"
    data = _upload_file(url, image_path, field_name="media")
    if "media_id" not in data:
        _err(f"上传封面图失败: {data}")
    return {"media_id": data["media_id"], "url": data.get("url", "")}


def upload_content_image(token: str, image_path: str) -> str:
    """上传正文内图片，返回可在正文中使用的 URL。自动压缩到 1MB 以内。"""
    image_path = _compress_image(image_path, CONTENT_MAX_BYTES, for_content=True)
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


# ── 配置读取 ────────────────────────────────────────────────

def _load_config() -> dict:
    """按优先级查找并读取 config.yaml。"""
    import yaml

    candidates = [
        Path(".aws-article/config.yaml"),
        Path.home() / ".aws-article" / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            _info(f"读取配置: {p}")
            return cfg

    _err(
        "未找到 config.yaml，请在以下位置创建：\n"
        "  项目级: .aws-article/config.yaml\n"
        "  用户级: ~/.aws-article/config.yaml\n"
        "参考示例: .aws-article/config.example.yaml"
    )


def _resolve_account(cfg: dict, account_alias: str = None) -> dict:
    """解析账号凭证，支持多账号。

    config.yaml 单账号格式：
        wechat_appid: xxx
        wechat_appsecret: xxx

    config.yaml 多账号格式：
        wechat_accounts:
          - name: 主号
            alias: main
            default: true
            appid: xxx
            appsecret: xxx
          - name: 副号
            alias: sub
            appid: xxx
            appsecret: xxx
    """
    accounts = cfg.get("wechat_accounts", [])

    if not accounts:
        appid = cfg.get("wechat_appid", "")
        appsecret = cfg.get("wechat_appsecret", "")
        if not appid or not appsecret:
            _err(
                "config.yaml 中缺少微信凭证。\n"
                "单账号：\n"
                "  wechat_appid: 你的AppID\n"
                "  wechat_appsecret: 你的AppSecret\n"
                "多账号：\n"
                "  wechat_accounts:\n"
                "    - name: 账号名\n"
                "      alias: main\n"
                "      appid: xxx\n"
                "      appsecret: xxx"
            )
        return {"name": "default", "appid": appid, "appsecret": appsecret}

    if account_alias:
        for acc in accounts:
            if acc.get("alias") == account_alias or acc.get("name") == account_alias:
                _info(f"使用账号: {acc.get('name', account_alias)}")
                return acc
        _err(f"未找到账号 '{account_alias}'，可用：{', '.join(a.get('alias', a.get('name', '?')) for a in accounts)}")

    if len(accounts) == 1:
        _info(f"使用账号: {accounts[0].get('name', '默认')}")
        return accounts[0]

    for acc in accounts:
        if acc.get("default"):
            _info(f"使用默认账号: {acc.get('name', '默认')}")
            return acc

    _info("多个账号可用，请用 --account 指定：")
    for acc in accounts:
        alias = acc.get("alias", "")
        name = acc.get("name", "")
        print(f"  --account {alias}  ({name})")
    _err("请指定账号")


def _get_credentials(account_alias: str = None) -> tuple[str, str]:
    """获取凭证。"""
    cfg = _load_config()
    acc = _resolve_account(cfg, account_alias)
    appid = acc.get("appid", acc.get("wechat_appid", ""))
    appsecret = acc.get("appsecret", acc.get("wechat_appsecret", ""))
    if not appid or not appsecret:
        _err(f"账号 '{acc.get('name', '?')}' 缺少 appid 或 appsecret")
    return appid, appsecret


# ── CLI ─────────────────────────────────────────────────────

_cli_account: str | None = None

def _init_api_base():
    """从 config 加载自定义 API 基础地址（用于固定 IP 转发代理）。"""
    global API_BASE
    try:
        cfg = _load_config()
    except SystemExit:
        return
    # 单账号：wechat_api_base
    # 多账号：当前账号的 api_base
    acc = _resolve_account(cfg, _cli_account) if _cli_account or cfg.get("wechat_accounts") else {}
    api_base = acc.get("api_base", "") or cfg.get("wechat_api_base", "")
    if api_base:
        API_BASE = api_base.rstrip("/")
        _info(f"API 端点: {API_BASE}")

def _get_token() -> str:
    _init_api_base()
    appid, appsecret = _get_credentials(_cli_account)
    return get_access_token(appid, appsecret)


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--account", help="指定账号（多账号时使用 alias 或 name）")
    sub = parser.add_subparsers(dest="command", help="子命令")

    sub.add_parser("token", help="获取 access_token")

    p_thumb = sub.add_parser("upload-thumb", help="上传封面图（永久素材，自动压缩）")
    p_thumb.add_argument("image", help="图片路径")

    p_img = sub.add_parser("upload-content-image", help="上传正文图片（自动压缩）")
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

    sub.add_parser("accounts", help="列出配置的账号")
    sub.add_parser("check", help="检查发布环境")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    global _cli_account
    _cli_account = args.account

    if args.command == "accounts":
        cfg = _load_config()
        accounts = cfg.get("wechat_accounts", [])
        if not accounts:
            appid = cfg.get("wechat_appid", "")
            print(f"单账号模式: appid={appid[:8]}..." if appid else "未配置账号")
        else:
            print(f"已配置 {len(accounts)} 个账号：")
            for acc in accounts:
                default_mark = " ⭐" if acc.get("default") else ""
                print(f"  {acc.get('alias', '?')} ({acc.get('name', '?')}){default_mark}")
        return

    if args.command == "check":
        _run_checks()
        return

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


def _run_checks():
    """检查发布环境。"""
    print("=== 发布环境检查 ===\n")
    issues = []

    # 1. config.yaml
    try:
        cfg = _load_config()
        _ok("config.yaml 找到")
    except SystemExit:
        print("❌ config.yaml 未找到")
        issues.append("创建 .aws-article/config.yaml")
        cfg = {}

    # 2. 微信凭证
    appid = cfg.get("wechat_appid", "")
    accounts = cfg.get("wechat_accounts", [])
    if accounts:
        _ok(f"多账号配置: {len(accounts)} 个账号")
        for acc in accounts:
            aid = acc.get("appid", "")
            asecret = acc.get("appsecret", "")
            name = acc.get("name", acc.get("alias", "?"))
            if aid and asecret:
                _ok(f"  {name}: 凭证已配置")
            else:
                print(f"  ❌ {name}: 缺少 appid 或 appsecret")
                issues.append(f"补充账号 {name} 的凭证")
    elif appid:
        appsecret = cfg.get("wechat_appsecret", "")
        if appsecret:
            _ok("微信凭证已配置")
        else:
            print("❌ 缺少 wechat_appsecret")
            issues.append("在 config.yaml 中添加 wechat_appsecret")
    else:
        print("⚠️  未配置微信凭证（如不需要 API 发布可忽略）")

    # 3. API 连通性（如有凭证）
    if appid and cfg.get("wechat_appsecret"):
        try:
            token = get_access_token(appid, cfg["wechat_appsecret"])
            _ok(f"API 连通正常 (token: {token[:16]}...)")
        except Exception as e:
            print(f"❌ API 连通失败: {e}")
            issues.append("检查 appid/appsecret 是否正确，IP 是否在白名单中")

    # 4. Python yaml
    try:
        import yaml
        _ok("PyYAML 已安装")
    except ImportError:
        print("❌ PyYAML 未安装")
        issues.append("pip install pyyaml")

    # 5. Pillow（图片压缩）
    try:
        from PIL import Image
        _ok("Pillow 已安装（图片压缩可用）")
    except ImportError:
        print("⚠️  Pillow 未安装（图片压缩不可用，大图上传可能失败）")
        issues.append("建议安装: pip install Pillow")

    # 6. 图片模型配置
    img_model = cfg.get("image_model", {})
    if img_model.get("api_key"):
        _ok(f"图片生成模型已配置: {img_model.get('model', '?')}")
    else:
        print("⚠️  图片生成模型未配置（如不需要 AI 生图可忽略）")

    # 7. 写作模型配置
    write_model = cfg.get("writing_model", {})
    if write_model.get("api_key"):
        _ok(f"写作模型已配置: {write_model.get('model', '?')}")
    else:
        print("⚠️  写作模型未配置（如不需要第三方模型写稿可忽略）")

    print("\n=== 检查完成 ===")
    if issues:
        print(f"\n需要处理的问题（{len(issues)} 个）：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        _ok("所有检查通过，可以发布！")


if __name__ == "__main__":
    main()
