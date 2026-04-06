#!/usr/bin/env python3
"""
微信公众号发布工具（skills/aws-wechat-article-publish/scripts/publish.py）

- check-screening：校验仓库 **`.aws-article/config.yaml`** 的 **`publish_method`**（`draft` / `published` / `none`）。
- 其余子命令：token、上传、草稿、发布、一键 full 等。

**publish_method**（`config.yaml` 顶层）：
  - **`draft`**（默认）：`full` 仅 **创建草稿**（进公众号草稿箱），不调用 freepublish 发出。
  - **`published`**：`full` 在创建草稿后 **提交发布**（异步）。命令行 `full --publish` 可**显式**强制带发布一步（即使当前为 draft）。
  - **`none`**：用户明确不填微信时写入；**`full` 直接退出**，不调任何微信接口；其它子命令（`token`、`create-draft` 等）仍须凭证，照常报错。

微信发布配置分工：
  - 仓库 **`.aws-article/config.yaml`**：`wechat_accounts`、`wechat_{i}_name`（1..N 槽位的数量与名称）
  - 仓库根 **`aws.env`**：`WECHAT_{i}_APPID`、`WECHAT_{i}_APPSECRET`、`WECHAT_{i}_API_BASE`（凭证与可选 API 基址）
  - `WECHAT_N_API_BASE` 可空（空则使用官方 https://api.weixin.qq.com）。

在仓库根执行示例：
    python skills/aws-wechat-article-publish/scripts/publish.py check-screening
    python skills/aws-wechat-article-publish/scripts/publish.py full path/to/article-dir/
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# base 仅域名；接口路径 /cgi-bin 拼在请求 URL 上
DEFAULT_API_BASE = "https://api.weixin.qq.com"
API_PATH = "/cgi-bin"
API_BASE = DEFAULT_API_BASE  # 运行时从 config 覆盖


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


# ── config.yaml（publish_method）──────────────────────────────

def _load_yaml_config(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        import yaml
    except ImportError:
        print("[ERROR] 需要 PyYAML：pip install pyyaml", file=sys.stderr)
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 无法解析 YAML（{path}）: {e}", file=sys.stderr)
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def errors_for_publish_method(data: dict) -> list[str]:
    """config.yaml 顶层的 publish_method：缺省视为 draft；有值则须为 draft | published | none。"""
    raw = data.get("publish_method")
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    pm = s.lower()
    if pm in ("draft", "published", "none"):
        return []
    return [f"publish_method 非法: {raw!r}，须为 draft、published 或 none"]


def cmd_check_screening(config_path: Path) -> int:
    """校验仓库 config.yaml 中的 publish_method（子命令名沿用 check-screening）。"""
    data = _load_yaml_config(config_path)
    if data is None:
        print(f"[ERROR] 未找到文件: {config_path.resolve()}", file=sys.stderr)
        return 1
    errs = errors_for_publish_method(data)
    if errs:
        print("[ERROR] config.yaml 中 publish_method 校验未通过：", file=sys.stderr)
        for line in errs:
            print(f"   - {line}", file=sys.stderr)
        return 1
    raw = data.get("publish_method")
    if raw is None or not str(raw).strip():
        print("[OK] publish_method 未设置（将按默认 draft：仅创建公众号草稿，不自动发布）")
    else:
        pm = str(raw).strip().lower()
        print(f"[OK] publish_method={pm} 合法")
        if pm == "draft":
            print("[INFO] draft：`full` 默认只进草稿箱；若要发出请改 published 或执行 full --publish")
        elif pm == "published":
            print(
                "[INFO] published：`full` 将在创建草稿后提交发布。微信凭证：aws.env；可运行 check-wechat-env"
            )
        elif pm == "none":
            print(
                "[INFO] none：`full` 将不调微信接口；其它子命令（token、create-draft 等）仍需要凭证"
            )
    return 0


def load_repo_config(config_path: Path | None = None) -> dict:
    """读取仓库 .aws-article/config.yaml；缺失或无效返回 {}。"""
    p = config_path if config_path is not None else Path(".aws-article/config.yaml")
    data = _load_yaml_config(p)
    if data is None or not isinstance(data, dict):
        return {}
    return data


def _parse_wechat_accounts_cfg(cfg: dict) -> int:
    raw = cfg.get("wechat_accounts")
    if raw is None or isinstance(raw, bool):
        return 0
    if isinstance(raw, int):
        return raw if raw >= 1 else 0
    s = str(raw).strip()
    if not s:
        return 0
    try:
        n = int(s)
    except ValueError:
        return 0
    return n if n >= 1 else 0


# ── access_token ────────────────────────────────────────────

def get_access_token(appid: str, appsecret: str) -> str:
    """获取 access_token（有效期 2 小时）。网络类失败会自动重试 1 次。"""
    url = (
        f"{API_BASE}{API_PATH}/token?"
        f"grant_type=client_credential&appid={appid}&secret={appsecret}"
    )
    data = _api_get(url)
    if "access_token" not in data:
        errcode = data.get("errcode")
        hint = ""
        if errcode in (40013, 40125, 40164, 89004):
            hint = "（多为 AppID/AppSecret 错误或 IP 未加白名单，请检查 aws.env 对应槽位）"
        elif errcode == 40001:
            hint = "（access_token 无效类错误，请核对凭证）"
        _err(f"获取 access_token 失败: {data}{hint}")
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
    url = f"{API_BASE}{API_PATH}/material/add_material?access_token={token}&type=image"
    data = _upload_file(url, image_path, field_name="media")
    if "media_id" not in data:
        _err(f"上传封面图失败: {data}")
    return {"media_id": data["media_id"], "url": data.get("url", "")}


def upload_content_image(token: str, image_path: str) -> str:
    """上传正文内图片，返回可在正文中使用的 URL。自动压缩到 1MB 以内。"""
    image_path = _compress_image(image_path, CONTENT_MAX_BYTES, for_content=True)
    url = f"{API_BASE}{API_PATH}/media/uploadimg?access_token={token}"
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
    url = f"{API_BASE}{API_PATH}/draft/add?access_token={token}"
    body = {"articles": articles}
    data = _api_post_json(url, body)
    if "media_id" not in data:
        _err(f"创建草稿失败: {data}")
    return data["media_id"]


# ── 发布 ────────────────────────────────────────────────────

def publish_draft(token: str, media_id: str) -> str:
    """发布草稿（异步），返回 publish_id。"""
    url = f"{API_BASE}{API_PATH}/freepublish/submit?access_token={token}"
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
    url = f"{API_BASE}{API_PATH}/freepublish/get?access_token={token}"
    return _api_post_json(url, {"publish_id": publish_id})


# ── 往期文章 ────────────────────────────────────────────────

def get_published_articles(token: str, offset: int = 0, count: int = 10,
                           no_content: bool = True) -> dict:
    """获取已发布的文章列表。

    Args:
        offset: 偏移位置，0 = 从最新开始
        count: 返回数量，1-20
        no_content: True = 不返回正文（省流量）
    """
    url = f"{API_BASE}{API_PATH}/freepublish/batchget?access_token={token}"
    body = {"offset": offset, "count": count, "no_content": 1 if no_content else 0}
    return _api_post_json(url, body)


def list_recent_articles(token: str, count: int = 10) -> list[dict]:
    """获取最近发布的文章，返回 [{title, url, update_time}]。"""
    result = get_published_articles(token, offset=0, count=count)
    articles = []
    for item in result.get("item", []):
        content = item.get("content", {})
        for art in content.get("news_item", []):
            articles.append({
                "title": art.get("title", ""),
                "url": art.get("url", ""),
                "digest": art.get("digest", ""),
                "update_time": item.get("update_time", ""),
            })
    return articles


# ── 全流程 ──────────────────────────────────────────────────

def full_publish(token: str, article_dir: str, do_publish: bool = False):
    """一键全流程：读取文章目录 → 上传图片 → 创建草稿 → 可选发布。

    文章目录结构：
        article_dir/
        ├── article.yaml    文章元信息（title, author, digest 等）
        ├── article.html    排版后的正文 HTML
        ├── cover.jpg       封面图
        └── imgs/           正文内图片（可选）
            ├── 01-xxx.png
            └── 02-xxx.jpg
    """
    article_dir = Path(article_dir)

    meta_path = article_dir / "article.yaml"
    if not meta_path.exists():
        _err(f"未找到 {meta_path}")

    import yaml  # lazy import，仅全流程需要
    with open(meta_path, encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    cfg = load_repo_config()
    author = (meta.get("author") or "").strip() or str(
        cfg.get("default_author") or ""
    ).strip()

    content_path = article_dir / "article.html"
    if not content_path.exists():
        _err(f"未找到 {content_path}")
    content = content_path.read_text(encoding="utf-8")

    # 上传封面（优先 article_dir/cover.*，fallback imgs/cover.* 和 imgs/*-cover.*）
    _cover_names = ["cover.jpg", "cover.png", "cover.jpeg", "cover.webp"]
    cover_path = _find_file(article_dir, _cover_names)
    if not cover_path:
        _imgs = article_dir / "imgs"
        if _imgs.is_dir():
            cover_path = _find_file(_imgs, _cover_names)
            if not cover_path:
                for _sfx in (".jpg", ".png", ".jpeg", ".webp"):
                    _cands = sorted(_imgs.glob(f"*-cover{_sfx}"))
                    if _cands:
                        cover_path = _cands[0]
                        break
    if not cover_path:
        _err("未找到封面图（cover.jpg/png/jpeg/webp）；支持 article_dir/ 或 imgs/ 下")
    _info(f"上传封面图: {cover_path}")
    thumb = upload_thumb(token, str(cover_path))
    _ok(f"封面图上传成功: media_id={thumb['media_id']}")

    # 上传正文图片并替换路径（仅上传 HTML 中实际引用的 imgs/ 文件）
    imgs_dir = article_dir / "imgs"
    if imgs_dir.exists():
        for fname in _content_image_refs_flat(content):
            img_file = imgs_dir / fname
            if not img_file.is_file():
                _err(f"正文引用了不存在的图片: imgs/{fname}")
            _info(f"上传正文图片: {img_file.name}")
            img_url = upload_content_image(token, str(img_file))
            content = content.replace(f"imgs/{img_file.name}", img_url)
            content = content.replace(img_file.name, img_url)
            _ok(f"  → {img_url}")

    if "tempkey=" in content or "tempkey%3D" in content:
        _err(
            "正文 HTML 仍含 tempkey 预览链（常见于 getdraft list-fields 返回的 url）。"
            "微信 draft/add 常因此返回 45166 invalid content。"
            "请改用已群发文章的永久链接（后台对该文「复制链接」），或从正文去掉相关超链后重试。"
        )

    # 构建草稿（author 优先 article.yaml，为空时用 config.yaml default_author）
    article = {
        "title": meta.get("title", ""),
        "author": author,
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
        print(
            "  python skills/aws-wechat-article-publish/scripts/publish.py publish "
            f"{media_id}"
        )

    return media_id


def _poll_publish_status(token: str, publish_id: str, max_wait: int = 60):
    """轮询发布状态，最多等待 max_wait 秒。"""
    status_map = {
        0: "[OK] 发布成功",
        1: "[INFO] 发布中",
        2: "[ERROR] 原创失败",
        3: "[ERROR] 常规失败",
        4: "[ERROR] 平台审核不通过",
        5: "[ERROR] 已删除",
        6: "[ERROR] 已封禁",
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
    print(
        "  python skills/aws-wechat-article-publish/scripts/publish.py status "
        f"{publish_id}"
    )


# ── HTTP 工具 ───────────────────────────────────────────────

def _is_transient_network_error(e: BaseException) -> bool:
    if isinstance(e, urllib.error.URLError):
        return True
    if isinstance(e, TimeoutError):
        return True
    if isinstance(e, urllib.error.HTTPError) and e.code >= 500:
        return True
    return False


def _api_get(url: str) -> dict:
    last: BaseException | None = None
    t_req, _ = _wechat_http_timeouts()
    for attempt in range(2):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=t_req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            last = e
            if attempt == 0 and _is_transient_network_error(e):
                _info("【网络】请求失败，1 秒后重试一次…")
                time.sleep(1)
                continue
            raise
    raise last  # pragma: no cover


def _api_post_json(url: str, body: dict) -> dict:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last: BaseException | None = None
    t_req, _ = _wechat_http_timeouts()
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=t_req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            last = e
            if attempt == 0 and _is_transient_network_error(e):
                _info("【网络】请求失败，1 秒后重试一次…")
                time.sleep(1)
                continue
            raise
    raise last  # pragma: no cover


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

    last: BaseException | None = None
    _, t_up = _wechat_http_timeouts()
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            with urllib.request.urlopen(req, timeout=t_up) as resp:
                return json.loads(resp.read())
        except Exception as e:
            last = e
            if attempt == 0 and _is_transient_network_error(e):
                _info("【网络】上传失败，1 秒后重试一次…")
                time.sleep(1)
                continue
            raise
    raise last  # pragma: no cover


def _find_file(directory: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        p = directory / name
        if p.exists():
            return p
    return None


def _content_image_refs_flat(html: str) -> list[str]:
    """从 article.html 中解析正文引用的 imgs/ 文件名（仅单层文件名，去重保序）。

    避免上传 imgs 目录下压缩缓存 *_compressed.jpg、prompts 子目录等未被引用的文件。
    """
    seen: set[str] = set()
    out: list[str] = []
    for m in re.finditer(r'imgs/([^"\'<>\s]+)', html, flags=re.IGNORECASE):
        name = m.group(1).strip()
        if not name or "/" in name or "\\" in name or ".." in name:
            continue
        low = name.lower()
        if not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


# ── 仓库根 aws.env ───────────────────────────────────────────

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
    path = _resolve_env_path()
    if not path.is_file():
        return {}
    try:
        return _parse_dotenv(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


# 微信 HTTP 超时（秒）：默认较原 30/60 放宽，慢代理或大图上传统计更稳
_DEFAULT_WECHAT_REQUEST_TIMEOUT = 60
_DEFAULT_WECHAT_UPLOAD_TIMEOUT = 120


def _wechat_http_timeouts() -> tuple[int, int]:
    """从仓库根 env 文件读取 (普通请求超时, 文件上传超时)，单位秒。"""
    env = _load_env_map()
    req = _DEFAULT_WECHAT_REQUEST_TIMEOUT
    up = _DEFAULT_WECHAT_UPLOAD_TIMEOUT
    raw_req = (env.get("WECHAT_REQUEST_TIMEOUT") or "").strip()
    if raw_req:
        try:
            req = max(5, int(raw_req))
        except ValueError:
            pass
    raw_up = (env.get("WECHAT_UPLOAD_TIMEOUT") or "").strip()
    if raw_up:
        try:
            up = max(10, int(raw_up))
        except ValueError:
            pass
    return req, up


def _wechat_slot_keys(i: int) -> tuple[str, str, str]:
    return (
        f"WECHAT_{i}_APPID",
        f"WECHAT_{i}_APPSECRET",
        f"WECHAT_{i}_API_BASE",
    )


def wechat_slot(cfg: dict, env: dict[str, str], i: int) -> dict:
    ak, sk, bk = _wechat_slot_keys(i)
    return {
        "slot": i,
        "name": str(cfg.get(f"wechat_{i}_name") or "").strip(),
        "appid": (env.get(ak) or "").strip(),
        "appsecret": (env.get(sk) or "").strip(),
        "api_base": (env.get(bk) or "").strip(),
    }


def missing_wechat_slot_fields(slot: dict) -> list[str]:
    """用于完整性提示：APPID、APPSECRET；API_BASE 可空。"""
    miss: list[str] = []
    if not slot["appid"]:
        miss.append("APPID")
    if not slot["appsecret"]:
        miss.append("APPSECRET")
    return miss


def list_wechat_slots(cfg: dict, env: dict[str, str]) -> list[dict]:
    n = _parse_wechat_accounts_cfg(cfg)
    return [wechat_slot(cfg, env, i) for i in range(1, n + 1)]


def cmd_check_wechat_env() -> int:
    """按 config.yaml 槽位检查 aws.env 中 WECHAT_N_APPID/APPSECRET 是否齐全。"""
    cfg = load_repo_config()
    env = _load_env_map()
    env_path = _resolve_env_path()
    if not env and not env_path.is_file():
        print("[ERROR] 未找到 aws.env（仓库根）", file=sys.stderr)
        return 1
    n = _parse_wechat_accounts_cfg(cfg)
    if n < 1:
        print("[ERROR] config.yaml 中 wechat_accounts 无效或未设置（须为 ≥1 的整数）", file=sys.stderr)
        return 1
    bad = False
    for slot in list_wechat_slots(cfg, env):
        miss = missing_wechat_slot_fields(slot)
        if miss:
            bad = True
            keys = ", ".join(f"WECHAT_{slot['slot']}_{m}" for m in miss)
            print(
                f"[ERROR] 第 {slot['slot']} 个微信账号未填完整：缺少 {', '.join(miss)}（{keys}）",
                file=sys.stderr,
            )
        else:
            _ok(
                f"槽位 {slot['slot']}: {slot['name'] or '(未命名)'} — APPID/SECRET 已填"
            )
    return 1 if bad else 0


# full 流程从 config.yaml wechat_publish_slot 写入的槽位（1..N），供 _get_credentials 使用
_draft_wechat_slot: int | None = None


def _resolve_slot_index(
    cfg: dict,
    env: dict[str, str],
    account_alias: str | None,
    preferred_slot: int | None,
) -> int:
    n = _parse_wechat_accounts_cfg(cfg)
    if n < 1:
        _err(
            "config.yaml 中 wechat_accounts 无效或未设置。\n"
            "请设置 wechat_accounts=1，并在 config.yaml 填写 wechat_1_name。"
        )
    # 命令行 --account 优先于 config.yaml 的 wechat_publish_slot
    if account_alias:
        s = str(account_alias).strip()
        if s.isdigit():
            si = int(s)
            if 1 <= si <= n:
                _info(f"使用 --account 指定槽位 {si}")
                return si
            _err(f"--account 槽位序号须在 1..{n} 之间")
        for i in range(1, n + 1):
            sl = wechat_slot(cfg, env, i)
            nm = sl["name"]
            if nm and (s == nm or s in nm):
                _info(f"使用名称匹配的槽位 {i}: {nm}")
                return i
        _err(
            f"未找到账号 '{account_alias}'。"
            f"请使用槽位序号 1..{n} 或 config.yaml 中 wechat_N_name 的展示名。"
        )
    if preferred_slot is not None:
        if 1 <= preferred_slot <= n:
            _info(f"使用 config.yaml 中的 wechat_publish_slot={preferred_slot}")
            return preferred_slot
        _err(
            f"config.yaml 中 wechat_publish_slot={preferred_slot} 超出范围，"
            f"当前 wechat_accounts={n}（有效 1..{n}）"
        )
    if n == 1:
        return 1
    _err(
        f"配置了 {n} 个微信槽位，请指定账号：\n"
        "  --account <1..N 或 wechat_N_name 子串>\n"
        "或在 .aws-article/config.yaml 中设置 wechat_publish_slot: <整数>"
    )


def _active_slot_dict(cfg: dict, env: dict[str, str], slot_index: int) -> dict:
    return wechat_slot(cfg, env, slot_index)


def _get_credentials(account_alias: str | None) -> tuple[str, str]:
    cfg = load_repo_config()
    env = _load_env_map()
    if not _resolve_env_path().is_file():
        _err(
            "未找到 aws.env。请在仓库根创建 aws.env，"
            "并填写 WECHAT_1_APPID、WECHAT_1_APPSECRET 等（见 .aws-article/env.example.yaml）。"
        )
    slot_i = _resolve_slot_index(cfg, env, account_alias, _draft_wechat_slot)
    slot = _active_slot_dict(cfg, env, slot_i)
    if not slot["appid"] or not slot["appsecret"]:
        miss = missing_wechat_slot_fields(slot)
        _err(
            f"第 {slot_i} 个账号缺少微信凭证（需 APPID、APPSECRET）。"
            f"缺: {', '.join(miss) if miss else 'APPID/APPSECRET'}\n"
            f"请补全 WECHAT_{slot_i}_APPID / WECHAT_{slot_i}_APPSECRET"
        )
    return slot["appid"], slot["appsecret"]


# ── CLI ─────────────────────────────────────────────────────

_cli_account: str | None = None


def _slot_for_api_base(cfg: dict, env: dict[str, str]) -> int | None:
    """不抛错；无法唯一确定槽位时返回 None。CLI --account 优先于 wechat_publish_slot。"""
    n = _parse_wechat_accounts_cfg(cfg)
    if n < 1:
        return None
    if _cli_account:
        s = str(_cli_account).strip()
        if s.isdigit():
            si = int(s)
            if 1 <= si <= n:
                return si
            return None
        for i in range(1, n + 1):
            sl = wechat_slot(cfg, env, i)
            nm = sl["name"]
            if nm and (s == nm or s in nm):
                return i
        return None
    if _draft_wechat_slot is not None and 1 <= _draft_wechat_slot <= n:
        return _draft_wechat_slot
    if n == 1:
        return 1
    return None


def _normalize_api_base(raw: str) -> str:
    api_base = raw.strip().rstrip("/")
    if api_base.endswith("/cgi-bin"):
        api_base = api_base[:-8].rstrip("/")
    return api_base


def _resolve_api_base(cfg: dict, slot: dict) -> str:
    """槽位 WECHAT_N_API_BASE 优先；为空时回退 config.yaml.wechat_api_base。"""
    slot_base = (slot.get("api_base") or "").strip()
    if slot_base:
        return _normalize_api_base(slot_base)
    cfg_base = str(cfg.get("wechat_api_base") or "").strip()
    if cfg_base:
        return _normalize_api_base(cfg_base)
    return ""


def _init_api_base():
    """优先用槽位 WECHAT_N_API_BASE；为空则回退 config.yaml.wechat_api_base。"""
    global API_BASE
    API_BASE = DEFAULT_API_BASE
    cfg = load_repo_config()
    env = _load_env_map()
    if not env:
        return
    slot_i = _slot_for_api_base(cfg, env)
    if slot_i is None:
        return
    slot = _active_slot_dict(cfg, env, slot_i)
    api_base = _resolve_api_base(cfg, slot)
    if not api_base:
        return
    API_BASE = api_base
    _info(f"API 端点: {API_BASE}{API_PATH}")

def _get_token() -> str:
    _init_api_base()
    appid, appsecret = _get_credentials(_cli_account)
    return get_access_token(appid, appsecret)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="微信公众号发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--account",
        help="微信槽位：填 1..N 或 config.yaml 中 wechat_N_name 的展示名",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_scr = sub.add_parser(
        "check-screening",
        help="校验仓库 .aws-article/config.yaml 中的 publish_method（draft / published / none）",
    )
    p_scr.add_argument(
        "--config",
        type=Path,
        default=Path(".aws-article/config.yaml"),
        metavar="FILE",
        help="默认 .aws-article/config.yaml",
    )

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

    sub.add_parser("accounts", help="列出 config.yaml 中的微信槽位与名称")
    sub.add_parser("check", help="检查发布环境（.env 微信槽位等）")
    sub.add_parser(
        "check-wechat-env",
        help="按 config.yaml 槽位检查 aws.env 的 WECHAT_N_APPID/APPSECRET 是否已填写",
    )

    p_recent = sub.add_parser("recent-articles", help="获取最近发布的文章")
    p_recent.add_argument("-n", "--count", type=int, default=5, help="数量（默认5）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    global _cli_account
    _cli_account = args.account

    if args.command == "check-screening":
        return cmd_check_screening(args.config)

    if args.command == "accounts":
        cfg = load_repo_config()
        env = _load_env_map()
        ep = _resolve_env_path()
        if not ep.is_file():
            print("[ERROR] 未找到 aws.env（仓库根）")
            return 1
        n = _parse_wechat_accounts_cfg(cfg)
        if n < 1:
            print("[ERROR] config.yaml 中 wechat_accounts 无效")
            return 1
        print(f"微信槽位（共 {n} 个，名称来自 config.yaml，凭证来自 {ep.name}）：")
        for i in range(1, n + 1):
            s = wechat_slot(cfg, env, i)
            miss = missing_wechat_slot_fields(s)
            mark = " [OK]" if not miss else f" [WARN] 缺: {','.join(miss)}"
            print(f"  {i}. {s['name'] or '(未命名)'}{mark}")
        return 0

    if args.command == "check-wechat-env":
        return cmd_check_wechat_env()

    if args.command == "check":
        _run_checks()
        return 0

    if args.command == "recent-articles":
        token = _get_token()
        articles = list_recent_articles(token, count=args.count)
        if not articles:
            _info("暂无已发布文章")
        else:
            print(f"最近 {len(articles)} 篇已发布文章：\n")
            for i, art in enumerate(articles, 1):
                print(f"  {i}. {art['title']}")
                print(f"     {art['url']}")
                print()
        return 0

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

        ay = Path(args.article_yaml)
        with open(ay, encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        default_author = str(load_repo_config().get("default_author") or "").strip()
        articles = meta.get("articles", [meta])
        for art in articles:
            if not (art.get("author") or "").strip():
                art["author"] = default_author
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
        global _draft_wechat_slot
        ad = Path(args.article_dir)
        _draft_wechat_slot = None
        cfg = load_repo_config()
        pe = errors_for_publish_method(cfg)
        if pe:
            for line in pe:
                print(f"[ERROR] {line}", file=sys.stderr)
            return 1
        pm = str(cfg.get("publish_method") or "draft").strip().lower() or "draft"
        if pm == "none":
            if args.publish:
                _info("已忽略 --publish：config.yaml 中 publish_method 为 none。")
            _info("publish_method: none — 不调用微信 API，不执行发布或草稿上传。")
            _ok("已按配置跳过 publish.py full（可继续本地写稿/排版等）")
            return 0
        if pm not in ("draft", "published"):
            print(
                f"[ERROR] config.yaml 中 publish_method 须为 draft、published 或 none，当前: {pm!r}",
                file=sys.stderr,
            )
            return 1
        do_publish = bool(args.publish) or (pm == "published")
        ws = cfg.get("wechat_publish_slot")
        if ws is not None and str(ws).strip() != "":
            try:
                _draft_wechat_slot = int(ws)
            except (TypeError, ValueError):
                print(
                    "[ERROR] config.yaml 中 wechat_publish_slot 须为整数",
                    file=sys.stderr,
                )
                return 1
        try:
            token = _get_token()
            full_publish(token, args.article_dir, do_publish=do_publish)
        finally:
            _draft_wechat_slot = None

    return 0


def _run_checks():
    """检查发布环境（aws.env 微信槽位、依赖等）。"""
    print("=== 发布环境检查 ===\n")
    issues: list[str] = []
    cfg = load_repo_config()
    n_cfg = _parse_wechat_accounts_cfg(cfg)

    ep = _resolve_env_path()
    if not ep.is_file():
        print("[ERROR] 未找到 aws.env（仓库根）")
        issues.append("在仓库根创建 aws.env（见 .aws-article/env.example.yaml）")
        env = {}
    else:
        _ok(f"环境文件找到: {ep.resolve()}")
        env = _load_env_map()
    if n_cfg < 1:
        print("[ERROR] config.yaml 中 wechat_accounts 无效")
        issues.append("在 config.yaml 中设置 wechat_accounts=1（或更多）")
    else:
        for i in range(1, n_cfg + 1):
            s = wechat_slot(cfg, env, i)
            if not s["name"]:
                print(f"  [ERROR] 槽位 {i}: config.yaml 缺少 wechat_{i}_name")
                issues.append(f"补全 config.yaml: wechat_{i}_name")
            miss = missing_wechat_slot_fields(s)
            if miss:
                print(f"  [ERROR] 槽位 {i} ({s['name'] or '未命名'}): 缺少 {', '.join(miss)}")
                keys = ", ".join(f"WECHAT_{i}_{m}" for m in miss)
                issues.append(f"补全 aws.env 槽位 {i}: {keys}")
            elif s["name"]:
                _ok(f"  槽位 {i} ({s['name']}): APPID/SECRET 已填")
            else:
                _ok(f"  槽位 {i}: APPID/SECRET 已填")

    # API 连通性：用第一个 APPID+SECRET 齐全的槽位探测
    probe_i: int | None = None
    for i in range(1, n_cfg + 1):
        s = wechat_slot(cfg, env, i)
        if s["appid"] and s["appsecret"]:
            probe_i = i
            break
    if probe_i is not None:
        s = wechat_slot(cfg, env, probe_i)
        global API_BASE
        API_BASE = DEFAULT_API_BASE
        api_base = _resolve_api_base(cfg, s)
        if api_base:
            API_BASE = api_base
        try:
            url = (
                f"{API_BASE}{API_PATH}/token?"
                f"grant_type=client_credential&appid={s['appid']}&secret={s['appsecret']}"
            )
            data = _api_get(url)
            if "access_token" in data:
                tok = data["access_token"]
                _ok(f"API 连通正常（槽位 {probe_i}，token: {tok[:16]}...）")
            else:
                print(f"[ERROR] 微信接口返回: {data}")
                issues.append(
                    f"槽位 {probe_i} 凭证或白名单有误（见 errcode/errmsg），请检查 .env"
                )
        except Exception as e:
            print(f"[ERROR] API 连通失败: {e}")
            issues.append("网络异常或微信接口不可用，可稍后重试")

    try:
        import yaml
        _ok("PyYAML 已安装")
    except ImportError:
        print("[ERROR] PyYAML 未安装")
        issues.append("pip install pyyaml")

    try:
        from PIL import Image
        _ok("Pillow 已安装（图片压缩可用）")
    except ImportError:
        print("[WARN] Pillow 未安装（大图上传可能失败）")
        issues.append("建议: pip install Pillow")

    # 写作 / 生图（与 validate_env 一致：config.yaml 的 *_model + aws.env 的 API Key）
    wm = cfg.get("writing_model")
    w_ok = (
        isinstance(wm, dict)
        and all((str(wm.get(k) or "").strip() for k in ("provider", "base_url", "model")))
        and bool((env.get("WRITING_MODEL_API_KEY") or "").strip())
    )
    im = cfg.get("image_model")
    i_ok = (
        isinstance(im, dict)
        and all((str(im.get(k) or "").strip() for k in ("provider", "base_url", "model")))
        and bool((env.get("IMAGE_MODEL_API_KEY") or "").strip())
    )
    if w_ok:
        _ok("写作模型已配置（config.yaml writing_model + aws.env WRITING_MODEL_API_KEY）")
    else:
        print("[WARN] 写作模型未齐（不影响纯发布，写稿需 config writing_model + WRITING_MODEL_API_KEY）")
    if i_ok:
        _ok("图片模型已配置（config.yaml image_model + aws.env IMAGE_MODEL_API_KEY）")
    else:
        print("[WARN] 图片模型未齐（不影响纯发布，生图需 config image_model + IMAGE_MODEL_API_KEY）")

    print("\n=== 检查完成 ===")
    if issues:
        print(f"\n需要处理的问题（{len(issues)} 个）：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        _ok("发布相关检查通过！")


if __name__ == "__main__":
    raise SystemExit(main())
