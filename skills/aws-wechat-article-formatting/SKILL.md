---
name: aws-wechat-article-formatting
description: 公众号排版｜Markdown 转 HTML｜排版主题｜段落样式 — 公众号一键排版工具，Markdown 文稿转微信后台可粘贴 HTML，多主题、多字号、段落样式切换，所见即所得。面向公众号编辑、独立作者、排版岗。触发词：「排版」「版式」「美化」「格式化」「字号」「段落样式」「换个排版主题」「换个版式」「转 HTML」「弄好看点」「调整格式」。换预设包/品牌包/整套主题配色请走 aws-wechat-article-assets；需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 排版

**公众号一键排版** —— Markdown 转微信后台可粘贴 HTML，多主题、多字号、所见即所得。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 为**纯本地** Markdown → HTML 转换，零网络、零凭证。

- **凭证**：无
- **网络**：无
- **文件读（仓库内）**：`.aws-article/config.yaml`、本篇 `article.yaml`、`article.md`、可选 `closing.md`、`.aws-article/presets/formatting/<名>.yaml`
- **文件读（仓库外）**：`format.py` 还会检查用户家目录 `~/.aws-article/presets/formatting/`（跨项目共享的自定义排版主题；**只读预设文件，不读凭证**）。不需要这个能力可清空 / 不创建该目录
- **文件写**：本篇 `article.html`
- **shell**：仅 `{python} {baseDir}/scripts/format.py`（`{python}` = 本机 Python 3 解释器，见 [main SKILL 第 0 步](../aws-wechat-article-main/SKILL.md)：Windows 用 `py -3 -X utf8`，macOS / Linux 用 `python3`）

## 配套 skill（informational）

本 skill 是 `aws-wechat-article-*` 一条龙公众号套件的**排版环节**（入口 `aws-wechat-article-main`）。

- **单独安装可直接使用**：本 skill 的脚本 `format.py` 零依赖、纯本地，无跨 skill 脚本调用。
- 工作流文档中会链接到 `../aws-wechat-article-main/references/*.md`（首次引导等）。套件未装齐时，链接跳转会断，但排版功能本身可用。

完整 9 slug 清单见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

## 路由

一键发文且未明确只要排版 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

将 Markdown 文章转换为微信公众号兼容的 HTML，所有样式 inline。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 用途 |
|------|------|
| `scripts/format.py` | Markdown → 微信兼容 HTML |

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。**单独启用本 skill** 时同上。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）。

## 内置主题

| 主题 | 风格 | 适用场景 |
|------|------|---------|
| `default` | 经典蓝 — 沉稳大气，色块小标题 | 科技、商业、通用 |
| `grace` | 优雅紫 — 柔和圆润，左边框小标题 | 文化、美学 |
| `modern` | 暖橙 — 活力大胆，色块小标题 | 自媒体、创业 |
| `simple` | 极简黑 — 极度克制，大量留白 | 思想深度、学术 |

每个主题包含：标题样式（h1-h4）、段落、引用块、列表、分割线、图片、代码块、链接、强调色等完整规则。

## 版式组件（:::块）

主题只能给标签配内联样式，表达不了结构——而微信没有伪元素，「标题前的角标」
「引用块的大引号」必须**真的插元素**。组件补的就是这一层：

```
:::section-title[01]
同一个模型，两个分数
:::

:::quote-card[AWS 团队]
基准分数衡量的是你缺哪个 harness，不是模型的能力上限。
:::
```

内置组件在 [references/components/](references/components/)，用户自定义放
`.aws-article/presets/components/<名>.yaml`，同名覆盖内置。每个组件的 YAML 里带
`when_to_use` / `when_not_to_use` / `anti_pattern`——**选组件前先读这三项**，
它们和配图方法里的判据是同一个作用：拦住「因为好看所以用」。

组件模板里的 `{primary-color}` `{text-color}` 等占位符从当前主题取值，所以组件
与任何主题组合都不会脱节。未知组件名或缺少结尾 `:::` 时按原文输出并告警，不吞内容。

## 设计新版式前必读 ⛔

微信正文只认**内联样式**，没有伪元素、没有伪类、`position` 与 `id` 会被整条删掉。
这决定了「装饰必须作为真实元素插进 HTML」，而不能靠 CSS 变出来。
能用什么、什么会被剥离，见 [wechat-html-constraints.md](references/wechat-html-constraints.md)。

## 工作流

```
排版进度：
- [ ] 第0步：配置检查（见本节「配置检查」）⛔
- [ ] 第1步：确定主题（与合并配置 / 用户指定）
- [ ] 第2步：转换
- [ ] 第3步：输出 HTML
```

