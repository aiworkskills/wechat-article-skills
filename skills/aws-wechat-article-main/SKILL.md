---
name: aws-wechat-article-main
description: 管理微信公众号从选题到发布的完整内容流程，路由到各子能力。当用户提到「公众号运营」「自动运营」「发篇文章」「内容规划」「怎么运营」「一条龙」「完整流程」「从头做」「帮我发一篇」「今天发什么」或需要了解整体流程时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-main
---

# 公众号运营总览

管理微信公众号内容全流程，路由到对应子 skill。

## 配置检查 ⛔ BLOCKING

**任何操作之前，必须先检查 config.yaml 是否存在**：

```bash
test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"
```

- ✅ 存在 → 读取配置，继续
- ⛔ 不存在 → **立即进入首次引导**，完成后才能继续。详见 [references/first-time-setup.md](references/first-time-setup.md)

## 流程

```
选题 → 写稿 → 审稿(内容审) → 排版 → 配图 → 审稿(终审) → 发布
```

| 步骤 | 子 skill | 读取 | 产出 |
|------|---------|------|------|
| 选题 | topics | config、web_search | `topic-card.md` `research.md` |
| 写稿 | writing | `topic-card.md`、writing-spec | `draft.md`（含配图标记） |
| 审稿(内容审) | review | `draft.md`、writing-spec | `review.md` → 修改循环 → `article.md` |
| 排版 | formatting | `article.md` | `article.html` |
| 配图 | images | `article.md` 中的标记 | `imgs/` 目录 |
| 审稿(终审) | review | `article.html`、`imgs/` | `review.md`（终审） |
| 发布 | publish | `article.html`、`imgs/` | `article.yaml` → 发布到公众号 |

所有文件存放在同一个文章目录下。

## 路由规则

根据用户说法路由到对应子 skill：

| 用户说法 | 路由到 |
|---------|--------|
| 选题、起标题、摘要、排期、爆款、内容日历、系列、专栏 | topics |
| 写正文、改写、公众号风格、结构、开头结尾 | writing |
| 审稿、合规、敏感词、检查 | review |
| 排版、版式、字号、段落、样式、转 HTML | formatting |
| 封面、配图、生成图片 | images |
| 贴图、多图推送、图片消息、发组图 | **sticker** |
| 发布、提交、群发 | publish |

## 运行模式

### 一条龙模式

当用户说「从选题到发布全做」「一条龙」「完整流程」时启用。

```
一条龙进度：
- [ ] 第1步：选题与标题
- [ ] 第2步：写稿
- [ ] 第3步：审稿（内容审 + 修改循环）
- [ ] 第4步：排版
- [ ] 第5步：配图
- [ ] 第6步：终审
- [ ] 第7步：发布
```

**执行规则**：
1. **创建文章目录**（见下方）
2. 按顺序执行每一步，调用对应子 skill
3. 每步完成后**暂停**，展示产出给用户
4. 用户说「继续」→ 进入下一步
5. 用户提出修改 → 按意见调整后重新展示，确认后继续
6. **第3步审稿**有特殊逻辑：若发现 🔴 项 → 修改 → 重审 → 直到通过才继续
7. **第6步终审**可选跳过（用户说「直接发布」）
8. 更新进度清单中的勾选状态

### 单步模式

用户只提到某一步时，仅执行该步骤。若当前无文章目录，自动检测最近的或询问用户。

### 贴图（多图推送）

贴图有独立的 skill：**aws-wechat-sticker**。当用户提到贴图/多图推送时，路由到 sticker skill。

## 文章目录

**一篇文章 = 一个目录**，所有过程文件集中存放。

由 topics 确认选题后自动创建：`{drafts_root}/{YYYY-MM-DD}-{标题slug}/`

```
drafts/2025-03-18-ai-agent-入门/
├── topic-card.md          ← topics
├── research.md            ← topics
├── draft.md               ← writing
├── review.md              ← review
├── article.md             ← 定稿
├── article.html           ← formatting
├── article.yaml           ← publish
└── imgs/                  ← images
    ├── outline.md
    ├── prompts/
    └── NN-type-slug.png
```

发布后整体移到 `published_root`。

系列规划存放在 `{series_root}/{系列slug}/plan.md`。

## 配置与自定义

### 配置

所有子 skill 共享 `config.yaml`，优先级：用户当次说法 > 项目级 > 用户级。

无配置时触发首次引导：[references/first-time-setup.md](references/first-time-setup.md)
完整字段与目录约定：[references/config-schema.md](references/config-schema.md)

### 用户可自定义的内容

全部放在 `.aws-article/` 下：

| 类型 | 位置 | 说明 |
|------|------|------|
| 配置 | `config.yaml` | 账号定位、写作偏好、模型、API 凭证 |
| 写作规范 | `writing-spec.md` | 用词、句式、品牌调性 |
| 排版主题 | `presets/formatting/*.yaml` | YAML 格式的排版主题 |
| 配图风格 | `presets/image-styles/*.yaml` | 配图风格预设 |
| 标题风格 | `presets/title-styles/*.md` | 标题风格预设 |
| 审稿规则 | `presets/review-rules.yaml` | 自定义审稿检查项 |
| 素材 | `assets/brand/`、`assets/covers/`、`assets/stock/` | 品牌元素、封面、通用素材 |
| 模板覆盖 | `templates/` | 覆盖内置模板 |

加载优先级：用户当次说法 > `.aws-article/` 用户文件 > skill 内置默认。
