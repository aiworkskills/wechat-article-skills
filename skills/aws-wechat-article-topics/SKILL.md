---
name: aws-wechat-article-topics
description: 为公众号找选题、起标题、写摘要，支持热点调研和系列策划。当用户提到「选题」「起标题」「取个标题」「写摘要」「排期」「爆款」「热点」「写什么好」「发什么」「本周选题」「内容日历」「系列」「专栏」「连载」「找个话题」「有什么好写的」时使用。
---

# 选题与标题

## 路由

要成文并发到公众号、或「今天发什么」需整条编排时 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

通过调研生成高质量选题，支持单篇和系列。

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

## 四种输入模式

根据用户输入自动识别模式：

| 模式 | 触发条件 | 示例 |
|------|---------|------|
| **A. 明确选题** | 用户给了具体话题 | 「写一篇 AI Agent 的文章」 |
| **B. 有方向** | 给了领域但没具体题目 | 「AI 最近有什么好写的」 |
| **C. 无方向** | 只说要选题 | 「这周写什么」「帮我找几个选题」 |
| **D. 系列策划** | 提到系列/专栏/连载 | 「做个 AI 入门系列」「写 10 篇专栏」 |

## 工作流

```
选题进度：
- [ ] 第1步：配置检查（见本节「配置检查」）
- [ ] 第2步：全局账号三键（`.aws-article/config.yaml` 的 `article_category` / `target_reader` / `default_author`）⛔ 与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致；缺则**问用户确认后**再写入，**禁止**从 `article.yaml` 擅自填充，**先于**方向确认与调研
- [ ] 第3步：确认是否已有选题或写作方向 ⛔
- [ ] 第4步：调研
- [ ] 第5步：生成选题
- [ ] 第6步：生成标题与大纲
- [ ] 第7步：展示并等待用户选择 ⛔
- [ ] 第8步：输出选题卡片（新建本篇目录时须具备或更新本篇 article.yaml）
```

## 配置与本篇文件（`config.yaml` + `article.yaml`）

- **全局**：**`.aws-article/config.yaml`** 含账号定位、`topic_direction`、`update_frequency`、`title_style`、文风等（模板 **`{baseDir}/../aws-wechat-article-main/references/config.example.yaml`**，字段见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)）。**本 skill 做选题前须能读到该文件**（或用户当次已等价说明）。
- **本篇**：**`{drafts_root}/YYYYMMDD-标题slug/article.yaml`** 含标题、作者、摘要、**`publish_completed`** 等（见 schema；可用 **`{baseDir}/../aws-wechat-article-publish/scripts/article_init.py`** 初始化/更新）。
- **总览一条龙**：[main](../aws-wechat-article-main/SKILL.md) 在「3) 本篇准备」中建目录并优先落 **`article.yaml`**，再进入选题；若目录已存在且含 **`article.yaml`**，**须先读**（与 **`config.yaml`** 一起）再产出 `topic-card.md` / `research.md`。
- **单独使用本 skill**：第 8 步若**新建**本篇目录，须在**同目录**创建或更新 **`article.yaml`**（至少 **`publish_completed: false`**，并尽量写入已定标题/摘要等），**不得**仅有 `topic-card.md` 就引导调用 **`write.py`** 却无任何本篇 YAML——**`write.py`** 依赖仓库 **`config.yaml`** 与本篇目录；本篇 **`article.yaml`** 可缺但推荐补齐以便元数据一致（见 [writing SKILL](../aws-wechat-article-writing/SKILL.md)）。

### 第1步：环境检查 ⛔

同本节 **「配置检查」**。

### 第2步：全局账号约束（`.aws-article/config.yaml`）⛔

**在调用 `web_search`、调研或与用户确认选题方向之前**（环境校验已通过的前提下），打开 **`.aws-article/config.yaml`**，检查 **`article_category`**、**`target_reader`**、**`default_author`** 是否 **trim 后均非空**。任一项缺失：**逐项询问用户**，用户确认后再**写回该文件**；**禁止**从 **`article.yaml`** 等擅自抄录填充。与 [main](../aws-wechat-article-main/SKILL.md)「2) 全局账号约束」一致；**一条龙**下若 main 已在本轮完成本步，可**不再重复**。

### 第3步：确认是否已有选题或写作方向 ⛔

**在调用 `web_search` / 调研之前**，先与用户对齐当前处于哪种情况（对应上文 **A/B/C/D**）：

- **先问清**（可一句话）：是否**已经有**想写的具体主题、还是**只有**大致领域、**完全没想法**要帮找选题、或要做**系列/专栏**。
- 若用户**本条消息里已经说清楚**（例如直接给出话题或明确「这周帮我找几个选题」），可做**简短确认**，不必重复盘问。
- **总览一条龙** 且 main 已在「3) 本篇准备」中问清写作意图：本步**口头确认一句**即可，再进入第 4 步。

**禁止**：在用户仍处于「只说找选题、没说领域/偏好」等模糊状态时，**直接开始联网调研**。

确认后 → 归入 **A/B/C/D**，再进入 **第 4 步：调研**。

### 第4步：调研

**须先读** **`.aws-article/config.yaml`**：选题边界、`topic_direction`、`update_frequency`、账号定位等以其为准。若本篇目录已存在 **`article.yaml`**（例如已定题），可一并读取已有 **`title` / `digest`** 等，避免与后序冲突。尚无本篇文件时，以用户当次说明与 skill 默认为准。

- 专业场景参考：`.aws-article/assets/stock/references/`（本地参考文档目录，含产品介绍、行业案例与术语资料，可供选题参考）**你可以读取文件夹内容自行选择是否使用**（如果需要使用，需严格匹配选题方向后使用）

