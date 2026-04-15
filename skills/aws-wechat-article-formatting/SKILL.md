---
name: aws-wechat-article-formatting
description: 给公众号文章排版，转换为可直接粘贴到微信后台的格式，支持多套主题。当用户提到「排版」「版式」「美化」「格式化」「字号」「段落样式」「换个主题」「转 HTML」「弄好看点」「调整格式」时使用。
---

# 排版

## 路由

一键发文且未明确只要排版 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。

将 Markdown 文章转换为微信公众号兼容的 HTML，所有样式 inline。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 用途 |
|------|------|
| `scripts/format.py` | Markdown → 微信兼容 HTML |

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。**单独启用本 skill** 时同上。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：


## 内置主题

| 主题 | 风格 | 适用场景 |
|------|------|---------|
| `default` | 经典蓝 — 沉稳大气，色块小标题 | 科技、商业、通用 |
| `grace` | 优雅紫 — 柔和圆润，左边框小标题 | 文化、美学 |
| `modern` | 暖橙 — 活力大胆，色块小标题 | 自媒体、创业 |
| `simple` | 极简黑 — 极度克制，大量留白 | 思想深度、学术 |

每个主题包含：标题样式（h1-h4）、段落、引用块、列表、分割线、图片、代码块、链接、强调色等完整规则。

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
python {baseDir}/scripts/format.py drafts/YYYYMMDD-slug/article.md -o drafts/YYYYMMDD-slug/article.html

# 显式指定主题（覆盖配置）
python {baseDir}/scripts/format.py drafts/YYYYMMDD-slug/article.md --theme grace -o drafts/YYYYMMDD-slug/article.html

# 自定义主色 / 字号
python {baseDir}/scripts/format.py article.md --theme modern --color "#A93226"
python {baseDir}/scripts/format.py article.md --font-size 15px

# 列出可用主题
python {baseDir}/scripts/format.py --list-themes
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
- 同目录存在 **`closing.md`** 时，`format.py` 会追加到文末（脚本既有行为）

## 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--theme <名称>` | 主题；**省略则按合并配置 → default** | 见上文 |
| `--color <hex>` | 自定义主色 | 主题默认 |
| `--font-size <px>` | 字号 | 16px |
| `-o <路径>` | 输出路径 | 同名 .html |
| `--list-themes` | 列出可用主题 | |

## 自定义主题

在 `.aws-article/presets/formatting/` 下新建主题文件即可。

主题文件格式和扩展方式详见：[references/presets/README.md](references/presets/README.md)

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md`、**`.aws-article/config.yaml` + 同目录 `article.yaml`**（默认主题与 `embeds`）、`closing.md`（可选） | `article.html` |
