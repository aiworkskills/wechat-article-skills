# 排版主题说明

## 使用主题

```bash
python format.py article.md --theme <主题名>
python format.py --list-themes              # 列出可用主题
```

## 内置主题

| 主题名 | 风格 | 适用场景 |
|--------|------|---------|
| `default` | 经典蓝 | 科技、干货、通用 |
| `grace` | 优雅紫 | 文艺、生活方式 |
| `modern` | 暖橙 | 现代感、品牌 |
| `simple` | 极简黑 | 极简主义、学术 |

## 自定义主题

在 `.aws-article/presets/formatting/` 下创建 `.yaml` 文件即可：

```yaml
# .aws-article/presets/formatting/my-brand.yaml

name: 我的品牌                 # 显示名称
description: 品牌专用排版       # 说明

variables:                     # 变量（可选，覆盖默认值）
  primary-color: "#A93226"
  text-color: "#333333"
  bg-light: "#FFF5F5"
  font-size: "16px"
  line-height: "1.8"
  paragraph-spacing: "1.5em"

styles:                        # 样式规则（可用 {变量名} 引用变量）
  h1: "text-align:center; font-size:22px; font-weight:bold; color:{primary-color};"
  h2: "font-size:18px; background:{primary-color}; color:#FFF; padding:6px 14px; border-radius:4px;"
  h3: "font-size:16px; font-weight:bold; color:{primary-color};"
  blockquote: "border-left:3px solid {primary-color}; background:{bg-light}; padding:12px 16px;"
  hr: "border:none; border-top:1px solid #EEE; width:60%; margin:2em auto;"
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
| `blockquote` | 引用块 |
| `hr` | 分割线 |
| `strong-color` | 加粗文字颜色 |

样式值为 CSS inline style 格式，可使用 `{变量名}` 引用变量。
