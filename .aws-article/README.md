# .aws-article 目录说明

本目录存放微信公众号运营的全局配置、预设、素材。

## 目录结构

```
.aws-article/
├── config.yaml                  # 全局配置（必需）
├── config.example.yaml          # 配置示例
├── writing-spec.md              # 写作规范（可选）
├── writing-spec.example.md      # 写作规范示例
│
├── presets/                     # 用户自定义预设
│   ├── structures/              # 文章结构预设
│   ├── closing-blocks/          # 文末区块预设
│   ├── title-styles/            # 标题风格预设
│   ├── formatting/              # 排版主题预设（YAML）
│   ├── image-styles/            # 配图风格预设
│   └── sticker-styles/          # 贴图风格预设
│
├── assets/                      # 素材库
│   ├── brand/                   # 品牌元素（头图、尾图、logo）
│   ├── covers/                  # 封面图素材
│   └── stock/                   # 通用素材图
│
└── templates/                   # 模板覆盖（保留）
```

## 预设系统

**每个预设目录下都有 README.md 说明 schema**——按 schema 创建文件放进去即可使用。

### 加载优先级

所有预设类型统一遵循：

```
用户当次说法 > config 默认值 > .aws-article/presets/ 用户文件 > skill 内置 fallback
```

### 使用方式

1. 读目录下的 README.md 了解 schema
2. 按 schema 创建 `.md` 或 `.yaml` 文件
3. 在 config.yaml 中设置默认预设名（可选）
4. 或对话时直接说「用 XX 预设」

### config 中的默认预设键

| 键 | 对应目录 | 用在 |
|----|---------|------|
| `default_structure` | `presets/structures/` | 写作 |
| `default_closing_block` | `presets/closing-blocks/` | 写作 |
| `default_title_style` | `presets/title-styles/` | 选题 |
| `default_format_preset` | `presets/formatting/` | 排版 |
| `default_image_style` | `presets/image-styles/` | 配图 |
| `default_sticker_style` | `presets/sticker-styles/` | 贴图 |

## 安全说明

`config.yaml`（含 API Key 等敏感信息）和所有用户自定义文件已在 `.gitignore` 中排除。
