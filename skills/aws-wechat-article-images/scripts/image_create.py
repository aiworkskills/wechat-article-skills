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

prompt 文件 frontmatter 的 `aspect`（如 "2.35:1"）会映射为 API 支持的最接近尺寸；生成后若装有 Pillow，
会按该比例居中裁切（未装则保留原尺寸并给出 [WARN]）。`aspect` 建议加引号：未加引号的 `16:9`
会被 YAML 1.1 解析成整数，脚本会尽量反推，但不保证所有写法。

退出码：
    0  成功
    1  硬错误（API 失败、文件缺失等）
    2  图片模型未配置（Agent 可降级自行生图）
"""

import argparse
import base64
import binascii
import io
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
    print(f"[OK] {msg}", flush=True)


def _info(msg: str):
    print(f"[INFO] {msg}", flush=True)


# ── 配置（config.yaml + aws.env）─────────────────────────────

def _resolve_env_path() -> Path:
    return Path("aws.env")


def _require_repo_root() -> None:
    """跑错目录时立刻停下，而不是报成「模型未配置」。

    配置按 cwd 相对路径解析，且刻意不向上遍历（见 getdraft.py `_repo_root`：
    避免在非预期的工作区读到别人的凭证）。但「找不到 .aws-article/config.yaml」
    原本会一路走到 [NO_MODEL] + 退出码 2，而 SKILL.md 规定退出码 2 意味着
    「模型没配」、Agent 可以改用自身能力代生图——于是配置完全正常的用户会看到
    一句假的「你没配图片模型」，然后同意降级，绕开自己配好的专用模型。
    目录错和没配置是两回事，必须分开报。
    """
    if Path(".aws-article/config.yaml").is_file():
        return
    _err(
        "未在当前工作目录下找到 .aws-article/config.yaml。\n"
        f"       当前目录：{Path.cwd()}\n"
        "       要么跑错了目录（请在仓库根、即含 .aws-article/ 的目录下运行），\n"
        "       要么首次引导还没走（见 aws-wechat-article-main/references/first-time-setup.md）。\n"
        "       两种都不是「图片模型未配置」，不要据此降级由 Agent 代生图。"
    )


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
    aspect_mode = (im.get("aspect_mode") or "auto").strip().lower()
    default_size = str(im.get("default_size") or "1024x1024").strip()
    default_quality = str(im.get("default_quality") or "standard").strip()
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": model,
        "provider": provider,
        "aspect_mode": aspect_mode,
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


def _fail_url(e: urllib.error.URLError | TimeoutError, what: str) -> None:
    _err(
        f"网络错误（可重试）—{what}: {getattr(e, 'reason', e)}\n"
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


# Gemini（含通过 OpenAI 兼容中转站调用的 gemini-*-image）原生支持的比例。
# 2.35:1 不在其中，最接近的是 21:9（2.33:1），差异 <1%，生成后无须再裁。
# `extra_body.imageConfig` 是 Gemini 家族特有的结构，不是 OpenAI 兼容协议的一部分。
# 往非 Gemini 端点发这个字段，宽松网关会忽略，严格网关会直接 400 —— 从「比例不对」
# 退化成「出不了图」。所以只在识别出 Gemini 系模型时才发，其余模型保持原有行为
# （尺寸并入提示 + 生成后按需裁切）。
GEMINI_MODEL_HINTS = ("gemini", "nano-banana", "nanobanana", "imagen")

# Gemini 的分辨率档位。不指定时同一 prompt 两次可能返回差一倍的尺寸
# （实测 1584x672 与 784x336），公众号封面要求长边 ≥900px，所以默认锁 2K。
GEMINI_IMAGE_SIZES = ("512", "1K", "2K", "4K")
DEFAULT_IMAGE_SIZE = "2K"

# 公众号封面长边建议 ≥900px（900x383 是官方推荐的 2.35:1 尺寸）。
# imageSize 未必被中转站透传：实测同一 prompt、同一 imageSize=2K，返回过 1376px
# 也返回过 384px。波动大且随机，所以出图后按实际像素检查，过小就重试一次。
#
# 不要用 4K：实测发 imageSize=4K 时该端点连 aspectRatio 一起忽略（3/3 返回 ~1.8:1），
# 比不发还差。2K 对公众号封面已绰绰有余。
MIN_LONG_EDGE = 900
CHECK_RETRIES = 3

# ── 封面标题区与出图检查 ────────────────────────────────
# 标题区默认位置（归一化 x0,y0,x1,y1）：右侧 55%~92%、垂直 30%~70%，与预设库里
# 绝大多数条目的「标题区」一致。prompt frontmatter 的 title_zone 可覆盖。
DEFAULT_TITLE_ZONE = (0.55, 0.30, 0.92, 0.70)
# 标题区边缘密度阈值（0~255）。按 12 张真实预览图标定：纯留白区中位数 4.9，
# 带宣纸纹理 / 印刷颗粒的留白区 10~12，模型画进去的标题字约 15~16。
# 只用于「合成标题前须留白」这条路径（frontmatter 写了 title:）；默认路径里
# 标题由模型画在区内，不做此检查。
ZONE_BUSY_THRESHOLD = 13.0
# 整图灰度标准差低于此值视为近单色（空白/生成失败）。
MONO_STDDEV_THRESHOLD = 8.0
TITLE_MAX_LINES = 2

_CJK_FONT_CANDIDATES: tuple[tuple[str, int], ...] = (
    # macOS
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1),  # index 1 = W6 粗体
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    # Linux：apt install fonts-noto-cjk 或 fonts-wqy-microhei
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 0),
    ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
    ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", 0),
    # Windows
    ("C:/Windows/Fonts/msyhbd.ttc", 0),
    ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0),
)

GEMINI_ASPECT_RATIOS = (
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1",
    "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
)


def _aspect_value(aspect: str) -> float | None:
    """`w:h` → w/h；无法解析返回 None。"""
    if not aspect or ":" not in aspect:
        return None
    try:
        w, h = (float(x) for x in aspect.split(":", 1))
    except ValueError:
        return None
    return w / h if h > 0 else None


def _nearest_supported_aspect(aspect: str) -> str | None:
    """把任意比例映射到 Gemini 支持的最接近比例；无法解析返回 None。"""
    target = _aspect_value(aspect)
    if target is None:
        return None
    if aspect in GEMINI_ASPECT_RATIOS:
        return aspect
    best = min(
        GEMINI_ASPECT_RATIOS,
        key=lambda a: abs((_aspect_value(a) or 0) - target),
    )
    return best


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
    if ("dashscope.aliyuncs.com" in base_url or "dashscope-intl.aliyuncs.com" in base_url) and (
        "/multimodal-generation/generation" in base_url or "/text2image/image-synthesis" in base_url
    ):
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


def _supports_image_config(model_cfg: dict) -> bool:
    """该端点是否接受 Gemini 的 imageConfig（比例/分辨率结构化参数）。

    `image_model.aspect_mode` 可显式指定：
      auto（默认）— 按模型名判断；imageconfig — 强制发送；none — 从不发送。
    """
    mode = (model_cfg.get("aspect_mode") or "auto").strip().lower()
    if mode == "imageconfig":
        return True
    if mode == "none":
        return False
    if mode != "auto":
        _err(f"image_model.aspect_mode 无效: {mode}（应为 auto | imageconfig | none）")
    model = (model_cfg.get("model") or "").lower()
    return any(h in model for h in GEMINI_MODEL_HINTS)


def _normalize_image_size(value) -> str | None:
    """把 frontmatter 的 resolution 归一到 Gemini 档位；无效值返回 None。"""
    if value is None:
        return None
    v = str(value).strip().upper().replace("K", "K")
    for allowed in GEMINI_IMAGE_SIZES:
        if v == allowed.upper():
            return allowed
    return None


def generate_image(model_cfg: dict, prompt: str, size: str = None,
                   quality: str = None, aspect: str = None,
                   resolution: str = None) -> bytes:
    """根据 provider/端点类型调度到不同实现。

    `aspect`（如 "2.35:1"）用于支持结构化比例参数的端点：chat/completions 走
    `extra_body.imageConfig.aspectRatio`，Gemini 原生走 `generationConfig.imageConfig`。
    不支持的端点忽略该参数，仍按 `size` 处理。
    """
    api_type = _detect_api_type(model_cfg)

    if api_type == "openai" or api_type == "volcengine":
        return _generate_image_openai_compatible(
            model_cfg, prompt, size, quality, api_type, aspect, resolution)
    if api_type == "gemini":
        return _generate_image_gemini(model_cfg, prompt, size, quality, aspect, resolution)
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
            except (urllib.error.URLError, TimeoutError) as e:
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
                    except (urllib.error.URLError, TimeoutError) as e:
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
                    except (urllib.error.URLError, TimeoutError) as e:
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
                            except (urllib.error.URLError, TimeoutError) as e:
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
                        except (urllib.error.URLError, TimeoutError) as e:
                            _fail_url(e, "下载图片")

    _err(f"API 返回无图片: {result}")


def _generate_image_openai_compatible(model_cfg: dict, prompt: str, size: str = None,
                                      quality: str = None, api_type: str = "openai",
                                      aspect: str = None, resolution: str = None) -> bytes:
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
    sent_aspect = None
    if use_chat:
        # Gemini 系走结构化比例参数。此前是把「（尺寸: 1792x1024）」当中文拼进 prompt
        # 末尾，模型基本不理会，实测出图一律是它自己的默认尺寸。
        if aspect and _supports_image_config(model_cfg):
            sent_aspect = _nearest_supported_aspect(aspect)
        body = {
            "model": model_cfg["model"],
            "messages": [{"role": "user", "content": prompt}],
        }
        if sent_aspect:
            image_cfg = {"aspectRatio": sent_aspect}
            sent_size = _normalize_image_size(resolution) or DEFAULT_IMAGE_SIZE
            image_cfg["imageSize"] = sent_size
            body["extra_body"] = {"imageConfig": image_cfg}
        else:
            # 非 Gemini 端点或未给比例：保持原有行为，尺寸并入提示；
            # 真实比例由调用方在生成后用 _crop_to_aspect 兜底
            sz = size or model_cfg["default_size"]
            q = quality or model_cfg["default_quality"]
            body["messages"][0]["content"] = f"{prompt}\n\n（尺寸: {sz}，质量: {q}）"
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
        if sent_aspect:
            note = f"比例: {sent_aspect} | 分辨率: {body['extra_body']['imageConfig']['imageSize']}（extra_body.imageConfig）"
            if aspect and sent_aspect != aspect:
                note += f"，比例由 {aspect} 就近映射"
            _info(f"模式: chat/completions | {note}")
        elif aspect:
            _info(
                f"模式: chat/completions | 端点不接受 imageConfig（模型 {model_cfg['model']}），"
                f"尺寸并入提示，生成后按 {aspect} 裁切"
            )
        else:
            _info("模式: chat/completions | 无可用比例，尺寸并入用户提示")
    else:
        _info(f"尺寸: {body['size']} | 质量: {body['quality']}")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except (urllib.error.URLError, TimeoutError) as e:
        _fail_url(e, "连接生图 API")

    return _image_bytes_from_openai_like_result(result, url)


def _generate_image_gemini(model_cfg: dict, prompt: str, size: str = None,
                           quality: str = None, aspect: str = None,
                           resolution: str = None) -> bytes:
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
            "responseModalities": ["TEXT", "IMAGE"],
        }
    }
    gemini_aspect = (
        _nearest_supported_aspect(aspect)
        if aspect and _supports_image_config(model_cfg)
        else None
    )
    if gemini_aspect:
        body["generationConfig"]["imageConfig"] = {
            "aspectRatio": gemini_aspect,
            "imageSize": _normalize_image_size(resolution) or DEFAULT_IMAGE_SIZE,
        }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if host.endswith("googleapis.com"):
        # Google 官方端点：API Key 走 x-goog-api-key，Bearer 仅用于 OAuth token
        headers["x-goog-api-key"] = model_cfg["api_key"]
    else:
        # 中转站通常沿用 Bearer
        headers["Authorization"] = f"Bearer {model_cfg['api_key']}"
    req = urllib.request.Request(url, data=data, headers=headers)
    _info(f"调用模型: {model_cfg['model']} @ {url} (gemini, auth={'x-goog-api-key' if 'x-goog-api-key' in headers else 'bearer'})")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except (urllib.error.URLError, TimeoutError) as e:
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

    # 允许仅填域名：默认走 multimodal 路径；已写完整路径（multimodal 或 text2image）则直接使用
    if bl.endswith("/multimodal-generation/generation") or bl.endswith("/image-synthesis"):
        url = base
    else:
        # 默认统一到多模态生成接口
        url = f"{base}/api/v1/services/aigc/multimodal-generation/generation"

    use_text2image = url.lower().endswith("/image-synthesis")

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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_cfg['api_key']}",
    }
    if use_text2image:
        # DashScope text2image（万相）仅支持异步：提交任务后轮询
        headers["X-DashScope-Async"] = "enable"
    req = urllib.request.Request(url, data=data, headers=headers)
    _info(f"调用模型: {model_cfg['model']} @ {url} (qwen_native {'text2image' if use_text2image else 'multimodal'})")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _err(_format_api_failure("API 调用失败", e.code, error_body))
    except (urllib.error.URLError, TimeoutError) as e:
        _fail_url(e, "连接生图 API")

    if use_text2image:
        task_id = (result.get("output") or {}).get("task_id")
        if not task_id:
            _err(f"text2image 未返回 task_id: {result}")
        result = _qwen_wait_task(model_cfg, url, task_id)

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
                    except (urllib.error.URLError, TimeoutError) as e:
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
                except (urllib.error.URLError, TimeoutError) as e:
                    _fail_url(e, "下载图片")
            b64 = r0.get("data", "")
            if b64:
                return base64.b64decode(b64)
    # 兜底：有些实现直接返回 data url
    if "data" in result and isinstance(result["data"], str):
        return base64.b64decode(result["data"])
    _err("API 未返回图片数据")

def _qwen_wait_task(model_cfg: dict, endpoint_url: str, task_id: str,
                    timeout: int = 180, interval: int = 3) -> dict:
    """轮询 DashScope 异步任务直到 SUCCEEDED；失败 / 超时走 _err。返回任务查询的完整响应。"""
    parsed = urllib.parse.urlparse(endpoint_url)
    task_url = f"{parsed.scheme}://{parsed.netloc}/api/v1/tasks/{task_id}"
    _info(f"text2image 为异步任务，轮询 {task_url}")
    deadline = time.time() + timeout
    while True:
        req = urllib.request.Request(
            task_url, headers={"Authorization": f"Bearer {model_cfg['api_key']}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            _err(_format_api_failure("轮询生图任务失败", e.code, error_body))
        except (urllib.error.URLError, TimeoutError) as e:
            _fail_url(e, "轮询生图任务")
        status = str((data.get("output") or {}).get("task_status") or "").upper()
        if status == "SUCCEEDED":
            return data
        if status in ("FAILED", "CANCELED", "UNKNOWN"):
            _err(f"生图任务 {status}: {data}")
        if time.time() > deadline:
            _err(f"生图任务超时（{timeout}s 仍为 {status or '未知'}）: {data}")
        time.sleep(interval)


def _coerce_aspect(value) -> str | None:
    """frontmatter 的 size / aspect 统一为字符串。

    PyYAML 按 YAML 1.1 把未加引号的 `16:9` 解析成六十进制整数 969、`1:1` 解析成 61，
    这里按 divmod(60) 反推回 `16:9` / `1:1`。
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        a, b = divmod(value, 60)
        return f"{a}:{b}"
    text = str(value).strip()
    return text or None


