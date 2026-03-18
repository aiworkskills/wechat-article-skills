---
name: aws-wechat-article-publish
description: 提供微信公众号发布前的最终检查清单和提交指引，确保内容可安全发布。当用户提到「发布」「提交」「群发」或需要发布到公众号时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-publish
---

# 发布

发布前最终检查 + 提交到公众号后台的操作指引。

## 工作流

```
发布进度：
- [ ] 第1步：发布前检查
- [ ] 第2步：提交指引
- [ ] 第3步：确认完成
```

### 第1步：发布前检查

执行 [references/pre-publish-checklist.md](references/pre-publish-checklist.md) 中的清单，与审稿结果衔接。

全部通过后进入提交步骤；有未通过项需先修正。

### 第2步：提交指引

按 [references/submit-guide.md](references/submit-guide.md) 指引用户完成提交。

当前支持手动复制粘贴方式。API 方式预留，待后续实现。

### 第3步：确认完成

确认已提交后，将稿件从 `drafts_root` 移动到 `published_root`（按配置路径）。

## 输入

- 审稿通过的完整稿件（标题 + 摘要 + 正文 + 封面图 + 配图）

## 输出

- 发布前检查结果
- 逐步提交操作指引
