---
name: aws-wechat-article-main
description: 公众号运营｜微信公众号｜公众号一条龙｜公众号全流程｜自媒体运营｜wechat automation｜content pipeline｜AIGC workflow — 公众号一条龙运营总控入口，选题→写稿→审稿→排版→配图→发布串联 8 个子 skill，单条指令完成整篇图文从 0 到上架。面向公众号小编、自媒体、品牌内容。触发词分层：**一条龙流程**「一条龙」「完整流程」「从头做」「从 0 到发布」；**新做新发**「帮我写篇公众号文章」「做一篇公众号文章」「我想发一篇」「帮我发一篇」「再来一篇」；**选题起点**「今天写什么好」「有什么好写的」「找个话题」「爆款选题」「热点选题」「起个爆款标题」；**策划起点**「内容日历」「系列策划」「专栏规划」「连载」；**流程恢复**「接着上次那篇」「继续昨天的」「继续上次的」「接着之前的进度」；**显式模型新写**「用 GPT 写一篇」「用 DeepSeek 写一篇」「把提纲写成文章」。子 skill（topics/writing/review/formatting/images/publish/sticker/assets）单独触发仅限对**已有产物**的修改场景（如"改标题""润色这段""排版""审稿""加封面""发布"）；新做/策划/多环节串联一律走本入口。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env:
        - WRITING_MODEL_API_KEY
        - IMAGE_MODEL_API_KEY
        - WECHAT_1_APPID
        - WECHAT_1_APPSECRET
      bins:
        - python3
    primaryEnv: aws.env
---

# 公众号运营总览

**一键式公众号 AI 内容流水线** —— 从选题到上架 8 个子 skill 串联。

> **套件说明** · `aws-wechat-article-*` 共 9 个 slug：`main / topics / writing / review / formatting / images / publish / assets`，外加 `aws-wechat-sticker`。跨 skill 的相对引用依赖同一 `skills/` 根目录；推荐 `clawhub sync` 一次性全装。源码：<https://github.com/aiworkskills/wechat-article-skills>

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

## 能力披露（Capabilities）

本 skill 是**编排入口**，真正调用外部 API 的是子 skill（writing / images / publish / sticker / review）。本入口自身只跑 `validate_env.py`：

- **凭证**：读 `aws.env` 的各 `*_API_KEY` 与 `WECHAT_{N}_*`，**仅校验键存在且非空**，值不用于任何网络请求
- **网络**：本入口无外发；**子 skill 有外发**，见各自的能力披露
- **文件读写**：`.aws-article/`、本篇 `article.yaml`
- **shell**：仅 `{python} {baseDir}/scripts/validate_env.py`

> 整体套件会调用外部 LLM、图像与微信 API，并在调用时外发 API key 与本篇内容。

只装 main 一个时仍可做环境校验；进入流水线会因子 skill 缺失而 `file not found`。

## 配置检查 ⛔ BLOCKING

**进入「全局账号约束」「本篇准备」及内容流水线之前**，必须按 **[首次引导](references/first-time-setup.md)** 完整走一遍「检测顺序」——判断 OS、探测 `{python}`、检查两份配置文件、跑 `validate_env.py`、创建预设目录。任一步失败**不得继续**。

那份文档同时是**唯一**的失败引导来源与行为约束（禁止自作主张、不得索取密钥）出处，本文件不再复述。

三个要点在这里说一次：

- **`publish_method` 默认 `draft`**（`publish.py full` 只写公众号草稿箱）。用户明确要求「发出去」才改 `published`，或临时用 `full --publish`。
- **用户明确不接微信** → 先设 `publish_method: none` 再过校验，之后 `full` 会直接跳过。
- **写作 / 图片模型是可选项**，缺失时只警告、不阻断。

## 主要配置文件（不要混用）

| 文件 | 位置 | 作用 |
|------|------|------|
| `aws.env` | **仓库根** | **只放密钥**：`*_API_KEY`、`WECHAT_N_APPID` / `WECHAT_N_APPSECRET`（键名见 `references/env.example.yaml`） |
| `.aws-article/config.yaml` | 仓库内 | **账号级非密钥配置**：文风、选题边界、模型端点、微信槽位与 `publish_method`（模板见 `references/config.example.yaml`） |
| `article.yaml` | **本篇目录** | **本篇发文元数据**与状态：`image_source`（`generated` / `user`）、`publish_completed`（新建 `false`，发布闭环后 `true`） |

字段说明见 [articlescreening-schema.md](references/articlescreening-schema.md)。

## 交互顺序

**上一步完成再进下一步。** 每步若缺必要输入（目录、元数据、主题、用户选择、发布意图），先问用户并取得确认；除非用户说明基于某个历史任务继续，那就按中间产物判断从哪个阶段接入。

