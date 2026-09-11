---
name: aws-wechat-article-review
description: 公众号审稿｜公众号校对｜敏感词检测｜内容合规 — 公众号发布前合规审查：敏感词扫描、错别字检测、政治合规、平台规范校验，一次性输出修改清单。面向公众号编辑、自媒体作者、合规岗。触发词：「审稿」「审核」「校对」「合规」「敏感词」「错别字」「稿子检查一下」「稿子帮我看看」「稿子写完了」「文章检查一下」「检查下有没有问题」「能不能发」「发布前检查」。需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 审稿与合规

**公众号发布前合规守门员** —— 敏感词、错别字、平台规范一次性筛查，输出可执行修改清单。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 为**纯本地规则/清单审稿**，零网络、零凭证。

- **凭证**：无
- **网络**：无
- **文件读**：`.aws-article/config.yaml`、`.aws-article/writing-spec.md`（如有）、`.aws-article/presets/review-rules.yaml`（如有）、本篇 `draft.md` / `article.html` / `article.yaml` / `imgs/`
- **文件写**：本篇 `draft-stripped.md`（中间产物）、`article.md`（定稿）、`review.md`
- **shell**：只在第 5 步调 `{python} .../aws-wechat-article-writing/scripts/write.py strip-citations`，第 2 步调同一脚本的 `check` 子命令。**两者都是纯本地正则/计数，不联网、不读凭证、不调 LLM。**

> 往期推荐链接的**自动补齐**由 [publish skill](../aws-wechat-article-publish/SKILL.md) 处理（那里才有微信 API 凭证与 `getdraft.py`）；本 skill 只按已有 `manual` 排占位符，**不直接调任何网络脚本**。

## 路由

