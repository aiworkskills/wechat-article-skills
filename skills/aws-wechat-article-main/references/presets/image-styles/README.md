# 配图风格预设

本目录下的 `.md` 文件为**配图风格预设**。生成配图时按合并配置中的 **`custom_cover_image_style`** > **`default_cover_image_style`**、**`custom_article_image_style`** > **`default_article_image_style`**（**须为 YAML 字符串列表**；`custom_*` 非空时优先；多候选须在本篇 **`article.yaml`** 同键改为**单元素列表**）加载对应 `.md`；未配置时按用户指定或自动推荐。

## Schema

- 每个文件描述一种视觉风格：风格名、描述、适用场景、**prompt 要点或关键词**（供 Agent/脚本生成图片时使用）。
- 完整风格库与 Type×Style 矩阵见 [styles.md](../../../../aws-wechat-article-images/references/image-styles/styles.md)。可基于内置风格名（如 `flat-vector`、`notion-line`）写简短说明与约束。
- 文件名即预设名（不含后缀）。

## 示例

见 `flat-vector.example.md`。复制后重命名并按需修改。
