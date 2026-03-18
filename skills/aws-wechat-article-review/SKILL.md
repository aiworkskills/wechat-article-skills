---
name: aws-wechat-article-review
description: 审核微信公众号文章草稿，检查合规、敏感词、错别字和链接，输出固定格式的审稿清单。当用户提到「审稿」「合规」「敏感词」「检查」或写稿完成后使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-review
---

# 审稿与合规

**时机**：写稿完成后立即执行，通过后再排版配图；发布前可再做一次终审。

## 工作流

```
审稿进度：
- [ ] 第1步：读取配置
- [ ] 第2步：逐项检查
- [ ] 第3步：输出审稿结果
```

### 第1步：读取配置

从 `config.yaml` 读取：`review_required`、`custom_sensitive_words`、`forbidden_words`、`review_output_format`。

### 第2步：逐项检查

对标题、摘要、正文、图、链接执行检查：

| 检查项 | 检查内容 |
|--------|---------|
| 敏感词 | 配置中的 `custom_sensitive_words` + 通用敏感词 |
| 禁用词 | 配置中的 `forbidden_words` |
| 错别字 | 常见错别字、用词不当 |
| 标题 | 长度、是否含禁用套路、与正文一致性 |
| 摘要 | 长度、信息量、与正文一致性 |
| 链接 | 外链有效性 |
| 原创标注 | 是否按配置的 `original_attribution` 处理 |

详细检查清单：[references/checklist.md](references/checklist.md)

### 第3步：输出审稿结果

按配置的 `review_output_format` 选择输出格式：

- **分块详细**：按标题/摘要/正文/图/链接分块，逐项列出结论和修改建议
- **简要清单**：仅列出通过/未通过项和必须修改项

输出模板：[references/output-format.md](references/output-format.md)

## 产出

审稿清单与修改建议 → 交给用户确认 → 通过后进入 **aws-wechat-article-formatting** 和 **aws-wechat-article-images**。
