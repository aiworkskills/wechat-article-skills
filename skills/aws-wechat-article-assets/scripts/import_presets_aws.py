#!/usr/bin/env python3
"""
导入 `.aws` 预设包（ZIP 格式）：解压到 `.aws-article/tmp/`，合并到 `.aws-article/presets/`；
包根若含 `config.yaml`：
  - 若本地尚无 `.aws-article/config.yaml`，则从包内复制一份；
  - 若本地已存在，则**不覆盖**；按包内字段在本地同名路径上递归比对，将差异以 **JSON 数组** 打印到 **stdout**（供智能体读取后询问用户再手改配置）。
    每条为 {"key": "点分路径", "old": …, "new": …}。其它日志在 stderr。

aws.env 增量写入：
  - 包内 config.yaml 的敏感字段（wechat_appid/wechat_appsecret、writing_model.api_key、
    image_model.api_key）会按 SECRET_FIELD_MAP 增量写入仓库根 `aws.env`：
      * 包内字段为空 → 不动 aws.env 现有键
      * aws.env 无该键 → 追加
      * aws.env 已有相同值 → 跳过
      * aws.env 已有不同值 → 写入前备份 `aws.env.bak.{ts}` 后覆盖
  - stderr 仅打印键名清单，不打印密钥值；保留原文件顺序、空行与注释。

运行前若缺少 `.aws-article` 则创建；若缺少 `.aws-article/tmp` 则创建。每次执行前若 `tmp` 已存在则整目录删除再解压；合并完成后保留解压内容供核对，下次执行会再次清空 `tmp` 再解压。

合并规则（以服务端为准的「替换式」）：
  - 对每个预设子目录，若**包内存在**该子目录，则**先清空本地 `.aws-article/presets/<同名>/`** 再写入包内内容——确保新包移除的旧文件不会残留；
  - 若包内**不存在**某子目录，本地对应子目录**保持不动**（不受本次导入影响）。

bundle 输入支持两种形态：
  - 本地 `.aws` 文件路径；
  - 白名单 HTTPS URL：`https://` 开头，host 为 `aiworkskills.cn` 或其子域，路径以 `.aws` 结尾。
    下载缓存到 `.aws-article/downloads/<原文件名>`（不受 tmp 清空影响，供事后核对）。

用法（仓库根）：
  python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws
  python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws --dry-run
  python skills/aws-wechat-article-assets/scripts/import_presets_aws.py https://aiworkskills.cn/bundles/brand-a.aws
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[misc, assignment]

PRESET_SUBDIRS = (
    "closing-blocks",
    "cover-styles",
    "formatting",
    "image-styles",
    "sticker-styles",
    "structures",
    "title-styles",
)

SKIP_NAMES = frozenset({"__MACOSX", ".DS_Store"})

ALLOWED_HOST_EXACT = "aiworkskills.cn"
ALLOWED_HOST_SUFFIX = ".aiworkskills.cn"
DOWNLOAD_TIMEOUT_SEC = 30

# config.yaml 字段（点分路径） → aws.env 键名。
# 当前前端导出仅支持单微信账号，固定映射到槽位 1。
SECRET_FIELD_MAP: tuple[tuple[str, str], ...] = (
    ("wechat_appid", "WECHAT_1_APPID"),
    ("wechat_appsecret", "WECHAT_1_APPSECRET"),
    ("writing_model.api_key", "WRITING_MODEL_API_KEY"),
    ("image_model.api_key", "IMAGE_MODEL_API_KEY"),
)


def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def _validate_url(url: str, allow_any_host: bool) -> None:
    p = urlparse(url)
    if p.scheme != "https":
        _err(f"仅允许 https:// 下载预设包，收到: {p.scheme}://")
    host = (p.hostname or "").lower()
    if not allow_any_host:
        if host != ALLOWED_HOST_EXACT and not host.endswith(ALLOWED_HOST_SUFFIX):
            _err(f"域名不在白名单（仅 aiworkskills.cn 及其子域）: {host}")
    if not Path(p.path).name.endswith(".aws"):
        _err("URL 路径须以 .aws 结尾")


def _download_bundle(url: str, repo: Path) -> Path:
    downloads = repo / ".aws-article" / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    fname = Path(urlparse(url).path).name or "bundle.aws"
    local = downloads / fname
    tmp_out = local.with_suffix(local.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "aws-wechat-article-assets/1.0"})
    _info(f"下载中: {url}")
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SEC) as resp, open(tmp_out, "wb") as out:
            shutil.copyfileobj(resp, out)
    except urllib.error.HTTPError as e:
        _err(f"HTTP {e.code} 下载失败: {url}")
    except urllib.error.URLError as e:
        _err(f"网络错误: {e.reason}")
    shutil.move(str(tmp_out), str(local))
    if not zipfile.is_zipfile(local):
        _err(f"下载内容不是有效 ZIP（已保留 {local} 供排查）")
    _ok(f"已下载: {local.as_posix()}")
    return local


def _err(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _info(msg: str) -> None:
    print(f"[INFO] {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"[OK] {msg}", file=sys.stderr)


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


def _should_skip_path(path: Path) -> bool:
    parts = path.parts
    if "__MACOSX" in parts:
        return True
    if path.name == ".DS_Store":
        return True
    return False


def _staging_dir(repo: Path) -> Path:
    """固定解压暂存路径：`.aws-article/tmp`（每次导入前会清空该目录）。"""
    return repo / ".aws-article" / "tmp"


def _reset_staging(staging: Path) -> None:
    """若暂存目录存在则删除并重建为空目录，供本次解压使用。"""
    if staging.exists():
        _info(f"清空暂存目录: {staging.as_posix()}")
        shutil.rmtree(staging, ignore_errors=False)
    staging.mkdir(parents=True, exist_ok=True)


def _safe_extractall(zf: zipfile.ZipFile, dest: Path) -> None:
    """安全解压：防御 ZIP slip（路径穿越）攻击。

    标准 `zf.extractall` 不校验成员路径，恶意 ZIP 可通过 `../` 或绝对路径
    让解压结果落在 `dest` 以外。本实现逐项校验：
      1. 拒绝绝对路径；
      2. 拒绝含 `..` 段的路径；
      3. 解析目标绝对路径后，验证仍位于 `dest` 内。
    任一项违反即立即退出，不写入任何文件。
    """
    dest_resolved = dest.resolve()
    for name in zf.namelist():
        member_path = Path(name)
        if member_path.is_absolute():
            _err(f"ZIP 内含绝对路径（可能的路径穿越攻击），已拒绝解压: {name}")
        if ".." in member_path.parts:
            _err(f"ZIP 内含 '..' 段（可能的路径穿越攻击），已拒绝解压: {name}")
        target = (dest / name).resolve()
        try:
            target.relative_to(dest_resolved)
        except ValueError:
            _err(f"ZIP 内路径指向解压目录外（可能的路径穿越攻击），已拒绝解压: {name}")
    zf.extractall(dest)


def _resolve_package_root(extracted: Path) -> Path:
    """若 ZIP 内仅一层目录且内含预设或 config，则以其为包根。"""
    items = [p for p in extracted.iterdir() if p.name not in SKIP_NAMES and not p.name.startswith(".")]
    if len(items) == 1 and items[0].is_dir():
        candidate = items[0]
        if (candidate / "config.yaml").is_file():
            return candidate
        if any((candidate / d).is_dir() for d in PRESET_SUBDIRS):
            return candidate
    return extracted


def _merge_preset_dir(src: Path, dest: Path, dry_run: bool) -> int:
    n = 0
    for f in src.rglob("*"):
        if not f.is_file() or _should_skip_path(f):
            continue
        rel = f.relative_to(src)
        out = dest / rel
        if dry_run:
            _info(f"  [dry-run] {out.as_posix()}")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
        n += 1
    return n


def _config_diff(old: dict[str, Any], new: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    """对包内 new 中出现的每个键，若在 old 中存在且值不同则记录；嵌套 dict 递归到叶子。"""
    out: list[dict[str, Any]] = []
    for k, nv in new.items():
        path = f"{prefix}.{k}" if prefix else k
        if k not in old:
            continue
        ov = old[k]
        if isinstance(nv, dict) and isinstance(ov, dict):
            out.extend(_config_diff(ov, nv, path))
        elif nv != ov:
            out.append({"key": path, "old": ov, "new": nv})
    return out


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    if yaml is None:
        _err("需要 PyYAML：请 pip install pyyaml")
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return {}
    if not isinstance(data, dict):
        _err(f"{label} 根节点须为 YAML mapping（字典），实际为 {type(data).__name__}")
    return data


def _print_config_diff_json(diffs: list[dict[str, Any]]) -> None:
    print(json.dumps(diffs, ensure_ascii=False, indent=2))


def _parse_dotenv(content: str) -> dict[str, str]:
    """与 skills/aws-wechat-article-main/scripts/validate_env.py 的 _parse_dotenv 保持同步。"""
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


def _get_dotted(d: Any, path: str) -> Any:
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _serialize_dotenv_line(key: str, value: str) -> str:
    if any(c in value for c in (' ', '\t', '#', '"', "'", '$', '\\', '\n', '\r')):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'{key}="{escaped}"'
    return f"{key}={value}"


def _write_aws_env_incremental(repo: Path, package_config: dict, dry_run: bool) -> None:
    """按 SECRET_FIELD_MAP 把包内 config.yaml 的密钥字段增量写入仓库根 aws.env。

    规则：
      - 包内字段为空字符串/None → 跳过（不会动 aws.env 现有键）
      - 现有 aws.env 无该键 → 新增（追加到末尾）
      - 现有值 == 包内值 → 跳过
      - 现有值 != 包内值 → 标记覆盖；写入前备份 aws.env.bak.{ts}
      - 保留原文件顺序、空行、注释；行内只替换需要覆盖的键
      - stderr 仅打印键名清单，不打印密钥值
    """
    aws_env_path = repo / "aws.env"

    candidates: dict[str, str] = {}
    for cfg_path, env_key in SECRET_FIELD_MAP:
        v = _get_dotted(package_config, cfg_path)
        if isinstance(v, str) and v.strip():
            candidates[env_key] = v

    if not candidates:
        _info("包内未发现可写入 aws.env 的密钥字段，跳过 aws.env 更新")
        return

    if aws_env_path.is_file():
        existing_content = aws_env_path.read_text(encoding="utf-8")
        existing = _parse_dotenv(existing_content)
    else:
        existing_content = ""
        existing = {}

    added: list[str] = []
    overwritten: list[str] = []
    unchanged: list[str] = []
    for k, new_v in candidates.items():
        if k not in existing:
            added.append(k)
        elif existing[k] == new_v:
            unchanged.append(k)
        else:
            overwritten.append(k)

    if not added and not overwritten:
        _info(f"aws.env 无需更新（包内 {len(candidates)} 项与现有一致）")
        return

    if dry_run:
        bits = []
        if added:
            bits.append(f"新增 {len(added)} 项 [{', '.join(added)}]")
        if overwritten:
            bits.append(f"覆盖 {len(overwritten)} 项 [{', '.join(overwritten)}]")
        _info("[dry-run] aws.env " + "，".join(bits))
        return

    if overwritten and aws_env_path.is_file():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = aws_env_path.with_name(f"aws.env.bak.{ts}")
        shutil.copy2(aws_env_path, backup)
        _ok(f"备份: {backup.as_posix()}")

    overwrite_set = set(overwritten)
    lines = existing_content.splitlines() if existing_content else []
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = line.partition("=")[0].strip()
        if key in overwrite_set:
            new_lines.append(_serialize_dotenv_line(key, candidates[key]))
        else:
            new_lines.append(line)

    for k in added:
        new_lines.append(_serialize_dotenv_line(k, candidates[k]))

    final = "\n".join(new_lines)
    if not final.endswith("\n"):
        final += "\n"
    aws_env_path.write_text(final, encoding="utf-8")

    parts = []
    if added:
        parts.append(f"新增 {len(added)} 项 [{', '.join(added)}]")
    if overwritten:
        parts.append(f"覆盖 {len(overwritten)} 项 [{', '.join(overwritten)}]")
    if unchanged:
        parts.append(f"未变 {len(unchanged)} 项 [{', '.join(unchanged)}]")
    _ok(f"aws.env 写入：{'，'.join(parts)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="导入 .aws 预设包到 .aws-article/presets；config 仅首次复制，已有则 stdout 输出差异 JSON"
    )
    parser.add_argument("bundle", help="路径或 URL：本地 .aws 文件，或 https://aiworkskills.cn/**/*.aws")
    parser.add_argument("--dry-run", action="store_true", help="只打印将执行的操作，不写盘")
    parser.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    parser.add_argument(
        "--allow-any-host",
        action="store_true",
        help="调试用，放宽域名白名单（仍强制 https）；不建议生产使用",
    )
    args = parser.parse_args()

    repo = _find_repo_root(Path(args.repo))
    _ensure_aws_article_dir(repo)

    raw = args.bundle
    if _is_url(raw):
        _validate_url(raw, args.allow_any_host)
        bundle = _download_bundle(raw, repo)
    else:
        bundle = Path(raw).resolve()

    if not bundle.is_file():
        _err(f"文件不存在: {bundle}")
    if not zipfile.is_zipfile(bundle):
        _err(f"不是有效的 ZIP 包（.aws 须为 zip）: {bundle}")

    presets_root = repo / ".aws-article" / "presets"
    config_dest = repo / ".aws-article" / "config.yaml"
    staging = _staging_dir(repo)

    _reset_staging(staging)
    with zipfile.ZipFile(bundle, "r") as zf:
        _safe_extractall(zf, staging)

    root = _resolve_package_root(staging)
    _info(f"解压目录: {staging.as_posix()}")
    _info(f"包根解析为: {root}")

    has_any = (root / "config.yaml").is_file() or any((root / d).is_dir() for d in PRESET_SUBDIRS)
    if not has_any:
        _err("包内未找到 config.yaml 或任一预设目录（closing-blocks / formatting / …），请检查 .aws 内容。")

    presets_root.mkdir(parents=True, exist_ok=True)

    total_files = 0
    for name in PRESET_SUBDIRS:
        src = root / name
        if not src.is_dir():
            # 部分平台导出的包把预设放在包根下 presets/<子目录>/
            src = root / "presets" / name
        if not src.is_dir():
            continue
        dest = presets_root / name
        if args.dry_run:
            if dest.exists():
                _info(f"替换预设目录（先清空后合并）: {name} -> {dest.as_posix()}")
            else:
                _info(f"新增预设目录: {name} -> {dest.as_posix()}")
        else:
            if dest.exists():
                shutil.rmtree(dest)
                _info(f"已清空本地预设目录: {dest.as_posix()}")
            dest.mkdir(parents=True, exist_ok=True)
        n = _merge_preset_dir(src, dest, args.dry_run)
        total_files += n
        if n:
            _ok(f"{name}: {n} 个文件")

    cfg = root / "config.yaml"
    if cfg.is_file():
        new_map = _load_yaml_mapping(cfg, "包内 config.yaml")
        if not config_dest.is_file():
            if args.dry_run:
                _info(f"[dry-run] 将复制包内 config 至 {config_dest.as_posix()}（本地尚无 config.yaml）")
            else:
                shutil.copy2(cfg, config_dest)
                _ok(f"已复制包内配置（本地原无）: {config_dest}")
        else:
            old_map = _load_yaml_mapping(config_dest, "本地 config.yaml")
            diffs = _config_diff(old_map, new_map)
            _print_config_diff_json(diffs)
            _info(
                f"config 差异 {len(diffs)} 项已输出至 stdout（JSON）；未修改 {config_dest.as_posix()}，请智能体根据用户确认再更新"
            )
        _write_aws_env_incremental(repo, new_map, args.dry_run)
    else:
        _info("包内无 config.yaml，跳过全局配置与 aws.env 更新")

    if args.dry_run:
        _ok(f"dry-run 完成（共将写入约 {total_files} 个预设文件 + 如上 config）；解压保留在 {staging.as_posix()}")
    else:
        _ok(f"导入完成（预设文件合计 {total_files}）；解压保留在 {staging.as_posix()} 供核对")


if __name__ == "__main__":
    main()
