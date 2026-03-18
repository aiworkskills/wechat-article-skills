# 排版主题说明

## 内置主题

脚本内置 4 套主题：`default`、`grace`、`modern`、`simple`。

## 自定义主题

在 `.aws-article/presets/formatting/` 下新建 `.css` 文件：

```css
/* .aws-article/presets/formatting/my-brand.css */
:root {
  --primary-color: #A93226;
  --text-color: #333333;
  --text-light: #666666;
  --text-muted: #999999;
  --bg-light: #FFF5F5;
  --border-color: #EEEEEE;
  --link-color: #576B95;
  --font-size: 16px;
  --line-height: 1.8;
  --paragraph-spacing: 1.5em;
}
```

文件名 = 主题名（如 `my-brand.css` → `--theme my-brand`）。

与内置主题同名则覆盖内置。

## 主题变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `--primary-color` | 主色，用于标题、强调、边框 | #0F4C81 |
| `--text-color` | 正文颜色 | #333333 |
| `--text-light` | 次要文字 | #666666 |
| `--text-muted` | 弱化文字（图注等） | #999999 |
| `--bg-light` | 浅色背景（引用块等） | #F7F7F7 |
| `--border-color` | 边框颜色 | #EEEEEE |
| `--link-color` | 链接颜色 | #576B95 |
| `--font-size` | 正文字号 | 16px |
| `--line-height` | 行高 | 1.8 |
| `--paragraph-spacing` | 段间距 | 1.5em |
