---
name: aws-wechat-article-formatting
description: 将公众号文章内容按预设排版规则格式化，支持多套排版预设，输出可直接粘贴到公众号后台的格式化内容。当用户提到「排版」「版式」「字号」「段落」「样式」「引导语」或需要格式化文章时使用。
version: 0.2.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-formatting
---

# 排版

从预设读取排版规则，应用到正文内容，输出格式化 HTML。

## 工作流

```
排版进度：
- [ ] 第1步：确定排版预设
- [ ] 第2步：读取预设规则
- [ ] 第3步：应用排版
- [ ] 第4步：输出格式化结果
```

### 第1步：确定排版预设

预设解析顺序（首个命中即用）：
1. 用户当次指定的预设名
2. 配置 `default_format_preset`
3. `.aws-article/presets/formatting/` 下的用户自定义预设
4. skill 内置 `references/presets/` 下的预设
5. 若以上均无 → 列出可用预设供用户选择

### 第2步：读取预设规则

按优先级查找预设文件：
1. `.aws-article/presets/formatting/<预设名>.md`（用户自定义）
2. skill 内置 `references/presets/<预设名>.md`（内置默认）

同名时用户文件覆盖内置。

### 第3步：应用排版

读取文章目录下的 `article.md`（定稿），按预设规则格式化。

配图标记 `![类型：描述](placeholder)` 保留不动，交给 images 处理。

### 第4步：输出格式化结果

输出 HTML 格式的排版结果，保存为文章目录下的 `article.html`。

## 预设查找路径

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 1 | `.aws-article/presets/formatting/` | 用户自定义预设 |
| 2 | skill 内置 `references/presets/` | 内置默认预设 |

内置预设：

| 预设 | 风格 | 适用场景 |
|------|------|---------|
| default | 简约科技 | 科技、互联网、干货类文章 |
| *更多预设持续添加中* | | |

## 自定义预设

在 `.aws-article/presets/formatting/` 下新建 `.md` 文件，按 [references/presets/README.md](references/presets/README.md) 中的格式编写。预设名 = 文件名。

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.md` | `article.html` |
