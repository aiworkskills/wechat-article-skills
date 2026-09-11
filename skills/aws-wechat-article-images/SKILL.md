---
name: aws-wechat-article-images
description: 公众号封面｜公众号配图｜公众号插图｜AI 生图 — 公众号 AI 封面与配图生成，按文章标题与内容自动匹配画风，一稿多方案，多风格预设可复用。面向公众号编辑、自媒体、品牌设计。触发词：「封面」「配图」「插图」「生成图片」「给文章加图」「做个封面」「文章插图」「配个图」。不写正文只发一组图请走 aws-wechat-sticker；需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env:
        - IMAGE_MODEL_API_KEY
      bins:
        - python3
    primaryEnv: aws.env
---

# 配图

**公众号封面 & 配图 AI 生成** —— 按文章内容自动匹配画风，风格体系可复用。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 调 `image_create.py` **调外部图像 API** 生成封面与正文配图，**会把图片提示词（可能含文章主题片段）发给用户配置的图像生成端点**。

- **凭证**：读 `aws.env` 的 `IMAGE_MODEL_API_KEY`，以 `Authorization: Bearer` 发往 `image_model.base_url`
- **内容外发**：每张图的 prompt 作为 JSON POST body 发送，来自本篇 `imgs/prompts/*.md`
- **SSRF 防御**：API 返回图片 URL 时**仅允许下载 http/https 公网地址**，内网 / 环回 / 保留地址一律拒绝
- **文件读**：`.aws-article/config.yaml`、本篇 `article.yaml` / `article.md` / `imgs/prompts/*.md`、本 skill 的 `references/*`、`.aws-article/products/{产品名}/images/*`
- **文件写**：本篇 `imgs/**`、可选 `img_analysis.md`
- **shell**：仅 `{python} {baseDir}/scripts/image_create.py`、`user_image_prepare.py`

**建议**用专用 key（最低权限、独立计费），不要用 account 级 master key。

单独安装本 skill 时，跨 skill 的引用会 `file not found`，但生图脚本仍可用。完整 9 slug 见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

## 路由

完整长文从选题到发布 → [main](../aws-wechat-article-main/SKILL.md)；图片消息 / 九宫格等多图推送 → [sticker](../aws-wechat-sticker/SKILL.md)。本 skill 专注**长文配图**。

配置检查按 [首次引导](../aws-wechat-article-main/references/first-time-setup.md) 执行；`image_model` 在 `config.yaml`、`IMAGE_MODEL_API_KEY` 在 `aws.env`。端点差异与比例传法见 [branches.md 第六节](references/branches.md)。

| 脚本 | 用途 |
|------|------|
| `scripts/image_create.py` | 调专用生图 API（`generate` / `batch` / `check` / `test`） |
| `scripts/user_image_prepare.py` | 用户供图模式：建 `imgs/` 并生成 `img_analysis.md` 模板 |

## 五条硬规则 ⛔

1. **封面必须脚本生成**，产出为文章目录下的 `cover.png`（或 `.jpg` / `.jpeg` / `.webp`）。**禁止**把素材库文件直接复制成 `cover.*`。例外：用户明确上传封面并声明「只用这一张」，须在结果中注明「用户指定封面」。
2. **正文优先用业务配图库**，缺图才生成。判断顺序见 [branches.md 第一节](references/branches.md)。
3. **删图有上限**：每篇最多删 1 个图位并写明理由。要删 2 个以上、**或把本篇 `image_density` 改小**（效果相同），都要先把「本篇内容与密度对不上」这个判断告诉用户。
4. **`imgs/` 目录分工**：根目录只放正文引用的最终图；`prompts/` 放生图 prompt，`sources/` 放实证图的来源说明，`raw/` 放截图与裁切的中间产物。
5. **先分工再选形态**：排版组件和信息位配图干同一件事，同一份内容只给其中一个。但**只有标准 markdown 够得到的组件才算数**——判给够不到的组件等于图和组件两头落空。实测归属见 [image-method 第一步半](references/image-method.md)：只有**金句卡片**归组件，对比两栏与清单要点一律出图。

