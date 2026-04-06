# 文末区块预设

本目录下的 `.md` 文件为**文末固定引导区块**。写作时按 config 的 `default_closing_block` 或 config 中的 `closing_block` 字符串加载。

## Schema

- 每个文件为一段 Markdown，用于文章末尾：关注引导、公众号名片、往期推荐、行动号召等。
- 可使用嵌入标记：`{embed:profile:名称}`、`{embed:miniprogram:名称}`、`{embed:miniprogram_card:名称}`、`{embed:link:名称}`。名片与小程序以 **`.aws-article/config.yaml`** 的 `embeds` 为准；**仅往期链接**可在本篇 `article.yaml` 写 `embeds.related_articles` 与全局合并（详见 [formatting SKILL](../../../../aws-wechat-article-formatting/SKILL.md)）。
- 文件名即预设名（不含后缀），如 `brand.md` → 预设名 `brand`。在 config 中设置 `default_closing_block: brand` 即可默认使用。

## 示例

见 `simple.example.md`。复制后重命名并按需修改。
