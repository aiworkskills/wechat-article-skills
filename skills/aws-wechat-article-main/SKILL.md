---
name: aws-wechat-article-main
description: 公众号运营｜微信公众号｜AI 写稿｜公众号排版｜公众号审稿｜公众号配图｜公众号发布｜一条龙｜自媒体运营｜WeChat Official Account｜content pipeline｜AIGC — 公众号 AI 一条龙运营总控入口，选题→写稿→审稿→排版→配图→发布串联 8 个子 skill，单条指令完成整篇图文从 0 到上架。面向公众号小编、自媒体、品牌内容。触发词：「帮我写篇公众号文章」「我想发一篇」「帮我发一篇」「一条龙」「完整流程」「从头做」「公众号运营」「今天写什么好」「有什么好写的」「再来一篇」「继续上次的」「接着写」等。仅当用户明确只要某一步（如仅排版、仅审稿）才跳过本入口直连子 skill。
---

# 公众号运营总览

**一键式公众号 AI 内容流水线** —— 从选题到上架 8 个子 skill 串联，公众号小编 / 自媒体 / 品牌内容团队一键产出整篇图文。

> **套件说明** · `aws-wechat-article-*` 是公众号一条龙套件，共 9 个 slug：`aws-wechat-article-main / topics / writing / review / formatting / images / publish / assets`，外加 `aws-wechat-sticker`。跨 skill 的相对引用依赖同一 `skills/` 根目录；推荐 `clawhub sync` 或逐个 `clawhub install` 一次性全装。源码：<https://github.com/aiworkskills/wechat-article-skills>

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

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

## 配置检查 ⛔ BLOCKING

**进入交互顺序「2) 全局账号约束」「3) 本篇准备」及内容流水线前**须完成 **第 0～2.5 步**配置检测（任一步失败则 **不得** 继续）。**第 3 步**是**调用 `publish.py` 前**的核对（非流水线起点）：**`.aws-article/config.yaml`** 中 **`publish_method`** 默认为 **`draft`**（**`publish.py full`** 只把图文写入**公众号草稿箱**）；仅当用户明确要求「发出去 / 对外发布」时，再将该键改为 **`published`**（或使用 **`full --publish`** 临时强制发布）。**微信**：**`validate_env.py`** 默认要求公众号账号配齐（见第 2 步）；用户**明确不接微信**时，先将 **`publish_method`** 设为 **`none`** 再过校验（脚本会跳过微信组），之后 **`publish.py full`** 仍直接跳过。要走草稿/发布，须补全 **`aws.env`** 与 **`config.yaml`** 微信槽位，并建议 **`check-wechat-env`**。文风与账号约束以 **`config.yaml`** 为准，发文元数据以本篇 **`article.yaml`** 为准。

### 第 0 步：判断操作系统

智能体在执行下列检测命令前，**先判断当前环境**：

- **Linux / macOS**：使用 Bash 命令（`test`、`echo` 等）。
- **Windows**：使用 **PowerShell** 命令（`Test-Path` 等）。

### 第 1 步：`.aws-article/config.yaml` 与 `aws.env` 是否存在

在**仓库根目录**（当前工作目录为项目根）执行：

**Linux / macOS：**

```bash
test -f .aws-article/config.yaml && test -f aws.env && echo "ok" || echo "missing"
```

**Windows（PowerShell）：**

```powershell
if ((Test-Path -LiteralPath ".aws-article\config.yaml") -and (Test-Path -LiteralPath "aws.env")) { "ok" } else { "missing" }
```

⛔ 输出为 `missing`（任一文件不存在）→ 按 [首次引导](references/first-time-setup.md) 创建或补全：可参考 **`{baseDir}/references/config.example.yaml`** 得到 **`config.yaml`**，在仓库根创建 **`aws.env`**（仅密钥与微信 `WECHAT_N_APPID` / `WECHAT_N_APPSECRET` 等，键名可与 `{baseDir}/references/env.example.yaml` 对照）。

