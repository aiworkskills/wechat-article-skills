---
name: aws-wechat-article-writing
description: 写公众号文章或改写已有内容，可调用第三方模型生成初稿。当用户提到「写文章」「写正文」「写稿」「出稿」「改写」「润色」「续写」「写个初稿」「帮我写」「公众号风格」「把提纲写成文章」「开头结尾」「用 DeepSeek 写」「用 GPT 写」时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-writing
---

# 长文写作

## 配置检查 ⛔

`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`
⛔ 不存在 → [首次引导](../aws-wechat-article-main/references/first-time-setup.md)

## 工作流

```
写稿进度：
- [ ] 第1步：读取配置与写作规范
- [ ] 第2步：确定输入与写作方式
- [ ] 第3步：写作
- [ ] 第4步：自检与修正
- [ ] 第5步：展示并等待用户确认 ⛔
```

### 第1步：读取配置与写作规范

从 `config.yaml` 读取写作配置和模型配置。加载 `.aws-article/writing-spec.md`（如有）。

### 第2步：确定输入与写作方式

**输入**：`topic-card.md` / 用户提供的提纲或素材 / 用户口述主题

**写作方式**：Agent 直写 / 调用第三方模型（`write.py`）。用户指定模型或长文推荐用第三方模型。

### 第3步：写作

按结构模板写作：[references/structure-template.md](references/structure-template.md)

写作时在需要图的位置插入配图标记 `![类型：描述](placeholder)`，详见结构模板中的「配图标记」章节。

**调用第三方模型**时的脚本用法：[references/usage.md](references/usage.md)

### 第4步：自检与修正

按写作规范做一轮自检（禁用词、段落长度、开头吸睛度、小标题密度），发现问题自动修正。

### 第5步：展示并等待用户确认 ⛔

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md` | `draft.md`（含配图标记） |