### 1) 配置自检 ⛔

按上文完成检测顺序，`validate_env.py` 退出码 0 且预设目录已建，才能进下一步。

- **退出码 0 + 可选项警告** → 不阻断，直接进下一步，不得要求用户先配写作/图片模型。
- **退出码 1**（微信不完整）→ 见 [branches.md 第三节](references/branches.md)。
- `validate_env.py` **不检查** `article_category` / `target_reader` / `default_author`，那三项在下一步查。

### 2) 全局账号约束 ⛔

打开 `.aws-article/config.yaml`，检查 **`article_category`、`target_reader`、`default_author`** trim 后是否非空。

三项齐全 → 静默通过，进下一步。任一为空 → 见 [branches.md 第四节](references/branches.md)：逐项问用户、取得当轮答复后写回文件，**禁止擅自填写或从别处反推**。

### 3) 本篇准备

**不了解用户要续写还是新开时，须先问**，再进入下面的步骤。**禁止**默认「最近修改」的目录、未确认就跑写作脚本、或假定沿用上一轮路径。

用户直接给了 `drafts/…` 路径 → 走 [branches.md 第一节「我已有目录」](references/branches.md)。

**涉及用户自身业务时**（产品 / 软件 / 服务）：先 `ls .aws-article/products/` 看有无相关目录，有就必读根下 `*.md` 作底稿、优先复用 `images/` 里的现成配图；流程中产生的业务介绍类内容，主动引导用户存回 `.aws-article/products/{产品名}/`。详见 [assets skill](../aws-wechat-article-assets/SKILL.md)。

#### 新建一篇（严格子顺序，勿跳步）

1. **写作意图** ⛔ **BLOCKING**：必须问清**本篇要写什么**（主题、角度、体裁或目标）。用户只想「帮我出选题」时须**明确确认**后再按无方向模式处理。
   ⛔ 用户未回答本步之前，**禁止** `web_search`、禁止执行 topics 的调研、禁止批量生成选题或标题。
   用户已在当次对话说清楚的，口头确认一句即可，不必重复盘问。
2. **定题与 slug**：确定发文标题（用户从候选中选或自定义），据此生成 slug，目录名 `YYYYMMDD-标题slug`。
3. **建目录与 `article.yaml`**：创建 `{drafts_root}/YYYYMMDD-标题slug/`（`drafts_root` 以 `config.yaml` 为准，默认 `drafts/`）。
   ⛔ **必须用 `{baseDir}/../aws-wechat-article-publish/scripts/article_init.py` 初始化，不要手写。** 手写一定会漏字段——实测三篇连着漏掉 `image_medium`，配图媒介的「避开上一篇」因此永远查不到东西。
4. **本篇预设单选落盘（必做）**：以 `config.yaml` 为来源，按 `custom_* > default_*` 结合本篇主题，为下列字段各选**单一预设**写回 `article.yaml` 为**单元素列表**：
   `default_structure`、`default_closing_block`、`default_title_style`、`default_format_preset`、`default_format_scheme`、`default_cover_image_style`、`default_sticker_style`。

   ⛔ **`default_article_image_style` 不在此列**，保持多元素候选池原样——正文形态是**每个图位各选一个**，收敛成一个等于整篇配图用同一种形态。实测三篇都被钉成「对比说明」，而实际三张图是实证、流程图、流程图。

   ⛔ **选模版与配色不要只看名字**：先跑 `format.py --list-themes`，按「适合 / 不适合」对本篇题材，再按配色说明选一档。**也不要连着几篇选同一套**——同一天发的几篇如果模版、配色、封面形态全同，读者一眼看出是套模板。开工前扫一眼最近几篇：

   ```bash
   grep -h "^default_format_preset:" -A1 $(ls -d drafts/*/ | sort -r | head -3 | sed 's#$#article.yaml#') 2>/dev/null
   ```

   续写 / 重入的处理见 [branches.md 第五节](references/branches.md)。
5. **脚本输出一律落盘 ⛔**：调本套件任何脚本都把 stdout 与 stderr 一起重定向到本篇目录下的 `<环节>.log`，不要只看屏幕。

   ```bash
   {python} {baseDir}/../aws-wechat-article-images/scripts/image_create.py generate … \
     > drafts/YYYYMMDD-slug/cover-generation.log 2>&1
   ```

   约定文件名：`cover-generation.log`、`image-generation.log`、`format.log`、`publish.log`。这些日志是出问题时唯一的凭据，**关键信息只在里面**——端点忽略比例把封面腰斩、模版从哪个文件加载、配色有没有应用、正文图传成了哪个 URL，屏幕上滚过去就没了。实测靠 `cover-generation.log` 里那行「已按 2.35:1 居中裁切: 1024x1024 → 1024x436」才定位到封面为什么难看。

