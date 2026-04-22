---
name: aws-wechat-article-images
description: 公众号封面｜公众号配图｜公众号插图｜AI 生图 — 公众号 AI 封面与配图生成，按文章标题与内容自动匹配画风，一稿多方案，多风格预设可复用。面向公众号编辑、自媒体、品牌设计。触发词：「封面」「配图」「插图」「生成图片」「给文章加图」「做个封面」「文章插图」「配个图」。不写正文只发一组图请走 aws-wechat-sticker；需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
---

# 配图

**公众号封面 & 配图 AI 生成** —— 按文章内容自动匹配画风，一稿多方案，风格体系可复用。

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

完整长文从选题到发布 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)；图片消息/九宫格等多图推送 → [aws-wechat-sticker](../aws-wechat-sticker/SKILL.md)。

读取文章中的配图标记，按 Type × Style 体系生成图片。专注于**长文配图**，贴图请用 sticker。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 用途 |
|------|------|
| `scripts/image_create.py` | 专用生图 API：读 **`.aws-article/config.yaml`** 的 **`image_model`** + 仓库根 **`aws.env`** 的 **`IMAGE_MODEL_API_KEY`**|
| `scripts/user_image_prepare.py` | 用户供图模式：确保本篇 `imgs/` 存在并生成 `img_analysis.md` 模板（封面仅 1 张） |

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

从选题到发布的**前置规则**见 [aws-wechat-article-main/SKILL.md](../aws-wechat-article-main/SKILL.md)；本 skill 只描述配图步骤。

**图片模型**：**`image_model`**（`provider`、`base_url`、`model`、`default_size`、`default_quality` 等）在 **`config.yaml`**；**`IMAGE_MODEL_API_KEY`** 在 **`aws.env`**。键名对照 **`{baseDir}/../aws-wechat-article-main/references/env.example.yaml`**。

**`base_url` 须为完整端点路径**，脚本根据路径判断调用模式：
- `https://xxx.com/v1/images/generations` — DALL-E / gpt-image 等
- `https://xxx.com/v1/chat/completions` — Gemini 等多模态模型（通过中转站生图）

**交互约定**：可提示用户上述项是否已填；**一条龙**下通常已通过 **`validate_env.py`**。须遵守 main 的**智能体行为约束**——未通过环境校验且未获用户明确「本次例外」时，不得假装已走专用生图 API。

## 封面风格 + 正文配图

- **封面风格**：独立预设体系，见 [references/cover-styles/](references/cover-styles/)。每个预设 `.md` 自包含视觉关键词。
- **正文配图**：Type（画面构成）决定"画什么"，Style（视觉风格）由 Agent 根据 tone/category 内部选择。Type 列表与 prompt 模板见 [references/image-styles/](references/image-styles/) 目录。

### 封面 vs 正文（资源策略）⛔

| 类型 | 要求 |
|------|------|
| **封面** | **必须**通过 **`image_create.py`** 生成（`generate` 或 `batch` 读 `imgs/prompts/*.md`），产出并保存为文章目录下的 **`cover.png`**（或 `cover.jpg` / `cover.jpeg` / `cover.webp`）。**禁止**将 `.aws-article/assets/stock/images/`（或其它素材库文件）**直接复制**为 `cover.*` 充当封面。**例外**：用户**明确上传**封面文件并声明「封面只用这一张」时，可跳过脚本，须在 **`img_analysis.md`** 与审稿记录中注明「用户指定封面」。 |
| **正文** | **可直接使用参考资料库**：`.aws-article/assets/stock/images/`（先读同名 `.md` 再复制到本篇 `imgs/` 或引用路径），见下文「正文配图来源优先级」。缺图时再走 **`image_create.py`** 或 Agent 降级生图。 |

> 说明：全局 `config.yaml` 的 **`image_source: user`** 表示「正文以用户/素材引用为主」；**不豁免**上述「封面须脚本生成」规则，除非用户同时提供了封面文件并声明仅用该封面。

## 工作流

```
配图进度：
- [ ] 第1步：环境检查 + 本篇约束与文章
- [ ] 第2步：解析配图标记
- [ ] 第3步：确定风格
- [ ] 第4步：生成配图方案
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片（**脚本失败时**见同节「调用失败」分支，勿静默吞掉报错）
- [ ] 第7步：插入文章
```

### 正文配图来源优先级（Agent）⛔

