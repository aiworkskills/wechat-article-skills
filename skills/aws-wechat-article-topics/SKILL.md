---
name: aws-wechat-article-topics
description: Produces topic ideas, multiple title candidates, and summary candidates for WeChat official account articles. Use when the user asks for "选题", "起标题", "摘要", "爆款", "排期", or needs a content calendar.
---

# 选题与标题

产出选题列表、标题多候选、摘要多候选；可选排期（本周/本月选题 + 建议发布时间）。配置约定见 aws-wechat-article-main 的 references。

## 步骤

1. **读配置**：账号类型、选题方向/禁区、标题风格、摘要长度、禁用标题套路（见 config-schema）。  
2. **产出选题列表**：按用户当次需求（如「5 个选题」「本周排期」）生成，可结合热点/常青/系列。  
3. **标题多候选**：每个选题给出 3–5 个标题，风格可区分（悬念型、干货型、数字型、反问型、故事型等）。  
4. **摘要多候选**：每个选题或选定标题给出 1–3 个摘要，控制在配置的摘要长度范围内。  
5. 若有**排期**需求：产出「本周/本月选题 + 建议发布时间」。

## 输出格式

- 选题列表：标题式一行一个，可带一句话说明。  
- 标题候选：明确标出 3–5 个，便于 writing 或用户选用。  
- 摘要候选：1–3 个，字数符合配置。  

便于下游 **aws-wechat-article-writing** 或用户直接选用。

## 标题风格预设（可选）

| 风格 | 特点 |
|------|------|
| 悬念型 | 制造信息差或认知冲突 |
| 干货型 | 直接给结论、承诺价值 |
| 数字型 | 用数字增强可信度 |
| 反问型 | 用问句引发思考 |
| 故事型 | 场景或故事感 |

禁用套路示例：浅谈、万字长文、建议收藏、震惊等（以配置为准）。
