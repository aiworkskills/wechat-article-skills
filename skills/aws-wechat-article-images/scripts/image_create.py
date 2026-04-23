#!/usr/bin/env python3
"""
图片生成工具

调用 OpenAI 兼容的图片生成 API（DALL-E、Flux、SD 等）。

图片模型（可选）：`image_model`（base_url / model / default_size / default_quality；provider 可选）须写在 **`.aws-article/config.yaml`**，
**`IMAGE_MODEL_API_KEY`** 写在仓库根 **`aws.env`**，与 **`validate_env.py`** 一致。

**base_url 须为完整端点路径**（含协议类型后缀），脚本根据路径判断调用模式：
  - https://xxx.com/v1/images/generations  — DALL-E / gpt-image 等
  - https://xxx.com/v1/chat/completions    — Gemini 等多模态模型（通过中转站）

未配置时 generate/batch/test 以退出码 2 退出（stderr 含 `[NO_MODEL]`），
Agent 可读取 `imgs/prompts/*.md` 中的 prompt 文件后用自身多模态能力生图。

用法（在仓库根执行）：
    python skills/aws-wechat-article-images/scripts/image_create.py generate <prompt.md> -o out.png
    python skills/aws-wechat-article-images/scripts/image_create.py batch imgs/prompts/ -o imgs/
    python skills/aws-wechat-article-images/scripts/image_create.py test

退出码：
    0  成功
    1  硬错误（API 失败、文件缺失等）
    2  图片模型未配置（Agent 可降级自行生图）
"""

import argparse
import base64
import binascii
import ipaddress
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml


def _is_safe_download_url(url: str) -> tuple[bool, str]:
    """SSRF 防御：校验从 API 响应里拿到的 URL 是否可安全下载。

    拒绝：
      - 非 http/https scheme
      - 空 hostname
      - 解析到内网 / 环回 / 链路本地 / 保留 / 多播 地址（防止 IP/DNS rebinding）
    返回 `(is_safe, reason)`；is_safe=False 时 reason 含拒绝原因。
    """
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"URL 解析失败: {e}"
    if parsed.scheme not in ("http", "https"):
        return False, f"仅允许 http/https，拒绝 {parsed.scheme}://"
    hostname = parsed.hostname
    if not hostname:
        return False, "URL 缺少 hostname"
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
        ips = {info[4][0] for info in addrinfo}
    except Exception as e:
        return False, f"无法解析 hostname {hostname}: {e}"
    for ip_str in ips:
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"无效 IP: {ip_str}"
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_unspecified or ip.is_reserved or ip.is_multicast:
            return False, f"拒绝访问内网/保留地址: {hostname} → {ip}"
    return True, ""


def _safe_urlopen_download(url: str, timeout: int = 60):
    """下载专用 urlopen：对 URL 做 SSRF 校验后再下载；不合规抛 URLError。

    专用于下载 API 响应中返回的图片 URL；POST 到用户配置端点的调用不经过此函数，
    那类请求由用户自己控制 `image_model.base_url`。
    """
    ok, reason = _is_safe_download_url(url)
    if not ok:
        raise urllib.error.URLError(f"SSRF 防御拒绝: {reason}")
    return urllib.request.urlopen(url, timeout=timeout)


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


# ── 配置（config.yaml + aws.env）─────────────────────────────

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


def _model_config_from_config_and_env(cfg: dict | None, env: dict[str, str]) -> dict | None:
    if not isinstance(cfg, dict):
        return None
    im = cfg.get("image_model")
    if not isinstance(im, dict):
        return None
    base_url = (im.get("base_url") or "").strip()
    api_key = (env.get("IMAGE_MODEL_API_KEY") or "").strip()
    model = (im.get("model") or "").strip()
    if not base_url or not api_key or not model:
        return None
    provider = (im.get("provider") or "").strip().lower()
    default_size = str(im.get("default_size") or "1024x1024").strip()
    default_quality = str(im.get("default_quality") or "standard").strip()
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": model,
        "provider": provider,
        "default_size": default_size,
        "default_quality": default_quality,
    }


def _resolve_model_config() -> dict | None:
    """Return model config dict, or None if not configured."""
    env_map = _load_env_map()
    cfg = _load_config_yaml()
    m = _model_config_from_config_and_env(cfg, env_map)
    if m:
        _info(f"图片模型已解析（API Key 等来自 {_resolve_env_path().name}）")
        return m
    return None


