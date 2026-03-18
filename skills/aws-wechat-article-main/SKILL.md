---
name: aws-wechat-article-main
description: 管理微信公众号从选题到发布的完整内容流程，路由到各子能力。当用户提到「公众号运营」「自动运营」「发篇文章」「内容规划」「怎么运营」「一条龙」「完整流程」「从头做」「帮我发一篇」「今天发什么」或需要了解整体流程时使用。
version: 0.4.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-main
---

# 公众号运营总览

## 配置检查 ⛔ BLOCKING

**任何操作前必须检查**：`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`

⛔ 不存在 → [首次引导](references/first-time-setup.md)，完成后才继续。

## 流程

```
选题 → 写稿 → 审稿(内容审) → 排版 → 配图 → 审稿(终审) → 发布
```

| 步骤 | 子 skill | 读取 | 产出 |
|------|---------|------|------|
| 选题 | topics | config、web_search | `topic-card.md` `research.md` |
| 写稿 | writing | `topic-card.md` | `draft.md` |
| 审稿 | review | `draft.md` | `review.md` → `article.md` |
| 排版 | formatting | `article.md` | `article.html` |
| 配图 | images | `article.md` 标记 | `imgs/` |
| 终审 | review | `article.html`+`imgs/` | `review.md` |
| 发布 | publish | `article.html`+`imgs/` | `article.yaml` |

## 路由

| 用户说法 | 路由到 |
|---------|--------|
| 选题、标题、摘要、排期、爆款、系列、专栏 | topics |
| 写文章、改写、续写、公众号风格 | writing |
| 审稿、审核、检查、校对、敏感词 | review |
| 排版、美化、格式化、转 HTML | formatting |
| 封面、配图、插图、生成图片 | images |
| 贴图、多图推送、发组图 | **sticker** |
| 发布、提交、群发、推送 | publish |

## 运行模式

### 一条龙

用户说「一条龙」「完整流程」时启用。按顺序执行每步，每步完成后**暂停**等用户确认。审稿有 🔴 项时进入修改循环。

### 单步

用户只提到某一步时，仅执行该步骤。

### 贴图

路由到独立的 **aws-wechat-sticker** skill。

## 配置与自定义

详见：[references/config-schema.md](references/config-schema.md)
