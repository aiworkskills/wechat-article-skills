---
name: aws-wechat-article-images
description: 为微信公众号文章生成封面图和正文配图，根据内容自动选择配图策略，支持多套风格预设。当用户提到「封面」「配图」「多图推送」「贴图」「图片规格」「生成图片」或需要文章配图时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-images
---

# 配图

为公众号文章生成封面图与正文配图。根据文章内容自动分析并决定配图策略。

## 工作流

```
配图进度：
- [ ] 第1步：读取配置
- [ ] 第2步：分析内容
- [ ] 第3步：确定配图方案
- [ ] 第4步：生成图片
- [ ] 第5步：产出配图结果
```

### 第1步：读取配置

从 `config.yaml` 读取：`cover_aspect`、`cover_style`、`image_density`、`caption_style`、`multi_image_count`、`assets_root`、`header_image`、`footer_image`。

### 第2步：分析内容

分析文章的标题、摘要、正文，提取：
- 主题与关键词
- 情绪与调性
- 适合的视觉风格

### 第3步：确定配图方案

根据内容分析，自动决定：

| 决策项 | 说明 |
|--------|------|
| 封面风格 | 根据文章调性选择风格预设 |
| 封面比例 | 按配置 `cover_aspect` |
| 正文配图数量 | 按配置 `image_density` |
| 配图位置 | 按正文结构建议插图位置 |

自动选择规则：[references/auto-selection.md](references/auto-selection.md)

将方案展示给用户确认，用户可调整后继续。

### 第4步：生成图片

按确定的方案调用图片生成能力，生成封面图与正文配图。

生成时读取对应风格预设的 prompt 模板：`references/presets/<预设名>.md`

### 第5步：产出配图结果

输出：
- 封面图（路径或生成结果）
- 正文配图列表（位置 + 图片 + 图注）
- 多图推送时：图序、每张配文、尺寸规格

## 输出格式

```markdown
## 配图方案

### 封面
- 风格：简约科技
- 比例：2.35:1（900×383）
- 描述：[封面内容描述]

### 正文配图
| 位置 | 描述 | 图注 |
|------|------|------|
| 小标题一之后 | [图片内容描述] | 图：XXX |
| 小标题三之后 | [图片内容描述] | 图：XXX |

### 品牌元素
- 头图：[路径或「无」]
- 尾图：[路径或「无」]
```

## 风格预设

预设文件存放在 `references/presets/`，每个预设包含用于生成图片的 prompt 模板和参数。

| 预设 | 风格 | 适用场景 |
|------|------|---------|
| default | 简约扁平 | 科技、互联网、通用 |
| *更多预设持续添加中* | | |

预设文件格式说明：[references/presets/README.md](references/presets/README.md)

## 图片规格

详见：[references/specs.md](references/specs.md)
