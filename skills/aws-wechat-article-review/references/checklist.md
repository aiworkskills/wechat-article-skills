# 审稿检查清单

按配置 `review_required` 执行，以下为全量检查项。

## 标题

- [ ] 字数不超过 `title_max_length`
- [ ] 不含 `forbidden_title_phrases` 中的套路
- [ ] 与正文内容一致，不做标题党

## 摘要

- [ ] 字数在 `summary_length` 范围内
- [ ] 能概括文章核心价值
- [ ] 与正文内容一致

## 正文

- [ ] 不含 `custom_sensitive_words` 和 `forbidden_words`
- [ ] 无明显错别字和语病
- [ ] 事实与数据有出处（如适用）
- [ ] 原创/转载标注按 `original_attribution` 处理

## 图片

- [ ] 封面图已指定或待生成
- [ ] 正文配图位置合理
- [ ] 图注格式符合 `caption_style`

## 链接

- [ ] 外链格式正确
- [ ] 无死链（如可检测）
