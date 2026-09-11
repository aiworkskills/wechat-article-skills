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

本 skill 调用 `write.py` 生成文章初稿，**会把文章内容发送给用户配置的 LLM 端点**：

- **凭证读取**：仓库根 `aws.env` 的 `WRITING_MODEL_API_KEY`
- **凭证外发**：该 key 以 `Authorization: Bearer <key>` 头**发送到** `config.yaml.writing_model.base_url` 配置的外部端点（DeepSeek / OpenAI / Anthropic 等 Chat Completions 兼容 API）。**请使用专用 key 并配置可信端点或内部代理**
- **内容外发**：Prompt 内含本篇 `article.yaml` / `topic-card.md` / 合并配置 / `--reference` 指定的参考文档全文 → 整体 POST 给上述端点
- **文件读（仓库内）**：`.aws-article/config.yaml`、本篇 `article.yaml`、`topic-card.md`、`.aws-article/products/{产品名}/*.md`
- **文件读（仓库外）**：仓库内 `.aws-article/` 缺失时从 `~/.aws-article/` 读 `writing-spec.md` 与 `presets/`（**只读预设，不读凭证**）
- **文件写**：仅本篇目录下 `draft.md`
- **shell**：仅 `{python} {baseDir}/scripts/write.py`

`write.py prompt` 子命令**只输出 prompt JSON 不调用 LLM**，由 Agent 代写 —— 不想把内容发给第三方时走这条。

## 路由

从零发文、一条龙、完整流程 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。本 skill 单独触发仅限**已有稿子的修改**（改写 / 润色 / 续写）。

## 配置检查 ⛔

任何操作前先按 **[首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)** 执行，通过后才继续（或用户明确书面确认「本次不检查」）。

**写作模型**：`writing_model`（`provider`、`base_url`、`model`）在 `.aws-article/config.yaml`；`WRITING_MODEL_API_KEY` 在仓库根 `aws.env`。键名对照 [env.example.yaml](../aws-wechat-article-main/references/env.example.yaml)。

环境检查未通过时，只按首次引导处理配置选项，**不要**在同一条回复里混入写稿、草稿路径或多草稿选择。须遵守 main 的**智能体行为约束**：未通过校验且未获用户明确「本次例外」时，不得默认改由当前 Agent 代写并假装流程完整。

## 工作流

```
写稿进度：
- [ ] 第0步：⛔ 首次引导 · 检测顺序
- [ ] 第1步：⛔ 全局账号三键非空
- [ ] 第2步：⛔ 续旧稿还是新稿（不了解时须先问）
- [ ] 第3步：读取本篇约束与写作规范
- [ ] 第4步：发布方式（publish_method）
- [ ] 第5步：确定输入与写作方式
- [ ] 第6步：写作
- [ ] 第7步：跑 check 自检
- [ ] 第8步：⛔ 展示并等待用户确认
```

### 第1步：全局账号三键 ⛔

打开 `.aws-article/config.yaml`，检查 `article_category`、`target_reader`、`default_author` 是否 **trim 后均非空**。任一项缺失：**逐项询问用户**，取得当轮明确答复后**写回该文件**。与 [main「2) 全局账号约束」](../aws-wechat-article-main/SKILL.md) 一致。

**须在续旧/新开询问之前完成。禁止**从 `article.yaml`、其它草稿或仓库文件静默推断并写盘；**禁止**只在对话里确认却不落盘。

### 第2步：续旧稿还是新稿 ⛔

**不清楚**用户要续写 `drafts/` 下某篇还是新开一篇时：**须先询问**（可列出候选目录），选定后再往下。用户已明确路径或意图（直接给出 `drafts/…`、或说「新开一篇」）时不再盘问。**禁止**未确认就调用写作脚本，也禁止自动选中某一 `drafts/…` 跑脚本。

**目录命名**：新开一篇必须为 `YYYYMMDD-标题slug`（如 `drafts/20260406-wechat-article-skills/`）。**禁止省略日期前缀**。

### 第3步：读取本篇约束

`write.py` 先读全局 `.aws-article/config.yaml`，再读本篇 `article.yaml`，把两边的键**叠成一张表**生成写作提示——**同一键两处都有时以本篇 `article.yaml` 为准**。字段分工见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

- **config.yaml**：文风、结构预设、禁用词、字数、`embeds` 等「写什么、怎么写」的顶层字段进入这张表。`writing_model` / `image_model` 两段只给脚本连 API 用，**不**整段放进写作说明。
- **article.yaml**：本篇标题、作者、摘要、`publish_completed` 等；重名键覆盖 config。`publish_completed` 新建时须为 `false`，由 [publish skill](../aws-wechat-article-publish/SKILL.md) 在发布结束后改为 `true`。

