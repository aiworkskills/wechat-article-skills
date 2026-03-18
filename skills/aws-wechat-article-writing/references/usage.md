# 写作脚本用法

脚本位于 `{baseDir}/scripts/write.py`。

## 子命令

```bash
# 按选题卡片写初稿
python write.py draft topic_card.md -o drafts/article.md

# 改写已有文章
python write.py rewrite article.md --instruction "改成口语化"

# 续写未完成的文章
python write.py continue article.md -o article.md
```

## 模型配置

支持任何 OpenAI 兼容端点（官方、中转、自建均可），在 `config.yaml` 中配置：

```yaml
writing_model:
  base_url: "https://api.deepseek.com"   # API 端点
  api_key: ""                             # API Key
  model: "deepseek-chat"                  # 模型名
  temperature: 0.7
  max_tokens: 4000
```

常用端点参考：

| 服务 | base_url | 模型示例 |
|------|----------|---------|
| DeepSeek | `https://api.deepseek.com` | deepseek-chat |
| OpenAI | `https://api.openai.com` | gpt-4o |
| 智谱 | `https://open.bigmodel.cn/api/paas` | glm-4-flash |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode` | qwen-plus |
| Moonshot | `https://api.moonshot.cn` | moonshot-v1-8k |
| 中转/代理 | 你的中转地址 | 按中转服务支持的模型 |

## 脚本行为

脚本自动将 config + 写作规范 + 结构模板注入 system prompt。输出完整 Markdown 文章（含配图标记）。
