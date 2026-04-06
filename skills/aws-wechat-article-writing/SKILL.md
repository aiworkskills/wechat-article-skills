---
name: aws-wechat-article-writing
description: 写公众号文章或改写已有内容，可调用第三方模型生成初稿。当用户提到「写文章」「写正文」「写稿」「出稿」「改写」「润色」「续写」「写个初稿」「帮我写」「公众号风格」「把提纲写成文章」「开头结尾」「用 DeepSeek 写」「用 GPT 写」时使用。注意：需要用户明确知道写什么的时候才能直接使用，否则先通过aws-wechat-article-topics获取文章的基本信息。
---

# 长文写作

## 路由

从零发文、一条龙、完整流程 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

从选题到发布的**前置规则**（阻断、禁止擅自降级、「本次例外」等）见 [aws-wechat-article-main/SKILL.md](../aws-wechat-article-main/SKILL.md)；本 skill 只描述写稿步骤。

**写作模型**：**`writing_model`**（`provider`、`base_url`、`model` 等）在 **`.aws-article/config.yaml`**；**`WRITING_MODEL_API_KEY`** 在仓库根 **`aws.env`**。键名对照 **`skills/aws-wechat-article-main/references/env.example.yaml`**。

**交互约定**：须遵守 main 的**智能体行为约束**——**未**通过环境校验且**未**获用户明确「本次例外」时，不得默认改由当前 Agent 代写并假装流程完整。**环境检查未通过时**，只按 [首次引导](../aws-wechat-article-main/references/first-time-setup.md) 处理配置选项，**不要**在同一条回复里混入写稿、草稿路径或多草稿选择；配置闭环后再进入本 skill 工作流。

## 工作流

```
写稿进度：
- [ ] 第0步：⛔ [首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)
- [ ] 第1步：⛔ **`.aws-article/config.yaml`** 中 **`article_category`**、**`target_reader`**、**`default_author`**（trim 后）须**均非空**；缺则**逐项问用户**、用户确认后再**写回文件**；**禁止**从 **`article.yaml`** 等擅自抄录（与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致）；**须先于**续旧/新开
- [ ] 第2步：⛔ **在不了解**用户要**续写既有草稿**还是**新开一篇**时，**须先询问**并确定本篇 `drafts/…` 目录，**再**进入以下步骤；**禁止**未确认就调用写作脚本（见 [main](../aws-wechat-article-main/SKILL.md)「3) 本篇准备」开头）
- [ ] 第3步：读取本篇约束与写作规范
- [ ] 第4步：发布方式（`publish_method`）⛔
- [ ] 第5步：确定输入与写作方式
- [ ] 第6步：写作
- [ ] 第7步：自检与修正
- [ ] 第8步：展示并等待用户确认 ⛔
```

**说明**：第 2 步在用户**已明确**路径或意图（例如直接给出 `drafts/…`、或明确说「新开一篇」）时可**不再重复盘问**。

**多草稿 / 未闭环**：与第 2 步同原则——**不了解**续写/新开时**须先问**，**禁止**自动选中某一 `drafts/…` 跑写作脚本。

### 第1步：全局账号三键（`.aws-article/config.yaml`）⛔

**在续旧/新开询问之前**，打开 **`.aws-article/config.yaml`**，检查 **`article_category`**、**`target_reader`**、**`default_author`** 是否 **trim 后均非空**。任一项缺失：**逐项询问用户**，取得**用户当轮明确答复**后再**写回该文件**，再进入第 2 步。**禁止**从 **`article.yaml`**、其它草稿或仓库文件**静默推断并写盘**；可把从某文件读到的内容**仅作建议展示**，须用户同意后再写入。**禁止**跳过本步。**禁止**仅在对话里确认却不落盘。与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致。

### 第2步：续旧稿还是新稿（不了解时须先问）⛔

**当不清楚**用户是要**续写 `drafts/` 下某篇进行中草稿**还是**新开一篇**时：**须先询问**（可列出候选目录），待用户选定后再进入第 3 步。**须在第 1 步全局三键已落盘之后执行**。**已明确**时跳过本步询问。

### 第3步：读取本篇约束与写作规范

**⛔ 关键字段不得空跑**：在调用 **`write.py`** 或按合并约束让 Agent 代写之前，确认合并后的 **`article_category`**、**`target_reader`** **均为非空字符串**（trim 后）；**`default_author`** 非空 **或** 本篇 **`article.yaml` 的 `author`** 非空。若任一项不满足，**须暂停写稿**，引导用户补全 **`.aws-article/config.yaml`**（及/或本篇 **`article.yaml`**），**并实际写入文件**——**不要**仅用对话表格收集「读者」却不落盘。全局三键的优先检查顺序见 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」；若第 1 步已正确落盘，此处多为合并 **`article.yaml` 覆盖**后的复核。

**约束从哪来**：`write.py` 会先读全局 **`.aws-article/config.yaml`**，再读本篇目录下的 **`article.yaml`**，把两边的键**叠成一张表**用来生成写作提示——**若同一键在两份文件里都有，以本篇 `article.yaml` 为准**。字段分工见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

1. **`.aws-article/config.yaml`**：**文风、结构预设、禁用词、字数、`embeds` 等**与「写什么、怎么写」有关的顶层字段会进入这张表。  
   **`writing_model` / `image_model`** 两段只给脚本**连 API 用**（地址、模型名等），**不**整段放进给大模型的「写作说明」里，以免把技术配置当成正文要求。
2. 本篇 **`article.yaml`**：本篇标题、作者、摘要、**`publish_completed`** 等；与 config **重名的键**会**覆盖** config。