| 字段 | 用途 |
|------|------|
| `target_reader` | 读者画像 → 深度、用词、案例 |
| `tone` | 调性 → 语气与句式 |
| `writing_style` | 结构表达方式（口语/书面/故事/方法论等） |

**⛔ 关键字段不得空跑**：调用 `write.py`（或让 Agent 代写）前，确认合并后的 `article_category`、`target_reader` 非空，且 `default_author` 或本篇 `author` 非空。不满足则**暂停写稿**并实际写入文件——不要只用对话表格收集「读者」却不落盘。

**另加载** `.aws-article/writing-spec.md`（如有）。`default_structure` / `default_closing_block` 在本篇 `article.yaml` 中须为**单元素列表** `[名]` 或 `[]`；含多个候选、或需要了解预设加载优先级时，见 [branches.md「四、结构 / 文末预设的多候选处理」](references/branches.md)。

**业务资料库**：本篇涉及用户自身业务（对外介绍 / 教程 / 案例 / 自家安利）时，**必须**先 `ls .aws-article/products/` 并读相关产品根下的 `*.md`，已有同主题文档优先增量改写。两种写作方式各自怎么用（Agent 直写标路径 vs `write.py --reference`）、写后如何回写，见 [branches.md「三、业务资料库的两条用法」](references/branches.md)。与自身业务无关的主题不读、不强求。

### 第4步：发布意图

确认 `.aws-article/config.yaml` 的 `publish_method` 是 `draft`（默认）/ `published` / `none` 之一。**已是合法值时静默通过，不重复盘问**。三者含义与询问口径见 [branches.md「五、发布意图」](references/branches.md)。

### 第5步：确定输入与写作方式

**输入**：`topic-card.md` / 用户提供的提纲或素材 / 用户口述主题，且已按第 3 步完成业务资料库判断。

**写作方式（优先级）**：

1. **优先**：调用第三方模型 `write.py draft|rewrite|continue`（用法见 [usage.md](references/usage.md)）
2. **自动降级**：模型未配置（退出码 2）→ `write.py prompt <mode> <input>` 取提示词 JSON，Agent 按**相同提示词**写，**无须**「本次例外」
3. **故障降级**：调用失败（退出码 1）→ 见 [branches.md「一、退出码处理」](references/branches.md)

**必须告知用户当前用的是哪种**：

- `ℹ️ 使用 write.py 调用第三方模型（{model}）`
- `ℹ️ 写作模型未配置，本次由当前对话模型直接写稿（使用相同写作约束）`
- `ℹ️ 第三方 API 不可用，本次由当前对话模型代写（使用相同写作约束）` + 原因

### 第6步：写作

写作必须遵循第 3 步读到的 `target_reader`、`tone`、`writing_style`：深度与用词贴合读者，语气贴合调性，结构贴合文章风格。

`image_source: user`（用户供图）时不输出 `placeholder`，改用真实路径——细则见 [branches.md「二、用户供图分支」](references/branches.md)。

#### Markdown 语法（硬性）

链路是「**markdown 语法 → 按语法输出 → 渲染器排版**」。写错的标记不会报错——渲染照常完成，**读者会在正文里直接看见 `__加粗__`、`###### 六级`、`[^1]` 这类符号**。

| 要表达的 | 写法 | 说明 |
|---|---|---|
| 小标题 | `## 二级` `### 三级` | 井号后必须有空格。**不写 `# 一级`**——文章标题由公众号后台单独填 |
| 加粗 | `**加粗**` | 正文最主要的强调手段，规则见下 |
| 斜体 | `*斜体*` | 中文里慎用，斜体的中文字形不好看 |
| 链接 | `[文字](https://…)` | 必须有可点的锚文本 |
| 配图 | `![类型名：画面内容](路径 "图注")` | 图注写在引号里；不写引号就没有图注 |
| 无序列表 | `- 一项` | 减号后必须有空格 |
| 有序列表 | `1. 一项` | 只在**真有先后**时用；并列的几项用 `-` |
| 待办清单 | `- [ ]` `- [x]` | **少用**——只有真正的检查项才用 |
| 引用 | `> 引文` | 每行都要有 `>` |
| 表格 | `\| a \| b \|` + `\|---\|---\|` | 分隔行不能省 |
| 代码 | 行内 `` `x` ``；成块用三反引号围栏 | **不要**用四空格缩进 |
| 分隔 | `---` 独占一行 | 上下各留一个空行 |

**禁止**：输出 HTML 标签（`<br>` `<div>`）；`:::` 之类自定义块语法；四空格缩进代码块；Setext 式标题（`====` / `----`）；裸 URL 当正文。

#### 产出配额（不是可选项）

语法规则模型都照做，但没有配额就一处都不产出。真稿实测：金句卡 0/10 篇，正文段落内的加粗 0/5 篇——加粗全在列表标签里，读者在手机上一屏扫过去没有任何落点。以下与 `write.py` 系统提示中的配额区**逐条对应**，改一处须同改两处。

