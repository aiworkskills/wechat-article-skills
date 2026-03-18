---
name: aws-wechat-article-images
description: 为公众号文章生成封面图和正文配图，根据文章内容自动匹配风格。当用户提到「封面」「配图」「插图」「生成图片」「给文章加图」「做个封面」「文章插图」「配个图」时使用。
version: 0.4.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-images
---

# 配图

读取文章中的配图标记，按 Type × Style 二维体系生成图片。

本 skill 专注于**长文配图**。贴图/多图推送请使用 aws-wechat-sticker。

## Type × Style 二维体系

Type × Style 体系为所有图片生成 skill 共用，详见共享资源：

| 资源 | 路径 |
|------|------|
| 风格库与兼容矩阵 | [shared/image-styles/styles.md](../shared/image-styles/styles.md) |
| 按文章类型的预设组合 | [shared/image-styles/style-presets.md](../shared/image-styles/style-presets.md) |
| 各 Type 的 prompt 构建模板 | [shared/image-styles/prompt-construction.md](../shared/image-styles/prompt-construction.md) |
| 内容信号→自动推荐 | [shared/image-styles/auto-selection.md](../shared/image-styles/auto-selection.md) |

### Type 类型

| 类型 | 最佳用途 | 对应 writing 标记 |
|------|---------|------------------|
| `信息图` | 数据、指标、技术概念 | `![信息图：...]` |
| `氛围` | 叙事、情感、场景 | `![氛围：...]` |
| `流程图` | 步骤、工作流 | `![流程图：...]` |
| `对比` | 并列比较、选择 | `![对比：...]` |
| `框架` | 模型、架构、体系 | `![框架：...]` |
| `封面` | 文章封面图 | `![封面：...]` |

### Style 核心风格

| 风格 | 适用场景 |
|------|---------|
| `扁平矢量` | 知识科普、教程、科技 |
| `简约线条` | 通用、知识分享 |
| `蓝图` | AI、前沿科技、系统设计 |
| `手绘` | 轻松、个人成长 |
| `水彩` | 生活、情感、文艺 |
| `海报` | 观点、评论、文化 |

## 工作流

```
配图进度：
- [ ] 第1步：读取配置与文章
- [ ] 第2步：解析配图标记
- [ ] 第3步：确定风格 ⚠️
- [ ] 第4步：生成配图方案（outline）
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片
- [ ] 第7步：插入文章
```

### 第1步：读取配置与文章

从 `config.yaml` 读取：`cover_aspect`、`cover_style`、`image_density`、`caption_style`。

读取文章目录下的 `article.md`（含配图标记）。

### 第2步：解析配图标记

提取所有 `![类型：描述](placeholder)` 标记，解析出位置、类型、描述。

`实证` 类型：提示用户提供素材，或从 `.aws-article/assets/` 搜索。

### 第3步：确定风格 ⚠️

风格确定顺序（首个命中即用）：
1. 用户当次指定
2. config 中的 `cover_style`
3. 根据文章内容自动推荐 → 询问用户确认

全文使用统一风格，保持视觉一致性。

### 第4步：生成配图方案

为每张图生成方案（类型、风格、描述、prompt 要点）。

### 第5步：展示方案并等待确认 ⛔

### 第6步：生成图片

使用共享图片生成脚本：

```bash
# 单张生成
python {baseDir}/../shared/scripts/image-gen.py generate imgs/prompts/00-cover.md -o imgs/00-cover.png

# 批量生成
python {baseDir}/../shared/scripts/image-gen.py batch imgs/prompts/ -o imgs/
```

图片规格：[references/specs.md](references/specs.md)

### 第7步：插入文章

将 placeholder 替换为实际图片路径，输出到 `{article-dir}/imgs/`。

## 预设查找路径

风格预设按优先级查找：
1. `.aws-article/presets/image-styles/`（用户自定义）
2. shared/image-styles/ 内置风格库

用户素材：`.aws-article/assets/`

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md` 中的配图标记 | `imgs/`（outline + prompts + 图片） |
