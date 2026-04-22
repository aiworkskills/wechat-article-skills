---
name: aws-wechat-article-review
description: 公众号审稿｜微信公众号审稿｜公众号校对｜敏感词检测｜错别字检测｜内容合规｜政治合规｜平台规范｜proofreading｜content review｜moderation — 公众号发布前合规审查：敏感词扫描、错别字检测、政治合规、平台规范校验，一次性输出修改清单。面向公众号编辑、自媒体作者、合规岗。触发词：「审稿」「审核」「检查一下」「校对」「合规」「敏感词」「错别字」「帮我看看」「写完了」「检查下有没有问题」「能不能发」。
---

# 审稿与合规

**公众号发布前合规守门员** —— 敏感词、错别字、平台规范一次性筛查，输出可执行修改清单。

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

「能不能发」若含代为发布或从稿到发出整条收尾 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

对文章做系统性检查，发现问题并引导修改。

## 两种审稿模式

| 模式 | 时机 | 检查重点 |
|------|------|---------|
| **内容审** | writing 之后、formatting 之前 | 内容质量、写作规范、敏感词、配图标记 |
| **终审** | publish 之前 | 排版完整性、图片就位、发布要素齐全 |

自动识别：有 `article.html` → 终审模式，否则 → 内容审模式。

## 工作流

```
审稿进度：
- [ ] 第1步：环境检查 + 本篇约束与规范
- [ ] 第2步：逐项检查
- [ ] 第3步：输出审稿结果
- [ ] 第4步：修改循环 🔄
- [ ] 第5步：确认通过 → **文末 embed（⛔ BLOCKING）** → 保存 `article.md` 定稿
```

### 智能体行为约束（与定稿强相关）

- **禁止**在未完成 **第5步「文末 embed」**（见下 **⛔ BLOCKING**）的情况下，将稿件称为「已定稿」、写入 **`article.md`**、或进入 **排版（`format.py`）**。
- **禁止**用「用户没提」「节省时间」等理由跳过文末占位符；**唯一例外**：用户**书面**声明本篇不要任何嵌入元素（名片/小程序/链接），则须在审稿记录中写明「用户声明跳过 embed」，且仍须确认不是误操作。
- **一条龙 / 完整流程**（[main SKILL](../aws-wechat-article-main/SKILL.md)）中，**内容审**产出的 **`article.md` 必须已含文末 embed**（按合并规则或合法省略），再进入排版。

### 第1步：环境检查 + 本篇约束与规范 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

从选题到发布的阻断规则见 [main SKILL](../aws-wechat-article-main/SKILL.md)；**单独启用本 skill** 时亦须先满足同一套环境检查（或用户按 main 约定声明「本次例外」）。

然后读取：

