---
name: aws-wechat-article-topics
description: 公众号选题｜爆款标题｜热点追踪｜系列策划 — 公众号 AI 选题与标题生成，覆盖热点调研、选题策划、起标题、写摘要、系列排期。面向自媒体编辑、内容运营。触发词（**单独触发仅限对已有标题/摘要的修改**）：「改标题」「换个标题」「重起标题」「优化标题」「标题再想想」「换个标题试试」「改摘要」「重写摘要」「优化摘要」「摘要再优化下」。新做选题、起新标题、策划系列/内容日历、追热点都请走 aws-wechat-article-main；需要多环节串联（写+审+排+配图+发）也走 main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 选题与标题

**公众号选题 & 爆款标题 AI 助手** —— 热点追踪、选题调研、起标题、写摘要、系列排期一次搞定。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 主要由 Agent 驱动（对话式选题调研、标题生成），脚本层只用于更新本篇元数据。

- **凭证**：无
- **网络**：Agent 可能使用 `web_search` / `web_fetch`（宿主内置能力，非本 skill 脚本层发起）。**本 skill 不调任何需要凭证的接口**——查已发布文章要微信凭证，那是 [publish](../aws-wechat-article-publish/SKILL.md) 的事
- **文件读**：`.aws-article/config.yaml`、本篇 `article.yaml`、`.aws-article/products/{产品名}/*.md`（选题涉及用户业务时必读）
- **文件写**：本篇目录下 `topic-card.md`、`research.md`、`article.yaml`；系列模式下 `{series_root}/{系列slug}/plan.md`
- **shell**：只可能调 `{python} {baseDir}/../aws-wechat-article-publish/scripts/article_init.py`（纯本地写 YAML，不联网）

## 路由

要成文并发到公众号、或「今天发什么」需整条编排 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。本 skill 单独触发仅限**已有标题/摘要的修改**。

## 配置检查 ⛔

任何操作前先按 **[首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)** 执行，通过后才继续（或用户明确书面确认「本次不检查」）。

## 四种输入模式

| 模式 | 触发条件 | 示例 |
|------|---------|------|
| **A. 明确选题** | 用户给了具体话题 | 「写一篇 AI Agent 的文章」 |
| **B. 有方向** | 给了领域但没具体题目 | 「AI 最近有什么好写的」 |
| **C. 无方向** | 只说要选题 | 「这周写什么」「帮我找几个选题」 |
| **D. 系列策划** | 提到系列/专栏/连载 | 「做个 AI 入门系列」「写 10 篇专栏」 |

## 工作流

```
选题进度：
- [ ] 第1步：⛔ 配置检查
- [ ] 第2步：⛔ 全局账号三键
- [ ] 第3步：⛔ 归类 A/B/C/D（先于任何联网调研）
- [ ] 第4步：调研
- [ ] 第5步：生成选题
- [ ] 第6步：生成标题与大纲
- [ ] 第7步：⛔ 展示并等用户选
- [ ] 第8步：落盘（topic-card.md + research.md + article.yaml）
```

一条龙下哪几步可以省、单独使用时要补什么，见 [branches.md「一」](references/branches.md)。

### 第2步：全局账号三键 ⛔

**在调用 `web_search`、调研或与用户确认方向之前**，打开 `.aws-article/config.yaml`，检查 `article_category`、`target_reader`、`default_author` 是否 **trim 后均非空**。任一项缺失：**逐项询问用户**，取得当轮明确答复后**写回该文件**。

**禁止**从 `article.yaml` 或其它草稿擅自抄录填充。与 [main「2) 全局账号约束」](../aws-wechat-article-main/SKILL.md) 一致。

### 第3步：归类 A/B/C/D ⛔

**在联网调研之前**先与用户对齐：是**已有**具体主题、**只有**大致领域、**完全没想法**，还是要做**系列/专栏**。

用户本条消息已说清（直接给出话题、或明确说「这周帮我找几个选题」）→ **简短确认**即可，不必重复盘问。

**禁止**：用户仍处于「只说找选题、没说领域/偏好」的模糊状态时就开始联网调研——搜出来的东西没有收敛方向，只会浪费一轮。

### 第4步：调研