使用 `web_search` 搜索 + `web_fetch` 深入阅读，为选题提供数据支撑。

| 模式 | 调研目标 |
|------|----------|
| A | 竞品文章怎么写、数据支撑、独特角度 |
| B | 该方向近期热点、读者关注什么 |
| C | **`config.yaml`** 中的账号定位、`topic_direction` 与近期热点 |
| D | 知识体系拆解、竞品系列分析、读者学习路径 |

各模式的搜索策略和搜索词模板：[references/research-strategy.md](references/research-strategy.md)

### 第5步：生成选题

基于调研结果。用 **`config.yaml` 的 `update_frequency`** 控制本批数量：周更约 3–5 个，日更可略多，月更可略少；无配置时按对话约定或 skill 默认。

| 模式 | 生成规则 |
|------|----------|
| A | 围绕用户主题，提供 3-4 个不同切入角度 |
| B/C | 筛选 3-5 个选题，标注类型（🔥热点 / 🌲常青 / 📚系列） |
| D | 规划系列总线 + 拆出每篇选题 |

### 第6步：生成标题与大纲

为每个选题生成完整的「选题卡片」：标题候选（3-5 个，混合风格）、切入角度、大纲预览、工作量评估、摘要候选。

**标题风格**：按优先级加载：
1. 用户指定（「用反问型」）
2. **`config.yaml`** 的 **`title_style`** / **`custom_title_style`** > **`default_title_style`**（若有；**须为 YAML 列表**；多候选时须按选题择一并写回本篇 **`article.yaml`** 同键为**单元素列表**；`custom_*` 非空时优先于 `default_*`）
3. `.aws-article/presets/title-styles/` 下的自定义风格
4. **fallback**：内置 5 种风格（悬念/干货/数字/反问/故事）混合生成，详见 [references/title-presets.md](references/title-presets.md)

输出模板：[references/output-format.md](references/output-format.md)

### 第7步：展示并等待用户选择 ⛔

**⚠️ 必须停下来等用户操作，不要自作主张继续。**

展示所有选题卡片后，提示用户：

```
请选择：
- 输入编号（如 1）→ 选定该选题
- 「调整 + 意见」→ 按意见修改后重新展示
- 「重新选」→ 换一批选题
- 「组合 1+3」→ 融合多个选题
- 系列模式：「先写第 N 篇」→ 按该篇进入写稿
```

**禁止的行为**：
- ❌ 不等用户选择就继续写稿
- ❌ 假设用户会选某个选题
- ❌ 跳过展示直接进入下一步

### 第8步：输出选题卡片

用户确认后：

1. **文章目录**：若 **main** 已创建本篇目录且内含 **`article.yaml`**，**不要改目录名**，直接在该目录写入；否则创建 `{drafts_root}/{YYYYMMDD}-{标题slug}/`（**`drafts_root`** / **`series_root`** 以 **`config.yaml`** 为准，无则与 [main SKILL](../aws-wechat-article-main/SKILL.md) 及仓库惯例一致）。
2. 将选题卡片保存为 **`topic-card.md`**
3. 将调研摘要保存为 **`research.md`**
4. 系列模式：将系列规划保存到 `{series_root}/{系列slug}/plan.md`
5. **`article.yaml`**：同目录**若无**或需更新已定题信息，**须在本步创建或补全**（**`publish_completed: false`**；标题、摘要等与用户选定一致时可写入）。推荐：`python {baseDir}/../aws-wechat-article-publish/scripts/article_init.py <本篇目录> --title "…" --digest "…"` 等。**总览一条龙**下 main 若已初始化，则**合并更新**缺失键即可。

→ 交给 **aws-wechat-article-writing**。须已具备 **`.aws-article/config.yaml`**（仓库根相对路径）；本篇目录建议已有 **`article.yaml`**（见 [writing SKILL](../aws-wechat-article-writing/SKILL.md)）。

## 过程文件

| 文件 | 说明 |
|------|------|
| **`.aws-article/config.yaml`** | 全局账号与选题/文风约束；选题全程以之为准 |
| **`article.yaml`** | 本篇元数据与 **`publish_completed`**；新建本篇须 **`false`**；单独 topics 须在目录内创建或更新 |
| **`topic-card.md`** | 选题卡片（标题、摘要、角度、大纲） |
| **`research.md`** | 调研摘要（搜索发现、竞品分析、数据点） |

## `article.yaml` 与文末推荐链接（智能体）

全局 **`.aws-article/config.yaml` 一般不修改**；`embeds.related_articles` 若在全局已配置 `manual`，各篇可用同一套 `{embed:link:名称}`。若全局未配或希望**每篇不同推荐**：

1. **本篇** `article.yaml` 中只增加 **`embeds.related_articles.manual`**（`name` + `url` 列表）；**不要**在本篇写名片/小程序（仍以全局为准）。
2. 排版时 **`format.py` 仅将本篇的 `embeds.related_articles` 与全局同名块深度合并**。
3. **智能体自动获取推荐**（全局 `manual` 为空或本篇需要单独列表时）：运行  
   `python {baseDir}/../aws-wechat-article-publish/scripts/getdraft.py published-fields`
   得到已发布正式文章的 `title` / `digest` / `url`，结合当前篇主题**挑选最多 3 条**，写入**本篇** `article.yaml` 的 `embeds.related_articles.manual`，并在 **`article.md`** 文末使用 `{embed:link:名称}`，`name` 与 `manual` 中一致。
4. 定稿前确认文末 `{embed:link:…}` 与合并后的 **`related_articles`** 一致（参见 [review SKILL](../aws-wechat-article-review/SKILL.md) 定稿说明）。