**`write.py`** 在仓库根执行，按**输入 `.md` 所在目录**找到本篇 **`article.yaml`**；叠完后的约束表不能为空（一般只要 **`config.yaml`** 里已有账号/文风等即可）。**`publish_completed`**：新建或补全本篇 **`article.yaml`** 时须为 **`false`**；本篇发布真正结束后由 [publish skill](../aws-wechat-article-publish/SKILL.md) 改为 **`true`**；**`publish.py` 不修改此字段**。

`default_structure` / `default_closing_block` 指向的 **预设正文**仍来自 **`.aws-article/presets/`**（及用户目录下同名 presets），与配置中的**文件主名**对应。二者**须为 YAML 列表**：`[]`、`[名]`，或多项候选；**多项时**须先在本篇 **`article.yaml`** 同键改为**单元素列表**再调用 **`write.py`**（勿用字符串标量）。

另加载 **`.aws-article/writing-spec.md`**（如有）。

| 字段 | 用途 |
|------|------|
| `target_reader` | 读者画像 → 深度、用词、案例 |
| `tone` | 调性 → 语气与句式 |
| `writing_style` | 结构表达方式（口语/书面/故事/方法论等） |

配置中其它与写稿相关的键（如 `topic_direction`、`forbidden_words`、`heading_density`、`target_word_count`）一并写入约束。

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

**输入**：`topic-card.md` / 用户提供的提纲或素材 / 用户口述主题

- 专业场景参考：`.aws-article/assets/stock/references/`（本地参考文档目录，按照命名放行业案例与术语资料，可供写文章参考）**你可以读取文件夹内容自行选择是否使用**（如果需要使用，需严格匹配文章后使用）

**写作方式（优先级）**：

1. **优先：调用第三方模型**（`write.py`）— 依赖 **`config.yaml` 的 `writing_model` + `aws.env` 的 `WRITING_MODEL_API_KEY`**（见 [usage.md](references/usage.md)）
2. **降级：当前 Agent 直接写** — 见下 **「`write.py` 调用失败时」**（网络重试后仍失败）、或用户按 main 约定明确接受「本次例外」、或当前场景不适用脚本时

**必须告知用户当前使用的方式**：

- 已配置且调用脚本 → `ℹ️ 使用 write.py 调用第三方模型（{model}）`
- Agent 直写 → `ℹ️ 本次由当前对话模型直接写稿（未走 write.py）`，并说明原因（网络降级 / 用户确认例外 / 等）

### `write.py` 调用失败时（智能体必选分支）

运行脚本后**须把终端里的具体报错原样摘要给用户**（或引用关键行），勿只说「调用失败」。

按报错**类型**分支处理（结合 stderr 中的 `❌`、`API 调用失败`、`网络错误`、HTTP 状态码等判断）：

| 类型 | 判断线索 | 智能体动作 |
|------|----------|------------|
| **网络类** | 超时、连接失败、`URLError`、`网络错误:`、临时性 502/503 等 | **必须自动再试 1 次**（可简短等待后重跑同一命令，并告知用户「正在重试」）。**第二次仍为网络类失败** → 可**降级为当前智能体**按本篇合并约束与 `topic-card.md` 直接写稿；**必须明确告知**：第三方 API 网络不可用，本次由对话模型代写。 |
| **配置/凭证类** | 401/403、Key 无效、写作模型配置不完整、`未找到写作约束`、YAML 解析失败等 | **不要**为「省事」自动降级掩盖问题。**列出须检查项**（`config.yaml` 的 `writing_model`、`aws.env` 的 `WRITING_MODEL_API_KEY`、本篇目录是否有 `article.yaml` 等），请用户修正后重跑 `write.py`。若用户**明确打字**愿意本次改由 Agent 代写，再按 [main](../aws-wechat-article-main/SKILL.md)「本次例外」处理并留痕。 |
| **业务/内容类** | 4xx 中除鉴权外（如 400 参数）、模型返回空等 | 将 API 返回体摘要给用户；可先根据提示改 `model` / 请求参数再试一次；仍失败则与用户商定是否 Agent 代写。 |

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
2. 合并约束中的 `default_structure`（若有；多候选列表须已在本篇 **`article.yaml`** 收敛为单项，见 schema）
3. `.aws-article/presets/structures/` 下的文件
4. 内置默认：[references/structure-template.md](references/structure-template.md)

**文末区块**：按优先级加载：

1. 合并约束中 `closing_block` 非空字符串（若有）
2. `.aws-article/presets/closing-blocks/` 下 `default_closing_block` 指定的文件
3. **fallback**：内置默认文末（分割线 + 一句关注引导）：`---\n觉得有用？点个关注，持续获取优质内容。`

默认模式下，写作时在需要图的位置插入配图标记 `![类型名：画面内容](placeholder)`（规则见 `write.py` 系统提示与 `references/structure-template.md`「配图标记」）。

**调用第三方模型**时的脚本用法：[references/usage.md](references/usage.md)

### 第7步：自检与修正

按写作规范做一轮自检（禁用词、段落长度、开头吸睛度、小标题密度），发现问题自动修正。

**续写补充（中间产物门禁）**：

- 续写新增 `![...](placeholder)` 时，必须把该占位计入“待配图清单”（供 images 步骤生成与替换）。
- 进入发布相关步骤前，必须复核本篇正文产物：`article.md` / `article.html` 若仍含 `placeholder`，只能标记为“正文配图未完成”，禁止宣称发布闭环完成。

### 第8步：展示并等待用户确认 ⛔

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`、**`.aws-article/config.yaml`**、本篇 **`article.yaml`** | `draft.md`（含配图标记）；**本 skill 可能更新** **`publish_method`**（发出去 → **`published`**；不填微信 → **`none`**；默认 **`draft`**）；新建/补全 **`article.yaml`** 时保持 **`publish_completed: false`** |
