#!/usr/bin/env python3
"""
导入 `.aws` 预设包（ZIP 格式）：解压到 `.aws-article/tmp/`，合并到 `.aws-article/presets/`；
包根若含 `config.yaml`：
  - 若本地尚无 `.aws-article/config.yaml`，则从包内复制一份；
  - 若本地已存在，则**不覆盖**；按包内字段在本地同名路径上递归比对，将差异以 **JSON 数组** 打印到 **stdout**（供智能体读取后询问用户再手改配置）。
    每条为 {"key": "点分路径", "old": …, "new": …}。其它日志在 stderr。

运行前若缺少 `.aws-article` 则创建；若缺少 `.aws-article/tmp` 则创建。每次执行前若 `tmp` 已存在则整目录删除再解压；合并完成后保留解压内容供核对，下次执行会再次清空 `tmp` 再解压。

合并规则：对每个预设子目录内文件，按相对路径写入目标；同名则覆盖，新文件则新增。
不包含密钥：包内 config 仅为运营配置模板（仓库内密钥在 aws.env）。

用法（仓库根）：
  python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws
  python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[misc, assignment]

PRESET_SUBDIRS = (
    "closing-blocks",
    "formatting",
    "image-styles",
    "sticker-styles",
    "structures",
    "title-styles",
)

SKIP_NAMES = frozenset({"__MACOSX", ".DS_Store"})


def _err(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _info(msg: str) -> None:
    print(f"[INFO] {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"[OK] {msg}", file=sys.stderr)


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / ".aws-article").is_dir():
            return p
    for p in [cur] + list(cur.parents):
        if (p / ".git").is_dir():
            return p
    _err("未找到仓库根（向上查找含 .aws-article 或 .git 的目录失败）。请在仓库根目录执行。")


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="导入 .aws 预设包到 .aws-article/presets；config 仅首次复制，已有则 stdout 输出差异 JSON"
    )
    parser.add_argument("bundle", help="路径：.aws 文件（ZIP）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将执行的操作，不写盘")
    parser.add_argument("--repo", default=".", help="仓库根（默认当前目录）")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    if not bundle.is_file():
        _err(f"文件不存在: {bundle}")
    if not zipfile.is_zipfile(bundle):
        _err(f"不是有效的 ZIP 包（.aws 须为 zip）: {bundle}")

    repo = _find_repo_root(Path(args.repo))
    _ensure_aws_article_dir(repo)
    presets_root = repo / ".aws-article" / "presets"
    config_dest = repo / ".aws-article" / "config.yaml"
    staging = _staging_dir(repo)

    _reset_staging(staging)
    with zipfile.ZipFile(bundle, "r") as zf:
        zf.extractall(staging)

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
            _info(f"合并预设目录: {name} -> {dest.as_posix()}")
        else:
            dest.mkdir(parents=True, exist_ok=True)
        n = _merge_preset_dir(src, dest, args.dry_run)
        total_files += n
        if n:
            _ok(f"{name}: {n} 个文件")

    cfg = root / "config.yaml"
    if cfg.is_file():
        if not config_dest.is_file():
            if args.dry_run:
                _info(f"[dry-run] 将复制包内 config 至 {config_dest.as_posix()}（本地尚无 config.yaml）")
            else:
                shutil.copy2(cfg, config_dest)
                _ok(f"已复制包内配置（本地原无）: {config_dest}")
        else:
            old_map = _load_yaml_mapping(config_dest, "本地 config.yaml")
            new_map = _load_yaml_mapping(cfg, "包内 config.yaml")
            diffs = _config_diff(old_map, new_map)
            _print_config_diff_json(diffs)
            _info(
                f"config 差异 {len(diffs)} 项已输出至 stdout（JSON）；未修改 {config_dest.as_posix()}，请智能体根据用户确认再更新"
            )
    else:
        _info("包内无 config.yaml，跳过全局配置")

    if args.dry_run:
        _ok(f"dry-run 完成（共将写入约 {total_files} 个预设文件 + 如上 config）；解压保留在 {staging.as_posix()}")
    else:
        _ok(f"导入完成（预设文件合计 {total_files}）；解压保留在 {staging.as_posix()} 供核对")


if __name__ == "__main__":
    main()