def _http_error_hint(code: int) -> str:
    if code in (401, 403):
        return "【配置/认证】请检查 IMAGE_MODEL_API_KEY、端点是否匹配、账号是否有生图权限。"
    if code == 429:
        return "【限流】请稍后重试或降低并发。"
    if 500 <= code < 600:
        return "【服务端】可能是临时故障，可稍后重试。"
    if 400 <= code < 500:
        return "【请求参数】请对照 API 文档检查 model、size、quality 等是否被该端点支持。"
    return ""


def _format_api_failure(label: str, code: int, error_body: str) -> str:
    hint = _http_error_hint(code)
    parts = [f"{label} (HTTP {code})"]
    if hint:
        parts.append(hint)
    parts.append(f"响应正文: {error_body}")
    return "\n".join(parts)


def _fail_url(e: urllib.error.URLError, what: str) -> None:
    _err(
        f"网络错误（可重试）—{what}: {e.reason}\n"
        "请检查网络、代理、DNS 以及 config.yaml 中 image_model.base_url 是否可达。"
    )


# ── 图片生成 ─────────────────────────────────────────────────

ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "2.35:1": "1792x1024",
    "4:3": "1024x768",
    "3:4": "768x1024",
}


def _detect_api_type(model_cfg: dict) -> str:
    """
    协议识别优先级：
    1) 显式 provider（若配置）
    2) 根据 base_url 自动识别
    返回值枚举：openai | volcengine | gemini | qwen
    """
    p = (model_cfg.get("provider") or "").strip().lower()
    allowed = {"openai", "volcengine", "gemini", "qwen"}
    if p:
        if p not in allowed:
            _err(
                f"未识别的 IMAGE_MODEL_PROVIDER: {p}，请使用 openai | volcengine | qwen | gemini"
            )
            raise RuntimeError("invalid image provider")
        return p

    base_url = (model_cfg.get("base_url") or "").strip().lower()

    # Gemini 自动识别：须为完整端点（:generateContent 在 URL 中，不在 model 字段）
    if "/v1beta/models/" in base_url and ":generatecontent" in base_url:
        return "gemini"
    # 通义原生多模态生图：北京或新加坡域名须同时带官方路径（同一 URL 不可能同时含两个域名）
    if ("dashscope.aliyuncs.com" in base_url and "/multimodal-generation/generation" in base_url) or ("dashscope-intl.aliyuncs.com" in base_url and "/multimodal-generation/generation" in base_url):
        return "qwen"
    if ("volces.com" in base_url and "ark." in base_url and "/api/v3/images/generations" in base_url):
        return "volcengine"
    if "/v1/images/generations" in base_url or "/v1/chat/completions" in base_url:
        return "openai"

    _err(
        "无法从 image_model.base_url / model 自动识别协议类型。"
        "请在 .aws-article/config.yaml 显式填写 image_model.provider（openai | volcengine | qwen | gemini），"
        "或者填写可识别的完整 image_model.base_url。"
    )
    raise RuntimeError("undetected image provider")


def generate_image(model_cfg: dict, prompt: str, size: str = None,
                   quality: str = None) -> bytes:
    """根据 provider/端点类型调度到不同实现。"""
    api_type = _detect_api_type(model_cfg)

    if api_type == "openai" or api_type == "volcengine":
        return _generate_image_openai_compatible(model_cfg, prompt, size, quality, api_type)
    if api_type == "gemini":
        return _generate_image_gemini(model_cfg, prompt, size, quality)
    if api_type == "qwen":
        return _generate_image_qwen(model_cfg, prompt, size, quality)

    _err(
        f"未识别的 IMAGE_MODEL_PROVIDER: {api_type}，请设置为 openai | volcengine | qwen | gemini"
    )
    raise RuntimeError("invalid image provider")