### 第1步：确定主题

主题解析顺序（**`format.py` 行为**与智能体择一）：

1. **命令行** `--theme <名称>`：显式指定时**始终优先**。
2. **未传 `--theme`**：`format.py` 仅读取 **与 `article.md` 同目录的 `article.yaml`** 中 **`default_format_preset`**（**须为 YAML 列表**：`[]` 或单元素 `[主题名]`）；为空则用内置主题名 **`default`**。
3. 智能体在对话中帮用户选主题时，按：用户口述 → 本篇 `article.yaml.default_format_preset` → `.aws-article/presets/formatting/` 自定义 → 内置 `default`。`custom_* / default_*` 候选池解析由 main 在“本篇准备”阶段完成并写回 `article.yaml`。

主题名须对应 **内置主题** 或 **`.aws-article/presets/formatting/<名>.yaml`**。字段说明见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)（与仓库 `config.yaml` 顶层字段对齐）。

### 第2步：转换

在**仓库根**执行（路径按实际本篇目录调整）：

```bash
# 不传 --theme：使用合并配置中的 default_format_preset，否则 default
{python} {baseDir}/scripts/format.py drafts/YYYYMMDD-slug/article.md -o drafts/YYYYMMDD-slug/article.html

# 显式指定主题（覆盖配置）
{python} {baseDir}/scripts/format.py drafts/YYYYMMDD-slug/article.md --theme grace -o drafts/YYYYMMDD-slug/article.html

# 自定义主色 / 字号
{python} {baseDir}/scripts/format.py article.md --theme modern --color "#A93226"
{python} {baseDir}/scripts/format.py article.md --font-size 15px

# 列出可用主题
{python} {baseDir}/scripts/format.py --list-themes
```

### 嵌入元素 `{embed:...}`

- **`format.py`**：**名片 / 小程序** 的 `embeds` 以 **`.aws-article/config.yaml`** 为准；**仅「往期链接」**：本篇 `article.yaml` 可写 **`embeds.related_articles`**，与全局 **`related_articles` 深度合并**（用于每篇不同推荐）。合并结果中非空 **`embeds`** 时解析 `{embed:profile|miniprogram|miniprogram_card|link:名称}`；否则不对嵌入占位符做替换（视为无配置）。
- 与 [writing 结构模板](../aws-wechat-article-writing/references/structure-template.md) 中的占位说明一致。

### 第3步：输出 HTML

输出的 HTML 特性：
- 所有样式 inline（微信编辑器兼容）
- **正文不含文章标题**：Markdown 中第一个 `#`（h1）在转换时被跳过，标题在公众号后台单独填写，正文不重复
- 配图标记 `![类型：描述](placeholder)` 保留为 `<img>` 标签，待 images skill 替换
- 图注自动从标记描述中提取
- 同目录存在 **`closing.md`** 时，`format.py` 会追加到文末（脚本既有行为）；`closing.md` 自己的首个 `#` 标题会保留，只有 `article.md` 的首个 `#` 被视为文章标题跳过
- 预格式化（中英文加空格、ASCII 引号转「」、合并空行）只作用于正文文字：围栏代码块、行内代码、链接/图片目标、`{embed:…}`、原生 HTML 标签与裸 URL 原样保留，行内代码内容做 HTML 转义。不需要预格式化时加 `--no-preformat`
- 表格支持 `|:---:|` 这类对齐行

## 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--theme <名称>` | 主题；**省略则按合并配置 → default** | 见上文 |
| `--color <hex>` | 自定义主色 | 主题默认 |
| `--font-size <px>` | 正文字号（同时覆盖主题 p / li 里的字号） | 16px |
| `-o <路径>` | 输出路径 | 同名 .html |
| `--list-themes` | 列出可用主题 | |
| `--export-theme <名称>` | 以 YAML 导出主题（合并默认变量与样式），重定向到文件即可作为自定义主题起点 | |
| `--no-preformat` | 跳过 Markdown 预格式化 | |

## 自定义主题

在 `.aws-article/presets/formatting/` 下新建主题文件即可。快速起步：

```bash
{python} {baseDir}/scripts/format.py --export-theme default > .aws-article/presets/formatting/my-brand.yaml
```

主题文件格式和扩展方式详见：[references/presets/README.md](references/presets/README.md)

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md`、**`.aws-article/config.yaml` + 同目录 `article.yaml`**（默认主题与 `embeds`）、`closing.md`（可选） | `article.html` |