**初始化约束**：新建 **`.aws-article/config.yaml`** 时，`publish_method` 默认必须为 **`draft`**；除非用户明确指定不接微信，否则禁止初始化或改写为 `none`。

### 第 2 步：校验配置内容（`validate_env.py`）

两文件均存在后，在仓库根运行：

```bash
python {baseDir}/scripts/validate_env.py
```

（默认读取 **`.aws-article/config.yaml`** 与 **`aws.env`**；可用 `--config` / `--env` 指定路径。）

脚本检查（规则摘要，具体交互文案统一以 [首次引导](references/first-time-setup.md) 为准）：

- **写作模型**：`config.yaml` 中 `writing_model.base_url` / `model` 与 `aws.env` 中 **`WRITING_MODEL_API_KEY`** 须同时非空（`provider` 可选，不填按 URL/模型名自动识别）；否则 **`failed`** + **`写作模型配置不完整`**，**退出码 1**。
- **图片模型**：`image_model.base_url` / `model` 与 **`IMAGE_MODEL_API_KEY`** 须同时非空（`provider` 可选，不填按 URL/模型名自动识别）；否则同上，**退出码 1**。
- **微信公众号**：`wechat_accounts`、`wechat_api_base`、各槽位名与 **`aws.env`** 中 **`WECHAT_{i}_APPID` / `WECHAT_{i}_APPSECRET`** 须成对完整；否则 **`failed`** + **`微信公众号配置不完整`**，**退出码 1**。**例外**：**`config.yaml`** 中 **`publish_method: none`**（用户明确不接微信）时，**跳过**微信组校验，仍输出 **`True`**（并附一行说明已跳过）。

**退出码 0**：写作、图片均通过，且（未声明 **`none`** 时）微信也通过 → **`True`** + **`配置校验通过`**。**退出码 1**：任一组未通过 → 不得进入一条龙默认流水线，并引导 [首次引导](references/first-time-setup.md) 补全或 **`publish_method: none`** 后重跑。

### 第 2.5 步：创建预设与素材目录（硬性前置，必须执行）

**仅当第 2 步退出码为 0** 才执行本步；执行成功后才允许进入「2) 全局账号约束」与后续流水线。  
目录要求与命令以 [首次引导第 2 步](references/first-time-setup.md) 为准（需覆盖 `presets/*`、`assets/*`、`tmp`）。

- **禁止**因为“环境检查通过”就跳过本步直接写稿。
- 若目录已存在，可视为本步通过；若缺失，必须立即补建并继续校验。

### 第 3 步：调用 `publish.py` 前（`publish_method` + 微信）

- **`publish_method`**（**`draft`** / **`published`** / **`none`**）写在 **`config.yaml`**，**默认 `draft`**。**`none`** = 用户明确不填微信：**`full`** 不调 API。要「发布出去」→ **`published`** 或 **`full --publish`**。
- **微信**：在 **`aws.env`**；槽位在 **`config.yaml`**。**`draft`/`published`** 走 **`full`** 前须就绪；**`none`** 下不调用微信。
- 运行 **`publish.py full`** 前：确认 **`publish_method`** 合法（小写）；**非 `none`** 时建议 **`check-wechat-env`**。

### 智能体行为约束（禁止自作主张）

检测到 **`.aws-article/config.yaml` 或 `aws.env` 缺失**、**`validate_env.py` 退出码 1**（微信配置不完整，且未声明 **`publish_method: none`**），或用户**已要求调用 `publish.py`** 而微信槽位 / 凭证未就绪时：

- **禁止**在未询问用户、未取得用户**明确文字确认**的情况下，自行决定：跳过微信配置、仅出 prompt 却继续宣称「一条龙已完成」、或继续排版/发布并假装配置已就绪。
- **必须先**：向用户说明**具体缺哪一类**（脚本 **`failed`** 下的 **`微信公众号配置不完整`**；或即将 **`publish.py`** 但微信未配齐），并**统一按** [首次引导](references/first-time-setup.md) 中「校验失败时的配置引导」文案执行。
- **输出约束**：该场景下除”环境检查结果”可按实际失败项替换外，其余引导文案须与首次引导保持一致。
- 用户补全并落盘后，智能体协助重跑 **`validate_env.py`**；若用户明确声明本次例外，按首次引导与本节约束继续处理。涉及 **`aws.env`** 的密钥仍由用户本地粘贴更安全，避免无必要重复口述 `AppSecret`。

