---
name: aws-wechat-article-writing
description: Writes or rewrites long-form WeChat official account articles with structure, tone, and closing blocks. Use when the user asks to "写正文", "改写", "结构", "开头结尾", "公众号风格", or to turn an outline into a full draft.
---

# 长文写作

按选题/提纲或用户提供的正文，写出或改写为带结构的公众号长文（标题、摘要、小标题、段落、引用、文末引导）。配置约定见 aws-wechat-article-main 的 references。

## 步骤

1. **读配置**：文章风格、段落长度、小标题密度、金句/案例频率、文末引导模板、禁用词（见 config-schema）。  
2. **确定输入**：topics 的选题/标题/摘要，或用户直接给的提纲/正文。  
3. **写作或改写**：  
   - 输出完整结构：标题、摘要、小标题、段落、列表、引用、文末固定区块。  
   - 开头吸睛，可含金句或案例；语气与配置的调性一致；避免使用配置中的禁用词。  
4. **原创/转载**：按配置的原创/转载标注习惯处理文末署名。

## 输出

- 完整正文稿（Markdown），可直接交给 **aws-wechat-article-review**（写稿完成后即审稿），通过后再交给 **aws-wechat-article-formatting**、**aws-wechat-article-images**。  
- 或改写稿、结构提纲（若用户仅要提纲）。

## 输入来源

- 可选：aws-wechat-article-topics 的选题列表、标题多候选、摘要多候选。  
- 或用户直接提供的素材、提纲、已有正文。
