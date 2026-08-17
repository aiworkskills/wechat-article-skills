#!/usr/bin/env python3
"""
校验 `.aws-article/config.yaml` 与仓库根 `aws.env` 中的配置是否完整。

写作模型（可选）：
  - config.yaml → writing_model：base_url、model（provider 可选）
  - aws.env → WRITING_MODEL_API_KEY
  - 未配置时仅警告，不阻断校验

图片模型（可选）：
  - config.yaml → image_model：base_url、model（provider 可选）
  - aws.env → IMAGE_MODEL_API_KEY
  - 未配置时仅警告，不阻断校验

微信公众号（阻断级；例外：`publish_method: none` 时跳过本组）：
  - config.yaml：wechat_accounts（≥1）、wechat_api_base
  - aws.env：WECHAT_{i}_APPID、WECHAT_{i}_APPSECRET
  - wechat_{i}_name 仅用于展示与选择，未配置时仅警告

用法（仓库根）：
    python skills/aws-wechat-article-main/scripts/validate_env.py
    python skills/aws-wechat-article-main/scripts/validate_env.py --config .aws-article/config.yaml --env aws.env
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_dotenv(content: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


def _nonempty_str(val: object) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return True
    return False


def _parse_wechat_accounts(raw: object) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw >= 1 else None
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        try:
            n = int(s)
            return n if n >= 1 else None
        except ValueError:
            return None
    return None


def _writing_ok(cfg: dict, env: dict[str, str]) -> bool:
    wm = cfg.get("writing_model")
    if not isinstance(wm, dict):
        return False
    if not all(_nonempty_str(wm.get(k)) for k in ("base_url", "model")):
        return False
    if not _nonempty_str(env.get("WRITING_MODEL_API_KEY")):
        return False
    return True


def _image_ok(cfg: dict, env: dict[str, str]) -> bool:
    im = cfg.get("image_model")
    if not isinstance(im, dict):
        return False
    if not all(_nonempty_str(im.get(k)) for k in ("base_url", "model")):
        return False
    if not _nonempty_str(env.get("IMAGE_MODEL_API_KEY")):
        return False
    return True


def _wechat_ok(cfg: dict, env: dict[str, str]) -> bool:
    n = _parse_wechat_accounts(cfg.get("wechat_accounts"))
    if n is None:
        return False
    if not _nonempty_str(cfg.get("wechat_api_base")):
        return False
    for i in range(1, n + 1):
        if not _nonempty_str(env.get(f"WECHAT_{i}_APPID")):
            return False
        if not _nonempty_str(env.get(f"WECHAT_{i}_APPSECRET")):
            return False
    return True


def _missing_wechat_names(cfg: dict) -> list[str]:
    n = _parse_wechat_accounts(cfg.get("wechat_accounts"))
    if n is None:
        return []
    return [
        f"wechat_{i}_name"
        for i in range(1, n + 1)
        if not _nonempty_str(cfg.get(f"wechat_{i}_name"))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 config.yaml 与 aws.env 中的模型与微信配置"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".aws-article") / "config.yaml",
        help="默认 .aws-article/config.yaml",
    )
    parser.add_argument(
        "--env",
        type=Path,
        default=Path("aws.env"),
        help="默认 仓库根 aws.env",
    )
    parser.add_argument(
        "--agent-image-capable",
        action="store_true",
        default=False,
        help="兼容旧调用；图片模型未配置现在默认仅警告",
    )
    parser.add_argument(
        "--agent-writing-approved",
        action="store_true",
        default=False,
        help="兼容旧调用；写作模型未配置现在默认仅警告",
    )
    args = parser.parse_args()
    config_path: Path = args.config
    env_path: Path = args.env

    if not config_path.is_file():
        print("failed", file=sys.stdout)
        print(f"未找到配置文件: {config_path.resolve()}", file=sys.stdout)
        return 1

    if not env_path.is_file():
        print("failed", file=sys.stdout)
        print(f"未找到环境文件: {env_path.resolve()}", file=sys.stdout)
        return 1

    try:
        import yaml
    except ImportError:
        print("failed", file=sys.stdout)
        print("需要 PyYAML：pip install pyyaml", file=sys.stdout)
        return 1

    try:
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as e:
        print("failed", file=sys.stdout)
        print(f"无法读取 config.yaml: {e}", file=sys.stdout)
        return 1
    except yaml.YAMLError as e:
        print("failed", file=sys.stdout)
        print(f"config.yaml 解析失败: {e}", file=sys.stdout)
        return 1

    if not isinstance(cfg, dict):
        print("failed", file=sys.stdout)
        print("config.yaml 须为 YAML 键值对象（映射）", file=sys.stdout)
        return 1

    try:
        env_map = _parse_dotenv(env_path.read_text(encoding="utf-8"))
    except OSError as e:
        print("failed", file=sys.stdout)
        print(f"无法读取 aws.env: {e}", file=sys.stdout)
        return 1

    bad: list[str] = []
    warnings: list[str] = []

    pm = str(cfg.get("publish_method") or "").strip().lower()
    skip_wechat = pm == "none"
    if not skip_wechat and not _wechat_ok(cfg, env_map):
        bad.append("微信公众号配置不完整")
    if not _writing_ok(cfg, env_map):
        warnings.append("未配置外部写作模型（可选）")
    if not _image_ok(cfg, env_map):
        warnings.append("未配置外部图片模型（可选）")
    missing_names = _missing_wechat_names(cfg)
    if missing_names:
        warnings.append(f"微信公众号展示名未配置（可选）：{', '.join(missing_names)}")

    if bad:
        print("failed", file=sys.stdout)
        for line in bad:
            print(line, file=sys.stdout)
        for line in warnings:
            print(line, file=sys.stdout)
        return 1

    print("True", file=sys.stdout)
    if warnings:
        print(f"配置校验通过（{'；'.join(warnings)}）", file=sys.stdout)
    else:
        print("配置校验通过", file=sys.stdout)
    if skip_wechat:
        print(
            "（已跳过微信公众号校验：publish_method 为 none）",
            file=sys.stdout,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