## 工作流

```
配图进度：
- [ ] 第1步：读配置与文章
- [ ] 第2步：解析配图标记
- [ ] 第3步：确定风格
- [ ] 第4步：写 prompt
- [ ] 第5步：展示方案并等待确认 ⛔
- [ ] 第6步：生成图片
- [ ] 第7步：插入文章 + 收尾自检 ⛔
```

### 第1步：读配置与文章

- **全局** `.aws-article/config.yaml`：`cover_aspect`、`image_density`、`caption_style`、`tone` 等以它为准（字段见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)）。
- **本篇** `article.yaml`：`default_cover_image_style`（单元素，本篇已选的封面形态）、`default_article_image_style`（**多元素候选池**，正文形态逐个图位选，**不收敛成单选**——收敛等于整篇配图用同一种形态）。
- 读 `article.md`。
- `image_source: user` 时改走[用户供图模式](references/branches.md)。

### 第2步：解析配图标记

提取所有 `![类型：描述](placeholder)`。写手只用四个类型，它们定的是**图位**不是形态：

| 类型 | 含义 | 本 skill 做什么 |
|---|---|---|
| `封面` | 文章封面 | 走 [cover-method.md](references/cover-method.md) |
| `实证` | 官方原帖截图、界面实拍 | **真实素材，不生成**；来源说明写进 `imgs/sources/` |
| `信息图` | 信息位，解释内容 | 按内容选形态，内容必须取自文章 |
| `氛围` | 节奏位，只为换口气 | 概念隐喻 / 场景还原，不放具体信息 |

存量草稿里的旧类型名（`流程图` / `对比`）按 `信息图` 处理。

### 第3步：确定风格

封面与正文**分别**定，各走各的预设目录。两者的加载优先级相同：用户当次指定 > 本篇 `article.yaml` > `custom_*` 候选池（为空即全选）。

- **封面**：内置 12 个形态于 `references/cover-styles/`（`<名>.example.md`），用户自定义放 `.aws-article/presets/cover-styles/`，同名覆盖。每个模板含**用于 / 主体 / 影调 / 文案 / 版式**五个字段，**「文案」不可缺省**——缺了产出的是背景图不是封面。挑选判据只有一条：主体在 345px 缩略图里能否一眼认出。
- **正文**：内置 8 个形态于 `references/image-styles/`。判据只有一条：删掉这张图读者会**看不懂**（信息位）还是**读不下去**（节奏位）？都不影响就删掉该图位。

### 第4步：写 prompt

- **封面**：按 [cover-method.md](references/cover-method.md) 走完前六步，产出一个 prompt 文件——frontmatter 含 `aspect`（取自 `cover_aspect`，**值须加引号**，未加引号的 `16:9` 会被 YAML 解析成整数），正文是 150–300 字散文，标题文案（4–7 字，字高占画面 25–35%）连同位置、字体感、颜色一起写在里面。不要关键词清单，不要写「不要 X」，不要照抄范例场景。
- **正文**：按 [image-method.md](references/image-method.md) 六步逐个图位处理。**信息位的内容必须从文章里取**——让模型自由发挥会生成无关鸡汤并自带 emoji。
- **图中文字必须为中文**，且在 prompt 里**直接写出要显示的那几个字**，不要写 "labels in Chinese"。
- 通用规则（媒介优先、构图要求、禁用绘图库重画）见 [prompt-construction.md](references/image-styles/prompt-construction.md)。

### 第5步：展示方案并等待确认 ⛔

- **一条龙**且用户对风格无特殊要求：按默认预设自动执行**不单独确认**，但结果里要列出每张图的类型、风格与 prompt 路径。
- **单独触发本 skill**、用户提了风格要求、或方案涉及用业务配图库替换图位：先展示方案（位置 / 类型 / 风格 / prompt 要点 / 来源），**等用户确认**再进第 6 步。

### 第6步：生成图片

在**仓库根**执行，**stdout 与 stderr 一起落盘**：