> **模型未配置例外**：写作模型默认阻断；仅当**用户明确同意**由 Agent 代写并传入 `--agent-writing-approved` 时，写作模型未配置才降为警告。图片模型同理，仅在**用户明确同意**使用 Agent 代生图并传入 `--agent-image-capable` 时降为警告；未获用户明确同意时，模型未配置均按阻断处理。须告知用户当前使用的方式。

> **单步子 skill**：用户只触发某一子能力（如仅排版、仅审稿）且**未走本总览流水线**时，仍以各子 skill 内说明为准；**一条龙 / 完整流程 / 从选题到发布** 必须满足本节 BLOCKING 与上条「禁止自作主张」。

## 主要配置文件（不要混用）

| 文件 | 位置 | 作用 |
|------|------|------|
| `aws.env` | **仓库根** | **密钥**：写作/图片 `*_API_KEY`、微信 `WECHAT_N_APPID` / `WECHAT_N_APPSECRET` 等（键名见 `references/env.example.yaml`；与 `config.yaml` 一起由 `validate_env.py` 校验） |
| `.aws-article/config.yaml` | 仓库内 | **非密钥配置**：账号文风、模型 `provider`/`base_url`/`model`、微信槽位数与 `wechat_api_base`、各槽位展示名等（模板见 `references/config.example.yaml`） |
| `references/env.example.yaml` | 仓库内示例 | **仅文档**：`aws.env` 键名说明 |
| `references/config.example.yaml` | 仓库内示例 | **仅文档**：`config.yaml` 结构示例 |
| `article.yaml` | **本篇目录** `drafts/YYYYMMDD-标题slug/` | **发文元数据**（标题/作者/摘要/封面等）及状态字段：**`image_source`**（仅 `generated` / `user`；默认 `generated`，用户上传配图时改为 `user`）与 **`publish_completed`**（新建 **`false`**，发布闭环结束 **`true`**），与 **`config.yaml`** 分工 |

### 发布方式与时间线

1. **账号与发布策略**：**文风、选题边界、`publish_method`（默认 **`draft`**）、微信槽位元数据**等均在 **`.aws-article/config.yaml`** 维护；**密钥**仅在 **`aws.env`**。
2. **本篇准备**（须先完成交互顺序 **「2) 全局账号约束」**）：在 **定题与 slug** 之后新建 `drafts/YYYYMMDD-标题slug/`，并**优先**创建 **`article.yaml`**（含 **`publish_completed: false`**、标题/作者/摘要等；通常为本目录内**首个**应落盘的文件），再进入内容流水线。
3. **执行原则（严格顺序）**：必须按下述流水线顺序依次执行，**不能跳过任何部分**；每到一步若缺少必要输入（目录、元数据、主题、用户选择、发布意图等），要**先及时询问用户并获得确认**，再进入下一步，除非用户指出基于某个历史任务继续创作，那么需要智能体根据中间产物判断从哪个阶段开始。
4. **内容流水线**（子 skill 串行，详见下文 **「交互顺序」第 4 步** 与 **「流程」** 表）：**选题**（[topics](../aws-wechat-article-topics/SKILL.md)）→ **写稿**（[writing](../aws-wechat-article-writing/SKILL.md)）→ **审稿（内容审）**（[review](../aws-wechat-article-review/SKILL.md)）→ **排版**（[formatting](../aws-wechat-article-formatting/SKILL.md)）→ **配图**（[images](../aws-wechat-article-images/SKILL.md)）→ **审稿（终审）**（review）。**内容审**产出的 **`article.md` 定稿须满足 [review 第 5 步](../aws-wechat-article-review/SKILL.md)（文末 **`{embed:…}`**，⛔ BLOCKING）后再排版。全程以 **`.aws-article/config.yaml`** 为账号与文风约束；典型产物依次为 `topic-card.md` / `draft.md` → `article.md` → `article.html` 与 `imgs/` 等。
5. **发布**（[publish](../aws-wechat-article-publish/SKILL.md)）：**`draft`** → **`full`** 仅**草稿箱**；**`published`** 或 **`full --publish`** → 再**提交发布**；**`none`** → **`full`** **立即跳过**、不调微信。前两档需微信凭证。

