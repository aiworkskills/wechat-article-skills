#!/usr/bin/env python3
"""
微信文章读取工具（独立于 publish.py，默认面向正式文章）。

用法示例（在仓库根目录执行）：
  python skills/aws-wechat-article-publish/scripts/getdraft.py published-fields
  python skills/aws-wechat-article-publish/scripts/getdraft.py publish-get <publish_id>
  python skills/aws-wechat-article-publish/scripts/getdraft.py article-get <article_id>
  # 兼容：草稿查询
  python skills/aws-wechat-article-publish/scripts/getdraft.py list-fields
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import NoReturn
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_API_BASE = "https://api.weixin.qq.com"
API_PATH = "/cgi-bin"


def _info(msg: str) -> None:
    print(f"[INFO] {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"[OK] {msg}", file=sys.stderr)


def _err(msg: str) -> NoReturn:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(1)


def _repo_root() -> Path:
    """定位仓库根：要求脚本在当前工作目录（`Path.cwd()`）下能读到 `.aws-article/config.yaml`。

    不再向上遍历脚本的父目录、也不再 fallback 到脚本所在的固定父路径，
    避免在非预期的工作区触发配置读取。
    """
    cwd = Path.cwd().resolve()
    if (cwd / ".aws-article" / "config.yaml").is_file():
        return cwd
    raise SystemExit(
        "未在当前工作目录下找到 .aws-article/config.yaml。\n"
        f"当前目录：{cwd}\n"
        "请在仓库根（含 .aws-article/config.yaml 的目录）下运行本脚本。"
    )


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        _err("缺少 PyYAML，请先安装：pip install pyyaml")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        _err(f"读取 YAML 失败：{path} - {e}")
    return data if isinstance(data, dict) else {}


def _parse_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip("'").strip('"')
    return out


def _normalize_api_base(raw: str) -> str:
    base = raw.strip().rstrip("/")
    if base.endswith("/cgi-bin"):
        base = base[:-8].rstrip("/")
    return base


def _resolve_slot(cfg: dict, account: str | None) -> int:
    raw_n = cfg.get("wechat_accounts")
    try:
        n = int(raw_n)
    except Exception:  # noqa: BLE001
        n = 0
    if n < 1:
        _err("config.yaml 中 wechat_accounts 无效（需 >= 1）")

    if account:
        s = account.strip()
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= n:
                return idx
            _err(f"--account 槽位超范围：{idx}（有效 1..{n}）")
        for i in range(1, n + 1):
            name = str(cfg.get(f"wechat_{i}_name") or "").strip()
            if name and (s == name or s in name):
                return i
        _err(f"未找到账号名匹配：{s}")

    if n == 1:
        return 1

    ws = cfg.get("wechat_publish_slot")
    if ws is not None and str(ws).strip():
        try:
            idx = int(ws)
        except Exception:  # noqa: BLE001
            _err("config.yaml 中 wechat_publish_slot 必须是整数")
        if 1 <= idx <= n:
            _info(f"使用 config.yaml wechat_publish_slot={idx}")
            return idx
        _err(f"wechat_publish_slot 超范围：{idx}（有效 1..{n}）")

    _err(
        f"配置了 {n} 个微信槽位，请传 --account <1..{n} 或 wechat_N_name> "
        "或在 config.yaml 中设置 wechat_publish_slot"
    )


def _api_get_json(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _api_post_json(url: str, body: dict) -> dict:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _build_runtime(account: str | None) -> tuple[str, str, str]:
    root = _repo_root()
    cfg = _load_yaml(root / ".aws-article" / "config.yaml")
    env = _parse_env(root / "aws.env")

    slot = _resolve_slot(cfg, account)
    appid = env.get(f"WECHAT_{slot}_APPID", "").strip()
    secret = env.get(f"WECHAT_{slot}_APPSECRET", "").strip()
    if not appid or not secret:
        _err(f"缺少 WECHAT_{slot}_APPID / WECHAT_{slot}_APPSECRET")

    slot_base = env.get(f"WECHAT_{slot}_API_BASE", "").strip()
    cfg_base = str(cfg.get("wechat_api_base") or "").strip()
    api_base = _normalize_api_base(slot_base or cfg_base or DEFAULT_API_BASE)
    _info(f"API 端点: {api_base}{API_PATH}")
    return appid, secret, api_base


def _draft_batchget_page(
    token: str, api_base: str, offset: int, count: int, no_content: int
) -> dict:
    body = {
        "offset": max(0, offset),
        "count": min(20, max(1, count)),
        "no_content": no_content,
    }
    url = f"{api_base}{API_PATH}/draft/batchget?access_token={token}"
    return _api_post_json(url, body)


def _freepublish_batchget_page(
    token: str, api_base: str, offset: int, count: int, no_content: int
) -> dict:
    body = {
        "offset": max(0, offset),
        "count": min(20, max(1, count)),
        "no_content": no_content,
    }
    url = f"{api_base}{API_PATH}/freepublish/batchget?access_token={token}"
    return _api_post_json(url, body)


def _fetch_all_draft_items(token: str, api_base: str, no_content: int = 1) -> list[dict]:
    """分页拉取草稿箱全部条目（draft/batchget，每页最多 20 条）。"""
    all_items: list[dict] = []
    offset = 0
    page_size = 20
    while True:
        data = _draft_batchget_page(token, api_base, offset, page_size, no_content)
        if data.get("errcode") not in (None, 0):
            _err(f"获取草稿列表失败: {data}")
        items = data.get("item") or []
        if not items:
            break
        all_items.extend(items)
        n = len(items)
        if n < page_size:
            break
        offset += page_size
        total = data.get("total_count")
        if total is not None and offset >= int(total):
            break
    return all_items


def _fetch_all_published_items(token: str, api_base: str, no_content: int = 1) -> list[dict]:
    """分页拉取已发布条目（freepublish/batchget，每页最多 20 条）。"""
    all_items: list[dict] = []
    offset = 0
    page_size = 20
    while True:
        data = _freepublish_batchget_page(token, api_base, offset, page_size, no_content)
        if data.get("errcode") not in (None, 0):
            _err(f"获取已发布列表失败: {data}")
        items = data.get("item") or []
        if not items:
            break
        all_items.extend(items)
        n = len(items)
        if n < page_size:
            break
        offset += page_size
        total = data.get("total_count")
        if total is not None and offset >= int(total):
            break
    return all_items


def _rows_title_digest_url(it: dict) -> list[dict[str, str]]:
    """从 batchget 单条 item 取出 title/digest/url（优先 content.news_item，否则顶层 news_item）。"""
    news: list | None = None
    content = it.get("content")
    if isinstance(content, dict):
        n = content.get("news_item")
        if isinstance(n, list):
            news = n
    if news is None:
        n2 = it.get("news_item")
        if isinstance(n2, list):
            news = n2
    if news:
        rows: list[dict[str, str]] = []
        for ni in news:
            if not isinstance(ni, dict):
                continue
            rows.append(
                {
                    "title": str(ni.get("title") or ""),
                    "digest": str(ni.get("digest") or ""),
                    "url": str(ni.get("url") or ""),
                }
            )
        if rows:
            return rows

    return [
        {
            "title": str(it.get("title") or ""),
            "digest": str(it.get("digest") or ""),
            "url": str(it.get("url") or ""),
        }
    ]


def _get_token(appid: str, secret: str, api_base: str) -> str:
    qs = urllib.parse.urlencode(
        {"grant_type": "client_credential", "appid": appid, "secret": secret}
    )
    url = f"{api_base}{API_PATH}/token?{qs}"
    data = _api_get_json(url)
    tok = data.get("access_token")
    if not tok:
        _err(f"获取 token 失败: {data}")
    return str(tok)


def cmd_list(args: argparse.Namespace) -> int:
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    data = _draft_batchget_page(
        token,
        api_base,
        max(0, int(args.offset)),
        min(20, max(1, int(args.count))),
        0 if args.with_content else 1,
    )
    if data.get("errcode") not in (None, 0):
        _err(f"获取草稿列表失败: {data}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_list_fields(args: argparse.Namespace) -> int:
    """输出所有草稿的 title、digest、url 列表（JSON 数组，每项一个对象）。"""
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    # no_content=0 才会带上 content.news_item 中的 title/digest/url；no_content=1 时常全空
    _info("list-fields 使用 no_content=0 拉取元数据（多图文会展开为多条）")
    items = _fetch_all_draft_items(token, api_base, no_content=0)
    out: list[dict[str, str]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.extend(_rows_title_digest_url(it))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    url = f"{api_base}{API_PATH}/draft/get?access_token={token}"
    data = _api_post_json(url, {"media_id": args.media_id.strip()})
    if data.get("errcode") not in (None, 0):
        _err(f"获取草稿详情失败: {data}")

    if args.content_only:
        items = data.get("news_item") or []
        if not items:
            _err("响应中没有 news_item，去掉 --content-only 查看完整 JSON")
        idx = int(args.index)
        if idx < 0 or idx >= len(items):
            _err(f"--index 越界：{idx}（可用 0..{len(items)-1}）")
        html = str(items[idx].get("content") or "")
        print(html)
        return 0

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_published_list(args: argparse.Namespace) -> int:
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    data = _freepublish_batchget_page(
        token,
        api_base,
        max(0, int(args.offset)),
        min(20, max(1, int(args.count))),
        0 if args.with_content else 1,
    )
    if data.get("errcode") not in (None, 0):
        _err(f"获取已发布列表失败: {data}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_published_fields(args: argparse.Namespace) -> int:
    """输出所有已发布文章的 title、digest、url 列表（JSON 数组，每项一个对象）。"""
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    _info("published-fields 使用 freepublish/batchget 拉取正式文章元数据")
    items = _fetch_all_published_items(token, api_base, no_content=0)
    out: list[dict[str, str]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.extend(_rows_title_digest_url(it))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_publish_get(args: argparse.Namespace) -> int:
    """按 publish_id 查询发布状态及 article_id。"""
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    url = f"{api_base}{API_PATH}/freepublish/get?access_token={token}"
    data = _api_post_json(url, {"publish_id": args.publish_id.strip()})
    if data.get("errcode") not in (None, 0):
        _err(f"按 publish_id 查询失败: {data}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_article_get(args: argparse.Namespace) -> int:
    """按 article_id 获取正式文章详情（含正式 URL）。"""
    appid, secret, api_base = _build_runtime(args.account)
    token = _get_token(appid, secret, api_base)
    url = f"{api_base}{API_PATH}/freepublish/getarticle?access_token={token}"
    data = _api_post_json(url, {"article_id": args.article_id.strip()})
    if data.get("errcode") not in (None, 0):
        _err(f"按 article_id 查询正式文章失败: {data}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="微信文章读取工具（正式文章优先）")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="兼容：获取草稿列表（draft/batchget）")
    p_list.add_argument("--account", help="槽位序号或 wechat_N_name")
    p_list.add_argument("--offset", type=int, default=0, help="偏移，默认 0")
    p_list.add_argument("-n", "--count", type=int, default=20, help="条数 1~20")
    p_list.add_argument(
        "--with-content",
        action="store_true",
        help="返回 content（默认不返回，便于只取 media_id）",
    )

    p_fields = sub.add_parser(
        "list-fields",
        help="兼容：拉取全部草稿，仅输出 title/digest/url 的 JSON 数组",
    )
    p_fields.add_argument("--account", help="槽位序号或 wechat_N_name")

    p_get = sub.add_parser("get", help="兼容：获取草稿详情（draft/get）")
    p_get.add_argument("media_id", help="草稿 media_id")
    p_get.add_argument("--account", help="槽位序号或 wechat_N_name")
    p_get.add_argument(
        "--content-only",
        action="store_true",
        help="只输出 news_item[index].content",
    )
    p_get.add_argument(
        "--index",
        type=int,
        default=0,
        help="多图文时取第几条（默认 0）",
    )

    p_pub_list = sub.add_parser("published-list", help="获取已发布列表（freepublish/batchget）")
    p_pub_list.add_argument("--account", help="槽位序号或 wechat_N_name")
    p_pub_list.add_argument("--offset", type=int, default=0, help="偏移，默认 0")
    p_pub_list.add_argument("-n", "--count", type=int, default=20, help="条数 1~20")
    p_pub_list.add_argument(
        "--with-content",
        action="store_true",
        help="返回 content（默认不返回）",
    )

    p_pub_fields = sub.add_parser(
        "published-fields",
        help="拉取全部已发布文章，仅输出 title/digest/url 的 JSON 数组",
    )
    p_pub_fields.add_argument("--account", help="槽位序号或 wechat_N_name")

    p_publish_get = sub.add_parser("publish-get", help="按 publish_id 查询发布状态（freepublish/get）")
    p_publish_get.add_argument("publish_id", help="发布任务 publish_id")
    p_publish_get.add_argument("--account", help="槽位序号或 wechat_N_name")

    p_article_get = sub.add_parser("article-get", help="按 article_id 查询正式文章详情（freepublish/getarticle）")
    p_article_get.add_argument("article_id", help="正式文章 article_id")
    p_article_get.add_argument("--account", help="槽位序号或 wechat_N_name")

    args = parser.parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "list-fields":
        return cmd_list_fields(args)
    if args.cmd == "get":
        return cmd_get(args)
    if args.cmd == "published-list":
        return cmd_published_list(args)
    if args.cmd == "published-fields":
        return cmd_published_fields(args)
    if args.cmd == "publish-get":
        return cmd_publish_get(args)
    if args.cmd == "article-get":
        return cmd_article_get(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
