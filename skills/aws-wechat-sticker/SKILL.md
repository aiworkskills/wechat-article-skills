---
name: aws-wechat-sticker
description: 创作公众号贴图和多图推送，从构思到生图到发布的完整流程。当用户提到「贴图」「多图推送」「发组图」「图片消息」「九宫格」「做一组图」「图片帖子」「发几张图」「图文消息」时使用。
version: 0.2.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-sticker
---

# 贴图 / 多图推送

创作以图片为主的公众号内容：多张图片 + 每张配文，统一风格。

## 配置检查 ⛔

`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`
⛔ 不存在 → [首次引导](../aws-wechat-article-main/references/first-time-setup.md)

## 工作流

```
贴图进度：
- [ ] 第1步：读取配置
- [ ] 第2步：确定选题
- [ ] 第3步：确定风格
- [ ] 第4步：规划图序
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片
- [ ] 第7步：审稿
- [ ] 第8步：发布
```

### 第1步：读取配置

从 `config.yaml` 读取：`cover_aspect`、`cover_style`、`multi_image_count`、`tone`、`target_reader`。

### 第2步：确定选题

topics 产出的贴图卡片 / 用户直接给主题 / 用户提供素材图片。

### 第3步：确定风格

使用共享 Type × Style 体系：[shared/image-styles/](../shared/image-styles/)

贴图常用 Type：`氛围`（场景图）、`信息图`（知识卡片）。全组图统一风格。

### 第4步：规划图序

详见：[references/workflow.md](references/workflow.md)

### 第5步：展示方案并等待确认 ⛔

### 第6步：生成图片

```bash
python {baseDir}/../shared/scripts/image-gen.py batch imgs/prompts/ -o imgs/
```

### 第7步：审稿

贴图专用清单：[references/checklist.md](references/checklist.md)

### 第8步：发布

```bash
python {baseDir}/../shared/scripts/publish.py full article/
```

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`（可选） | `imgs/`（outline + prompts + 图片） |