- **摘要** —— 第一个 `##` 之前写一段 `>` 引用，80–128 字，**且与 `article.yaml` 的摘要字段不是同一句话**（实测 7 篇逐字相同，读者同一段读两遍）。
- **加粗 = 划重点** —— 读者没时间读完两千字，加粗要让他只看这些就知道你说了什么。
  **验收标准：把全文的加粗按顺序抽出来连读，应该是一篇能独立看懂的缩写版。** 读起来像词云（「透明度 / 瓶颈 / 采用」）或像把段落重念一遍，都是挑错了。
  据此倒推：每个 `##` 小节至少贡献一处，正文每 2–3 段一处、一段最多两处；每处都要**能独立看懂**——数字连着它的意思（`**省 88% Token**`），判断连着它的对象（`**打断不等于撤销**`），术语连着它的定性（`**按问题找证据**`）。关键数字尽量覆盖到。**不要**加粗整句的概括，**不要**每段都加在首句同一位置。
- **三项以上的并列** —— 写成 `- **标签**：说明` 列表，不要压进一个长段落。即使段落偏好要求「完整自然段」，那管的是叙述段，枚举仍然用列表。
- **金句恰好一处** —— 最值得截图转发的那一句写成 `> 金句。 —— 出处`，排版会排成金句卡。写两处以上卡片就退化成装饰条；不写出处就是普通引用。
- **`---`** —— 需要一个明显转场时用，独占一行、上下各留空行。排版会换成本模版的分隔装饰。
- **段距** —— 段与段之间空**一行**。空两行或用两个空格换行都不需要，段距由版式控制。

#### 配图占位

`image_source` 不为 `user` 时，按 `image_density` 生成占位，格式 `![类型名：画面内容](placeholder)`，每个占位**独占一行**，**封面占位放在标题之前**。类型名与细则见 [structure-template.md](references/structure-template.md)「配图标记」。

密度词是本套件自造的，不能只把词丢给模型让它猜（实测五篇真稿，标记数每篇都少于 `##` 小节数）：

| `image_density` | 就是说 |
|---|---|
| 每节一图 | 每个 `##` 小节各配一张，不多不少 |
| 按需配图 | 只在文字讲不清的地方配（流程、对比、数据），其余不配 |
| 少图 | 全篇只配 1–2 张最关键的 |
| 多图 | 每 2–3 个自然段配一张 |

**这是硬配额不是参考值**，写完自己数一遍。同一张表在 `write.py` 的 `_DENSITY_RULES` 与 [image-method.md](../aws-wechat-article-images/references/image-method.md) 里各有一份，措辞须一致。未配置时默认**每节一图**。

### 第7步：跑 check 自检 ⛔

`draft.md` 写完后**跑一遍脚本**，不合格先补再往下走。这些实测最容易漏，而且漏了不报错、只是版式悄悄少一块：

```bash
{python} {baseDir}/scripts/write.py check drafts/YYYYMMDD-slug/draft.md
```

它按上面的产出配额逐条量，并把**全文的加粗抽出来串成一行**打印——验收标准就是**这一串读起来像不像一份提要**，串不起来说明挑错了，不是数量不够。退出码非 0 表示有硬性项没达标。脚本只量数得出来的部分，**加粗挑得对不对仍要自己读一遍那一串**。

脚本管不到的两项，手工核对：

- **配图占位数**与 `image_density` 是否一致，格式是否合法；
- 禁用词、段落长度、开头吸睛度、小标题密度的**粗扫**。

⛔ 这一步**不**替代 [review skill](../aws-wechat-article-review/SKILL.md)：合规、敏感词、文末 embed、引用标注剥离都归 review，本步禁止越界。

续写时的中间产物门禁见 [branches.md「七」](references/branches.md)。

### 第8步：展示并等待用户确认 ⛔

向用户展示 `draft.md`，确认后**移交 [review skill](../aws-wechat-article-review/SKILL.md) 做内容审**。

**⛔ 产物边界**：本 skill 产出**只到 `draft.md`**。禁止在 writing 阶段：

- 自行写入 `article.md`（那是 review 第 5 步的 BLOCKING 产物，须含文末 `{embed:…}` 且已剥离引用标注）
- 自行剥离 `（资料路径：…）` 引用标注（由 review 调 `write.py strip-citations` 完成）
- 跳过 review 直接进入 [formatting](../aws-wechat-article-formatting/SKILL.md)

## 分支与异常

退出码四分类、用户供图、业务资料库细则、预设多候选、发布意图口径、确认轮次优化、续写门禁 → [references/branches.md](references/branches.md)。

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`、`.aws-article/config.yaml`、本篇 `article.yaml` | `draft.md`（含配图标记）；可能更新 `publish_method`；新建/补全 `article.yaml` 时保持 `publish_completed: false` |
