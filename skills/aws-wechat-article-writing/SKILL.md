---
name: aws-wechat-article-writing
description: 为微信公众号写作或改写长文，包含结构、调性、开头结尾和文末引导。当用户提到「写正文」「改写」「公众号风格」「结构」「开头结尾」或需要将提纲变成完整文章时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-writing
---

# 长文写作

按选题/提纲或用户提供的素材，写出或改写为公众号长文。

## 工作流

```
写稿进度：
- [ ] 第1步：读取配置
- [ ] 第2步：确定输入
- [ ] 第3步：写作或改写
- [ ] 第4步：产出完整正文
```

### 第1步：读取配置

从 `config.yaml` 读取：`article_style`、`tone`、`paragraph_preference`、`heading_density`、`closing_block`、`forbidden_words`、`original_attribution`。

### 第2步：确定输入

输入来源（任选其一）：
- aws-wechat-article-topics 的选题/标题/摘要
- 用户直接提供的提纲、素材或已有正文
- 用户口述的主题

### 第3步：写作或改写

按文章结构模板写作，详见：[references/structure-template.md](references/structure-template.md)

**写作要求**：
- 开头 2-3 句必须吸睛：可用提问、场景、数据或金句切入
- 语气与配置的 `tone` 一致
- 段落长度遵循 `paragraph_preference`
- 小标题密度遵循 `heading_density`
- 避免使用 `forbidden_words` 中的词
- 文末按 `closing_block` 和 `original_attribution` 处理

### 第4步：产出完整正文

输出为 Markdown 格式的完整正文，包含标题、摘要、正文、文末区块。

## 输出格式

```markdown
# [文章标题]

> [摘要，80-150字]

## [小标题一]

[正文段落……]

## [小标题二]

[正文段落……]

……

## 写在最后

[结尾段落：总结 + 金句或行动号召]

---

[文末引导语：如关注提示、往期推荐等]
```

产出后即交给 **aws-wechat-article-review** 审稿，通过后再排版配图。
