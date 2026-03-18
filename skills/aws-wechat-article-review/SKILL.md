---
name: aws-wechat-article-review
description: 审核公众号文章，检查敏感词、错别字、合规性和写作规范，输出修改清单。当用户提到「审稿」「审核」「检查一下」「校对」「合规」「敏感词」「错别字」「帮我看看」「写完了」「检查下有没有问题」「能不能发」时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-review
---

# 审稿与合规

对文章做系统性检查，发现问题并引导修改。

## 两种审稿模式

| 模式 | 时机 | 检查重点 |
|------|------|---------|
| **内容审** | writing 之后、formatting 之前 | 内容质量、写作规范、敏感词、配图标记 |
| **终审** | publish 之前 | 排版完整性、图片就位、发布要素齐全 |

自动识别：有 `article.html` → 终审模式，否则 → 内容审模式。

## 工作流

```
审稿进度：
- [ ] 第1步：读取配置与写作规范
- [ ] 第2步：逐项检查
- [ ] 第3步：输出审稿结果
- [ ] 第4步：修改循环 🔄
- [ ] 第5步：确认通过 → 保存定稿
```

### 第1步：读取配置与写作规范

从 `config.yaml` 读取：`review_required`、`custom_sensitive_words`、`forbidden_words`、`review_output_format`、`title_max_length`、`summary_length`、`forbidden_title_phrases`、`original_attribution`。

加载写作规范：`.aws-article/writing-spec.md`（如有）。

加载自定义检查规则：`.aws-article/presets/review-rules.yaml`（如有）。

### 第2步：逐项检查

按模式执行不同检查项，详见：[references/checklist.md](references/checklist.md)

**内容审** 检查 6 个维度：

| 维度 | 检查内容 |
|------|---------|
| **标题** | 长度、禁用套路、与正文一致性 |
| **摘要** | 长度、信息量、与正文一致性 |
| **正文** | 敏感词、禁用词、错别字、事实出处 |
| **写作规范** | 对照 writing-spec.md 检查用词、句式、段落、AI 味 |
| **配图标记** | 封面标记存在、数量与 image_density 匹配、描述清晰 |
| **原创标注** | 按 original_attribution 处理 |

**终审** 额外检查：

| 维度 | 检查内容 |
|------|---------|
| 排版 | article.html 存在且完整 |
| 图片 | imgs/ 下图片齐全、placeholder 已替换 |
| 发布要素 | 标题/摘要/作者/封面 全部就绪 |

### 第3步：输出审稿结果

按 `review_output_format` 输出：
- **分块详细**：按维度分块，逐项列 ✅/❌ + 修改建议
- **简要清单**：表格式，一行一项

输出模板：[references/output-format.md](references/output-format.md)

结果分三级：
- 🔴 **必须修改**：不改不能过（敏感词、严重错别字、缺封面）
- 🟡 **建议修改**：改了更好（用词优化、段落调整）
- 🟢 **通过**：无问题

### 第4步：修改循环 🔄

有 🔴 项时**必须进入修改循环**：

```
发现问题 → 展示审稿结果 → 等用户/agent 修改 → 重新检查 → 直到无 🔴
```

修改方式：
- Agent 直接修改 `draft.md`
- 用户手动修改后说「改好了」
- 调用 writing skill 的 rewrite 能力

每轮修改后自动重审被标记为 🔴 的项，不需要全量重审。

### 第5步：确认通过 → 保存定稿

全部 🔴 项消除后：
1. 展示最终审稿结果
2. 等待用户确认 ⛔
3. 将修改后的稿件保存为 `article.md`（定稿）

## 自定义检查规则

用户可在 `.aws-article/presets/review-rules.yaml` 添加自定义检查项：

```yaml
# .aws-article/presets/review-rules.yaml
custom_rules:
  - name: 品牌名称规范
    check: 正文中「XX公司」必须使用全称，不能简写
    level: 必须    # 必须 / 建议

  - name: 数据来源
    check: 所有引用的数据必须标注来源和日期
    level: 必须

  - name: CTA 检查
    check: 文末必须包含明确的行动号召
    level: 建议
```

自定义规则会追加到标准检查项之后执行。

## 过程文件

| 模式 | 读取 | 产出 |
|------|------|------|
| 内容审 | `draft.md`、`writing-spec.md` | `review.md`、`article.md`（定稿） |
| 终审 | `article.html`、`imgs/` | `review.md`（终审结果） |