- **`.aws-article/writing-spec.md`**（如有）
- **`.aws-article/presets/review-rules.yaml`**（如有）
- **本篇合并配置**（与 [writing](../aws-wechat-article-writing/SKILL.md)、`format.py` 一致）：先 **`.aws-article/config.yaml`** 顶层（不含 `writing_model` / `image_model`），再叠 **本篇目录 `article.yaml`**（**同键本篇优先**；**仅** `embeds.related_articles` 与全局深度合并，其余 `embeds` 仍以全局为准）。审稿与内容向检查以合并结果为准（如 `review_output_format`、`custom_sensitive_words`、`forbidden_words`、`target_reader`、`tone`、`image_density` 等）。字段说明：[articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

**fallback**：合并后仍缺关键约束时向用户说明「部分维度无法按本篇约束对齐」，并建议补全 `config.yaml` / `article.yaml`；无写作规范时跳过规范检查项；无自定义审稿规则时仅执行内置检查清单 [references/checklist.md](references/checklist.md)。

### 第2步：逐项检查

按模式执行不同检查项，详见：[references/checklist.md](references/checklist.md)

**内容审** 检查 6 个维度：

| 维度 | 检查内容 |
|------|---------|
| **标题** | 长度、禁用套路、与正文一致性 |
| **摘要** | 长度、信息量、与正文一致性 |
| **正文** | 敏感词、禁用词、错别字、事实出处 |
| **写作规范** | 对照 writing-spec.md 检查用词、句式、段落、AI 味；深度与调性是否与 **本篇合并配置** 的 `target_reader`、`tone` 一致 |
| **配图标记** | 封面标记存在、数量与 **本篇合并配置** 的 `image_density` 匹配、描述清晰 |
| **文末 embed** | 定稿前须完成 **第5步 ⛔ BLOCKING**（与 `format.py` 的 `{embed:…}` 一致）；未写入 `article.md` 不得定稿 |
| **原创标注** | 按 original_attribution 处理 |

**终审** 额外检查：

| 维度 | 检查内容 |
|------|---------|
| 排版 | article.html 存在且完整 |
| 图片 | imgs/ 下图片齐全、placeholder 已替换 |
| 发布要素 | 标题/摘要/作者/封面 全部就绪 |

### 第3步：输出审稿结果

按 `review_output_format` 输出：
- **分块详细**：按维度分块，逐项列 ✅/❌ + 修改建议
- **简要清单**：表格式，一行一项

输出模板：[references/output-format.md](references/output-format.md)

结果分三级：
- 🔴 **必须修改**：不改不能过（敏感词、严重错别字、缺封面）
- 🟡 **建议修改**：改了更好（用词优化、段落调整）
- 🟢 **通过**：无问题

### 第4步：修改循环 🔄

有 🔴 项时**必须进入修改循环**：

```
发现问题 → 展示审稿结果 → 等用户/agent 修改 → 重新检查 → 直到无 🔴
```

修改方式：
- Agent 直接修改 `draft.md`
- 用户手动修改后说「改好了」
- 调用 writing skill 的 rewrite 能力

每轮修改后自动重审被标记为 🔴 的项，不需要全量重审。

> ⚠️ **Step 4 完成不代表可以保存 `article.md`**。必须先完成 Step 5（文末 embed ⛔⛔ BLOCKING）才能写入 `article.md` 或进入排版。

### 第5步：确认通过 → 文末 embed → 保存定稿 ⛔⛔ BLOCKING

全部 🔴 项消除后：
1. 展示最终审稿结果
2. 等待用户确认 ⛔
3. **⛔ BLOCKING · 文末 `embeds`**：**在写入 `article.md` 之前**完成本节下方「规则与表格」——**先读取** `.aws-article/config.yaml` 并与本篇 `article.yaml` **合并**（与第 1 步一致：**除 `embeds.related_articles` 外，`embeds` 仅以全局为准**；**`related_articles` 与全局深度合并**），再在**正文末尾**（原有正文之后）按规则**追加或合法省略**占位符。**占位符必须与合并后可解析的配置一致**，否则排版阶段会失败。**未完成本节不得保存定稿、不得调用 `format.py`。**
4. 将已含文末 embed（或已按规则省略并记录在审稿说明中）的稿件保存为 **`article.md`（定稿）**。

**定稿文末 `embeds`（规则与表格）**

| 占位符 | 何时写入文末 | 配置对齐 |
|--------|----------------|----------|
| `{embed:profile:…}` | 全局 **`embeds.profiles`** 存在**至少一条有效项**（非空 `nickname`） | 每条有效 profile **一行**，占位中 `…` = 该项 `nickname` |
| `{embed:miniprogram:…}` | 全局 **`embeds.miniprograms`** 存在**至少一条有效项**（非空 `title`） | 每条有效项一行，`…` = `title` |
| `{embed:miniprogram_card:…}` | 全局 **`embeds.miniprogram_cards`** 存在**至少一条有效项**（非空 `title`） | 每条有效项一行，`…` = `title` |
| `{embed:link:…}` | **往期链接**：合并后 **`embeds.related_articles.manual`** 有有效项时；或见下方「无 manual」 | `…` = 该项 `name`；**文末相关链接至多 3 条** |

- **前三类（名片 / 小程序文字链 / 小程序卡片）**：若对应列表**未配置或为空或无非空关键字段**，**不追加**该类占位符，无需处理。
- **往期 `{embed:link:…}`**：
  - 若合并后 **`manual` 已有** `name` + `url`：在文末追加对应占位符，**最多 3 条**（超过则只保留 3 条，优先与本文主题最相关的条目或按列表顺序取前 3）。
  - 若合并后 **`manual` 缺失或为空**：在**仓库根**执行  
    `python {baseDir}/../aws-wechat-article-publish/scripts/getdraft.py published-fields`  
    输出为 JSON 数组（每项含 `title`、`digest`、`url`）。结合**本文主题与摘要**，从已发布正式文章中**选取至多 3 篇**相关条目；将选中项写入**本篇** `article.yaml` 的 **`embeds.related_articles.manual`**（每项 `name`（与占位一致、简短可读）+ `url`），再在 `article.md` 文末追加 `{embed:link:name}`。**勿改**全局 `config.yaml` 仅为本篇补链接。若命令失败（无凭证、网络、接口错误）或用户书面声明跳过往期：**不伪造** `manual`，可省略该类占位并在审稿说明中注明原因。

字段含义与示例见 **`{baseDir}/../aws-wechat-article-main/references/config.example.yaml`** 的 `embeds` 注释及 **[topics SKILL](../aws-wechat-article-topics/SKILL.md)** 文末「推荐链接」说明；排版脚本据此生成 `article.html`。

**全空时的处理**：当所有 embed 配置（profiles / miniprograms / miniprogram_cards / related_articles）均为空或未配置时，仍须在审稿输出中**显式标注**「文末 embed：无配置，已跳过」，**不得静默跳过**。这确保流程可追溯，避免遗漏。

## 自定义检查规则

用户可在 `.aws-article/presets/review-rules.yaml` 添加自定义检查项：

```yaml
# .aws-article/presets/review-rules.yaml
custom_rules:
  - name: 品牌名称规范
    check: 正文中「XX公司」必须使用全称，不能简写
    level: 必须    # 必须 / 建议

  - name: 数据来源
    check: 所有引用的数据必须标注来源和日期
    level: 必须

  - name: CTA 检查
    check: 文末必须包含明确的行动号召
    level: 建议
```

自定义规则会追加到标准检查项之后执行。

## 过程文件

| 模式 | 读取 | 产出 |
|------|------|------|
| 内容审 | `draft.md`、**`.aws-article/config.yaml` + 本篇 `article.yaml`**、`writing-spec.md` | `review.md`、`article.md`（定稿） |
| 终审 | `article.html`、`imgs/`、同上合并配置、`article.yaml`（发布元数据等） | `review.md`（终审结果） |
