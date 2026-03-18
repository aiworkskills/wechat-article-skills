---
name: aws-wechat-article-topics
description: 为微信公众号产出选题列表、标题多候选和摘要多候选，可选内容排期。当用户提到「选题」「起标题」「摘要」「排期」「爆款」「内容日历」或需要文章选题时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-topics
---

# 选题与标题

产出选题列表、标题多候选、摘要多候选；可选排期。

## 工作流

```
选题进度：
- [ ] 第1步：读取配置
- [ ] 第2步：产出选题列表
- [ ] 第3步：标题多候选
- [ ] 第4步：摘要多候选
- [ ] 第5步：排期（可选）
```

### 第1步：读取配置

从 `config.yaml` 读取：`account_type`、`target_reader`、`tone`、`topic_direction`、`title_style`、`title_max_length`、`summary_length`、`forbidden_title_phrases`。

无配置时触发首次引导（见 aws-wechat-article-main）。

### 第2步：产出选题列表

按用户需求（如「5 个选题」「本周排期」）生成选题，可结合：
- **热点型**：当下热门话题
- **常青型**：长期有价值的内容
- **系列型**：可连载的主题

### 第3步：标题多候选

每个选题给出 3–5 个标题候选，按不同风格区分。

标题风格详见：[references/title-presets.md](references/title-presets.md)

### 第4步：摘要多候选

每个选题或选定标题给出 2–3 个摘要候选，字数控制在配置的 `summary_length` 范围内。

### 第5步：排期（可选）

若用户需要排期，产出「本周/本月选题 + 建议发布时间」。

## 输出格式

```markdown
## 选题列表

### 选题 1：[选题名称]
> 一句话说明选题角度与目标读者痛点

**标题候选：**
1. 【干货型】为什么 90% 的人学不会 XXX？因为忽略了这 3 点
2. 【悬念型】我用了这个方法后，XXX 效率翻了 3 倍
3. 【数字型】5 个立刻能用的 XXX 技巧，第 3 个最实用
4. 【反问型】你还在用老方法做 XXX？难怪效果差

**摘要候选：**
1. 很多人在 XXX 上踩过坑，本文总结了 3 个核心方法……（86字）
2. 从入门到上手，一篇讲透 XXX 的底层逻辑……（92字）

---

### 选题 2：[选题名称]
...
```

产出后交给 **aws-wechat-article-writing** 或由用户选用。