def _resolve_size(cli_size: str | None, meta: dict) -> tuple[str | None, str | None]:
    """返回 (发给 API 的尺寸, 生成后需裁切到的比例或 None)。

    - `WxH`：原样传给 API，不裁切
    - 已知比例（ASPECT_TO_SIZE）：映射到最接近的支持尺寸，再按比例裁切
    - 未知比例 `w:h`：按横竖方向选一个宽幅 / 竖幅 / 方形尺寸，再按比例裁切
    """
    raw = _coerce_aspect(cli_size) or _coerce_aspect(meta.get("size")) or _coerce_aspect(meta.get("aspect"))
    if not raw:
        return None, None
    if raw in ASPECT_TO_SIZE:
        return ASPECT_TO_SIZE[raw], raw
    if ":" in raw:
        try:
            w, h = (float(x) for x in raw.split(":", 1))
        except ValueError:
            _err(f"无法识别的比例 / 尺寸: {raw!r}（应为 16:9 这类比例或 1024x1024 这类尺寸）")
        if w > h:
            size = "1792x1024"
        elif w < h:
            size = "1024x1792"
        else:
            size = "1024x1024"
        _info(f"比例 {raw} 不在预设表中，先按 {size} 生成再裁切")
        return size, raw
    return raw, None


def _crop_to_aspect(img_data: bytes, aspect: str) -> bytes:
    """按 `w:h` 居中裁切；与目标比例相差 <1% 时原样返回；未装 Pillow 时给 [WARN] 并原样返回。"""
    try:
        w_r, h_r = (float(x) for x in aspect.split(":", 1))
    except ValueError:
        return img_data
    if w_r <= 0 or h_r <= 0:
        return img_data
    target = w_r / h_r
    try:
        from PIL import Image
    except ImportError:
        print(f"[WARN] 未安装 Pillow，无法把图片裁切到 {aspect}，保留 API 返回尺寸（pip install Pillow）", file=sys.stderr)
        return img_data
    import io
    try:
        im = Image.open(io.BytesIO(img_data))
        im.load()
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 图片无法解析，跳过裁切: {e}", file=sys.stderr)
        return img_data
    w, h = im.size
    if abs(w / h - target) / target < 0.01:
        return img_data
    if w / h > target:
        new_w = max(1, round(h * target))
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        new_h = max(1, round(w / target))
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)
    fmt = im.format or "PNG"
    cropped = im.crop(box)
    if fmt == "JPEG" and cropped.mode not in ("RGB", "L"):
        cropped = cropped.convert("RGB")
    buf = io.BytesIO()
    cropped.save(buf, format=fmt)
    _info(f"已按 {aspect} 居中裁切: {w}x{h} -> {cropped.size[0]}x{cropped.size[1]}")
    return buf.getvalue()


