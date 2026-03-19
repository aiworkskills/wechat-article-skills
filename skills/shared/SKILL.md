---
name: aws-wechat-shared
description: 公众号 skill 共享资源：发布脚本、图片生成脚本、Type×Style 图片风格体系。由其他 skill 引用，不直接面向用户。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#shared
---

# 共享资源

供其他 skill 引用的脚本和图片风格体系，不直接面向用户。

## 脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| publish.py | `{baseDir}/scripts/publish.py` | 微信公众号 API 发布（上传图片、创建草稿、群发） |
| image-gen.py | `{baseDir}/scripts/image-gen.py` | 调用 OpenAI 兼容 API 生成图片 |

### publish.py

```bash
python {baseDir}/scripts/publish.py check                  # 环境检查
python {baseDir}/scripts/publish.py token                  # 获取 access_token
python {baseDir}/scripts/publish.py upload-thumb <img>     # 上传封面
python {baseDir}/scripts/publish.py upload-content-image <img>  # 上传正文图
python {baseDir}/scripts/publish.py create-draft <yaml>    # 创建草稿
python {baseDir}/scripts/publish.py full <dir>             # 完整发布流程
python {baseDir}/scripts/publish.py full <dir> --publish   # 含群发
python {baseDir}/scripts/publish.py --account <alias> full <dir>  # 指定账号
python {baseDir}/scripts/publish.py accounts               # 列出账号
python {baseDir}/scripts/publish.py recent-articles        # 最近文章
```

### image-gen.py

```bash
python {baseDir}/scripts/image-gen.py generate <prompt.md> -o <out.png>  # 单图
python {baseDir}/scripts/image-gen.py batch <dir> -o <out-dir>           # 批量
python {baseDir}/scripts/image-gen.py test                               # 连通性测试
```

## Type × Style 图片风格体系

| 文件 | 用途 |
|------|------|
| [image-styles/styles.md](image-styles/styles.md) | 14 种视觉风格完整列表 |
| [image-styles/auto-selection.md](image-styles/auto-selection.md) | 自动风格匹配规则 |
| [image-styles/prompt-construction.md](image-styles/prompt-construction.md) | Prompt 构建模板 |
| [image-styles/style-presets.md](image-styles/style-presets.md) | 预设组合速查 |
