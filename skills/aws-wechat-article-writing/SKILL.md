---
name: aws-wechat-article-writing
description: 公众号写稿｜长文写作｜文章润色｜改写续写 — 公众号长文 AI 写作，从话题或提纲生成完整初稿，支持改写、续写、润色、开头结尾优化，可调 DeepSeek / GPT / Claude 或由 Agent 代写。面向自媒体作者、公众号运营、品牌文案。触发词（**单独触发仅限对已有稿子的修改**）：「改写」「润色」「续写」「续一段」「往下写」「接着这段写」「重写开头」「改结尾」「调整语气」「这段润色下」「把这段改活泼点」「优化用词」「用 GPT 重写」「用 DeepSeek 重写」。新写一篇请走 aws-wechat-article-main（main 内部会调用本 skill 生成初稿）；需要多环节串联（写+审+排+配图+发）也走 main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env:
        - WRITING_MODEL_API_KEY
      bins:
        - python3
    primaryEnv: aws.env
---

# 长文写作

**公众号长文 AI 写作引擎** —— 从提纲或话题生成完整初稿，支持改写、续写、润色，多模型可切。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 调用 `write.py` 生成文章初稿，**会把文章内容发送给用户配置的 LLM 端点**。使用前请阅读以下全部行为说明：

- **凭证读取**：`write.py` 读取仓库根 `aws.env` 的 `WRITING_MODEL_API_KEY`
- **凭证外发**：该 API key 以 `Authorization: Bearer <key>` 头**发送到**用户在 `config.yaml.writing_model.base_url` 配置的外部端点（常见为 DeepSeek / OpenAI / Anthropic 等 Chat Completions 兼容 API）。**请使用专用 key 并配置可信端点或内部代理**
- **内容外发**：Prompt 内包含本篇 `article.yaml` / `topic-card.md` / 合并配置 / 用户通过 `--reference` 指定的参考文档 `.md` 全文 → 整体 POST 给上述端点
- **文件读（仓库内）**：`.aws-article/config.yaml`、本篇 `article.yaml`、`topic-card.md`、`.aws-article/products/{产品名}/*.md`（业务介绍 .md，直接挂在产品根）
- **文件读（仓库外）**：若仓库内 `.aws-article/` 缺失，`write.py` 会从用户家目录 `~/.aws-article/` 读取 `writing-spec.md` 与 `presets/`（**只读预设，不读凭证**）
- **文件写**：仅本篇目录下 `draft.md`、`article.md`
- **shell**：仅 `python3 {baseDir}/scripts/write.py`

可使用 `write.py prompt` 子命令**只输出 prompt JSON 不调用 LLM**，由 Agent 代写 —— 想避免把内容发给第三方时用这条路径。

## 配套 skill（informational）

本 skill 是 `aws-wechat-article-*` 一条龙公众号套件的**写稿环节**（入口 `aws-wechat-article-main`）。工作流中的若干步骤会读取同级 `../aws-wechat-article-main/references/*.md` 等共享文档（首次引导、env/config 示例、articlescreening schema 等）。

- **套件完整装齐到同一 `skills/` 根目录**时，跨 skill 引用都能读到。
- **单独安装本 skill** 时，跨 skill 引用的步骤会在读取阶段遇到 `file not found`；本 skill 内的纯本地步骤仍可用。

完整 9 slug 清单见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

## 路由

从零发文、一条龙、完整流程 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

从选题到发布的**前置规则**（阻断、禁止擅自降级、「本次例外」等）见 [aws-wechat-article-main/SKILL.md](../aws-wechat-article-main/SKILL.md)；本 skill 只描述写稿步骤。

**写作模型**：**`writing_model`**（`provider`、`base_url`、`model` 等）在 **`.aws-article/config.yaml`**；**`WRITING_MODEL_API_KEY`** 在仓库根 **`aws.env`**。键名对照 **`{baseDir}/../aws-wechat-article-main/references/env.example.yaml`**。