def _image_long_edge(data: bytes) -> int | None:
    """返回图片长边像素；无 Pillow 或无法解析时返回 None（视为无法判断，不拦截）。"""
    try:
        from PIL import Image
    except ImportError:
        return None
    import io
    try:
        im = Image.open(io.BytesIO(data))
    except Exception:  # noqa: BLE001
        return None
    return max(im.size)


def _parse_zone(value) -> tuple[float, float, float, float] | None:
    """'x0,y0,x1,y1'（归一化 0~1）→ tuple；非法返回 None。也接受 4 元素列表。"""
    if value is None:
        return None
    parts = value if isinstance(value, (list, tuple)) else str(value).replace("，", ",").split(",")
    if len(parts) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(v) for v in parts)
    except (ValueError, TypeError):
        return None
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        return None
    return (x0, y0, x1, y1)


def _find_cjk_font(explicit: str | None = None) -> tuple[str, int] | None:
    """找一款可用的中文字体，返回 (路径, ttc index)；找不到返回 None。"""
    if explicit:
        if Path(explicit).is_file():
            return (explicit, 0)
        print(f"[WARN] 指定字体不存在: {explicit}，改为自动搜索", file=sys.stderr)
    for path, idx in _CJK_FONT_CANDIDATES:
        if Path(path).is_file():
            return (path, idx)
    return None


