---
name: aws-wechat-article-topics
description: 为公众号找选题、起标题、写摘要，支持热点调研和系列策划。当用户提到「选题」「起标题」「取个标题」「写摘要」「排期」「爆款」「热点」「写什么好」「发什么」「本周选题」「内容日历」「系列」「专栏」「连载」「找个话题」「有什么好写的」时使用。
version: 0.2.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-topics
---

# 选题与标题

通过调研生成高质量选题，支持单篇和系列。

## 四种输入模式

根据用户输入自动识别模式：

| 模式 | 触发条件 | 示例 |
|------|---------|------|
| **A. 明确选题** | 用户给了具体话题 | 「写一篇 AI Agent 的文章」 |
| **B. 有方向** | 给了领域但没具体题目 | 「AI 最近有什么好写的」 |
| **C. 无方向** | 只说要选题 | 「这周写什么」「帮我找几个选题」 |
| **D. 系列策划** | 提到系列/专栏/连载 | 「做个 AI 入门系列」「写 10 篇专栏」 |

## 工作流

```
选题进度：
- [ ] 第1步：识别模式与读取配置
- [ ] 第2步：调研
- [ ] 第3步：生成选题
- [ ] 第4步：生成标题与大纲
- [ ] 第5步：展示并等待用户选择 ⛔
- [ ] 第6步：输出选题卡片
```

### 第1步：识别模式与读取配置 ⛔

`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`
⛔ 不存在 → [首次引导](../aws-wechat-article-main/references/first-time-setup.md)

✅ 存在 → 判断 A/B/C/D 模式，读取 config。

### 第2步：调研

使用 `web_search` 搜索 + `web_fetch` 深入阅读，为选题提供数据支撑。

| 模式 | 调研目标 |
|------|---------|
| A | 竞品文章怎么写、数据支撑、独特角度 |
| B | 该方向近期热点、读者关注什么 |
| C | config 领域的热点趋势 |
| D | 知识体系拆解、竞品系列分析、读者学习路径 |

各模式的搜索策略和搜索词模板：[references/research-strategy.md](references/research-strategy.md)

### 第3步：生成选题

基于调研结果：

| 模式 | 生成规则 |
|------|---------|
| A | 围绕用户主题，提供 3-4 个不同切入角度 |
| B/C | 筛选 3-5 个选题，标注类型（🔥热点 / 🌲常青 / 📚系列） |
| D | 规划系列总线 + 拆出每篇选题 |

### 第4步：生成标题与大纲

为每个选题生成完整的「选题卡片」：标题候选（3-5 个，混合风格）、切入角度、大纲预览、工作量评估、摘要候选。

**标题风格**：按优先级加载：
1. 用户指定（「用反问型」）
2. config `default_title_style`
3. `.aws-article/presets/title-styles/` 下的自定义风格
4. **fallback**：内置 5 种风格（悬念/干货/数字/反问/故事）混合生成，详见 [references/title-presets.md](references/title-presets.md)

输出模板：[references/output-format.md](references/output-format.md)

### 第5步：展示并等待用户选择 ⛔

**⚠️ 必须停下来等用户操作，不要自作主张继续。**

展示所有选题卡片后，提示用户：

```
请选择：
- 输入编号（如 1）→ 选定该选题
- 「调整 + 意见」→ 按意见修改后重新展示
- 「重新选」→ 换一批选题
- 「组合 1+3」→ 融合多个选题
- 系列模式：「先写第 N 篇」→ 按该篇进入写稿
```

**禁止的行为**：
- ❌ 不等用户选择就继续写稿
- ❌ 假设用户会选某个选题
- ❌ 跳过展示直接进入下一步

### 第6步：输出选题卡片

用户确认后：

1. **创建文章目录**：`{drafts_root}/{YYYY-MM-DD}-{标题slug}/`
2. 将选题卡片保存为 `topic-card.md`
3. 将调研摘要保存为 `research.md`
4. 系列模式：将系列规划保存到 `{series_root}/{系列slug}/plan.md`

→ 交给 **aws-wechat-article-writing**

## 过程文件

| 文件 | 说明 |
|------|------|
| `topic-card.md` | 选题卡片（标题、摘要、角度、大纲） |
| `research.md` | 调研摘要（搜索发现、竞品分析、数据点） |