**交互约定**：须遵守 main 的**智能体行为约束**——**未**通过环境校验且**未**获用户明确「本次例外」时，不得默认改由当前 Agent 代写并假装流程完整。**环境检查未通过时**，只按 [首次引导](../aws-wechat-article-main/references/first-time-setup.md) 处理配置选项，**不要**在同一条回复里混入写稿、草稿路径或多草稿选择；配置闭环后再进入本 skill 工作流。

## 工作流

```
写稿进度：
- [ ] 第0步：⛔ [首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)
- [ ] 第1步：⛔ **`.aws-article/config.yaml`** 中 **`article_category`**、**`target_reader`**、**`default_author`**（trim 后）须**均非空**；缺则**逐项问用户**、用户确认后再**写回文件**；**禁止**从 **`article.yaml`** 等擅自抄录（与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致）；**须先于**续旧/新开
- [ ] 第2步：⛔ **在不了解**用户要**续写既有草稿**还是**新开一篇**时，**须先询问**并确定本篇 `drafts/…` 目录，**再**进入以下步骤；**禁止**未确认就调用写作脚本（见 [main](../aws-wechat-article-main/SKILL.md)「3) 本篇准备」开头）
- [ ] 第3步：读取本篇约束与写作规范；**写稿前先按下文「业务资料库」判断是否查阅/是否传 `--reference`**
- [ ] 第4步：发布方式（`publish_method`）⛔
- [ ] 第5步：确定输入与写作方式
- [ ] 第6步：写作
- [ ] 第7步：自检与修正
- [ ] 第8步：展示并等待用户确认 ⛔
```

**说明**：第 2 步在用户**已明确**路径或意图（例如直接给出 `drafts/…`、或明确说「新开一篇」）时可**不再重复盘问**。

**多草稿 / 未闭环**：与第 2 步同原则——**不了解**续写/新开时**须先问**，**禁止**自动选中某一 `drafts/…` 跑写作脚本。

### 确认轮次优化

以下步骤可**合并或静默通过**以减少交互轮次：

1. **Step 1**（全局三键）：若 `article_category`、`target_reader`、`default_author` 已非空 → **静默通过**，无需再确认。
2. **Step 4**（publish_method）：若已是 `draft`/`published`/`none`（合法值）→ **静默通过**（规则第3条已允许）。
3. **合并询问**：当需要同时确认 Step 2（新篇/续写）和 Step 4（发布意图）时，**合并为一轮提问**。
4. **配图确认**：若用户已给出明确主题且未提出风格要求，images skill 可按默认风格自动生成，**无需单独确认配图方案**。

**最少轮次**：用户意图明确时（如给出主题 + "写一篇文章"），理想轮次为 **1 轮**（确认标题/摘要）+ **写完后展示结果**。

### 第1步：全局账号三键（`.aws-article/config.yaml`）⛔

**在续旧/新开询问之前**，打开 **`.aws-article/config.yaml`**，检查 **`article_category`**、**`target_reader`**、**`default_author`** 是否 **trim 后均非空**。任一项缺失：**逐项询问用户**，取得**用户当轮明确答复**后再**写回该文件**，再进入第 2 步。**禁止**从 **`article.yaml`**、其它草稿或仓库文件**静默推断并写盘**；可把从某文件读到的内容**仅作建议展示**，须用户同意后再写入。**禁止**跳过本步。**禁止**仅在对话里确认却不落盘。与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致。

### 第2步：续旧稿还是新稿（不了解时须先问）⛔

**当不清楚**用户是要**续写 `drafts/` 下某篇进行中草稿**还是**新开一篇**时：**须先询问**（可列出候选目录），待用户选定后再进入第 3 步。**须在第 1 步全局三键已落盘之后执行**。**已明确**时跳过本步询问。

**目录命名**：新开一篇时，目录名**必须**为 `YYYYMMDD-标题slug`（如 `drafts/20260406-wechat-article-skills/`）。`YYYYMMDD` 为当日日期，`slug` 为小写、连字符分隔的标题缩写。**禁止省略日期前缀**。

### 第3步：读取本篇约束与写作规范

