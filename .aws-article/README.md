# .aws-article 目录说明

本目录存放微信公众号运营的全局配置、预设、素材和文章过程文件。

## 目录结构

```
.aws-article/
├── config.yaml                  # 全局配置（必需）
├── config.example.yaml          # 配置示例
├── writing-spec.md              # 写作规范（可选）
├── writing-spec.example.md      # 写作规范示例
│
├── presets/                     # 用户自定义预设（可选，扩展或覆盖内置）
│   ├── formatting/              # 排版预设
│   ├── image-styles/            # 配图风格预设
│   └── title-styles/            # 标题风格预设
│
├── assets/                      # 素材库（可选）
│   ├── brand/                   # 品牌元素（头图、尾图、logo 等）
│   ├── covers/                  # 封面图素材
│   └── stock/                   # 通用素材图
│
└── templates/                   # 模板覆盖（可选）
    └── article-structure.md     # 覆盖默认文章结构模板
```

## 加载优先级

所有可自定义内容遵循统一优先级：

```
用户当次说法 > .aws-article/ 用户文件 > skill 内置默认
```

## 预设扩展

在 `presets/` 对应子目录下新建 `.md` 文件即可。文件名 = 预设名。

- 与内置预设**同名** → 覆盖内置
- 新名称 → 新增预设

## 安全说明

`config.yaml` 含敏感信息（API Key 等），已在 `.gitignore` 中排除。