**再强调**：**`aws.env`** = 密钥；**`config.yaml`** = 账号/文风/模型与微信元数据及 **`publish_method`**；**本篇 `article.yaml`** = 发文元数据。

## 交互顺序（一步步，最小提问）

按以下顺序与用户交互，**上一步完成再进下一步**；上一环节就绪后再进入下一环节。

### 1) 配置自检（必做）

- 按上文 **配置检查** 完成：**`config.yaml` 与 `aws.env` 均存在** → 运行 **`validate_env.py`**（默认不加 `--agent-image-capable`）**且退出码 0**。**退出码 1** 时按 [首次引导](references/first-time-setup.md) 补全环境；仅当用户**明确表示不接微信**时才可设 **`none`**；走**本次例外**需用户明确书面确认。
- **`validate_env.py` 退出码 0 后，必须立即执行「第 2.5 步目录创建」**（可复用 [首次引导第 2 步](references/first-time-setup.md) 命令）；该步完成前，**禁止**进入「2) 全局账号约束」与任何写稿流程。
- **退出码 0 + 模型警告**：流程**不阻断**，可直接进入下一步。模型警告仅在用户已明确同意并传入对应参数时出现：写作模型用 `--agent-writing-approved`，图片模型用 `--agent-image-capable`。
- **禁止擅自加参数**：未获用户明确同意前，禁止自行追加 `--agent-image-capable` 或宣称可按代生图模式继续。
- **退出码 1（微信不完整）时**：只展示 [首次引导](references/first-time-setup.md) 中的 **配置选项**，**不要**在同一轮回复里再问「写哪篇 / 继续哪篇草稿 / 新选题」等；须等配置闭环（重跑校验通过或「本次例外」已书面确认）后，**再**进入下方 **「2) 全局账号约束」**。
- **`validate_env.py` 不检查** `article_category`、`target_reader`、`default_author`；须在 **「2) 全局账号约束」** 中单独检查并落盘。

### 2) 全局账号约束（`.aws-article/config.yaml`）⛔

**在 `validate_env.py` 已通过**（或已按总览完成「本次例外」）**之后、进入「3) 本篇准备」之前**，**必须**打开 **`.aws-article/config.yaml`**，检查下列键 **trim 后是否非空**：

- **`article_category`**、**`target_reader`**、**`default_author`**

任一项缺失或空白：**逐项询问用户**（1.账号领域2.目标读者3.作者名字），取得**用户当轮明确答复**后再**写回** **`.aws-article/config.yaml`**，再进入 **「3) 本篇准备」**。**禁止**仅在对话里口头确认却不写入文件。**禁止**跳过本步直接假定可写稿。

**⛔ 禁止擅自填写（必须写进行为约束）**

- **不得**从本篇或其它目录的 **`article.yaml`**、历史草稿、**`topic-card.md`**、对话记忆或仓库内任意文件**静默抄录、推断或「顺手补全」**后写入 **`article_category` / `target_reader` / `default_author`**。对 **`tone`** 等与账号画像强相关的全局项，要直接询问用户，**同样禁止**未询问就写盘。
- **允许的做法**：向用户说明「当前为空」，**请用户填写或确认**；若你想根据某篇 `article.yaml` 给**建议**，只能**展示为待选文案**，并问「是否采用 / 要改哪几个字」，**用户明确同意后再写入** `config.yaml`。
- **顺序**：在尚未完成 **「3) 本篇准备」** 中「续旧 / 新开」的确认前，**禁止**用某一 `drafts/…/article.yaml` **反推**全局三键，避免误把单篇元数据当成整号定位。