**仅适用于正文插图**（不含封面；封面见上文「封面 vs 正文」）。**在**为正文 `placeholder` 调用 `image_create.py`、写入 `imgs/prompts/` **之前**，须先判断是否可用**本地素材库**，避免教程类、产品界面类文章「有截图资源却重新生成」：

1. **仓库素材库（参考资料库）**：列出并阅读 **`.aws-article/assets/stock/images/`** 下 **同名 `.md`**（含路径与画面说明），按主题匹配后，在 `article.md` 中直接引用对应 **`.png` / `.webp`**（或复制到本篇 `imgs/` 再引用）。**与正文严格相关才用**，避免硬凑。
2. **用户上传 / 本篇 `image_source: user`**：用户提供的图或上述引用策略，走「用户供图模式」与 `img_analysis.md`（正文部分）。
3. **仍缺图或须原创插画**：再进入 **Type × Style**、`imgs/prompts/` 与 **`image_create.py`**（或 Agent 降级生图）。

> 说明：素材库属「仓库内预设资源」，**不必**等用户手动上传才查；与「用户供图模式」并列，而非仅附属于后者。

### 第1步：环境检查 + 本篇约束与文章

- **全局**：读 **`.aws-article/config.yaml`** — `cover_aspect`、`cover_style`、`image_density`、`caption_style`、`multi_image_count`、`tone` 等以之为准（完整字段见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md) 与 **`config.example.yaml`**）。
- **本篇**：若同目录有 **`article.yaml`**，读取 **`default_cover_image_style`**、**`default_article_image_style`**（应为单元素列表，代表本篇已选预设）及 `cover_image` 等字段。
- 读取 **`article.md`**（或当前流程规定的正文来源）。
- 当 `image_source: user`（全局或本篇）时，进入「用户供图模式」：先创建本篇 `imgs/` 并生成/更新 `img_analysis.md`，记录每张图的内容分析、建议章节与推荐用途。

### 第2步：解析配图标记

提取所有 `![类型：描述](placeholder)`。`实证` 类型提示用户提供素材或从 `.aws-article/assets/` 搜索。

### 用户供图模式（新增分支）

当用户上传图片并指定主题时，按以下顺序执行：

1. 立即确保 `{article_dir}/imgs/` 存在，并将用户图片放入该目录。
2. 生成/维护 `{article_dir}/img_analysis.md`（每图至少包含：文件名、图片内容、建议章节、推荐用途、图注建议）。
3. **硬性约束**：`img_analysis.md` 中“推荐用途：封面”**必须且只能出现 1 次**；其余图片用途应为“正文”。
4. 同步更新本篇 `article.yaml`：`image_source: user`（从模型生图切换到用户供图状态）。
   - 字段取值只允许 `generated` / `user`。
5. 写稿阶段直接使用用户图片路径（如 `imgs/淘米.png`），**不再使用 placeholder**。

**顺序说明**：`imgs/` 落图 → 分析并写好 `img_analysis.md` → 再跑 `write.py`；写稿时以 `img_analysis.md` 为准，把图片插到与内容匹配的章节位置。

### 发布后换图重发（新增分支）

当用户明确说「这篇文章配图不满意，换成我上传的新图并重新发草稿箱」时，按以下流程：

1. 用户指定目标文章目录（`drafts/YYYYMMDD-slug/`）。
2. 将新图放入该目录 `imgs/`，并更新 `img_analysis.md`（仍需满足“封面仅 1 张”）。
   - 同步把本篇 `article.yaml.image_source` 更新为 `user`。
3. 按 `img_analysis.md` 重新映射图片到 `article.md` 对应章节（允许重排章节以匹配图序）。
4. 运行 `format.py` 重新生成 `article.html`（不要只改旧 html 局部）。
5. 进入终审：确认 `article.md` / `article.html` 无 `placeholder`，且引用图片文件均存在。
6. 回到发布步骤执行 `publish.py full`（`publish_method: draft` 时写入草稿箱）。

**可用素材库**（与上文「配图来源优先级」一致）：

- `.aws-article/assets/stock/images/`：本地参考/产品截图目录；**优先读同名 `.md` 再选图**。若已用素材库满足正文，可不再走生图 API。

### 第3步：确定风格

封面与正文配图**分别**确定风格，走各自的预设目录。

#### 封面风格

