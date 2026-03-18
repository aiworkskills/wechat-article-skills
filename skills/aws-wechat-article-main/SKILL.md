---
name: aws-wechat-article-main
description: 微信公众号内容运营总流程与路由。管理选题→写稿→审稿→排版→配图→发布的完整链路，支持一条龙模式与单步模式。当用户提到「公众号运营」「自动运营」「发文章」「内容规划」「怎么运营」或需要了解整体流程时使用。
version: 0.2.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-main
---

# 公众号运营总览

管理微信公众号内容全流程，路由到对应子 skill。

## 流程与过程文件

```
选题 → 写稿 → 审稿 → 排版 → 配图 → 发布
```

| 步骤 | 子 skill | 读取 | 产出 |
|------|---------|------|------|
| 选题 | topics | config | `topic-card.md` `research.md` |
| 写稿 | writing | `topic-card.md` | `draft.md`（含配图标记） |
| 审稿 | review | `draft.md` | `review.md` `article.md` |
| 排版 | formatting | `article.md` | `article.html` |
| 配图 | images | `article.md` 中的标记 | `imgs/` 目录 |
| 发布 | publish | `article.html` `imgs/` | `article.yaml` |

所有文件存放在同一个文章目录下，详见「文章目录」。

## 路由规则

根据用户说法路由到对应子 skill：

| 用户说法 | 路由到 |
|---------|--------|
| 选题、起标题、摘要、排期、爆款、内容日历 | aws-wechat-article-topics |
| 写正文、改写、公众号风格、结构、开头结尾 | aws-wechat-article-writing |
| 审稿、合规、敏感词、检查 | aws-wechat-article-review |
| 排版、版式、字号、段落、样式 | aws-wechat-article-formatting |
| 封面、配图、贴图、生成图片、多图推送 | aws-wechat-article-images |
| 发布、提交、群发 | aws-wechat-article-publish |

## 运行模式

### 一条龙模式

当用户说「从选题到发布全做」「一条龙」「完整流程」时启用。

```
一条龙进度：
- [ ] 第1步：选题与标题
- [ ] 第2步：写稿
- [ ] 第3步：审稿
- [ ] 第4步：排版
- [ ] 第5步：配图
- [ ] 第6步：发布检查
```

**执行规则**：
1. **创建文章目录**（见下方「文章目录」）
2. 按顺序执行每一步，调用对应子 skill
3. 每步完成后**暂停**，展示产出给用户
4. 用户说「继续」→ 进入下一步
5. 用户提出修改 → 按意见调整后重新展示，确认后继续
6. 更新进度清单中的勾选状态

### 单步模式

用户只提到某一步时，仅执行该步骤。若当前无文章目录，自动检测最近的或询问用户。

### 贴图（多图推送）模式

多图推送走精简流程，跳过写稿和排版：

```
贴图进度：
- [ ] 第1步：选题（贴图文案与主题）
- [ ] 第2步：配图（图序、配文、规格）
- [ ] 第3步：审稿
- [ ] 第4步：发布检查
```

## 文章目录

**一篇文章 = 一个目录**，所有过程文件集中存放。

### 创建时机

由 topics 确认选题后自动创建：

```
{drafts_root}/{YYYY-MM-DD}-{标题slug}/
```

如：`drafts/2025-03-18-ai-agent-入门/`

### 目录结构

```
drafts/2025-03-18-ai-agent-入门/
├── topic-card.md          ← topics 产出
├── research.md            ← topics 产出
├── draft.md               ← writing 产出
├── review.md              ← review 产出
├── article.md             ← 定稿
├── article.html           ← formatting 产出
├── article.yaml           ← publish 元信息
└── imgs/                  ← images 产出
    ├── outline.md
    ├── prompts/
    └── NN-type-slug.png
```

### 生命周期

```
topics 创建目录 → 各 skill 在目录下读写 → 发布后移到 published_root
```

### 系列目录

```
{series_root}/{系列slug}/
├── plan.md                ← 系列总规划
└── progress.md            ← 进度追踪
```

系列中每篇文章仍是独立的文章目录，`topic-card.md` 中标注系列归属。

## 配置与自定义

### 配置

所有子 skill 共享 `config.yaml`：

| 优先级 | 来源 |
|--------|------|
| 1（最高） | 用户当次对话中的说法 |
| 2 | 项目级 `.aws-article/config.yaml` |
| 3 | 用户级 `~/.aws-article/config.yaml` |

### 用户自定义

| 类型 | 位置 | 说明 |
|------|------|------|
| 写作规范 | `.aws-article/writing-spec.md` | 用词、句式、品牌调性 |
| 预设 | `.aws-article/presets/` | 排版/配图风格/标题风格 |
| 素材 | `.aws-article/assets/` | 品牌元素、封面素材 |
| 模板覆盖 | `.aws-article/templates/` | 覆盖内置模板 |

加载优先级：用户文件 > skill 内置默认。

- 无配置时触发首次引导：[references/first-time-setup.md](references/first-time-setup.md)
- 完整字段说明与目录约定：[references/config-schema.md](references/config-schema.md)