### 3) 本篇准备（二选一，默认「新建一篇」）

**在完成「2) 全局账号约束」之后**，**在不了解用户是要续写既有草稿还是新开一篇时**（例如未指定 `drafts/…` 路径、且仓库 **`drafts/`** 下存在进行中目录或多个候选）：**须先询问**并让用户选定 **「继续哪一篇」** 或 **「新开一篇」**，**再**进入下列 A/B 或调用写作脚本。**禁止**默认「最近修改」目录、未确认就运行写作脚本、或假定沿用上一轮路径。

#### A. 新建一篇（**严格子顺序**，勿跳步）

1. **写作意图** ⛔ **BLOCKING**：必须问清用户 **本篇要写什么**（具体主题、角度、体裁或目标）。若用户只想「帮我出选题」，须**明确确认**后再当无方向模式处理。  
   - **禁止**在用户未回答本步（且当前对话也未等价说明）之前：**调用 web_search**、**执行 topics 的调研**、**批量生成选题或标题**。  
   - 用户已在当次对话中说清楚「写什么」的，可本步口头确认一句即可，不必重复盘问。
2. **定题与 slug**：在写作意图已明确的前提下，确定**发文章标题**——用户从候选中选一个，或**自定义标题**；据此生成 **slug**，目录名为 `YYYYMMDD-标题slug`（slug 规则：小写、连字符、与项目习惯一致即可）。
3. **建目录与 `article.yaml`**：创建 `{drafts_root}/YYYYMMDD-标题slug/`（`drafts_root` 以 **`config.yaml`** 为准，默认 `drafts/`）。随即初始化本篇 **`article.yaml`**（含 **`publish_completed: false`**，及标题、作者、摘要等；目录内**宜最先写入**；可用 `{baseDir}/../aws-wechat-article-publish/scripts/article_init.py`）。
   - **`publish_method`**：默认 **`draft`**；要发出去 → **`published`** 或 **`full --publish`**；用户明确不填微信 → **`none`**。
4. **本篇预设单选落盘（必做）**：初始化后按场景执行：**新建首轮**以 **`.aws-article/config.yaml`** 为来源，按 **`custom_* > default_*`** 结合本篇主题/选题卡，为以下字段各选**单一预设**并写回本篇 **`article.yaml`** 为**单元素列表**：`default_structure`、`default_closing_block`、`default_title_style`、`default_format_preset`、`default_cover_image_style`、`default_article_image_style`、`default_sticker_style`。**续写/重入**时若本篇 `article.yaml` 对应字段已为单元素列表，视为本篇已选并优先保留，不重选不覆盖。若 `config.yaml` 不存在或候选为空，可保持 `[]`。
5. 至此才进入 **第 4 步内容流水线**。

#### B. 我已有目录

- 用户给出路径。必读 **`.aws-article/config.yaml`**（账号与发布策略）；本篇目录内需有 **`article.yaml`**（或按用户状态后补）。若已有 `article.html`/`cover.jpg` 可直接从流水线中靠后的步骤接入。
- 若用户意图是「发布后换图并重发草稿箱」，也走本分支：指定既有目录后，从 **配图（用户供图分支）** 接入，再执行 **终审 → 发布**。

### 4) 内容流水线（子 skill）

须已具备 **本篇目录** 与 **`article.yaml`**（「已有目录」分支按上条处理）；账号侧约束以 **`config.yaml`** 为准。

**确认轮次优化**：全局三键已非空时静默通过；`publish_method` 已为合法值时不重复盘问；多个待确认项可合并为一轮提问。用户意图明确时（如给出主题 + "写一篇文章"），理想轮次为 **1 轮**（确认标题/摘要）+ **写完后展示结果**。配图方案在用户无特殊要求时按默认风格自动执行，不单独确认。

