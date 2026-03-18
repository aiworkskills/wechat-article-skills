---
name: aws-wechat-article-images
description: 为公众号文章生成封面图和正文配图，根据文章内容自动匹配风格。当用户提到「封面」「配图」「插图」「生成图片」「给文章加图」「做个封面」「文章插图」「配个图」时使用。
version: 0.5.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-images
---

# 配图

读取文章中的配图标记，按 Type × Style 体系生成图片。专注于**长文配图**，贴图请用 sticker。

## 配置检查 ⛔

`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`
⛔ 不存在 → [首次引导](../aws-wechat-article-main/references/first-time-setup.md)

## Type × Style 体系

Type（画面构成）× Style（视觉风格）自由组合。

完整风格库、兼容矩阵、预设组合、prompt 模板：见 [shared/image-styles/](../shared/image-styles/) 目录。

## 工作流

```
配图进度：
- [ ] 第1步：读取配置与文章
- [ ] 第2步：解析配图标记
- [ ] 第3步：确定风格
- [ ] 第4步：生成配图方案
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片
- [ ] 第7步：插入文章
```

### 第1步：读取配置与文章

从 `config.yaml` 读取：`cover_aspect`、`cover_style`、`image_density`、`caption_style`。读取 `article.md`。

### 第2步：解析配图标记

提取所有 `![类型：描述](placeholder)`。`实证` 类型提示用户提供素材或从 `.aws-article/assets/` 搜索。

### 第3步：确定风格

用户指定 > config `cover_style` > 自动推荐。全文统一风格。

自动推荐规则：[shared/image-styles/auto-selection.md](../shared/image-styles/auto-selection.md)

### 第4步：生成配图方案

为每张图生成方案（类型、风格、prompt 要点）。

Prompt 构建：[shared/image-styles/prompt-construction.md](../shared/image-styles/prompt-construction.md)

### 第5步：展示方案并等待确认 ⛔

### 第6步：生成图片

```bash
python {baseDir}/../shared/scripts/image-gen.py batch imgs/prompts/ -o imgs/
```

图片规格：[references/specs.md](references/specs.md)

### 第7步：插入文章

替换 placeholder 为实际图片路径，输出到 `imgs/`。

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md` 中的标记 | `imgs/`（outline + prompts + 图片） |