「能不能发」若含代为发布、或从稿到发出整条收尾 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

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
- [ ] 第2步：逐项检查（含机器自检）
- [ ] 第3步：输出审稿结果
- [ ] 第4步：修改循环 🔄
- [ ] 第5步：⛔ 剥离引用标注 → 文末 embed → 保存 article.md 定稿
```

### 智能体行为约束 ⛔

- **禁止**在未完成第 5 步「文末 embed」的情况下，把稿件称为「已定稿」、写入 `article.md`、或进入排版（`format.py`）。
- **禁止**用「用户没提」「节省时间」等理由跳过文末占位符。**唯一例外**：用户**书面**声明本篇不要任何嵌入元素，则须在审稿记录中写明「用户声明跳过 embed」，且仍须确认不是误操作。
- 一条龙流程中，内容审产出的 `article.md` **必须已含文末 embed**（按合并规则或合法省略），再进入排版。

### 第1步：环境检查 + 读取约束 ⛔

任何操作前先按 **[首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)** 执行，通过后才继续（或用户明确书面确认「本次不检查」）。单独启用本 skill 时的口径见 [branches.md「四」](references/branches.md)。

然后读取：

- **`.aws-article/writing-spec.md`**（如有）
- **`.aws-article/presets/review-rules.yaml`**（如有，见 [branches.md「二」](references/branches.md)）
- **本篇合并配置**（与 [writing](../aws-wechat-article-writing/SKILL.md)、`format.py` 一致）：先 `.aws-article/config.yaml` 顶层（不含 `writing_model` / `image_model`），再叠本篇 `article.yaml`（**同键本篇优先**；**仅** `embeds.related_articles` 与全局深度合并，其余 `embeds` 仍以全局为准）。审稿以合并结果为准（`review_output_format`、`custom_sensitive_words`、`forbidden_words`、`target_reader`、`tone`、`image_density` 等）。字段说明见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

约束缺失时按 [branches.md「三」](references/branches.md) 降级，**不要中断审稿**。

### 第2步：逐项检查

完整清单见 [references/checklist.md](references/checklist.md)。

**先跑机器自检**（内容审模式）—— 产出配额里能数出来的部分不该靠眼睛：

```bash
{python} {baseDir}/../aws-wechat-article-writing/scripts/write.py check <本篇 draft.md>
```

与 [writing 第 7 步](../aws-wechat-article-writing/SKILL.md) 同一套判据。writing 阶段本该跑过，但稿子可能是用户自己贴进来的、或中途手改过，**这里是最后一道能机器量的关口**。映射：脚本报的**硬性项 → 🔴**，**提醒项 → 🟡**。它还会把全文加粗串成一行打印出来——**那一串读起来像不像一份提要，仍要自己读一遍**，脚本量不了挑得对不对。

**内容审**再逐维度人工过：

| 维度 | 检查内容 |
|------|---------|
| **标题** | 长度、禁用套路、与正文一致性 |
| **摘要** | 长度、信息量、与正文一致；**且与正文首个 `>` 导语不是同一句话** |
| **正文** | 敏感词、禁用词、错别字、事实出处 |
| **写作规范** | 对照 writing-spec.md 检查用词、句式、段落；深度与调性是否与合并配置的 `target_reader`、`tone` 一致 |
| **AI 味自检** | 对照 [ai-flavor-check.md](references/ai-flavor-check.md) 逐处诊断并标注信号强度。**默认只诊断**：一律折算 🟡，不 blocking、不影响定稿（两套判级的区别见 [branches.md「五」](references/branches.md)） |
| **配图标记** | 封面标记存在、数量与 `image_density` 匹配、描述具体 |
| **文末 embed** | 定稿前须完成第 5 步 ⛔；未写入 `article.md` 不得定稿 |
| **原创标注** | 按 `original_attribution` 处理 |

**终审**额外检查：

| 维度 | 检查内容 |
|------|---------|
| 排版 | `article.html` 存在且完整，无乱码 |
| 图片 | **文章目录下有 `cover.*`**（封面不在 `imgs/` 里）、`imgs/` 正文图齐全、`placeholder` 已全部替换、文件真实存在 |
| 发布要素 | 标题/摘要/作者/封面全部就绪 |

### 第3步：输出审稿结果

按 `review_output_format` 输出：**分块详细**（按维度分块，逐项 ✅/❌ + 修改建议）或**简要清单**（表格，一行一项）。模板见 [references/output-format.md](references/output-format.md)。

结果分三级：

- 🔴 **必须修改**：不改不能过（敏感词、严重错别字、缺封面、机器自检的硬性项）
- 🟡 **建议修改**：改了更好（用词优化、段落调整、AI 味、机器自检的提醒项）
- 🟢 **通过**

### 第4步：修改循环 🔄

有 🔴 项时**必须进入修改循环**：`发现问题 → 展示审稿结果 → 修改 → 重新检查 → 直到无 🔴`。

修改方式：Agent 直接改 `draft.md` / 用户手改后说「改好了」/ 调 [writing](../aws-wechat-article-writing/SKILL.md) 的 rewrite。

每轮只重审被标为 🔴 的项，不必全量重审。

> ⚠️ **第 4 步完成不代表可以保存 `article.md`**，必须先走完第 5 步。

### 第5步：剥离引用标注 → 文末 embed → 保存定稿 ⛔ BLOCKING

全部 🔴 消除后：

1. 展示最终审稿结果，**等待用户确认** ⛔。
2. **剥离引用标注** —— 在仓库根执行：

   ```bash
   {python} {baseDir}/../aws-wechat-article-writing/scripts/write.py strip-citations <本篇 draft.md> -o <本篇 draft-stripped.md>
   ```

   纯本地正则剥掉正文里所有 `（资料路径：…）`（writing 阶段为事实溯源强制注入，发布版必须去除，以免泄露内部产品目录路径）。**禁止**用 sed 或肉眼撕替代该脚本——历史上多次「撕一遍漏一条」。

3. **文末 `embeds`** —— **在写入 `article.md` 之前**，按第 1 步的合并结果在 `draft-stripped.md` 的**正文末尾**追加占位符：

   | 占位符 | 何时写入 | 配置对齐 |
   |--------|----------|----------|
   | `{embed:profile:…}` | `embeds.profiles` 有至少一条非空 `nickname` | 每条有效项一行，`…` = 该项 `nickname` |
   | `{embed:miniprogram:…}` | `embeds.miniprograms` 有至少一条非空 `title` | 每条有效项一行，`…` = `title` |
   | `{embed:miniprogram_card:…}` | `embeds.miniprogram_cards` 有至少一条非空 `title` | 每条有效项一行，`…` = `title` |
   | `{embed:link:…}` | `embeds.related_articles.manual` 有有效项 | `…` = 该项 `name`；**至多 3 条** |

   **占位符必须与合并后可解析的配置一致**，否则排版阶段会失败。列表为空、`manual` 缺失、用户声明跳过、以及全空时仍须显式标注——见 [branches.md「一」](references/branches.md)。

4. 将**已剥离引用标注且含文末 embed**（或已按规则省略并记入审稿说明）的稿件保存为 **`article.md`（定稿）**。中间产物 `draft-stripped.md` 可保留备查或删除。

**未完成第 3 小步不得保存定稿、不得调用 `format.py`。**

## 分支与异常

往期链接三种情况与全空标注、自定义检查规则、约束缺失 fallback、单独启用本 skill、AI 味两套判级 → [references/branches.md](references/branches.md)。

## 过程文件

| 模式 | 读取 | 产出 |
|------|------|------|
| 内容审 | `draft.md`、`.aws-article/config.yaml` + 本篇 `article.yaml`、`writing-spec.md` | `review.md`、`article.md`（定稿） |
| 终审 | `article.html`、`cover.*`、`imgs/`、同上合并配置、`article.yaml` | `review.md`（终审结果） |