### 4) 内容流水线

```
选题 → 写稿 → 审稿(内容审) → 排版 → 配图 → 审稿(终审)
```

| 步骤 | 子 skill | 读取 | 产出 |
|------|---------|------|------|
| 选题 | [topics](../aws-wechat-article-topics/SKILL.md) | `config.yaml`、web_search | `topic-card.md` `research.md` |
| 写稿 | [writing](../aws-wechat-article-writing/SKILL.md) | `topic-card.md`、`config.yaml` | `draft.md` |
| 内容审 | [review](../aws-wechat-article-review/SKILL.md) | `draft.md`、`config.yaml` | `review.md` → `article.md` |
| 排版 | [formatting](../aws-wechat-article-formatting/SKILL.md) | `article.md`、`config.yaml` | `article.html` |
| 配图 | [images](../aws-wechat-article-images/SKILL.md) | `article.md`、`config.yaml` | `imgs/`、`cover.*` |
| 终审 | review | `article.html`、`imgs/` | `review.md` |

⛔ **内容审产出的 `article.md` 定稿须先满足 [review 第 5 步](../aws-wechat-article-review/SKILL.md)（文末 `{embed:…}`，BLOCKING）再排版。**

**topics / `web_search`** 须在 3-1（用户已说明写什么，或已确认只帮出选题）之后才可执行。

**确认轮次**：全局三键非空时静默通过；`publish_method` 合法时不重复盘问；多个待确认项合并为一轮。用户意图明确时理想轮次为 **1 轮**（确认标题/摘要）+ 写完展示。配图在用户无特殊要求时按默认风格自动执行，不单独确认。

### 5) 发布

以 `config.yaml` 的 `publish_method` 为准：`draft` → `publish.py full` 只写草稿箱；`published` 或 `full --publish` → 再提交发布；`none` → `full` 无操作退出。

前两档需微信凭证配齐，建议先跑 `publish.py check-wechat-env`。完成后输出小结与回执，目录按需移至 `published_root`。

用户说「草稿箱里图不满意要换图重发」→ 见 [branches.md 第二节](references/branches.md)。

## 中间产物门禁 ⛔

进入下一步前先检查本步所需产物；缺什么补什么，**禁止跳步并宣称已完成**。

| 阶段 | 必要产物 | 缺失时 |
|------|---------|--------|
| 写稿完成 | `article.md` 存在且非空 | 继续写稿或回 writing |
| 排版完成 | `article.html` 存在，且由**当前** `article.md` 重新生成 | 先重跑 formatting |
| 配图完成 | 有 `cover.(png/jpg/jpeg/webp)`；`article.md` 与 `article.html` 都不含 `placeholder` | 先跑 images 生成并替换 |
| 发布就绪 | `article.yaml` 含 `title/author/digest/content_source`；发布环境检查通过 | 先补元数据或环境 |
| 发布闭环 | 发布命令成功**且回执可用** | 才允许写回 `publish_completed: true` |

**禁止**仅凭单一信号（如「草稿创建成功」）就宣称全流程完成。正文仍有 `placeholder` 时，状态必须标记为「草稿已提交，正文配图未完成」。

## 路由

**默认与长文发文相关时优先 main**，由本 skill 按步编排；不要因为用户说了「写」「选题」「发」就跳过 main 直连子 skill。

**何时可直连子 skill**：用户**明确只要该步产物**且不隐含「从零到发出」整条链。

| 用户说法 | 路由到 |
|---------|--------|
| 从0开始、一条龙、完整流程、帮我发一篇、发到公众号、今天写什么好（要成文并发）、不确定从哪步开始 | **main** |
| 「能不能发」且含代为发布、或要从稿到发出整条收尾 | **main** |
| **只要**选题卡 / 标题 / 摘要 / 排期 / 系列策划 | topics |
| **只要**在已有选题或草稿上写稿 / 改写 / 润色 / 续写 | writing |
| **只要**审稿 / 校对 / 合规清单 | review |
| **只要**排版 / 换主题 / 转 HTML | formatting |
| **只要**长文封面或正文配图 | images |
| **只要**执行发布 / 提交 / 群发 | publish |
| 贴图、图片消息、多图推送、九宫格 | **sticker** |

表述含糊、可能还要后续发文的，仍从 main 问起。单步子 skill 的边界见 [branches.md 第六节](references/branches.md)。

## 分支与补充规则

不在主路径上的情况全部写在 [references/branches.md](references/branches.md)：已有目录分支、发布后换图重发、退出码 1 的处理、全局三键为空时怎么问、续写重入的预设处理、单步子 skill 的边界。