```bash
{python} {baseDir}/scripts/image_create.py batch drafts/YYYYMMDD-slug/imgs/prompts/ \
  -o drafts/YYYYMMDD-slug/imgs/ > drafts/YYYYMMDD-slug/image-generation.log 2>&1
```

单张用 `generate <prompt.md> -o <out.png>`；重跑批量时加 `--skip-existing`，已生成合格的不重复付费。图片规格见 [specs.md](references/specs.md)。

**⛔ 先看日志里有没有「腰斩」告警。** 端点会间歇性忽略 `aspectRatio` 返回方图，脚本再把它居中裁到目标比例——而模型是**按方画布构图**的（「左侧四成…右侧六成…字高 28%」），砍掉一大半之后主体偏位、标题错位。实测四张封面里三张如此。看到 `[WARN] … 只剩 43%……腰斩` 就重跑这一张（`--retries 1`）：这和分辨率略低不同，那个读者看不出，这个一眼就看得出。

**⛔ 出字问题先改 prompt，不要换工具。** 不许因为「API 出来的字有裁切」就改用 matplotlib / PIL 重画——那样媒介和形态整套方法论被绕开，钱还付两遍。理由见 [prompt-construction.md](references/image-styles/prompt-construction.md)。

**封面回看（必做）**：打开图片对四条——主体位置与标题区、元素 ≤3、缩略图可读、与文章相关。不过关**回到出问题的那一步改 prompt** 再生成，不要不改 prompt 盲目重跑。看不了图时退而用 `image_create.py check cover.png`（**只有尺寸与近单色两项**）。

脚本非零退出或 stderr 有 API / 网络错误 → 走 [branches.md 第四节](references/branches.md)，**必须分类并摘要报错**，不得只说「生图失败」。

### 第7步：插入文章 + 收尾自检

替换 placeholder 为实际图片路径。**封面不进正文**：`![封面：…]` 仅用于微信封面上传，替换时跳过或删除该行，封面单独存为文章根目录的 `cover.{ext}`。

仅当 `article.html` 里**确实存在** `href="placeholder"` 或 placeholder 被渲染成链接时，才去修 HTML；不要默认每次都执行「修复 HTML」。

**⛔ 收尾自检（六条，缺一不可）**

1. **每张正文图各有一个 `imgs/prompts/*.md`**，文件名主干与图片一致。**先落 prompt 再生成，不许反过来**——否则出了问题没法复现，想只重跑一张也做不到，只能整批重来（按张计费）。Agent 自己生图时同样要落盘。
2. **实证图的说明放 `imgs/sources/`，不许放 `prompts/`**。`batch` 是整目录 glob 的，混在里面会照着「来源：https://x.com/…」生成一张**伪造的原帖截图**覆盖掉真的那张——而文章正拿它当证据。脚本已有防线（首行「来源：」或 frontmatter `type: source` 会跳过并告警），但目录放对才是根本。
3. **`article.yaml` 的 `image_medium` 非空**，且等于第四步实际用的媒介。它是下一篇「平手时避开上一篇」的唯一依据。
4. **正文图数量与 `image_density` 对得上**。删过图位要写明删了哪个、为什么。
5. **生成日志已落盘**且看过有没有腰斩告警。封面为什么难看，正是靠日志里「已按 2.35:1 居中裁切: 1024x1024 → 1024x436」定位到的——屏幕上滚过去就没了。
6. **`imgs/` 根目录只剩正文引用的图**，中间产物已归入 `raw/`；**本篇所有信息位配图共用同一个媒介**，而每个图位的形态各自按内容选。

重跑生图后**必须复核引用**——返回格式会变（这次 PNG 下次 JPEG），引用会断且不报错。细则见 [branches.md 第五节](references/branches.md)。

## 分支与异常

不在主路径上的情况全部写在 [references/branches.md](references/branches.md)：正文配图来源优先级、用户供图模式、发布后换图重发、调用失败四分类、故障降级终点、重跑复核、端点差异与比例传法。
