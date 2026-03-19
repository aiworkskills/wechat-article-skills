#!/usr/bin/env bash
# 将 skills/ 下的所有 skill 和共享资源以符号链接方式安装到 .cursor/skills/，供 Cursor 加载（不拷贝，改源码即生效）。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.cursor/skills"

# 安装各 skill（长文流程 + 贴图）：创建符号链接
for d in "$ROOT/skills"/aws-wechat-article-* "$ROOT/skills"/aws-wechat-sticker; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  rm -rf "$ROOT/.cursor/skills/$name"
  ln -s "$ROOT/skills/$name" "$ROOT/.cursor/skills/$name"
  echo "Linked: $name"
done

# 安装共享资源：符号链接
if [ -d "$ROOT/skills/shared" ]; then
  rm -rf "$ROOT/.cursor/skills/shared"
  ln -s "$ROOT/skills/shared" "$ROOT/.cursor/skills/shared"
  echo "Linked: shared"
fi

echo "Done. Skills in .cursor/skills (symlinks):"
ls -la "$ROOT/.cursor/skills/"
