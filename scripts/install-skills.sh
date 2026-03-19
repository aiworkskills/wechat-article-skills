#!/usr/bin/env bash
# 将 skills/ 下的所有 skill 和共享资源安装到各 AI 编程工具的指定目录。
#
# 支持的目标：
#   cursor      → .cursor/skills/        （复制完整 skill 目录）
#   claude-code → .claude/rules/          （从 SKILL.md 生成规则文件）
#   codex       → AGENTS.md              （已在仓库中维护，仅提示）
#   openclaw    → skills/                （原生读取，无需安装）
#
# 用法：
#   bash scripts/install-skills.sh                  # 安装全部目标
#   bash scripts/install-skills.sh cursor            # 仅 Cursor
#   bash scripts/install-skills.sh cursor claude-code # 指定多个目标
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 收集 skill 目录
SKILL_DIRS=()
for d in "$ROOT/skills"/aws-wechat-article-* "$ROOT/skills"/aws-wechat-sticker; do
  [ -d "$d" ] && SKILL_DIRS+=("$d")
done

# ── Cursor ──────────────────────────────────────────────
install_cursor() {
  echo "=== Cursor ==="
  local target="$ROOT/.cursor/skills"
  mkdir -p "$target"

  for d in "${SKILL_DIRS[@]}"; do
    local name=$(basename "$d")
    rm -rf "$target/$name"
    cp -R "$d" "$target/"
    echo "  Installed: $name"
  done

  if [ -d "$ROOT/skills/shared" ]; then
    rm -rf "$target/shared"
    cp -R "$ROOT/skills/shared" "$target/"
    echo "  Installed: shared"
  fi
}

# ── Claude Code ─────────────────────────────────────────
install_claude_code() {
  echo "=== Claude Code ==="
  local target="$ROOT/.claude/rules"
  mkdir -p "$target"

  # 为每个 skill 生成规则文件：保留 SKILL.md 正文，将 {baseDir} 替换为实际路径
  for d in "${SKILL_DIRS[@]}"; do
    local name=$(basename "$d")
    local skill_file="$d/SKILL.md"
    [ -f "$skill_file" ] || continue

    # 去掉 YAML frontmatter（--- 到 --- 之间的内容），替换 {baseDir}
    python3 -c "
import sys, re, pathlib
text = pathlib.Path(sys.argv[1]).read_text()
text = re.sub(r'^---\n.*?\n---\n*', '', text, count=1, flags=re.DOTALL)
text = text.replace('{baseDir}', 'skills/$name')
pathlib.Path(sys.argv[2]).write_text(text)
" "$skill_file" "$target/${name}.md"
    echo "  Installed: $name"
  done
}

# ── Codex ───────────────────────────────────────────────
install_codex() {
  echo "=== Codex ==="
  echo "  AGENTS.md 已在仓库根目录维护，Codex 自动读取。"
}

# ── OpenClaw ────────────────────────────────────────────
install_openclaw() {
  echo "=== OpenClaw ==="
  echo "  OpenClaw 直接读取 skills/ 目录，无需安装。"
  echo "  当前可用 skill：${#SKILL_DIRS[@]} 个"
}

# ── 主流程 ──────────────────────────────────────────────
if [ $# -eq 0 ]; then
  TARGETS=(cursor claude-code codex openclaw)
else
  TARGETS=("$@")
fi

for t in "${TARGETS[@]}"; do
  case "$t" in
    cursor)      install_cursor ;;
    claude-code) install_claude_code ;;
    codex)       install_codex ;;
    openclaw)    install_openclaw ;;
    *)           echo "未知目标: $t（可选: cursor, claude-code, codex, openclaw）" >&2; exit 1 ;;
  esac
done

echo ""
echo "Done."