**预设发现**：Agent 扫描两个目录合并可用封面预设列表：
1. **内置**：`{baseDir}/references/cover-styles/`（随 skill 安装）
2. **用户自定义**：`.aws-article/presets/cover-styles/`（用户创建或预设包导入）

**加载优先级**：
1. 用户当次指定（如「封面要简约风」）
2. **本篇 `article.yaml.default_cover_image_style`**（单元素列表）→ 从内置或 **`.aws-article/presets/cover-styles/<名>.md`** 加载（用户文件同名优先于内置）
3. **fallback**：根据 `tone` / `article_category` 从可用封面预设中自动推荐（规则见 [auto-selection.md](references/image-styles/auto-selection.md)）

每个封面预设 `.md` 自包含视觉关键词（`Prompt 要点`），无须引用外部 Style 维度。Schema 见 [cover-styles/README.md](references/cover-styles/README.md)。

#### 正文配图风格

**预设发现**：Agent 扫描 `.aws-article/presets/image-styles/` 获取可用正文配图预设。

**加载优先级**：
1. 用户当次指定（如「正文要扁平插画」）
2. **本篇 `article.yaml.default_article_image_style`**（单元素列表）→ 加载 **`.aws-article/presets/image-styles/<名>.md`**
3. **fallback**：根据正文内容信号与 `tone` 自动推荐 Type 和视觉风格（规则见 [auto-selection.md](references/image-styles/auto-selection.md)），视觉风格为 Agent 内部决策

### 第4步：生成配图方案

为每张图生成方案（类型、风格、prompt 要点）。

**封面 prompt frontmatter 必须包含 `aspect`**：从 `config.yaml` 的 `cover_aspect` 读取（如 `2.35:1`），写入 YAML frontmatter。`image_create.py` 据此转换为实际像素尺寸；**缺少 aspect 会导致 fallback 到 1:1**。

**图片内文字**：画面中出现的文字必须为中文。在 prompt 里**直接写出要显示的中文文案**（如「传统对话AI」「OpenClaw」），禁止只写 “labels in Chinese” 或 “Chinese or English OK”，否则模型会生成英文。

Prompt 构建：[references/image-styles/prompt-construction.md](references/image-styles/prompt-construction.md)

### 第5步：展示方案并等待确认 ⛔

### 第6步：生成图片

**封面**：见「封面 vs 正文」— **默认必须先**写好 **`imgs/prompts/`** 中封面 prompt（含 `aspect` 与 `config.yaml` 的 **`cover_aspect`** 一致），再执行 **`image_create.py generate … -o ../cover.png`**（或等价输出路径）。

**生成方式（优先级，正文）**：

0. **已在「正文配图来源优先级」中用尽素材库 / 用户图**：本节不再对**该图位**重复生图（封面仍须单独按上款处理）。
1. **缺图时优先：调用专用生图 API**（`scripts/image_create.py`）— 依赖 **`config.yaml` 的 `image_model` + `aws.env` 的 `IMAGE_MODEL_API_KEY`**
2. **自动降级：模型未配置**（退出码 2、stderr 含 `[NO_MODEL]`）且当前 Agent 支持图片生成、并已获用户明确同意代生图 → Agent 读取 `imgs/prompts/*.md` 中的 prompt + frontmatter（size/quality），用自身多模态能力按**相同 prompt** 生图 → 告知用户 `ℹ️ 图片模型未配置，本次由当前对话模型直接生图（使用相同配图方案）` → 生成后**正常执行第 7 步**（插入文章）
3. **故障降级**（退出码 1）→ 按本节下方「调用失败」表格分类处理
4. **用户供图：跳过生图** — 当 `image_source=user` 或用户明确”使用我上传的图片”时，不调用 `image_create.py`，改为”读图分析 + 写稿引用 + 重排版”

**必须告知用户当前使用的方式**：

- 已配置且调用脚本 → `ℹ️ 使用 image_create.py 调用专用生图模型（{model}）`
- Agent 降级生图（退出码 2）→ `ℹ️ 图片模型未配置，本次由当前对话模型直接生图（使用相同配图方案）`
- 故障降级 / 仅 prompts → `ℹ️ 本次未走 image_create.py（原因：…）`

