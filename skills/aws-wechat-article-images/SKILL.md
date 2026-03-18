---
name: aws-wechat-article-images
description: 为微信公众号文章生成配图，采用 Type×Style 二维体系。读取 writing 阶段的配图标记，按类型和风格生成图片。当用户提到「封面」「配图」「多图推送」「贴图」「生成图片」或需要文章配图时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-images
---

# 配图

读取文章中的配图标记，按 Type × Style 二维体系生成图片。

## Type × Style 二维体系

| 维度 | 控制 | 说明 |
|------|------|------|
| **Type（类型）** | 信息结构 | 决定画面的构成方式 |
| **Style（风格）** | 视觉美学 | 决定画面的视觉风格 |

两个维度自由组合，如：`信息图 × 蓝图风`、`氛围 × 水彩风`。

### Type 类型

| 类型 | 最佳用途 | 对应 writing 标记 |
|------|---------|------------------|
| `信息图` | 数据、指标、技术概念 | `![信息图：...]` |
| `氛围` | 叙事、情感、场景 | `![氛围：...]` |
| `流程图` | 步骤、工作流 | `![流程图：...]` |
| `对比` | 并列比较、选择 | `![对比：...]` |
| `框架` | 模型、架构、体系 | `![框架：...]` |
| `封面` | 文章封面图 | `![封面：...]` |

### Style 风格

核心风格（快速选择）：

| 风格 | 适用场景 |
|------|---------|
| `扁平矢量` | 知识科普、教程、科技 |
| `简约线条` | 通用、知识分享 |
| `蓝图` | AI、前沿科技、系统设计 |
| `手绘` | 轻松、个人成长 |
| `水彩` | 生活、情感、文艺 |
| `海报` | 观点、评论、文化 |

完整风格库与 Type × Style 兼容矩阵：[references/styles.md](references/styles.md)

### 风格预设

按文章类型一键选择 Type + Style 组合：[references/style-presets.md](references/style-presets.md)

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

从 `config.yaml` 读取：`cover_aspect`、`cover_style`、`image_density`、`caption_style`、`assets_root`、`header_image`、`footer_image`。

读取 writing 产出的文章（含配图标记）。

### 第2步：解析配图标记

提取文章中所有 `![类型：描述](placeholder)` 标记，解析出：
- 位置（在哪个段落之后）
- 类型（封面/信息图/氛围/流程图/对比/实证）
- 描述（画面内容和意图）

对于 `实证` 类型：提示用户提供素材，或从 `assets_root` 搜索。

### 第3步：确定风格 ⚠️

**风格确定顺序**（首个命中即用）：
1. 用户当次指定
2. config 中的 `cover_style`（作为默认风格基调）
3. 根据文章内容自动推荐 → 询问用户确认

自动推荐规则：[references/auto-selection.md](references/auto-selection.md)

**全文使用统一风格**，保持视觉一致性。封面可用相同风格的变体。

### 第4步：生成配图方案

为每张图生成方案：

```markdown
## 配图方案

### 图1：封面
- 类型：封面
- 风格：扁平矢量
- 比例：2.35:1
- 描述：[来自标记的描述]
- Prompt 要点：[结构化 prompt 摘要]

### 图2：信息图
- 类型：信息图
- 风格：扁平矢量
- 位置：小标题一之后
- 描述：[来自标记的描述]
- Prompt 要点：[结构化 prompt 摘要]

### 图3：实证
- 类型：实证
- 位置：小标题二之后
- ⚠️ 需用户提供截图
```

Prompt 构建模板：[references/prompt-construction.md](references/prompt-construction.md)

### 第5步：展示方案并等待确认 ⛔

展示配图方案，等待用户：
- 「确认」→ 开始生成
- 修改某张图的描述或风格 → 更新方案
- 提供实证类素材

### 第6步：生成图片

按方案逐张生成：
- 封面/氛围/对比：调用图片生成能力，使用结构化 prompt
- 信息图/流程图/框架：生成 HTML → 导出为图片（或使用生成能力）
- 实证：使用用户提供的素材

图片规格：[references/specs.md](references/specs.md)

### 第7步：插入文章

将 `![类型：描述](placeholder)` 替换为实际图片路径：

```markdown
![描述](imgs/01-cover-title.png)
```

输出目录：`{article-dir}/imgs/`

## 多图推送模式

多图推送时跳过文章标记解析，直接按 `multi_image_count` 生成图序：
- 每张：主题 + 配文 + 风格统一
- 统一比例和风格

## 预设查找路径

风格预设按优先级查找：
1. `.aws-article/presets/image-styles/<风格名>.md`（用户自定义）
2. skill 内置风格库

用户素材查找：`.aws-article/assets/`（brand/covers/stock）

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md` 中的配图标记 | `imgs/` 目录（outline + prompts + 图片） |

```
imgs/
├── outline.md                   # 配图方案
├── prompts/                     # 各图的 prompt 文件
│   ├── 00-cover.md
│   └── 01-infographic-xxx.md
├── 00-cover.png
├── 01-infographic-xxx.png
└── 02-scene-xxx.png
```

## References

| 文件 | 内容 |
|------|------|
| [references/styles.md](references/styles.md) | 风格库与 Type×Style 兼容矩阵 |
| [references/style-presets.md](references/style-presets.md) | 按文章类型的预设组合 |
| [references/prompt-construction.md](references/prompt-construction.md) | 各 Type 的 prompt 构建模板 |
| [references/auto-selection.md](references/auto-selection.md) | 内容信号→自动推荐 |
| [references/specs.md](references/specs.md) | 图片尺寸与格式规格 |