```
选题 → 写稿 → 审稿(内容审) → 排版 → 配图 → 审稿(终审)
```

- **topics**：仅在 **写作意图已明确**（见上 3-A-1）之后执行；仍须遵守 **aws-wechat-article-topics** 中「展示后等用户选」等规则。
- **writing**：结合 **`.aws-article/config.yaml`** 与 `topic-card.md`（或用户素材）；**`publish_method`** 见 **`config.yaml`**（上文「发布方式与时间线」）；产物 `draft.md` → 内容审后 `article.md`。
- **review（内容审）**：定稿 **`article.md` 前**须按 [review 第 5 步 ⛔ BLOCKING](../aws-wechat-article-review/SKILL.md) 完成文末 **`{embed:…}`**（或规则允许的省略并留痕）；**未完成不得进入 formatting**。
- **formatting**：`article.md` → `article.html`（用户当次指定排版主题可覆盖默认）。
- **images**：按 **aws-wechat-article-images**（配置与行为约束以本节「配置检查」为准）。
- **review（终审）**：检查 `article.html` 与 `imgs/`；有问题给出清单，等用户确认或修复。

### 5) 发布

- 以 **`config.yaml`** 的 **`publish_method`** 为准；**`draft`** / **`published`** / **`none`** 含义见上文。**`none`** 时运行 **`full`** 会无操作退出。
- **`draft`/`published`**：**微信**须配齐后再调 **`publish.py`**；建议 **`check-wechat-env`**。**`none`**：不调微信，说明即可。
- 完成后输出小结与回执，目录按需移至 `published_root`。

### 6) 发布后换图重发（补充分支）

当用户说「草稿箱里图不满意，换我上传的图重新发」：

1. 锁定目标 `drafts/…` 目录；
2. 将新图放入本篇 `imgs/`，生成/更新 `img_analysis.md`（封面仅 1 张）；
   - 同步更新本篇 `article.yaml`：`image_source: user`；
   - 开始重做流程前，将 `publish_completed` 置回 `false`；
3. 依据分析结果更新 `article.md` 图片映射（允许重排）；
4. 重新执行 `format.py` 生成 `article.html`；
5. 终审通过后执行 `publish.py full`（`draft` 写草稿箱）；
6. 发布命令成功且回执可用后，写回 `publish_completed: true`。

## 流程

```
选题 → 写稿 → 审稿(内容审) → 排版 → 配图 → 审稿(终审) → 发布
```

## 中间产物门禁（缺啥补啥）⛔

进入下一步前，必须先检查本步所需中间产物；缺什么就先补什么，禁止跳步并宣称已完成。

| 阶段 | 必要产物（最小集合） | 缺失时动作 |
|------|----------------------|------------|
| 写稿完成 | `article.md` 存在且非空 | 继续写稿或回滚到 writing |
| 排版完成 | `article.html` 存在，且由当前 `article.md` 重新生成 | 先执行 formatting 重转 |
| 配图完成 | 文章目录存在 `cover.(png/jpg/jpeg/webp)`；`article.md` 与 `article.html` 不含 `placeholder` | 先执行 images 生成并替换（`image_source=user` 时走用户供图映射与重排） |
| 发布就绪 | `article.yaml` 含 `title/author/digest/content_source`；发布环境检查通过 | 先补齐元数据或环境 |
| 发布闭环 | 发布命令成功且回执可用 | 才允许写回 `publish_completed: true` |

**禁止**：仅凭单一信号（如“草稿创建成功”）就宣称全流程完成。若正文仍有 `placeholder`，状态必须标记为“草稿已提交，正文配图未完成”。