def _image_bytes_from_openai_like_result(result: dict, url: str) -> bytes:
    """解析 images/generations 或 chat/completions 返回中的图片数据。"""
    items = result.get("data", [])
    if items:
        b64 = items[0].get("b64_json", "")
        if b64:
            return base64.b64decode(b64)
        img_url = items[0].get("url", "")
        if img_url:
            _info("下载图片...")
            try:
                with _safe_urlopen_download(img_url, timeout=60) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8", errors="replace")
                _err(_format_api_failure("下载图片失败", e.code, error_body))
            except urllib.error.URLError as e:
                _fail_url(e, "下载图片")

    if "/v1/chat/completions" in url.lower():
        choices = result.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if isinstance(content, str):
                s = content.strip()
                # 部分网关返回 Markdown：![](data:image/png;base64,...)
                m_data = re.search(
                    r"data:image/[\w.+-]+;base64,([A-Za-z0-9+/=\s]+)",
                    s,
                    re.I,
                )
                if m_data:
                    try:
                        return base64.b64decode(re.sub(r"\s+", "", m_data.group(1)))
                    except (ValueError, TypeError, binascii.Error):
                        pass
                if s.startswith("http://") or s.startswith("https://"):
                    _info("下载图片...")
                    try:
                        with _safe_urlopen_download(s, timeout=60) as r:
                            return r.read()
                    except urllib.error.HTTPError as e:
                        error_body = e.read().decode("utf-8", errors="replace")
                        _err(_format_api_failure("下载图片失败", e.code, error_body))
                    except urllib.error.URLError as e:
                        _fail_url(e, "下载图片")
                m = re.search(r"https?://[^\s\)\]\"']+", s)
                if m:
                    u = m.group(0).rstrip(").,;")
                    _info("下载图片...")
                    try:
                        with _safe_urlopen_download(u, timeout=60) as r:
                            return r.read()
                    except urllib.error.HTTPError as e:
                        error_body = e.read().decode("utf-8", errors="replace")
                        _err(_format_api_failure("下载图片失败", e.code, error_body))
                    except urllib.error.URLError as e:
                        _fail_url(e, "下载图片")
            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") == "image_url":
                        u = (part.get("image_url") or {}).get("url") or ""
                        if u:
                            _info("下载图片...")
                            try:
                                with _safe_urlopen_download(u, timeout=60) as r:
                                    return r.read()
                            except urllib.error.HTTPError as e:
                                error_body = e.read().decode("utf-8", errors="replace")
                                _err(_format_api_failure("下载图片失败", e.code, error_body))
                            except urllib.error.URLError as e:
                                _fail_url(e, "下载图片")
                    u = part.get("url") or ""
                    if u and (u.startswith("http://") or u.startswith("https://")):
                        _info("下载图片...")
                        try:
                            with _safe_urlopen_download(u, timeout=60) as r:
                                return r.read()
                        except urllib.error.HTTPError as e:
                            error_body = e.read().decode("utf-8", errors="replace")
                            _err(_format_api_failure("下载图片失败", e.code, error_body))
                        except urllib.error.URLError as e:
                            _fail_url(e, "下载图片")

    _err(f"API 返回无图片: {result}")


def _generate_image_openai_compatible(model_cfg: dict, prompt: str, size: str = None,
                                      quality: str = None, api_type: str = "openai") -> bytes:
    """OpenAI 兼容生图。base_url 须为完整端点（含 /v1/images/generations 或 /v1/chat/completions）。"""
    b = model_cfg["base_url"].rstrip("/")
    bl = b.lower()
    if api_type == "volcengine":
        url = b if "/api/v3/images/generations" in bl else f"{b}/api/v3/images/generations"
    elif api_type == "openai":
        if "/v1/chat/completions" in bl:
            url = b
        elif "/v1/images/generations" in bl:
            url = b
        else:
            _err(
                "image_model.base_url 须包含完整端点路径。示例：\n"
                "  - https://xxx.com/v1/images/generations  （DALL-E / gpt-image 等）\n"
                "  - https://xxx.com/v1/chat/completions    （Gemini 等多模态模型通过中转站生图）"
            )
    else:
        _err(f"provider 无效: {api_type}（应为 openai | volcengine | qwen | gemini）")
        raise RuntimeError("invalid image provider")

    use_chat = "/v1/chat/completions" in url.lower()
    if use_chat:
        sz = size or model_cfg["default_size"]
        q = quality or model_cfg["default_quality"]
        user_text = f"{prompt}\n\n（尺寸: {sz}，质量: {q}）"
        body = {
            "model": model_cfg["model"],
            "messages": [{"role": "user", "content": user_text}],
        }
    else:
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
    _info(f"调用模型: {model_cfg['model']} @ {url} ({api_type})")
    if use_chat:
        _info(f"模式: chat/completions | 尺寸/质量已并入用户提示")
    else:
        _info(f"尺寸: {body['size']} | 质量: {body['quality']}")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except urllib.error.URLError as e:
        _fail_url(e, "连接生图 API")

    return _image_bytes_from_openai_like_result(result, url)


