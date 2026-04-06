# 标题风格预设

本目录下的 `.md` 文件为**标题风格预设**。选题生成标题时按 **`default_title_style`**（**须为 YAML 字符串列表**；多候选时由智能体择一，写回本篇 **`article.yaml`** 为**单元素列表**）或用户指定加载。

## Schema

- 每个文件描述一种标题风格：风格名、特点、适用场景、**示例句式或模板**（可含占位符如 XX、N）。
- 选题 skill 会混合多种风格生成标题候选；若指定本目录下的预设名，则优先按该风格的示例生成。
- 文件名即预设名（不含后缀）。内置风格见 [title-presets](../../../aws-wechat-article-topics/references/title-presets.md)：悬念型、干货型、数字型、反问型、故事型。

## 示例

见 `suspense.example.md`。复制后重命名并按需修改。
