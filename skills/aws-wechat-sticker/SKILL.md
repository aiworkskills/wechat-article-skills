---
name: aws-wechat-sticker
description: 创作公众号贴图和多图推送，从构思到生图到发布的完整流程。当用户提到「贴图」「多图推送」「发组图」「图片消息」「九宫格」「做一组图」「图片帖子」「发几张图」「图文消息」时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-sticker
---

# 贴图 / 多图推送

创作以图片为主的公众号内容：多张图片 + 每张配文，统一风格。

## 与长文的区别

| 维度 | 长文 | 贴图 |
|------|------|------|
| 核心内容 | HTML 正文 | 多张图片 + 配文 |
| 流程 | 选题→写稿→审稿→排版→配图→发布 | **选题→创作→审稿→发布** |
| 张数 | 不限 | 单条最多 9 张 |
| 图片角色 | 辅助正文 | **图片即内容** |

## 工作流

```
贴图进度：
- [ ] 第1步：读取配置
- [ ] 第2步：确定选题（或读取 topic-card）
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

三种来源：
- topics 产出的贴图选题卡片（`topic-card.md` 中标注为贴图类型）
- 用户直接给主题（如「做一组程序员摸鱼的贴图」）
- 用户提供素材图片，需要加工配文

若需要 topics 先行选题，告知用户调用 aws-wechat-article-topics。

### 第3步：确定风格

使用共享的 Type × Style 体系：

| 资源 | 路径 |
|------|------|
| 风格库与兼容矩阵 | [shared/image-styles/styles.md](../shared/image-styles/styles.md) |
| 风格预设组合 | [shared/image-styles/style-presets.md](../shared/image-styles/style-presets.md) |
| 自动推荐规则 | [shared/image-styles/auto-selection.md](../shared/image-styles/auto-selection.md) |

贴图常用 Type：`氛围`（场景图）、`信息图`（知识卡片）。

风格确定顺序：用户指定 > config `cover_style` > 自动推荐。

**全组图使用统一风格**。

### 第4步：规划图序

规划每张图的内容和配文：

```markdown
## 贴图方案：[主题名]

**张数**：N 张
**风格**：[选定的 Type × Style]
**叙事线**：[叙事逻辑说明]

| 序号 | 画面描述 | 配文 | Prompt 要点 |
|------|---------|------|-------------|
| 1 | [画面内容] | 「配文内容」 | [结构化 prompt 摘要] |
| 2 | [画面内容] | 「配文内容」 | ... |
| ... | | | |
```

Prompt 构建：[shared/image-styles/prompt-construction.md](../shared/image-styles/prompt-construction.md)

### 第5步：展示方案并等待确认 ⛔

展示图序方案，等待用户：
- 「确认」→ 开始生成
- 修改某张的描述或配文 → 更新方案
- 调整张数或顺序

### 第6步：生成图片

使用共享图片生成脚本逐张生成：

```bash
python {baseDir}/../shared/scripts/image-gen.py batch imgs/prompts/ -o imgs/
```

保存到文章目录的 `imgs/`：

```
imgs/
├── outline.md               # 贴图方案
├── prompts/
│   ├── 01-scene-xxx.md
│   └── 02-scene-xxx.md
├── 01-scene-xxx.png
├── 02-scene-xxx.png
└── ...
```

### 第7步：审稿

贴图专用审稿清单：[references/checklist.md](references/checklist.md)

结果分三级：🔴 必须改 / 🟡 建议改 / 🟢 通过。有 🔴 则修改循环。

### 第8步：发布

使用共享发布脚本：`{baseDir}/../shared/scripts/publish.py`

贴图发布时 `article_type` 设为 `newspic`，每张图作为独立素材上传。

API 参考：aws-wechat-article-publish 的 [references/api-reference.md](../aws-wechat-article-publish/references/api-reference.md)

## 贴图类型

| 类型 | 说明 | 典型张数 |
|------|------|---------|
| 场景故事 | 用图片讲一个小故事 | 4-6 张 |
| 知识卡片 | 每张一个知识点 | 6-9 张 |
| 产品展示 | 产品多角度/多功能展示 | 3-6 张 |
| 节日祝福 | 节日主题图 + 祝福语 | 1-3 张 |
| 投票/互动 | 选项图片 + 引导文案 | 2-4 张 |

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`（可选） | `imgs/`（outline + prompts + 图片） |

贴图使用与长文相同的文章目录结构：`{drafts_root}/{日期}-{slug}/`