def _generate_image_gemini(model_cfg: dict, prompt: str, size: str = None,
                           quality: str = None) -> bytes:
    """Gemini generateContent（图片以 inlineData 返回）。base_url：完整 ...:generateContent 或网关根。"""
    b = model_cfg["base_url"].rstrip("/")
    model = (model_cfg["model"] or "").strip()
    bl = b.lower()
    if ":generatecontent" in bl:
        url = b
    else:
        url = f"{b}/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
        }
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
    _info(f"调用模型: {model_cfg['model']} @ {url} (gemini)")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except urllib.error.URLError as e:
        _fail_url(e, "连接生图 API")

    candidates = result.get("candidates", [])
    if not candidates:
        _err(f"API 返回无图片: {result}")
    content = candidates[0].get("content", {})
    for part in content.get("parts", []):
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    _err("API 未返回图片数据")


def _generate_image_qwen(model_cfg: dict, prompt: str, size: str = None,
                         quality: str = None) -> bytes:
    """通义千问原生：支持两种端点
    - text2image: .../services/aigc/text2image/image-synthesis
    - multimodal: .../services/aigc/multimodal-generation/generation
    base_url 需为上述完整路径之一。
    """
    base = model_cfg["base_url"].rstrip("/")
    bl = base.lower().rstrip("/")

    # 允许仅填域名：默认走 multimodal 路径；已写完整路径则直接使用（不区分路径大小写）
    if bl.endswith("/multimodal-generation/generation"):
        url = base
    else:
        # 默认统一到多模态生成接口
        url = f"{base}/api/v1/services/aigc/multimodal-generation/generation"

    use_text2image = url.endswith("/image-synthesis")
    use_multimodal = url.endswith("/multimodal-generation/generation")

    if use_text2image:
        body = {
            "model": model_cfg["model"],
            "input": {"prompt": prompt},
            "parameters": {"size": size or model_cfg["default_size"]},
        }
    else:
        # multimodal generation body（纯文生图）
        mm_size = (size or model_cfg["default_size"] or "").replace("x", "*").replace("X", "*")
        if not mm_size:
            mm_size = "1024*1024"
        body = {
            "model": model_cfg["model"],
            "input": {
                "messages": [
                    {"role": "user", "content": [{"text": prompt}]}
                ]
            },
            "parameters": {"size": mm_size},
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
    _info(f"调用模型: {model_cfg['model']} @ {url} (qwen_native {'text2image' if use_text2image else 'multimodal'})")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except urllib.error.URLError as e:
        _fail_url(e, "连接生图 API")

    # 兼容常见返回（若为异步，需另行适配轮询逻辑）
    if "output" in result:
        out = result["output"]
        # 1) 新版：choices[].message.content[].image
        choices = out.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            parts = msg.get("content") or []
            for part in parts:
                img_url = part.get("image")
                if img_url:
                    _info("下载图片...")
                    try:
                        with _safe_urlopen_download(img_url, timeout=60) as r:
                            return r.read()
                    except urllib.error.HTTPError as e:
                        error_body = e.read().decode("utf-8", errors="replace")
                        _err(_format_api_failure("下载图片失败", e.code, error_body))
                    except urllib.error.URLError as e:
                        _fail_url(e, "下载图片")
        # 2) 旧版/兼容：results[].url / results[].data
        results = out.get("results", [])
        if results:
            r0 = results[0]
            img_url = r0.get("url", "")
            if img_url:
                _info("下载图片...")
                try:
                    with _safe_urlopen_download(img_url, timeout=60) as r:
                        return r.read()
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8", errors="replace")
                    _err(_format_api_failure("下载图片失败", e.code, error_body))
                except urllib.error.URLError as e:
                    _fail_url(e, "下载图片")
            b64 = r0.get("data", "")
            if b64:
                return base64.b64decode(b64)
    # 兜底：有些实现直接返回 data url
    if "data" in result and isinstance(result["data"], str):
        return base64.b64decode(result["data"])
    _err("API 未返回图片数据")

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

    model_cfg = _resolve_model_config()
    if model_cfg is None:
        print(
            "[NO_MODEL] 图片模型未配置（image_model 或 IMAGE_MODEL_API_KEY 缺失）。"
            "Agent 可读取 imgs/prompts/*.md 后用自身多模态能力生图。",
            file=sys.stderr,
        )
        sys.exit(2)

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
