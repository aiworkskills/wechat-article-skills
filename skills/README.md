# 微信公众号自动运营 Skills（源码）

本目录为 7 个子 skill 的**源代码**，与实施计划一致。

## 子 skill 列表

| 目录 | 职责 |
|------|------|
| aws-wechat-article-main | 总览与路由、配置与首次引导 |
| aws-wechat-article-topics | 选题与标题、摘要多候选、排期 |
| aws-wechat-article-writing | 长文写作与改写 |
| aws-wechat-article-formatting | 排版（从预设直接读取） |
| aws-wechat-article-images | 贴图（素材库 / OpenAI 生成 / HTML 导出） |
| aws-wechat-article-review | 审稿与合规（写稿后即做） |
| aws-wechat-article-publish | 发布前检查与提交指引 |

## 流程顺序

选题 → 写稿 → **审稿** → 排版 → 配图 → 发布。

## 在 Cursor 中使用

**一键安装（项目级）**：在项目根目录执行  
`bash scripts/install-skills.sh`  
会将本目录下 7 个子 skill 安装到 `.cursor/skills/`，供 Cursor 加载。

或手动复制到 **项目级** `.cursor/skills/` 或 **用户级** `~/.cursor/skills/`。每个 skill 独立一个文件夹，文件夹名与 SKILL.md 中的 `name` 一致。

**配置**：项目 `.aws-article/` 或用户 `~/.aws-article/`。示例见 `.aws-article/config.example.yaml`，复制为 `config.yaml` 后按需修改，或由 main 首次引导生成。
