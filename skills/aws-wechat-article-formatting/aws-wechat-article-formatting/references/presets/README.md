# 排版主题说明

## 使用主题

不传 `--theme` 时，**`format.py`** 从合并配置读取 **`custom_format_preset`**（优先）> **`default_format_preset`**（**`.aws-article/config.yaml`** + 本篇 **`article.yaml`**）。该键**须为 YAML 字符串列表**：`[]`、单元素 `[主题名]`，或多候选；**多候选**须在本篇同键改为**单元素列表**后再运行，否则报错。

```bash
python format.py article.md --theme <主题名>
python format.py --list-themes              # 列出可用主题
```

## 内置主题

| 主题名 | 风格 | 适用场景 |
|--------|------|---------|
| `default` | 经典蓝 — 沉稳大气的编辑风格 | 科技、商业、通用 |
| `grace` | 优雅紫 — 柔和圆润的风格 | 文化、美学 |
| `modern` | 暖橙 — 活力大胆的风格 | 自媒体、创业 |
| `simple` | 极简黑 — 极度克制的留白风格 | 思想深度、学术 |

## 自定义主题

在 `.aws-article/presets/formatting/` 下创建 `.yaml` 文件即可：

```yaml
# .aws-article/presets/formatting/my-brand.yaml

name: 我的品牌                 # 显示名称
description: 品牌专用排版       # 说明

variables:                     # 变量（可选，覆盖默认值）
  primary-color: "#A93226"
  bg-accent-color: "#FFF5F5"
  text-color: "#333333"
  bg-light: "#FFF5F5"
  font-size: "16px"
  line-height: "1.8"
  paragraph-spacing: "1.5em"

styles:                        # 样式规则（可用 {变量名} 引用变量）
  h1: "text-align:center; font-size:22px; font-weight:bold; color:{primary-color};"
  h2: "font-size:18px; background:{primary-color}; color:#FFF; padding:6px 14px; border-radius:4px;"
  h3: "font-size:16px; font-weight:bold; color:{primary-color};"
  h4: "font-size:15px; font-weight:bold; color:#444;"
  p: "font-size:15px; line-height:1.8; color:#3a3a3a; margin:10px 0;"
  strong: "color:{primary-color}; font-weight:bold;"
  em: "font-style:italic; color:#555;"
  a: "color:{primary-color}; text-decoration:none; border-bottom:1px solid {primary-color};"
  blockquote: "border-left:3px solid {primary-color}; background:{bg-light}; padding:12px 16px;"
  ul: "padding-left:20px; margin:0.6em 0;"
  ol: "padding-left:20px; margin:0.6em 0;"
  li: "margin-bottom:6px; line-height:1.75; color:#3a3a3a;"
  hr: "border:none; border-top:1px solid #EEE; width:60%; margin:2em auto;"
  img: "max-width:100%; border-radius:5px; display:block; margin:0 auto;"
  figcaption: "text-align:center; font-size:12px; color:#999; margin-top:6px;"
  code: "color:{primary-color}; background:{bg-accent-color}; padding:2px 6px; border-radius:3px; font-size:90%;"
  pre: "background:#1a1a2e; color:#e0e0e0; padding:16px; border-radius:10px; font-size:13px; line-height:1.8; overflow-x:auto;"
  strong-color: "{primary-color}"
```

保存后 `--theme my-brand` 立即可用。与内置主题同名则覆盖内置。

## 快速创建自定义主题

基于内置主题导出 YAML，再修改：

```bash
python format.py --export-theme default > .aws-article/presets/formatting/my-brand.yaml
# 编辑 my-brand.yaml，修改颜色和样式
```

## 可用变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `primary-color` | 主色 | #0F4C81 |
| `bg-accent-color` | 强调背景色 | #F0F4F8 |
| `text-color` | 正文颜色 | #333333 |
| `text-light` | 次要文字 | #666666 |
| `text-muted` | 弱化文字 | #999999 |
| `bg-light` | 浅色背景 | #F7F7F7 |
| `border-color` | 边框颜色 | #EEEEEE |
| `link-color` | 链接颜色 | #576B95 |
| `font-size` | 正文字号 | 16px |
| `font-family` | 字体 | system fonts |
| `line-height` | 行高 | 1.8 |
| `paragraph-spacing` | 段间距 | 1.5em |

## 可用样式键

| 键 | 控制元素 |
|----|---------|
| `h1` | 一级标题（文章标题） |
| `h2` | 二级标题（小标题） |
| `h3` | 三级标题 |
| `h4` | 四级标题 |
| `p` | 段落（留空则用变量自动拼接） |
| `strong` | 加粗文字（留空则用 `strong-color`） |
| `em` | 斜体文字 |
| `a` | 链接（留空则用 `link-color`） |
| `blockquote` | 引用块 |
| `ul` | 无序列表容器 |
| `ol` | 有序列表容器 |
| `li` | 列表项 |
| `hr` | 分割线 |
| `img` | 图片 |
| `figcaption` | 图片说明 |
| `code` | 行内代码 |
| `pre` | 代码块 |
| `strong-color` | 加粗文字颜色（兼容旧主题） |

样式值为 CSS inline style 格式，可使用 `{变量名}` 引用变量。
