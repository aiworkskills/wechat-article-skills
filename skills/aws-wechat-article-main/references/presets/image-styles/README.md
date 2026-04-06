# 正文配图风格预设

本目录下的 `.md` 文件为**正文配图风格预设**。生成正文配图时按 **`custom_article_image_style`**（本篇 **`article.yaml`** > **`config.yaml`**；**须为 YAML 字符串列表**；多候选须在本篇改为**单元素列表**）加载对应 `.md`；未配置时按用户指定或自动推荐。

> **封面风格预设**在 `skills/aws-wechat-article-images/references/cover-styles/`，与正文配图预设分开管理。

## Schema

- 每个文件描述一种视觉风格：风格名、描述、适用场景、**prompt 要点或关键词**（供 Agent/脚本生成图片时使用）。
- 正文配图风格库见 [styles.md](../../../../aws-wechat-article-images/references/image-styles/styles.md)。
- 文件名即预设名（不含后缀）。

## 示例

见 `flat-vector.example.md`。复制后重命名并按需修改。
