#!/usr/bin/env bash
# 将 skills/ 下的 7 个子 skill 安装到 .cursor/skills/，供 Cursor 加载。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.cursor/skills"
for d in "$ROOT/skills"/aws-wechat-article-*; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  rm -rf "$ROOT/.cursor/skills/$name"
  cp -R "$d" "$ROOT/.cursor/skills/"
  echo "Installed: $name"
done
echo "Done. Skills in .cursor/skills:"
ls -la "$ROOT/.cursor/skills/"
