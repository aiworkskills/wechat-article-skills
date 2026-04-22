---
name: aws-wechat-sticker
description: 公众号贴图｜微信贴图｜微信公众号贴图｜九宫格｜多图推送｜图片消息｜图文消息｜发组图｜表情包｜sticker｜image post｜nine grid — 贴图与多图推送：从创意构思、AI 生图到公众号图片消息发布全流程，含九宫格自动排布、多图压缩、图文消息打包。面向公众号运营、自媒体、IP 账号。触发词：「贴图」「多图推送」「发组图」「图片消息」「九宫格」「做一组图」「图片帖子」「发几张图」「图文消息」。
---

# 贴图 / 多图推送

**贴图 / 多图推送一条龙** —— 构思→生图→图片消息群发，九宫格自动排布、多图打包。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 前置依赖 ⛔ 套件必须装齐

`aws-wechat-article-*` 一条龙套件的 9 个 skill 互相引用首次引导、环境校验与规则文档。**单独安装任一 skill 无法正常工作**，必须装齐 9 个：

```
aws-wechat-article-main
aws-wechat-article-topics
aws-wechat-article-writing
aws-wechat-article-review
aws-wechat-article-formatting
aws-wechat-article-images
aws-wechat-article-publish
aws-wechat-article-assets
aws-wechat-sticker
```

**Agent：进入下方工作流前，先检查当前 `skills/` 目录下上述 9 个子目录是否都存在。**

**若任一缺失** → 停止本 skill 工作流，**不得**尝试代替用户跑脚本或继续；按下述话术回复用户：

> 本套件需 9 个 skill 都装齐才能使用。检测到缺少：`<列出缺失项>`。请执行：
>
> ```bash
> # macOS / Linux / Git Bash
> for slug in aws-wechat-article-main aws-wechat-article-topics aws-wechat-article-writing aws-wechat-article-review aws-wechat-article-formatting aws-wechat-article-images aws-wechat-article-publish aws-wechat-article-assets aws-wechat-sticker; do
>   clawhub install "$slug"
> done
> ```
>
> ```powershell
> # Windows PowerShell
> 'aws-wechat-article-main','aws-wechat-article-topics','aws-wechat-article-writing','aws-wechat-article-review','aws-wechat-article-formatting','aws-wechat-article-images','aws-wechat-article-publish','aws-wechat-article-assets','aws-wechat-sticker' | ForEach-Object { clawhub install $_ }
> ```
>
> 装完再回本 skill 让我继续。

**9 个全部存在** → 按下方工作流继续。

## 路由

长文图文（标题+正文+插图+后台发文）→ [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)；长文内单篇插图 → [aws-wechat-article-images](../aws-wechat-article-images/SKILL.md)。

创作以图片为主的公众号内容：多张图片 + 每张配文，统一风格。

## 产出目标（先看这个）

- 输入：主题 / 选题卡 / 用户素材图（任选其一）
- 输出：`imgs/`（outline + prompts + 图片）与可发布的多图内容
- 风格：整组统一（避免每张图风格漂移）

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

从选题到发布的**前置规则**见 [aws-wechat-article-main/SKILL.md](../aws-wechat-article-main/SKILL.md)；本 skill 描述贴图子流程。

**图片模型**：**`image_model`**（`provider`、`base_url`、`model` 等）在 **`config.yaml`**；**`IMAGE_MODEL_API_KEY`** 在 **`aws.env`**。键名对照 **`{baseDir}/../aws-wechat-article-main/references/env.example.yaml`**（与 **`image_create.py`** 一致）。

**交互约定**：须遵守 main 的**智能体行为约束**——未通过环境校验且未获用户明确「本次例外」时，不得假装已走专用生图 API。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 路径（相对仓库 `skills/`） | 用途 |
|------|---------------------------|------|
| `image_create.py` | `aws-wechat-article-images/scripts/image_create.py` | 专用生图 API：读取 **`.aws-article/config.yaml`** 的 `image_model` + 根目录 **`aws.env`** 的 `IMAGE_MODEL_API_KEY` |
| `publish.py` | `{baseDir}/../aws-wechat-article-publish/scripts/publish.py` | 发布（与 [publish skill](../aws-wechat-article-publish/SKILL.md) 一致） |

