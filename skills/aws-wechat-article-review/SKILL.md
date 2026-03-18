---
name: aws-wechat-article-review
description: Reviews WeChat article drafts for compliance, sensitive words, and pre-publish checks; outputs a fixed-format checklist. Use when the user asks for "审稿", "合规", "敏感词", "发布前检查", or after writing is done.
---

# 审稿与合规

**时机**：**写稿完成后即应执行**（早于排版与配图），先审内容与合规，通过后再做排版、配图；发布前可再做一次终审（可选）。

## 步骤

1. **读配置**：必检项、自定义敏感词/禁用词表、审稿输出格式（见 aws-wechat-article-main 的 config-schema）。  
2. **检查**：对标题、摘要、正文、图、链接做检查（敏感词、错别字、链接有效性、原创标注等；事实与出处按配置的核查级别）。  
3. **输出**：固定格式的审稿结果（如「标题/摘要/正文/图」分块 + 修改建议列表），可当 brief 用。

## 在流程中的位置

- **writing** 产出正文后即可调用；通过后再进入 **formatting**、**images**。  
- 发布前可再次调用做终审。

## References

- [references/checklist.md](references/checklist.md)：发布前检查项。  
- [references/output-format.md](references/output-format.md)：审稿输出模板。

## 产出

审稿清单与修改建议，格式统一，便于协作与交给 **aws-wechat-article-publish**。
