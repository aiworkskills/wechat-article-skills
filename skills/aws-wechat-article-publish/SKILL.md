---
name: aws-wechat-article-publish
description: 将文章发布到微信公众号，支持 API 发布和手动提交，含发布前检查。当用户提到「发布」「提交」「群发」「推送」「发出去」「上传到公众号」「发到公众号」「可以发了吗」「发布前检查」时使用。
version: 0.4.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-publish
---

# 发布

通过微信公众号 API 或手动方式发布文章。

## 前置条件 ⛔

`test -f .aws-article/config.yaml || test -f "$HOME/.aws-article/config.yaml"`
⛔ 不存在 → [首次引导](../aws-wechat-article-main/references/first-time-setup.md)

需要 `config.yaml` 中的 `wechat_appid` + `wechat_appsecret`（API 方式）。

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

执行 [references/pre-publish-checklist.md](references/pre-publish-checklist.md)。全部通过后继续。

可先运行环境检查：`python {baseDir}/../shared/scripts/publish.py check`

### 第2步：准备文章目录

文章目录结构和 article.yaml 格式：[references/usage.md](references/usage.md)

### 第3步：上传图片与创建草稿

脚本用法和命令详情：[references/usage.md](references/usage.md)

图片上传前自动压缩（封面 ≤10MB，正文 ≤1MB）。

### 第4步：确认并发布

建议先在公众号后台草稿箱预览，确认后再发布。

### 第5步：归档

发布后文章目录从 `drafts_root` 移到 `published_root`。

## 提交方式

| 方式 | 说明 |
|------|------|
| API（推荐） | 脚本调用微信 API → [references/usage.md](references/usage.md) |
| 手动 | 复制粘贴 → [references/submit-guide.md](references/submit-guide.md) |

API 接口详情：[references/api-reference.md](references/api-reference.md)

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.html` `imgs/` | `article.yaml` → 发布到公众号 |
