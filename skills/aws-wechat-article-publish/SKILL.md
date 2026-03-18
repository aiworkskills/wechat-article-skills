---
name: aws-wechat-article-publish
description: Provides pre-publish checklist and instructions for submitting content to WeChat official account backend. Use when the user asks to "发布公众号", "发布", "提交", or needs the final step before going live.
---

# 发布入口

**必做**：发布前检查清单 + 如何提交到后台（复制粘贴步骤或自建脚本/API 说明）。**可选**：脚本或 API 调用（当前可不实现，仅预留说明）。

## 输入与输出

- **输入**：review 通过的稿子（正文 + 标题/摘要/图等）。  
- **输出**：检查清单执行结果 + 提交方式指引；用户能按清单自检并按文档完成提交。

## 发布前检查

执行 [references/pre-publish-checklist.md](references/pre-publish-checklist.md) 中的项，与 review 衔接；确认无误后再提交。

## 提交方式

按 [references/submit-guide.md](references/submit-guide.md) 执行：手动复制粘贴步骤，或自建脚本/API 的调用说明。若实现脚本或 API，在 submit-guide 中说明用法与注意点。
