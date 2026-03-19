#!/usr/bin/env bash
# 将 skills/ 下的所有 skill 和共享资源安装到 .cursor/skills/，供 Cursor 加载。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.cursor/skills"

# 安装各 skill（长文流程 + 贴图）
for d in "$ROOT/skills"/aws-wechat-article-* "$ROOT/skills"/aws-wechat-sticker "$ROOT/skills"/cloud-agent-starter; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  rm -rf "$ROOT/.cursor/skills/$name"
  cp -R "$d" "$ROOT/.cursor/skills/"
  echo "Installed: $name"
done

# 安装共享资源
if [ -d "$ROOT/skills/shared" ]; then
  rm -rf "$ROOT/.cursor/skills/shared"
  cp -R "$ROOT/skills/shared" "$ROOT/.cursor/skills/"
  echo "Installed: shared"
fi

echo "Done. Skills in .cursor/skills:"
ls -la "$ROOT/.cursor/skills/"
