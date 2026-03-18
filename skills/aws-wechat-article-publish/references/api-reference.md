# 微信公众号 API 参考

## 接口一览

| 接口 | 方法 | 路径 | 用途 |
|------|------|------|------|
| 获取 token | GET | `/token` | 获取 access_token |
| 上传永久素材 | POST | `/material/add_material` | 上传封面图，返回 media_id |
| 上传正文图片 | POST | `/media/uploadimg` | 上传正文内图片，返回 URL |
| 新增草稿 | POST | `/draft/add` | 创建图文草稿 |
| 发布草稿 | POST | `/freepublish/submit` | 发布草稿（异步） |
| 查询发布状态 | POST | `/freepublish/get` | 查询发布结果 |

所有接口基础 URL：`https://api.weixin.qq.com/cgi-bin`

## 获取 access_token

```
GET /token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}
```

返回：
```json
{"access_token": "...", "expires_in": 7200}
```

有效期 2 小时，需缓存复用，避免频繁请求。

## 上传封面图（永久素材）

```
POST /material/add_material?access_token={TOKEN}&type=image
Content-Type: multipart/form-data
```

- 字段名：`media`
- 限制：10MB，支持 bmp/png/jpeg/jpg/gif
- 永久素材上限：100,000 张

返回：
```json
{"media_id": "...", "url": "..."}
```

`media_id` 用于 `draft/add` 的 `thumb_media_id` 字段。

## 上传正文图片

```
POST /media/uploadimg?access_token={TOKEN}
Content-Type: multipart/form-data
```

- 字段名：`media`
- 限制：1MB，支持 jpg/png
- 不占用素材库配额
- 返回的 URL 可直接在正文 HTML 中使用

返回：
```json
{"url": "https://mmbiz.qpic.cn/..."}
```

## 新增草稿

```
POST /draft/add?access_token={TOKEN}
Content-Type: application/json
```

请求体：
```json
{
  "articles": [{
    "title": "标题（≤32字）",
    "author": "作者（≤16字）",
    "digest": "摘要（≤128字，仅单图文）",
    "content": "HTML 正文（≤2万字符，图片 URL 必须来自 uploadimg）",
    "thumb_media_id": "封面图 media_id",
    "content_source_url": "原文链接",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
  }]
}
```

返回：
```json
{"media_id": "..."}
```

## 发布草稿

```
POST /freepublish/submit?access_token={TOKEN}
Content-Type: application/json
```

请求体：
```json
{"media_id": "草稿的 media_id"}
```

返回：
```json
{"publish_id": "...", "msg_data_id": "..."}
```

**注意**：发布为异步操作，返回成功仅表示任务提交成功。

## 查询发布状态

```
POST /freepublish/get?access_token={TOKEN}
Content-Type: application/json
```

请求体：
```json
{"publish_id": "..."}
```

返回 `publish_status`：

| 值 | 含义 |
|----|------|
| 0 | 发布成功 |
| 1 | 发布中 |
| 2 | 原创失败 |
| 3 | 常规失败 |
| 4 | 平台审核不通过 |
| 5 | 已删除 |
| 6 | 已封禁 |

## 常见错误码

| 错误码 | 含义 | 处理 |
|--------|------|------|
| 40001 | access_token 无效 | 重新获取 token |
| 40004 | 不合法的媒体文件类型 | 检查图片格式 |
| 40009 | 图片大小超限 | 封面 ≤10MB，正文图 ≤1MB |
| 45009 | API 调用超限 | 等待后重试 |
| 45028 | 接口无权限 | 检查公众号类型和权限 |
| 48001 | API 未授权 | 检查公众号开发者设置 |

## 凭证配置

在 `config.yaml` 中配置（config.yaml 已在 .gitignore 中，不会被提交）：

```yaml
wechat_appid: "你的AppID"
wechat_appsecret: "你的AppSecret"
```

脚本按以下顺序查找配置文件：
1. 项目级：`.aws-article/config.yaml`
2. 用户级：`~/.aws-article/config.yaml`

## 权限要求

- 需要已认证的服务号或订阅号
- AppID 和 AppSecret 在「开发 → 基本配置」获取
- 调用服务器 IP 需加入白名单

## 官方文档

- [新增草稿](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add)
- [发布草稿](https://developers.weixin.qq.com/doc/subscription/api/public/api_freepublish_submit.html)
- [上传永久素材](https://developers.weixin.qq.com/doc/subscription/api/material/permanent/api_addmaterial.html)
- [上传正文图片](https://developers.weixin.qq.com/doc/subscription/en/api/material/permanent/api_uploadimage)