**⛔ 关键字段不得空跑**：在调用 **`write.py`** 或按合并约束让 Agent 代写之前，确认合并后的 **`article_category`**、**`target_reader`** **均为非空字符串**（trim 后）；**`default_author`** 非空 **或** 本篇 **`article.yaml` 的 `author`** 非空。若任一项不满足，**须暂停写稿**，引导用户补全 **`.aws-article/config.yaml`**（及/或本篇 **`article.yaml`**），**并实际写入文件**——**不要**仅用对话表格收集「读者」却不落盘。全局三键的优先检查顺序见 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」；若第 1 步已正确落盘，此处多为合并 **`article.yaml` 覆盖**后的复核。

**约束从哪来**：`write.py` 会先读全局 **`.aws-article/config.yaml`**，再读本篇目录下的 **`article.yaml`**，把两边的键**叠成一张表**用来生成写作提示——**若同一键在两份文件里都有，以本篇 `article.yaml` 为准**。字段分工见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

1. **`.aws-article/config.yaml`**：**文风、结构预设、禁用词、字数、`embeds` 等**与「写什么、怎么写」有关的顶层字段会进入这张表。  
   **`writing_model` / `image_model`** 两段只给脚本**连 API 用**（地址、模型名等），**不**整段放进给大模型的「写作说明」里，以免把技术配置当成正文要求。
2. 本篇 **`article.yaml`**：本篇标题、作者、摘要、**`publish_completed`** 等；与 config **重名的键**会**覆盖** config。

**`write.py`** 在仓库根执行，按**输入 `.md` 所在目录**找到本篇 **`article.yaml`**；叠完后的约束表不能为空（一般只要 **`config.yaml`** 里已有账号/文风等即可）。**`publish_completed`**：新建或补全本篇 **`article.yaml`** 时须为 **`false`**；本篇发布真正结束后由 [publish skill](../aws-wechat-article-publish/SKILL.md) 改为 **`true`**；**`publish.py` 不修改此字段**。

`default_structure` / `default_closing_block` 指向的 **预设正文**来自 **`.aws-article/presets/`**（及用户目录下同名 presets），与配置中的**文件主名**对应。两者在本篇 **`article.yaml`** 中必须为**单元素列表** `[名]`（或空列表 `[]`）；`write.py` 对预设选择仅读取本篇 `article.yaml`，不再在执行阶段从 `custom_*` / `default_*` 候选池推断。

**多候选自动选择**：当 `default_structure`（或 `default_closing_block`）含**多个候选**时，Agent 须：
1. 读取每个候选预设文件（如 `.aws-article/presets/structures/<名>.md`），了解其适用场景；
2. 结合本篇主题 / 选题卡内容，判断最匹配的一个；
3. 将该名写入 `article.yaml` 同键为单元素列表 `[名]`；
4. 然后再调用 `write.py`。
**禁止**盲选第一个——须基于内容匹配。若无法判断，向用户展示候选及说明后请用户选择。

另加载 **`.aws-article/writing-spec.md`**（如有）。

| 字段 | 用途 |
|------|------|
| `target_reader` | 读者画像 → 深度、用词、案例 |
| `tone` | 调性 → 语气与句式 |
| `writing_style` | 结构表达方式（口语/书面/故事/方法论等） |

配置中其它与写稿相关的键（如 `topic_direction`、`forbidden_words`、`heading_density`、`target_word_count`）一并写入约束。

### 业务资料库（写稿前 + 写后）⛔

**目的**：`.aws-article/products/{产品名}/` 是用户业务（产品/软件/服务）的原始资料库——业务介绍 `.md` **直接挂在产品根**（如 `项目介绍.md`），`images/` 子目录存业务配图。

**触发口径**：

- **若本篇主题涉及用户自身业务（对外介绍 / 教程 / 案例 / 自家业务安利）**：**必须**先 `ls .aws-article/products/`，对相关产品根下的 `*.md` **必读**，已有同主题文档**优先增量改写**而非另起炉灶。
- 若本篇主题与用户自身业务无关（行业资讯 / 通用教程等）：**不读**、不强求查阅。

写作只有 **两种方式**，业务资料用法如下（二选一，勿混用同一条命令里的职责）。

#### 方式一：智能体直接写稿

