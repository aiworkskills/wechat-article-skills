---
name: aws-wechat-article-publish
description: 将文章发布到微信公众号，支持 API 发布和手动提交，含发布前检查。当用户提到「发布」「提交」「群发」「推送」「发出去」「上传到公众号」「发到公众号」「可以发了吗」「发布前检查」时使用。
version: 0.3.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-publish
---

# 发布

通过微信公众号 API 或手动方式将文章发布到公众号。

## 脚本目录

发布脚本位于共享目录，供 publish 和 sticker 共用。

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`，脚本路径为 `{baseDir}/../shared/scripts/publish.py`。

| 脚本 | 用途 |
|------|------|
| `shared/scripts/publish.py` | 微信公众号 API 发布工具 |

## 前置条件

在 `config.yaml` 中填写公众号凭证：

```yaml
wechat_appid: "你的AppID"
wechat_appsecret: "你的AppSecret"
```

获取方式：登录 [微信公众平台](https://mp.weixin.qq.com) → 开发 → 基本配置 → 获取 AppID 和 AppSecret。

需要 IP 白名单：在公众平台「基本配置」中将服务器 IP 加入白名单。

## 工作流

```
发布进度：
- [ ] 第1步：发布前检查
- [ ] 第2步：准备文章目录
- [ ] 第3步：上传图片与创建草稿
- [ ] 第4步：确认并发布
- [ ] 第5步：归档
```

### 第1步：发布前检查

执行 [references/pre-publish-checklist.md](references/pre-publish-checklist.md) 中的清单。全部通过后继续。

### 第2步：准备文章目录

将排版后的稿件整理为如下目录结构：

```
article/
├── article.yaml    # 文章元信息
├── content.html    # 排版后的正文 HTML
├── cover.jpg       # 封面图
└── images/         # 正文内图片（可选）
    ├── img1.png
    └── img2.jpg
```

**article.yaml 格式**：

```yaml
title: "文章标题"
author: "作者名"
digest: "摘要，不超过128字"
content_source_url: ""           # 原文链接（可选）
need_open_comment: 1             # 开启评论：0=否 1=是
only_fans_can_comment: 0         # 仅粉丝可评：0=否 1=是
```

### 第3步：上传图片与创建草稿

**一键全流程**（推荐）：

```bash
python {baseDir}/../shared/scripts/publish.py full article/
```

脚本自动执行：上传封面图 → 上传正文图片并替换路径 → 创建草稿。

**分步执行**：

```bash
# 1. 上传封面图，获取 thumb_media_id
python {baseDir}/../shared/scripts/publish.py upload-thumb article/cover.jpg

# 2. 上传正文图片，获取 URL
python {baseDir}/../shared/scripts/publish.py upload-content-image article/images/img1.png

# 3. 手动替换 content.html 中的图片路径为上传后的 URL
# 4. 创建草稿
python {baseDir}/../shared/scripts/publish.py create-draft article/article.yaml
```

### 第4步：确认并发布

草稿创建后会返回 `media_id`。建议先在公众号后台（草稿箱）预览确认，再发布：

```bash
# 发布草稿
python {baseDir}/../shared/scripts/publish.py publish <media_id>

# 查询发布状态
python {baseDir}/../shared/scripts/publish.py status <publish_id>
```

或一键全流程直接发布：

```bash
python {baseDir}/../shared/scripts/publish.py full article/ --publish
```

### 第5步：归档

发布成功后，将稿件从 `drafts_root` 移动到 `published_root`。

## 提交方式

| 方式 | 说明 |
|------|------|
| **API**（推荐） | 通过脚本调用微信 API，详见上方工作流 |
| **手动** | 复制粘贴到公众号后台，详见 [references/submit-guide.md](references/submit-guide.md) |

## API 参考

接口详情与错误码：[references/api-reference.md](references/api-reference.md)

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.html` `article.yaml` `imgs/` | 发布结果 |

`article.yaml` 由 publish 自动从文章目录下的其他文件生成（标题从 `article.md`、封面从 `imgs/00-cover.*`）。

发布成功后，整个文章目录从 `drafts_root` 移动到 `published_root`。
