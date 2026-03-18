---
name: aws-wechat-article-main
description: Explains the full WeChat official account content workflow and routes to the right sub-skill. Use when the user asks about "公众号运营", "自动运营", "发什么内容", "怎么运营", or wants an overview of the article pipeline.
---

# 公众号运营总览与路由

说明整条内容链路及各环节对应的子 skill，便于用户从「发什么」或任意一步进入。

## 流程顺序

固定顺序（审稿在写稿后即做，再排版配图）：

1. **选题与标题** → aws-wechat-article-topics  
2. **写稿** → aws-wechat-article-writing  
3. **审稿** → aws-wechat-article-review（写稿完成后即做，通过后再排版、配图）  
4. **排版** → aws-wechat-article-formatting  
5. **配图/贴图** → aws-wechat-article-images  
6. **发布** → aws-wechat-article-publish  

每次只跑用户当前提到的那一步；若要一条龙，用户需明确说「从选题到发布全做」或逐步说「先选题」「再写稿」等。

## 各环节对应 skill

| 用户意图 / 说法 | 使用 skill |
|----------------|------------|
| 起选题、起标题、要摘要、排期 | aws-wechat-article-topics |
| 写正文、改写、改成公众号风格、结构/开头结尾 | aws-wechat-article-writing |
| 审稿、合规、敏感词、发布前检查 | aws-wechat-article-review |
| 排版、版式、字号、段落、引导语 | aws-wechat-article-formatting |
| 封面、配图、多图推送、贴图、图片规格、素材库、生成图片 | aws-wechat-article-images |
| 发布公众号、提交、发布 | aws-wechat-article-publish |

## 配置

- 各子 skill 共用一份配置，路径优先级：项目 `.aws-article/` → 用户 `~/.aws-article/`。  
- 配置约定与首次引导见本 skill 的 [references/config-schema.md](references/config-schema.md)、[references/first-time-setup.md](references/first-time-setup.md)。  
- 无配置时由 main 或首个被调用的子 skill 触发首次引导，问完并写入配置后再继续。

## 新号搭建（可选）

新号从 0 搭：定位 → 栏目 → 选题库 → 首月内容规划。可先做定位与栏目，再交给 **aws-wechat-article-topics** 产出首批选题。

## 贴图（多图推送）流程

若发多图贴图而非长文：topics（贴图文案/主题）→ images（图序、每张配文、规格）→ review → publish；writing、formatting 仅在发长文时参与。