**⛔ 故障降级（退出码 1）时的终点**：只做到第 4 步（或第 5 步）。产出 `imgs/prompts/*.md` 与方案；**不执行**「替换 article 中的 placeholder」或「修复 HTML」。若 `imgs/README.md` 尚不存在或需补充当前方案的说明，可创建/更新（如何配置 **`aws.env` / `config.yaml`**、如何跑 `image_create.py batch`、如何在 `article.html` 中替换）；若已存在且已涵盖当前方案，**不必重写**。

**注意**：退出码 2（模型未配置）且 Agent 支持图片生成、并已获用户明确同意代生图时，**不受上述终点限制**——Agent 降级生图后继续执行第 7 步。

**调用专用 API 时**（在**仓库根**执行，`{baseDir}` 按上表解析；路径按本篇 `imgs/` 调整）：

```bash
python {baseDir}/scripts/image_create.py batch drafts/YYYYMMDD-slug/imgs/prompts/ -o drafts/YYYYMMDD-slug/imgs/
```

单张：`python {baseDir}/scripts/image_create.py generate imgs/prompts/01-cover.md -o imgs/01-cover.png`

连通性自检：`python {baseDir}/scripts/image_create.py test`

图片规格：[references/specs.md](references/specs.md)

#### `image_create.py` 调用失败时（智能体必选分支）

只要执行了 `image_create.py` 且**非零退出或 stderr 有 API/网络错误**，就必须走本节，**不得**只说「生图失败」而不分类、不摘要报错。

运行脚本后**须把终端 stderr 中的具体报错摘要给用户**（含 `❌`、HTTP 状态码、`【配置/认证】`、`网络错误（可重试）`、`[NO_MODEL]` 等关键行），勿只说「失败」。

| 类型 | 判断线索 | 智能体动作 |
|------|----------|------------|
| **未配置** | 退出码 2、`[NO_MODEL]` | Agent 支持图片生成且用户明确同意代生图 → 读取 `imgs/prompts/*.md` 中的 prompt + frontmatter（size/quality），用自身多模态能力按相同 prompt 生图并继续第 7 步。Agent 不支持图片生成，或 Agent 代生图失败 → 明确告知“我当前不能完成生图”，给用户二选一：**配置图片模型后重试**，或**本篇不配图继续**（保留 prompts 并在结果中标注无配图）。 |
| **网络类** | `URLError`、`网络错误（可重试）`、超时、临时 502/503 | **必须自动再试 1 次**（可短暂等待后重跑同一命令）。**第二次仍为网络类** → 可降级为 **Agent 多模态生图** 或仅保留 prompts；**须明确告知**用户本次未走专用 API。 |
| **配置/凭证类** | 401/403、图片模型配置不完整、`【配置/认证】` | **不要**静默降级。**列出须检查项**（**`config.yaml` 的 `image_model`**、**`aws.env` 的 `IMAGE_MODEL_API_KEY`**、端点、权限），请用户改正后重跑。用户**明确打字**接受本次仅用 Agent/仅 prompts 时，再按 main「本次例外」处理。 |
| **业务/参数类** | `【请求参数】`、400、返回体提示 model/size 不支持 | 将响应摘要给用户；可改 **`config.yaml` 或 env** 中的 model/尺寸后再试；仍失败则与用户商定是否 Agent 生图。 |

**禁止**：配置明显错误时静默改用 Agent 却不说明；网络降级后不告知「本次未走专用生图」。

### 第7步：插入文章

仅当**已生成图片**时执行：替换 placeholder 为实际图片路径，输出到 `imgs/`。

**封面排除**：封面图（`![封面：...]`）**仅用于微信文章封面上传**，**禁止**作为 `<img>` 嵌入 HTML 正文。替换 placeholder 时**跳过封面标记行**（或直接删除该行），封面图单独复制到文章根目录 `cover.{ext}`。`publish.py` 也支持从 `imgs/` 目录自动发现封面图（`cover.*` 或 `*-cover.*`）。

**修复 HTML 的触发条件**：仅当在 `article.html` 中**确实存在** `href="placeholder"` 或 placeholder 被渲染成可点击链接时，才将误转的 `<a>` 改为 `<img>` 或占位说明；**不要**默认每次都执行「修复流程图占位」或「修复 HTML」。

## 过程文件

| 读取 | 产出 |
|------|------|
| **`article.md`**、**`.aws-article/config.yaml`**、本篇可选 **`article.yaml`** 中的标记与配图约束 | `imgs/`（outline + prompts + 图片；未走 API 时为 prompts + 可选 imgs/README.md） |
