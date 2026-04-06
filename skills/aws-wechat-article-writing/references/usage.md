# 写作脚本用法

脚本位于 `{baseDir}/scripts/write.py`。

## 子命令

```bash
# 在仓库根执行；输入文件所在目录一般含本篇 article.yaml
python skills/aws-wechat-article-writing/scripts/write.py draft drafts/20260324-example/topic-card.md -o drafts/20260324-example/draft.md

# 改写已有文章
python skills/aws-wechat-article-writing/scripts/write.py rewrite article.md --instruction "改成口语化"

# 续写未完成的文章
python skills/aws-wechat-article-writing/scripts/write.py continue article.md -o article.md
```

## 模型配置

支持任何 OpenAI 兼容端点（官方、中转、自建均可）。

**须同时配置（与 `validate_env.py` 一致）**：在 **`.aws-article/config.yaml`** 填写 `writing_model`（`base_url`、`model` 必填；`provider`、`temperature`、`max_tokens` 可选），在仓库根 **`aws.env`** 仅填密钥 **`WRITING_MODEL_API_KEY`**。

```yaml
# .aws-article/config.yaml 片段
writing_model:
  provider: openai
  base_url: https://api.deepseek.com
  model: deepseek-chat
  temperature: 0.7
  max_tokens: 4000
```

```env
# aws.env
WRITING_MODEL_API_KEY=你的APIKey
```

常用端点参考：

| 服务 | base_url | 模型示例 |
|------|----------|----------|
| DeepSeek | `https://api.deepseek.com` | deepseek-chat |
| OpenAI | `https://api.openai.com` | gpt-4o |
| 智谱 | `https://open.bigmodel.cn/api/paas` | glm-4-flash |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode` | qwen-plus |
| Moonshot | `https://api.moonshot.cn` | moonshot-v1-8k |
| 中转/代理 | 你的中转地址 | 按中转服务支持的模型 |

## 写作约束（合并）

合并顺序：**`.aws-article/config.yaml`（顶层）** → 本篇 **`article.yaml`**（本篇覆盖同名字段）。须至少合并出非空约束（通常已有全局 `config.yaml`）。字段说明见 `skills/aws-wechat-article-main/references/articlescreening-schema.md`。

## 脚本行为

脚本将 **合并后的约束** + **`.aws-article/writing-spec.md`**（如有）+ 结构模板注入 system prompt。输出完整 Markdown 文章（含配图标记）。