1. **写稿前**：先 `ls .aws-article/products/`；若本篇涉及某产品业务，**必读**该产品根下相关 `*.md`。
2. **写作时**：将业务资料转化为账号文风后引用；**与业务无关或无相关文档时不引用，不阻断写稿**。
3. **`draft.md`**：凡正文中**实际引用或依据**了某份业务介绍的，在**该处表述之后**用括号附上**该文件的仓库相对路径**（路径须真实存在）；**未引用则不必加括号**。
4. **配图占位（硬性）**：当 **`image_source` 不为 `user`**（合并 `config.yaml` + 本篇 `article.yaml`）时，按 **`image_density`** 生成配图占位；若未配置或为空，默认**每节一图**。格式必须为 `![类型名：画面内容](placeholder)`，每个占位**独占一行**，**封面**占位放在**标题之前**；类型名与细则见 [references/structure-template.md](references/structure-template.md)「配图标记」。
5. **下游产物 `article.md`**：本 skill 产物**只到 `draft.md`**，括号路径**保留在 `draft.md` 中**用于事实溯源。`article.md` 是 [review skill 第 5 步](../aws-wechat-article-review/SKILL.md) 的产物，由 review 调用 `write.py strip-citations <draft.md> -o <临时文件>` 自动剥离括号路径，再追加文末 `{embed:…}` 后写入。**writing 阶段禁止**自行命名 `article.md`、自行剥离括号路径、或假装"自检"等同于审稿。

#### 方式二：`write.py` 写稿

1. **运行脚本前**：同样先 `ls .aws-article/products/`，判断是否有相关产品的业务介绍 `.md`。
2. **有相关文档**：在仓库根执行 `write.py` 时传入 **`--reference <路径>`**（可重复，**最多 5 个**；路径须形如 `.aws-article/products/<产品名>/<文件名>.md`——**直接挂在产品根**，**不接受** `images/` 子目录下的图片说明 `.md`，详见脚本与 [usage](references/usage.md)）。脚本将全文注入系统提示「参考资料库」，并约定模型在依据处标注资料路径。
3. **无相关文档**：**不传 `--reference`**，仅靠选题卡与合并配置写稿即可。
4. 若写作 API 因上下文/token 超限失败，减少 `--reference` 篇数或换更短文档后重试。

