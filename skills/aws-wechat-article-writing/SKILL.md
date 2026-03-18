---
name: aws-wechat-article-writing
description: 为微信公众号写作或改写长文，支持调用第三方模型（DeepSeek/OpenAI/通义千问等）生成初稿，并按用户自定义写作规范约束输出。当用户提到「写正文」「改写」「公众号风格」「结构」「开头结尾」或需要将提纲变成完整文章时使用。
version: 0.2.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-writing
---

# 长文写作

按选题卡片或用户素材写出公众号长文。支持调用第三方模型生成 + 用户自定义写作规范。

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

| 脚本 | 用途 |
|------|------|
| `scripts/write.py` | 调用第三方 LLM 写文章 |

## 两种写作方式

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| **Agent 直写** | 当前 agent 直接写 | 简单改写、短文、agent 模型能力够用 |
| **调用第三方模型** | 通过脚本调用配置的 LLM API | 长文初稿、需要特定模型风格、模型能力更强 |

Agent 根据任务复杂度自动判断，或由用户指定「用 DeepSeek 写」「用 GPT 写」。

## 写作规范

用户可创建自定义写作规范文件，**所有写作（无论哪种方式）都必须遵守**。

| 优先级 | 来源 |
|--------|------|
| 1（最高）| 用户当次对话中的要求 |
| 2 | 项目 `.aws-article/writing-spec.md` |
| 3 | 用户 `~/.aws-article/writing-spec.md` |
| 4 | config.yaml 中的写作配置 |

写作规范示例：`.aws-article/writing-spec.example.md`

规范可包含：用词规范、句式偏好、段落规范、标题规范、禁止事项、品牌调性等。

## 工作流

```
写稿进度：
- [ ] 第1步：读取配置与写作规范
- [ ] 第2步：确定输入与写作方式
- [ ] 第3步：写作
- [ ] 第4步：自检与修正
- [ ] 第5步：展示并等待用户确认 ⛔
```

### 第1步：读取配置与写作规范

从 `config.yaml` 读取：
- 写作配置：`article_style`、`tone`、`paragraph_preference`、`heading_density`、`closing_block`、`forbidden_words`、`original_attribution`
- 模型配置：`writing_model`（provider、model、api_key 等）

加载写作规范：`.aws-article/writing-spec.md`

### 第2步：确定输入与写作方式

**输入来源**（任选其一）：
- aws-wechat-article-topics 的选题卡片
- 用户提供的提纲、素材或已有正文
- 用户口述的主题

**写作方式判断**：
- 用户指定了模型 → 用第三方模型
- 输入是完整选题卡片且需要长文 → 推荐第三方模型
- 简单改写或短内容 → Agent 直写

### 第3步：写作

#### Agent 直写

按写作规范 + 结构模板直接输出。

结构模板：[references/structure-template.md](references/structure-template.md)

#### 调用第三方模型

```bash
# 按选题卡片写初稿
python {baseDir}/scripts/write.py draft topic_card.md -o drafts/article.md

# 改写已有文章
python {baseDir}/scripts/write.py rewrite article.md --instruction "改成口语化"

# 续写未完成的文章
python {baseDir}/scripts/write.py continue article.md
```

脚本自动将 config + 写作规范 + 结构模板注入到模型的 system prompt 中。

### 第4步：自检与修正

初稿生成后，按写作规范做一轮自检：
- 是否有禁用词/AI 味表达
- 段落长度是否符合要求
- 开头是否吸睛
- 结尾是否有力
- 小标题密度是否达标

发现问题则自动修正。

### 第5步：展示并等待用户确认 ⛔

将文章展示给用户，等待反馈：
- 「通过」→ 交给 review 审稿
- 提出修改意见 → 按意见修改后重新展示
- 「重写」→ 用不同角度或模型重新生成

## 支持的模型

| Provider | 默认模型 | 端点 |
|----------|---------|------|
| `deepseek` | deepseek-chat | api.deepseek.com |
| `openai` | gpt-4o | api.openai.com |
| `zhipu` | glm-4-flash | open.bigmodel.cn |
| `qwen` | qwen-plus | dashscope.aliyuncs.com |
| `moonshot` | moonshot-v1-8k | api.moonshot.cn |
| `custom` | 自定义 | 自定义 base_url |

所有 provider 使用 OpenAI 兼容格式（Chat Completions API）。

## 输出格式

```markdown
# [文章标题]

> [摘要，80-150字]

## [小标题一]

[正文段落……]

## [小标题二]

[正文段落……]

## 写在最后

[结尾段落]

---

[文末引导语]
```

产出后交给 **aws-wechat-article-review** 审稿。
