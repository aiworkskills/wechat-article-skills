---
name: aws-wechat-article-formatting
description: 将公众号文章内容按预设排版规则格式化，支持多套排版预设，输出可直接粘贴到公众号后台的格式化内容。当用户提到「排版」「版式」「字号」「段落」「样式」「引导语」或需要格式化文章时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-formatting
---

# 排版

从预设读取排版规则，应用到正文内容，输出格式化结果。

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
3. 若以上均无 → 列出可用预设供用户选择

可用预设列表见 `references/presets/` 目录下的文件，每个文件名即预设名。

### 第2步：读取预设规则

从 `references/presets/<预设名>.md` 读取该预设的完整排版规则，包含：
- 字号与字体
- 颜色方案
- 段落间距
- 标题样式
- 引用块样式
- 列表样式
- 分割线
- 其他自定义规则

### 第3步：应用排版

将 aws-wechat-article-writing 的产出（或用户提供的正文）按预设规则格式化。

### 第4步：输出格式化结果

输出格式化后的内容（Markdown 或 HTML，由预设决定），可直接用于公众号后台。

## 预设目录

预设文件存放在 `references/presets/`，每个预设为独立的 `.md` 文件。

| 预设 | 风格 | 适用场景 |
|------|------|---------|
| default | 简约科技 | 科技、互联网、干货类文章 |
| *更多预设持续添加中* | | |

预设文件格式说明：[references/presets/README.md](references/presets/README.md)

## 自定义预设

在 `references/presets/` 下新建 `.md` 文件，按 README 中的格式编写排版规则即可。预设名 = 文件名（不含 `.md`）。
