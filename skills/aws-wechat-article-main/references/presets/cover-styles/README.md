# 封面配图风格预设（仓库侧说明）

内置封面预设随 **`aws-wechat-article-images`** 提供，路径为 **`references/cover-styles/`**。本目录说明如何在仓库里**扩展或覆盖**封面风格。

## 放置位置

- **日常自定义**：`.aws-article/presets/cover-styles/<名>.md`
- **`.aws` 预设包**：包内包含 **`cover-styles/`** 目录，由 `import_presets_aws.py` 合并到上述路径。

## 配置键

- **`default_cover_image_style`**：账号级默认候选（YAML 字符串列表）
- **`custom_cover_image_style`**：非空时覆盖同名 **`default_*`**
- **本篇 `article.yaml`**：同名键再覆盖全局

合并后须收窄为**单元素列表**再跑配图流程。完整规则见 [articlescreening-schema.md](../../articlescreening-schema.md) 与 **`config.example.yaml`**。

## Schema 与示例

字段结构与内置一致，见 [cover-styles/README.md](../../../../aws-wechat-article-images/references/cover-styles/README.md)。可将本目录下的 `*.example.md` 复制到 `.aws-article/presets/cover-styles/` 后去掉 `.example` 再按需修改。
