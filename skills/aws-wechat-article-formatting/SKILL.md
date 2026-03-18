---
name: aws-wechat-article-formatting
description: 给公众号文章排版，转换为可直接粘贴到微信后台的格式，支持多套主题。当用户提到「排版」「版式」「美化」「格式化」「字号」「段落样式」「换个主题」「转 HTML」「弄好看点」「调整格式」时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-formatting
---

# 排版

将 Markdown 文章转换为微信公众号兼容的 HTML，所有样式 inline。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 用途 |
|------|------|
| `scripts/format.py` | Markdown → 微信兼容 HTML |

## 内置主题

| 主题 | 风格 | 适用场景 |
|------|------|---------|
| `default` | 经典蓝 — 左边框小标题，底部分割线大标题 | 科技、干货、通用 |
| `grace` | 优雅紫 — 圆角色块小标题，文字阴影 | 文艺、生活方式 |
| `modern` | 暖橙 — 胶囊圆角小标题，宽松行高 | 现代感、品牌 |
| `simple` | 极简黑 — 底线小标题，最少装饰 | 极简主义、学术 |

每个主题包含：标题样式、引用块样式、分割线、强调色、段落间距等完整规则。

## 工作流

**⛔ 先检查 config.yaml 是否存在**，不存在则进入首次引导（见 [aws-wechat-article-main/references/first-time-setup.md](../aws-wechat-article-main/references/first-time-setup.md)）。

```
排版进度：
- [ ] 第0步：检查配置 ⛔
- [ ] 第1步：确定主题
- [ ] 第2步：转换
- [ ] 第3步：输出 HTML
```

### 第1步：确定主题

主题解析顺序（首个命中即用）：
1. 用户当次指定（如「用 grace 主题」「用优雅风」）
2. config `default_format_preset`
3. 若以上均无 → 列出主题供用户选择

### 第2步：转换

```bash
# 基础转换
python {baseDir}/scripts/format.py article.md --theme default

# 自定义主色
python {baseDir}/scripts/format.py article.md --theme modern --color "#A93226"

# 自定义字号
python {baseDir}/scripts/format.py article.md --font-size 15px

# 指定输出路径
python {baseDir}/scripts/format.py article.md --theme grace -o article.html

# 列出可用主题
python {baseDir}/scripts/format.py --list-themes
```

### 第3步：输出 HTML

输出的 HTML 特性：
- 所有样式 inline（微信编辑器兼容）
- 配图标记 `![类型：描述](placeholder)` 保留为 `<img>` 标签，待 images skill 替换
- 图注自动从标记描述中提取

## 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--theme <名称>` | 主题 | default |
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
| `article.md` | `article.html` |