**写后识别（双向回写）**：若本次写作产生的内容**语义属于用户业务介绍**（不是文章主体而是侧重产品/服务自介），按 [assets skill 一、业务介绍 .md 入库](../aws-wechat-article-assets/SKILL.md#一业务介绍-md-入库product-intro) 引导用户保存到 `.aws-article/products/{产品名}/`，下次写涉及业务的文章会自动用上。

**禁止**：将与主题无关的文档硬塞进正文；伪造业务资料中不存在的事实。

### 第4步：发布意图（`publish_method`）⛔

在**调用 `write.py` 或进入第6步写作之前**，确认 **`.aws-article/config.yaml`** 中的 **`publish_method`**（与 [发布 skill](../aws-wechat-article-publish/SKILL.md)、[articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md) 一致）：

| 取值 | 含义（向用户说明时用 plain 语言） |
|------|----------------------------------|
| **`draft`**（**默认**） | 定稿后若走 **`publish.py full`**，只把图文写入**公众号草稿箱**，不自动「发出去」。 |
| **`published`** | 定稿后 **`publish.py full`** 会在创建草稿后**再提交发布**（异步）。也可用 **`full --publish`** 单次强制带发布。 |
| **`none`** | 询问微信配置后用户**明确不想填写**：写入 **`publish_method: none`**。**`publish.py full`** 会**直接跳过**、不调微信；写稿/审稿/排版等照常。 |

**规则**：

1. **默认保持或写入 `publish_method: draft`**，除非用户**明确要对外发布** → 改为 **`published`**；**明确不填微信、不走上传** → 改为 **`none`**。
2. **微信**：提醒发布需要 **`aws.env`**；用户拒绝填写 → **`none`**，不要代跑 **`publish.py full`**（跑了也会无操作退出）。
3. **若已是 `draft` / `published` / `none`**（小写）：可**不重复盘问**。

**禁止**：在 `publish_method` **非法**时调用 `write.py`；禁止未经同意默认 **`published`**。

### 第5步：确定输入与写作方式

**输入**：`topic-card.md` / 用户提供的提纲或素材 / 用户口述主题；**并已按上文「说明文档资源库」完成判断**（直接写稿则已决定是否引用；走 `write.py` 则已决定是否传 `--reference`）。

**写作方式（优先级）**：

1. **优先：调用第三方模型**（`write.py draft/rewrite/continue`）— 依赖 **`config.yaml` 的 `writing_model` + `aws.env` 的 `WRITING_MODEL_API_KEY`**（见 [usage.md](references/usage.md)）
2. **自动降级：模型未配置**（退出码 2）→ 先 `write.py prompt <mode> <input>` 获取提示词 JSON，再由 Agent 按**相同提示词**直接写，**无须**「本次例外」确认
3. **故障降级：调用失败**（退出码 1）→ 按下方重试/排错逻辑

**必须告知用户当前使用的方式**：

- 已配置且调用脚本 → `ℹ️ 使用 write.py 调用第三方模型（{model}）`
- 模型未配置自动降级 → `ℹ️ 写作模型未配置，本次由当前对话模型直接写稿（使用相同写作约束）`
- 故障降级 Agent 直写 → `ℹ️ 第三方 API 不可用，本次由当前对话模型代写（使用相同写作约束）`，并说明原因

### `write.py` 退出码处理（智能体必选分支）

运行脚本后**须把终端里的具体报错原样摘要给用户**（或引用关键行），勿只说「调用失败」。

按**退出码与报错类型**分支处理：

| 类型 | 判断线索 | 智能体动作 |
|------|----------|------------|
| **未配置（退出码 2）** | stderr 含 `[NO_MODEL]` | **自动降级**：运行 `write.py prompt <mode> <input>` 获取提示词 JSON（`{"system_prompt": "...", "user_prompt": "..."}`）→ Agent 按该 `system_prompt` 和 `user_prompt` 写文章 → 输出到 `-o` 指定路径或展示给用户。**无须**用户确认或「本次例外」。 |
| **网络类（退出码 1）** | 超时、连接失败、`URLError`、`网络错误:`、临时性 502/503 等 | **必须自动再试 1 次**（可简短等待后重跑同一命令，并告知用户「正在重试」）。**第二次仍为网络类失败** → 改用 `write.py prompt` 获取提示词后由 Agent 按相同约束代写；**必须明确告知**：第三方 API 网络不可用，本次由对话模型代写。 |
| **配置/凭证类（退出码 1）** | 401/403、Key 无效、`未找到写作约束`、YAML 解析失败等 | **不要**为「省事」自动降级掩盖问题。**列出须检查项**（`config.yaml` 的 `writing_model`、`aws.env` 的 `WRITING_MODEL_API_KEY`、本篇目录是否有 `article.yaml` 等），请用户修正后重跑 `write.py`。若用户**明确打字**愿意本次改由 Agent 代写，再按 [main](../aws-wechat-article-main/SKILL.md)「本次例外」处理并留痕。 |
| **业务/内容类（退出码 1）** | 4xx 中除鉴权外（如 400 参数）、模型返回空等 | 将 API 返回体摘要给用户；可先根据提示改 `model` / 请求参数再试一次；仍失败则与用户商定是否 Agent 代写。 |

**Agent 代写时提示词获取**：无论哪种降级路径，Agent 代写前都应先运行 `write.py prompt <mode> <input>`（`--instruction` 按需传入），取回与 `write.py` 调第三方模型时**完全相同**的 `system_prompt` 和 `user_prompt`，确保写作约束一致。

**禁止**：配置明显错误时静默改用 Agent 写稿却不说明；网络降级后不告知用户「本次未走第三方模型」。

### 第6步：写作

写作时**必须遵循第3步读取的 `target_reader`、`tone`、`writing_style`**（来自合并后的约束）：深度与用词贴合读者，语气贴合调性，结构与表达方式贴合文章风格。

**用户供图分支（`image_source: user`）**：

- 用户图片须先放入本篇 `imgs/`；随后由智能体**读图分析**并生成或补全 `img_analysis.md`（可用 `user_image_prepare.py` 先生成模板再填写）。**未落盘 `img_analysis.md` 不得调用 `write.py`**，否则脚本会报错退出。
- `img_analysis.md` 是写稿时配图与章节顺序的**唯一依据**：`write.py` 会把它并入提示，按「建议章节 / 推荐用途」把每张图放到合理位置（可重排章节以匹配叙事）。
- `img_analysis.md` 中“推荐用途：封面”**必须且只能有 1 处**；否则不得写稿。
- 写稿时直接使用用户图片路径（`imgs/xxx.png`），不再输出 `placeholder`。
- `image_source` 只允许：`generated` / `user`。**禁止写** `user_provided`。
- 该字段由智能体按流程动态更新：默认 `generated`；进入用户供图替换流程时写为 `user`。

**状态切换规则（`article.yaml`）**：

- 新建文章默认：`image_source: generated`、`publish_completed: false`。
- 当进入“用户上传图片替换/重写”流程时：将 `image_source` 改为 `user`，并将 `publish_completed` 置回 `false`（表示需重新发布闭环）。
- 重新发布成功且有回执后：再写回 `publish_completed: true`。

**文章结构**：按优先级加载结构预设：

1. 用户指定（「用清单体结构」）
2. 本篇 `article.yaml` 的 `default_structure`（单元素列表）
3. `.aws-article/presets/structures/` 下的文件
4. 内置默认：[references/structure-template.md](references/structure-template.md)

**文末区块**：按优先级加载：

1. 本篇 `article.yaml` 的 `default_closing_block` 指定的文件（单元素列表）
2. 合并约束中 `closing_block` 非空字符串（若有）
3. **fallback**：内置默认文末（分割线 + 一句关注引导）：`---\n觉得有用？点个关注，持续获取优质内容。`

默认模式下，写作时在需要图的位置插入配图标记 `![类型名：画面内容](placeholder)`（规则见 `write.py` 系统提示与 `references/structure-template.md`「配图标记」）。

**调用第三方模型**时的脚本用法：[references/usage.md](references/usage.md)

### 第7步：自检与修正（仅粗扫，不替代 review）

仅做**粗扫**：禁用词、段落长度、开头吸睛度、小标题密度，发现明显问题自动修正。**不**替代 [review skill](../aws-wechat-article-review/SKILL.md) 的内容审 —— 完整的合规、敏感词、文末 embed、引用标注剥离均归 review 处理；本步禁止越界做 review 的工作。

**配图占位自检（默认模式）**：当 **`image_source != user`** 时，核对 `draft.md` 是否满足 **`image_density`**（未配置则按**每节一图**）；缺失或格式不合法时，先补齐/修正 `![类型名：画面内容](placeholder)` 再进入审稿或配图步骤。

**续写补充（中间产物门禁）**：

- 续写新增 `![...](placeholder)` 时，必须把该占位计入“待配图清单”（供 images 步骤生成与替换）。
- 进入发布相关步骤前，必须复核本篇正文产物：`article.md` / `article.html` 若仍含 `placeholder`，只能标记为“正文配图未完成”，禁止宣称发布闭环完成。

### 第8步：展示并等待用户确认 ⛔

向用户展示 `draft.md`，确认后**移交 [review skill](../aws-wechat-article-review/SKILL.md) 做内容审**。

**⛔ 产物边界（硬性）**：本 skill 产出**只到 `draft.md`**。**禁止**在 writing 阶段：
- 自行写入 `article.md`（`article.md` 是 review 第 5 步 ⛔ BLOCKING 的产物，须含文末 `{embed:…}` 且已剥离引用标注）
- 自行剥离 `（资料路径：...）` 引用标注（剥离动作由 review 调用 `write.py strip-citations` 完成）
- 跳过 review 直接进入 [formatting](../aws-wechat-article-formatting/SKILL.md)

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`、**`.aws-article/config.yaml`**、本篇 **`article.yaml`** | `draft.md`（含配图标记）；**本 skill 可能更新** **`publish_method`**（发出去 → **`published`**；不填微信 → **`none`**；默认 **`draft`**）；新建/补全 **`article.yaml`** 时保持 **`publish_completed: false`** |
