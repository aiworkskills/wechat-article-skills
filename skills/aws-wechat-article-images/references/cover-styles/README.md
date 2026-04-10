# 封面风格预设

本目录下的 `.md` 文件为**封面风格预设**（内置）。用户自定义预设放在 `.aws-article/presets/cover-styles/` 下。

## 加载规则

生成封面时按 **`article.yaml` > `custom_cover_image_style` > `default_cover_image_style`** 合并后的预设名加载对应 `.md`（`custom_*` 非空时覆盖同名 `default_*`；须收窄为单元素列表后再执行配图）。

**预设发现**：Agent 运行时扫描两个目录合并可用列表：

1. **内置**：`skills/aws-wechat-article-images/references/cover-styles/`（随 skill 安装）
2. **用户自定义**：`.aws-article/presets/cover-styles/`（用户创建或由 `.aws` 预设包导入）

用户自定义同名文件优先于内置。

## Schema

每个 `.md` 文件描述一种封面视觉风格：

```markdown
# 风格名

## 描述
[1-2 句视觉风格描述]

## 适用场景
[适合什么类型的文章/账号]

## Prompt 要点
- [视觉关键词，直接用于生图 prompt]
- [构图/色彩/氛围等具体指导]
- 画面内文字必须为中文，在 prompt 中直接写出要显示的中文文案
```

- 文件名即预设名（不含后缀），如 `简约.md` → 预设名 `简约`。
- `Prompt 要点` 部分会被 Agent 直接嵌入封面 prompt 的「风格」字段。
- 每个预设自包含视觉风格描述，无须引用外部 Style 维度。

## 示例

见同目录下的 `.example.md` 文件。复制到 `.aws-article/presets/cover-styles/` 并重命名为 `.md` 后按需修改。