_TITLE_BREAK_PUNCT = "：:，,、；;—|"


def _split_title(title: str, max_lines: int = TITLE_MAX_LINES) -> list[str]:
    """标题折行：≤8 字一行；更长优先在离中点最近的标点处折（标点丢弃），否则按字数对半。"""
    t = title.strip()
    if max_lines < 2 or len(t) <= 8:
        return [t]
    mid = len(t) // 2
    best = None
    for i, ch in enumerate(t):
        if ch in _TITLE_BREAK_PUNCT and 2 <= i <= len(t) - 3:
            if best is None or abs(i - mid) < abs(best - mid):
                best = i
    if best is not None:
        return [t[:best].strip(), t[best + 1:].strip()]
    return [t[:mid].strip(), t[mid:].strip()]


def _compose_title(img_data: bytes, title: str, zone=None, font_path: str | None = None) -> bytes:
    """把标题合成到标题区：自动字号、自动折行、按底色选深浅字色并加细描边。

    模型渲染长中文标题不遵守画布边界（实测五种约束写法全部被裁，还出过「一」变「5」），
    所以封面 prompt 里不写字，标题在这里精确排版。无 Pillow 或找不到中文字体时原样
    返回并告警，不阻断流程。
    """
    zone = zone or DEFAULT_TITLE_ZONE
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageStat
    except ImportError:
        print("[WARN] 未安装 Pillow，无法合成标题（pip install Pillow）", file=sys.stderr)
        return img_data
    font = _find_cjk_font(font_path)
    if not font:
        print("[WARN] 未找到中文字体，无法合成标题。macOS 自带 PingFang/Hiragino；"
              "Linux 请 apt install fonts-noto-cjk；或用 --title-font 指定。", file=sys.stderr)
        return img_data
    fpath, fidx = font
    try:
        im = Image.open(io.BytesIO(img_data))
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 图片无法解析，跳过标题合成: {e}", file=sys.stderr)
        return img_data
    fmt = im.format or "PNG"
    im = im.convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = int(W * zone[0]), int(H * zone[1]), int(W * zone[2]), int(H * zone[3])
    zw, zh = x1 - x0, y1 - y0
    if zw < 20 or zh < 20:
        print("[WARN] 标题区过小，跳过合成", file=sys.stderr)
        return img_data

    def measure(lines, size):
        f = ImageFont.truetype(fpath, size, index=fidx)
        boxes = [f.getbbox(l) for l in lines]
        widths = [b[2] - b[0] for b in boxes]
        heights = [b[3] - b[1] for b in boxes]
        gap = int(size * 0.25)
        return f, boxes, widths, heights, gap, sum(heights) + gap * (len(lines) - 1)

    def fit(lines):
        lo, hi, best = 8, zh, 8
        while lo <= hi:
            mid = (lo + hi) // 2
            _, _, widths, _, _, total_h = measure(lines, mid)
            if max(widths) <= zw * 0.94 and total_h <= zh * 0.92:
                best, lo = mid, mid + 1
            else:
                hi = mid - 1
        return best

    lines = [title.strip()]
    size = fit(lines)
    if len(lines[0]) > 8:
        alt = _split_title(lines[0])
        if len(alt) == 2:
            alt_size = fit(alt)
            if alt_size > size * 1.15:  # 折行明显更大才折
                lines, size = alt, alt_size
    if size < H * 0.045:
        print(f"[WARN] 标题「{title}」在标题区只能排到 {size}px，建议缩到 12 字以内或加大标题区",
              file=sys.stderr)

    f, boxes, widths, heights, gap, total_h = measure(lines, size)
    lum = ImageStat.Stat(im.crop((x0, y0, x1, y1)).convert("L")).mean[0]
    light_text = lum < 140
    fill = (255, 255, 255) if light_text else (30, 30, 30)
    stroke = (0, 0, 0) if light_text else (255, 255, 255)
    sw = max(1, size // 28)
    draw = ImageDraw.Draw(im)
    y = y0 + (zh - total_h) // 2
    for line, box, w, h in zip(lines, boxes, widths, heights):
        x = x0 + (zw - w) // 2 - box[0]
        draw.text((x, y - box[1]), line, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
        y += h + gap
    buf = io.BytesIO()
    if fmt == "JPEG":
        im.save(buf, format="JPEG", quality=92)
    else:
        im.save(buf, format="PNG")
    _info(f"标题已合成：{' / '.join(lines)}（{size}px，{'浅字' if light_text else '深字'}）")
    return buf.getvalue()


def _zone_edge_density(img_data: bytes, zone=None) -> float | None:
    """标题区边缘密度（0~255）。留白应接近 0；主体被画进来会明显升高。无 Pillow 返回 None。"""
    zone = zone or DEFAULT_TITLE_ZONE
    try:
        from PIL import Image, ImageFilter, ImageStat
    except ImportError:
        return None
    try:
        im = Image.open(io.BytesIO(img_data)).convert("L")
    except Exception:  # noqa: BLE001
        return None
    W, H = im.size
    crop = im.crop((int(W * zone[0]), int(H * zone[1]), int(W * zone[2]), int(H * zone[3])))
    if crop.size[0] < 4 or crop.size[1] < 4:
        return None
    return ImageStat.Stat(crop.filter(ImageFilter.FIND_EDGES)).mean[0]


def _image_stddev(img_data: bytes) -> float | None:
    try:
        from PIL import Image, ImageStat
    except ImportError:
        return None
    try:
        im = Image.open(io.BytesIO(img_data)).convert("L")
    except Exception:  # noqa: BLE001
        return None
    return ImageStat.Stat(im).stddev[0]


def _cover_problems(img_data: bytes, zone=None) -> list[str]:
    """出图后的纯代码检查（不需要任何模型），返回问题列表，空即通过。"""
    problems = []
    edge = _image_long_edge(img_data)
    if edge is not None and edge < MIN_LONG_EDGE:
        problems.append(f"长边 {edge}px 不足 {MIN_LONG_EDGE}px")
    sd = _image_stddev(img_data)
    if sd is not None and sd < MONO_STDDEV_THRESHOLD:
        problems.append(f"整图近单色（灰度标准差 {sd:.1f}），疑似生成失败")
    if zone:
        d = _zone_edge_density(img_data, zone)
        if d is not None and d > ZONE_BUSY_THRESHOLD:
            problems.append(f"标题区不干净（边缘密度 {d:.1f} > {ZONE_BUSY_THRESHOLD}），主体可能画进了标题位")
    return problems


def _generate_with_checks(label: str, gen, zone=None) -> bytes:
    """生成并做纯代码检查，不合格就重试，所有结果里取最好的一张。

    端点返回的尺寸波动很大（同参数实测 384px~1584px 都出现过）；模型也时常无视
    「标题区留白」的要求。实测同一 prompt 连着跑，返回 683px 的概率接近一半，
    只重试一次不够——跑完整篇文章五张图，仍有两张卡在 683px。仍不合格则保留较好的
    并告警，由 Agent 决定是否再跑。
    """
    def score(data):
        probs = _cover_problems(data, zone)
        return (-len(probs), _image_long_edge(data) or 0), probs

    best = gen()
    best_score, best_probs = score(best)
    for attempt in range(CHECK_RETRIES):
        if not best_probs:
            return best
        _info(f"{label} 检查未通过（{'；'.join(best_probs)}），重试第 {attempt + 1} 次")
        cand = gen()
        cand_score, cand_probs = score(cand)
        if cand_score > best_score:
            best, best_score, best_probs = cand, cand_score, cand_probs
    if best_probs:
        print(f"[WARN] {label} 重试后仍有问题：{'；'.join(best_probs)}\n"
              f"       已保留较好的一张，可重跑本条。分辨率问题勿设 resolution: 4K，"
              f"实测会连比例一起失效。", file=sys.stderr)
    return best


def _write_if_not_worse(out_path: Path, img_data: bytes, zone=None) -> bool:
    """写出图片；若新图不合格而磁盘上已有一张合格的同名图，则保留旧图。

    端点的分辨率是随机的，重跑同一条 prompt 完全可能拿到更差的一张。实测跑完
    整篇文章后补跑两张，其中一张把上一轮已经合格的图覆盖成了 683px——重跑只能
    让结果变好，不该让它变坏。
    """
    new_probs = _cover_problems(img_data, zone)
    if new_probs:
        for old in out_path.parent.glob(out_path.stem + ".*"):
            if old.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                continue
            if not _cover_problems(old.read_bytes(), zone):
                print(f"[WARN] {out_path.stem} 新图不合格（{'；'.join(new_probs)}），"
                      f"磁盘上的 {old.name} 是合格的，保留旧图未覆盖。", file=sys.stderr)
                return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_data)
    _clear_stale_siblings(out_path)
    return True


def _clear_stale_siblings(out_path: Path) -> None:
    """删掉同名不同后缀的旧图。

    返回格式会变（同一 prompt 这次 PNG 下次 JPEG），不清理的话目录里会同时留下
    05-x.jpg 和 05-x.png，后续按 glob 取文件时可能拿到上一次的旧图——排查过一次
    「重生成没生效」，实际是取到了残留的旧后缀。
    """
    for f in out_path.parent.glob(out_path.stem + ".*"):
        if f != out_path and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            f.unlink()
            print(f"[WARN] 已删除同名旧图 {f.name}（本次返回 {out_path.suffix}）。"
                  f"若该图已插入 article.md / article.html，引用会断，"
                  f"须把 imgs/{f.name} 改成 imgs/{out_path.name}。", file=sys.stderr)


def _detect_image_ext(data: bytes) -> str | None:
    """按文件头识别图片格式，返回 .png/.jpg/.webp/.gif；无法识别返回 None。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    return None


def _read_prompt_file(path: Path) -> tuple[str, dict]:
    """读取 prompt 文件，支持 YAML frontmatter。"""
    text = path.read_text(encoding="utf-8")

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            if not isinstance(meta, dict):
                meta = {}
            prompt = parts[2].strip()
            return prompt, meta

    return text.strip(), {}


def _resolve_title(meta: dict, cli_title, cli_zone) -> tuple[str | None, tuple | None]:
    """标题与标题区：CLI 优先，其次 frontmatter 的 title / title_zone。zone 非法直接报错。"""
    raw_title = cli_title if cli_title is not None else meta.get("title")
    title = str(raw_title).strip() if raw_title not in (None, "") else None
    raw_zone = cli_zone if cli_zone else meta.get("title_zone")
    zone = _parse_zone(raw_zone) if raw_zone else None
    if raw_zone and zone is None:
        _err(f"title_zone 须为归一化坐标 'x0,y0,x1,y1'（0~1，如 0.55,0.30,0.92,0.70），当前: {raw_zone!r}")
    return title, zone


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
    p_gen.add_argument("--title", help="合成到封面的标题文案（覆盖 frontmatter 的 title）")
    p_gen.add_argument("--title-zone", help="标题区归一化坐标 x0,y0,x1,y1（覆盖 frontmatter 的 title_zone）")
    p_gen.add_argument("--title-font", help="中文字体文件路径（默认自动搜索系统字体）")

    p_batch = sub.add_parser("batch", help="批量生成（读取目录下所有 prompt 文件）")
    p_batch.add_argument("prompts_dir", help="prompt 文件目录")
    p_batch.add_argument("-o", "--output-dir", help="输出目录（默认同目录）")
    p_batch.add_argument("--size", help="统一尺寸")
    p_batch.add_argument("--quality", help="统一质量")
    p_batch.add_argument("--title-font", help="中文字体文件路径（标题/标题区从各 prompt 的 frontmatter 读）")

    p_comp = sub.add_parser("compose", help="把标题合成到已有图片的标题区（不调 API）")
    p_comp.add_argument("image", help="图片路径")
    p_comp.add_argument("--title", required=True, help="标题文案")
    p_comp.add_argument("--title-zone", help="归一化 x0,y0,x1,y1，默认 0.55,0.30,0.92,0.70")
    p_comp.add_argument("--title-font", help="中文字体文件路径")
    p_comp.add_argument("-o", "--output", help="输出路径（默认覆盖原图）")

    p_chk = sub.add_parser("check", help="出图后纯代码检查：尺寸 / 单色 / 标题区干净度（不调 API）")
    p_chk.add_argument("image", help="图片路径")
    p_chk.add_argument("--title-zone", help="归一化 x0,y0,x1,y1；仅用于合成标题前确认该区域是空的。"
                            "标题由模型直接画进图里时不要用——文字本身就是高边缘密度，会误判")

    p_test = sub.add_parser("test", help="测试 API 连通性")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "compose":
        src = Path(args.image)
        if not src.exists():
            _err(f"文件不存在: {src}")
        zone = _parse_zone(args.title_zone) if args.title_zone else None
        if args.title_zone and zone is None:
            _err(f"title_zone 非法: {args.title_zone!r}")
        data = _compose_title(src.read_bytes(), args.title, zone=zone, font_path=args.title_font)
        out = Path(args.output) if args.output else src
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        _ok(f"已保存: {out}")
        return

    if args.command == "check":
        src = Path(args.image)
        if not src.exists():
            _err(f"文件不存在: {src}")
        # 标题区检查只在显式给 --title-zone 时做：默认路径标题由模型画在区内，查了就是误报
        zone = _parse_zone(args.title_zone) if args.title_zone else None
        if args.title_zone and zone is None:
            _err(f"title_zone 非法: {args.title_zone!r}")
        data = src.read_bytes()
        edge = _image_long_edge(data); sd = _image_stddev(data)
        if edge is None:
            _err("无法读取图片（缺少 Pillow 或文件损坏）")
        line = f"长边 {edge}px | 灰度标准差 {sd:.1f}"
        if zone:
            line += f" | 标题区边缘密度 {_zone_edge_density(data, zone):.1f}（阈值 {ZONE_BUSY_THRESHOLD}）"
        _info(line)
        problems = _cover_problems(data, zone)
        if problems:
            for pr in problems:
                print(f"[FAIL] {pr}", file=sys.stderr)
            sys.exit(1)
        _ok("检查通过")
        return

    _require_repo_root()
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
        img_data = generate_image(model_cfg, "A simple blue circle on white background",
                                  size="1024x1024", quality="standard", aspect="1:1")
        _ok(f"API 连通正常，收到 {len(img_data)} 字节图片数据")
        return

    if args.command == "generate":
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            _err(f"文件不存在: {prompt_path}")

        prompt, meta = _read_prompt_file(prompt_path)

        size, crop_aspect = _resolve_size(args.size, meta)
        quality = args.quality or meta.get("quality")
        title, zone = _resolve_title(meta, args.title, args.title_zone)
        check_zone = zone or (DEFAULT_TITLE_ZONE if title else None)

        def gen():
            data = generate_image(model_cfg, prompt, size=size, quality=quality,
                                  aspect=crop_aspect, resolution=meta.get("resolution"))
            # 端点已按比例出图时裁切是空操作（差异 <1% 直接返回原图）
            return _crop_to_aspect(data, crop_aspect) if crop_aspect else data

        img_data = _generate_with_checks(prompt_path.name, gen, zone=check_zone)
        if title:
            img_data = _compose_title(img_data, title, zone=check_zone, font_path=args.title_font)

        ext = _detect_image_ext(img_data) or ".png"
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() not in (ext, ".jpeg" if ext == ".jpg" else ext):
                print(f"[WARN] 输出后缀 {output_path.suffix or '(无)'} 与实际图片格式 {ext} 不一致", file=sys.stderr)
        else:
            output_path = prompt_path.with_suffix(ext)
        if _write_if_not_worse(output_path, img_data, zone=check_zone):
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
        failed: list[tuple[str, str]] = []
        for i, pf in enumerate(prompt_files, 1):
            _info(f"[{i}/{len(prompt_files)}] {pf.name}")
            # 单条失败不该丢掉整批：批量常跑几十条，一次读超时就全废代价太高
            try:
                prompt, meta = _read_prompt_file(pf)

                size, crop_aspect = _resolve_size(args.size, meta)
                quality = args.quality or meta.get("quality")
                title, zone = _resolve_title(meta, None, None)
                check_zone = zone or (DEFAULT_TITLE_ZONE if title else None)

                def gen(p=prompt, sz=size, q=quality, ca=crop_aspect, m=meta):
                    data = generate_image(model_cfg, p, size=sz, quality=q, aspect=ca,
                                          resolution=m.get("resolution"))
                    return _crop_to_aspect(data, ca) if ca else data

                img_data = _generate_with_checks(pf.name, gen, zone=check_zone)
                if title:
                    img_data = _compose_title(img_data, title, zone=check_zone,
                                              font_path=args.title_font)
                out_path = output_dir / (pf.stem + (_detect_image_ext(img_data) or ".png"))
                if _write_if_not_worse(out_path, img_data, zone=check_zone):
                    _ok(f"  → {out_path}")
            except SystemExit:
                # _err 已打印原因；记下并继续下一条
                failed.append((pf.name, "见上方错误"))
                print(f"[WARN] {pf.name} 失败，继续处理后续文件", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                failed.append((pf.name, f"{type(e).__name__}: {e}"))
                print(f"[WARN] {pf.name} 失败（{type(e).__name__}: {e}），继续处理后续文件",
                      file=sys.stderr)

            if i < len(prompt_files):
                time.sleep(1)

        done = len(prompt_files) - len(failed)
        if failed:
            print(f"[WARN] 批量结束：成功 {done}，失败 {len(failed)}", file=sys.stderr)
            for name, why in failed:
                print(f"       - {name}: {why}", file=sys.stderr)
            print("       重跑本命令即可，已成功的会被覆盖重生成；"
                  "或把失败的 prompt 单独放一个目录再跑。", file=sys.stderr)
            sys.exit(1)
        _ok(f"批量生成完成：{done} 张")


if __name__ == "__main__":
    main()
