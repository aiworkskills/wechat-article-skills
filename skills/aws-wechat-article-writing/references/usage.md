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

# 业务资料库（最多 5 个路径；须形如 .aws-article/products/<产品名>/<文件名>.md，直接挂在产品根）
python skills/aws-wechat-article-writing/scripts/write.py draft drafts/foo/topic-card.md -o drafts/foo/draft.md \
  --reference .aws-article/products/公众号AI运营助手/项目介绍.md
```

## 模型配置（可选）

支持任何 OpenAI 兼容端点（官方、中转、自建均可）。

在 **`.aws-article/config.yaml`** 填写 `writing_model`（`base_url`、`model`；`provider`、`temperature`、`max_tokens` 可选），在仓库根 **`aws.env`** 仅填密钥 **`WRITING_MODEL_API_KEY`**。

**未配置时**：`draft`/`rewrite`/`continue` 以退出码 2 退出（`[NO_MODEL]`），可改用 `prompt` 子命令获取提示词后由 Agent 代写。

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

## 参考资料 `--reference`

- 可与 `draft` / `rewrite` / `continue` / `prompt` 共用；**重复 `--reference <路径>`，最多 5 个**。
- 路径必须形如 **`.aws-article/products/<产品名>/<文件名>.md`**（直接挂在产品根；脚本会校验）。**不接受** `images/` 子目录下的图片说明 `.md`，也**不接受**老路径 `assets/stock/references/`。
- 正文**全文**注入系统提示「参考资料库」，**不设脚本内截断**；若 API 报上下文/token 超限，请减少 `--reference` 篇数或缩短文档后重试。
- 模型输出要求：若依据某条资料，须在对应表述后附上与块内 **`资料路径：`** 反引号中**完全一致**的路径。

## `prompt` 子命令（不调 LLM）

```bash
# 只输出 system_prompt + user_prompt 的 JSON，不调用 LLM，不需要模型配置
python skills/aws-wechat-article-writing/scripts/write.py prompt draft drafts/20260324-example/topic-card.md
python skills/aws-wechat-article-writing/scripts/write.py prompt rewrite article.md --instruction "改成口语化"
python skills/aws-wechat-article-writing/scripts/write.py prompt continue article.md

# 与 draft 相同，可带 --reference 查看注入后的 system_prompt
python skills/aws-wechat-article-writing/scripts/write.py prompt draft drafts/foo/topic-card.md \
  --reference .aws-article/products/公众号AI运营助手/项目介绍.md
```

输出格式：`{"system_prompt": "...", "user_prompt": "..."}`

用途：模型未配置时，Agent 先通过此命令获取与 `draft`/`rewrite`/`continue` 完全相同的提示词，再按该提示词直接写文章。

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功（`draft`/`rewrite`/`continue` 输出文章；`prompt` 输出提示词 JSON） |
| 1 | 硬错误（API 失败、YAML 解析、文件缺失等） |
| 2 | 写作模型未配置（仅 `draft`/`rewrite`/`continue`），stderr 含 `[NO_MODEL]` |

## 脚本行为

脚本将 **合并后的约束** + **`.aws-article/writing-spec.md`**（如有）+ 结构模板注入 system prompt；若传入 **`--reference`**，再将 **`.aws-article/products/<产品名>/`** 根下对应 **`.md` 全文** 拼入「参考资料库」区块。输出完整 Markdown 文章（含配图标记）。
