# 微信公众号自动运营 Skills

8 个 skill + 共享资源，组成公众号内容全流程工具链。运行在 Cursor / OpenClaw 上。

## 长文流程

```
选题 → 写稿 → 审稿 → 排版 → 配图 → 终审 → 发布
```

## 贴图流程

```
选题 → 贴图创作 → 审稿 → 发布
```

## Skill 列表

| 目录 | 职责 |
|------|------|
| **aws-wechat-article-main** | 总览与路由，管理长文全流程 |
| **aws-wechat-article-topics** | 选题与标题（调研驱动，四种模式） |
| **aws-wechat-article-writing** | 长文写作（支持第三方模型） |
| **aws-wechat-article-review** | 审稿与合规（内容审 + 终审） |
| **aws-wechat-article-formatting** | 排版（Markdown → 微信 HTML） |
| **aws-wechat-article-images** | 长文配图（Type × Style 体系） |
| **aws-wechat-article-publish** | 发布（API + 手动） |
| **aws-wechat-sticker** | 贴图/多图推送（独立流程） |

## 共享资源

| 目录 | 内容 | 谁在用 |
|------|------|--------|
| `shared/image-styles/` | Type × Style 体系（风格库、预设、prompt 模板） | images + sticker |
| `shared/scripts/publish.py` | 微信公众号 API 发布脚本 | publish + sticker |

## 安装

```bash
bash scripts/install-skills.sh
```

将所有 skill + shared 安装到 `.cursor/skills/`。

## 配置

所有 skill 共享一份配置文件 `config.yaml` + 用户自定义内容，详见 `.aws-article/README.md`。
