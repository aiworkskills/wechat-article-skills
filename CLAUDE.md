# CLAUDE.md

微信公众号 AI 运营助手 — Cursor / OpenClaw / Claude Code 上的 AI Skills 集合。

## 安装

```bash
bash scripts/install-skills.sh claude-code
```

将 8 个 skill 的指令安装到 `.claude/rules/`，Claude Code 自动加载。

## 仓库结构

- `skills/` — 8 个子 skill（SKILL.md + 脚本 + 参考文档）
- `skills/shared/` — 共享脚本（publish.py、image-gen.py）和图片风格体系
- `scripts/install-skills.sh` — 多平台安装脚本（Cursor / Claude Code / Codex / OpenClaw）
- `.aws-article/config.example.yaml` — 配置模板（复制为 config.yaml 使用）
- `AGENTS.md` — Codex / Cursor Cloud agent 指令

## Skill 路由

| 用户说法 | 路由到 | SKILL.md 路径 |
|---------|--------|--------------|
| 公众号运营、一条龙、完整流程 | **main** | `skills/aws-wechat-article-main/SKILL.md` |
| 选题、标题、热点、系列 | **topics** | `skills/aws-wechat-article-topics/SKILL.md` |
| 写文章、改写、续写 | **writing** | `skills/aws-wechat-article-writing/SKILL.md` |
| 审稿、校对、敏感词 | **review** | `skills/aws-wechat-article-review/SKILL.md` |
| 排版、格式化、转 HTML | **formatting** | `skills/aws-wechat-article-formatting/SKILL.md` |
| 封面、配图、插图 | **images** | `skills/aws-wechat-article-images/SKILL.md` |
| 发布、提交、群发 | **publish** | `skills/aws-wechat-article-publish/SKILL.md` |
| 贴图、多图推送 | **sticker** | `skills/aws-wechat-sticker/SKILL.md` |

收到匹配请求时，读取对应 SKILL.md 获取完整工作流指令。

## 脚本

SKILL.md 中用 `{baseDir}` 表示该 skill 所在目录。各脚本实际路径：

| 脚本 | 路径 | 用途 |
|------|------|------|
| format.py | `skills/aws-wechat-article-formatting/scripts/format.py` | Markdown → 微信 HTML |
| write.py | `skills/aws-wechat-article-writing/scripts/write.py` | 调用 LLM 写文章 |
| image-gen.py | `skills/shared/scripts/image-gen.py` | 调用 LLM 生图 |
| publish.py | `skills/shared/scripts/publish.py` | 微信 API 发布 |

依赖：Python 3.10+、PyYAML。Pillow 可选（图片压缩）。

## 配置

```bash
cp .aws-article/config.example.yaml .aws-article/config.yaml
```

必填：`account_type`、`target_reader`、`tone`。其余按需。`config.yaml` 已在 .gitignore 中。

## 验证

```bash
bash -n scripts/install-skills.sh
python3 -c "import yaml; yaml.safe_load(open('.aws-article/config.example.yaml'))"
python3 -m py_compile skills/aws-wechat-article-formatting/scripts/format.py
python3 skills/shared/scripts/publish.py check
```