## 工作流

```
贴图进度：
- [ ] 第1步：环境检查 + 本篇约束（合并 YAML）
- [ ] 第2步：确定选题
- [ ] 第3步：确定风格
- [ ] 第4步：规划图序
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片（**脚本失败时**见同节「调用失败」分支）
- [ ] 第7步：审稿
- [ ] 第8步：发布
```

### 第1步：环境检查 + 本篇约束（合并 YAML）

若本篇在 **`drafts/…/`** 下：按 **`.aws-article/config.yaml` → 本篇 `article.yaml`** 合并读取约束（同键本篇优先，最后层覆盖），重点字段：`multi_image_count`、`tone`、`target_reader`、`custom_sticker_style` > `default_sticker_style`（**须为 YAML 字符串列表**；`custom_*` 非空时优先于 `default_*`；多候选时智能体择一并写回本篇为**单元素列表**）。若无有效 YAML，以用户口述主题 + skill 默认值作为约束。

### 第2步：确定选题

topics 产出的贴图卡片 / 用户直接给主题 / 用户提供素材图片。

### 第3步：确定风格

**贴图风格加载优先级**：
1. 用户指定（「用知识卡片风格」）
2. 本篇合并配置中的 `custom_sticker_style` > `default_sticker_style`（若有；`custom_*` 优先；列表多元素时须先择一）
3. `.aws-article/presets/sticker-styles/` 下的自定义风格
4. **fallback**：根据贴图主题自动选择 Type（氛围 or 信息图）× 默认 Style（扁平矢量），使用共享 [image-styles/](../aws-wechat-article-images/references/image-styles/)

全组图统一风格。

### 第4步：规划图序

产出 `imgs/outline.md`：每张图的用途、文案要点、文件名。详见：[references/workflow.md](references/workflow.md)

### 第5步：展示方案并等待确认 ⛔

### 第6步：生成图片

**生成方式（优先级）**：

1. **优先**：调用 **`image_create.py`** — 依赖 **`config.yaml`** 的 **`image_model`** + **`aws.env`** 的 **`IMAGE_MODEL_API_KEY`**
2. **降级**：当前 Agent 多模态 / 仅出 prompts — 仅当环境未就绪、用户接受 main「本次例外」、或**已按本节下方「调用失败」表格处理**（网络重试后仍失败等）时

**必须告知用户当前使用的方式**：

- 已配置且调用脚本 → `ℹ️ 使用 image_create.py 调用专用生图模型（{model}）`
- Agent 生图 / 仅 prompts → `ℹ️ 本次未走 image_create.py（原因：…）`

**调用专用 API 时**（在**仓库根**执行，路径按本篇 `imgs/` 调整）：

```bash
python {baseDir}/../aws-wechat-article-images/scripts/image_create.py batch drafts/YYYYMMDD-slug/imgs/prompts/ -o drafts/YYYYMMDD-slug/imgs/
```

单张：`python {baseDir}/../aws-wechat-article-images/scripts/image_create.py generate imgs/prompts/01.md -o imgs/01.png`

连通性自检：`python {baseDir}/../aws-wechat-article-images/scripts/image_create.py test`

图片内文字与 prompt 构建规则与长文配图一致，见 [aws-wechat-article-images/SKILL.md](../aws-wechat-article-images/SKILL.md) 与 [prompt-construction.md](../aws-wechat-article-images/references/image-styles/prompt-construction.md)。

#### `image_create.py` 调用失败时（智能体必选分支）

沿用配图 skill 的同一规则：必须摘要 stderr 关键行，按 **网络 / 配置·凭证 / 业务·参数** 分类处理；**禁止**配置错误时静默降级。细则参照 [aws-wechat-article-images/SKILL.md](../aws-wechat-article-images/SKILL.md) 第 6 步「调用失败」表格。

### 第7步：审稿

贴图专用清单：[references/checklist.md](references/checklist.md)

### 第8步：发布

```bash
python {baseDir}/../aws-wechat-article-publish/scripts/publish.py full article/
```

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`（可选）、**`.aws-article/config.yaml` + 本篇 `article.yaml`** | `imgs/`（outline + prompts + 图片） |