| 步骤 | 子 skill | 读取 | 产出 |
|------|---------|------|------|
| 选题 | topics | **`.aws-article/config.yaml`**、`aws.env`、web_search | `topic-card.md` `research.md` |
| 写稿 | writing | `topic-card.md`、**`.aws-article/config.yaml`**、`aws.env`（专用写作 API） | `draft.md` |
| 审稿 | review | `draft.md`、`aws.env`、**`.aws-article/config.yaml`** | `review.md` → `article.md`（定稿须含文末 embed，见 [review 第 5 步](../aws-wechat-article-review/SKILL.md)） |
| 排版 | formatting | `article.md`、**`.aws-article/config.yaml`** | `article.html` |
| 配图 | images | `article.md`、`aws.env`、**`.aws-article/config.yaml`** | `imgs/` |
| 终审 | review | `article.html`、`imgs/`、**`.aws-article/config.yaml`** | `review.md` |
| 发布 | publish | `article.html`+`imgs/`、**`config.yaml`**、`aws.env`（调用 publish.py 时） | 草稿 media_id / 发布 publish_id、URL、`out/` 记录 |

**账号与文风约束**：以 **`.aws-article/config.yaml`** 为准。

**topics / `web_search`**：须满足上文 **3-A-1**（用户已说明本篇写什么，或已确认「只帮忙出选题」）之后才可调研与生成选题；不得默认跳过提问直接搜索。

> 提示：发布前需就绪本篇 `article.yaml`（标题/作者/摘要/封面等元数据；`content_source` 默认 `article.html`）。可用 `{baseDir}/../aws-wechat-article-publish/scripts/article_init.py` 快速初始化或更新。

## 路由

**默认**：与长文发文相关时 **优先 main**，由本 skill 按步编排；不要因用户说了「写」「选题」「发」就跳过 main 直连子 skill。

**何时直连子 skill**（可跳过 main 入口）：用户**明确只要该步产物**、且不隐含「从零到发出」整条链。例如：已有 `article.md` 只要排版；已有稿只要审稿清单；已有 `article.html`+`imgs/` 只要发布前检查或提交；已有选题卡只要扩写等。

| 用户说法 | 路由到 |
|---------|--------|
| 从0开始、从零、从头、一条龙、完整流程、帮我发一篇、发到公众号（含各前置步）、今天发什么/写什么好（要成文并发）、不确定从哪步开始 | **main** |
| **只要**选题卡、标题、摘要、排期、系列策划（明确不做后续编排） | topics |
| **只要**在已有选题/大纲/草稿上写稿、改写、润色、续写（明确不要全流程） | writing |
| **只要**审稿/校对/合规清单（成稿或已定版 HTML） | review |
| 「能不能发」且含代为发布、或要从稿到发出整条收尾 | **main** |
| **只要**排版、换主题、转 HTML | formatting |
| **只要**长文封面/正文配图（有正文或插图位） | images |
| 贴图、图片消息、多图推送、九宫格（非长文图文链路） | **sticker** |
| **只要**执行发布/提交/群发（已有约定产物） | publish |

## 运行模式

### 一条龙

用户说「一条龙」「完整流程」时启用。按 **交互顺序** 的 1→2→3→4→5 执行；**3-A** 内子步骤亦须逐步完成。流水线中每步完成后**暂停**等用户确认。审稿有 🔴 项时进入修改循环。

### 单步

用户**明确只要某一步**且已有对应输入产物（或声明不做全流程）时，可仅执行该步骤；若表述含糊、可能还要后续发文，仍从 **main** 问起或按一条龙拆步确认。

### 贴图

路由到独立的 **aws-wechat-sticker** skill。

## 配置与自定义

- **`aws.env`**（仓库根，密钥）与 **`.aws-article/config.yaml`**（非密钥与模型/微信元数据及 **`publish_method`**）：校验 **`{baseDir}/scripts/validate_env.py`**；`aws.env` 键名见 **`references/env.example.yaml`**
- **`config.yaml` / `article.yaml` / `aws.env` 字段说明**：[references/articlescreening-schema.md](references/articlescreening-schema.md)
- 发布前微信：**`{baseDir}/../aws-wechat-article-publish/scripts/publish.py check-wechat-env`**（仓库根执行，试换微信 **access_token**；凭证在 **`aws.env`**）