**先读 `.aws-article/config.yaml`**：选题边界、`topic_direction`、`update_frequency`、账号定位以它为准。本篇目录已有 `article.yaml`（例如已定题）时一并读 `title` / `digest`，避免与后序冲突。

选题涉及用户自身业务时须读业务资料库，口径见 [branches.md「三」](references/branches.md)。

用 `web_search` 搜 + `web_fetch` 深读，为选题提供数据支撑：

| 模式 | 调研目标 |
|------|----------|
| A | 竞品文章怎么写、数据支撑、独特角度 |
| B | 该方向近期热点、读者关注什么 |
| C | `config.yaml` 的账号定位、`topic_direction` 与近期热点 |
| D | 知识体系拆解、竞品系列分析、读者学习路径 |

各模式的搜索策略与搜索词模板见 [references/research-strategy.md](references/research-strategy.md)。

### 第5步：生成选题

数量用 `config.yaml` 的 `update_frequency` 控制：周更约 3–5 个，日更略多，月更略少；无配置时按对话约定。

| 模式 | 生成规则 |
|------|----------|
| A | 围绕用户主题，给 3-4 个不同切入角度 |
| B/C | 筛 3-5 个选题，标类型（🔥热点 / 🌲常青 / 📚系列） |
| D | 规划系列总线 + 拆出每篇选题（见 [branches.md「四」](references/branches.md)） |

### 第6步：生成标题与大纲

每个选题出一张**选题卡片**：标题候选（3-5 个，混合风格）、切入角度、大纲预览、工作量评估、摘要候选。输出模板见 [references/output-format.md](references/output-format.md)。

**标题风格**的加载优先级与多候选收敛规则见 [branches.md「二」](references/branches.md)；内置 5 种风格（悬念/干货/数字/反问/故事）见 [references/title-presets.md](references/title-presets.md)。

**摘要候选**要能独立成立：它会进 `article.yaml` 的 `digest`，显示在后台文章列表里。**别写成正文开头那段的复述**——正文首个 `>` 导语是另一段文字，两者逐字相同的话读者等于同一段读两遍（[review](../aws-wechat-article-review/SKILL.md) 会拦这一条）。

### 第7步：展示并等用户选 ⛔

**必须停下来等用户操作。** 展示所有选题卡片后提示：

```
请选择：
- 输入编号（如 1）→ 选定该选题
- 「调整 + 意见」→ 按意见修改后重新展示
- 「重新选」→ 换一批选题
- 「组合 1+3」→ 融合多个选题
- 系列模式：「先写第 N 篇」→ 按该篇进入写稿
```

**禁止**：不等用户选就继续写稿；假设用户会选某一个；跳过展示直接进下一步。

### 第8步：落盘

用户确认后：

1. **文章目录**：main 已建好目录且内含 `article.yaml` → **不要改目录名**，直接往里写。否则创建 `{drafts_root}/{YYYYMMDD}-{标题slug}/`（`drafts_root` / `series_root` 以 `config.yaml` 为准）。
2. 选题卡片 → `topic-card.md`
3. 调研摘要 → `research.md`
4. 系列模式：系列规划 → `{series_root}/{系列slug}/plan.md`
5. **`article.yaml`**：同目录若无、或已定题信息需更新，**本步必须创建或补全**（`publish_completed: false`；标题、摘要与用户选定一致时写入）：

   ```bash
   {python} {baseDir}/../aws-wechat-article-publish/scripts/article_init.py <本篇目录> --title "…" --digest "…"
   ```

→ 交给 [aws-wechat-article-writing](../aws-wechat-article-writing/SKILL.md)。须已具备 `.aws-article/config.yaml`，本篇目录建议已有 `article.yaml`。

## 分支与细则

一条龙 vs 单独使用、预设候选池收敛、业务资料库、系列策划、文末推荐链接归谁做 → [references/branches.md](references/branches.md)。

## 过程文件

| 文件 | 说明 |
|------|------|
| `.aws-article/config.yaml` | 全局账号与选题/文风约束；选题全程以之为准 |
| `article.yaml` | 本篇元数据与 `publish_completed`；新建本篇须 `false` |
| `topic-card.md` | 选题卡片（标题、摘要、角度、大纲） |
| `research.md` | 调研摘要（搜索发现、竞品分析、数据点） |
