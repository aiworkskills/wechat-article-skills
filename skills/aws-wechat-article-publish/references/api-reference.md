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

在仓库根 **`aws.env`** 中配置微信槽位（勿提交含真密钥的文件）：

```env
NUMBER_ACCOUNTS=1
WECHAT_1_NAME=主号
WECHAT_1_APPID=你的AppID
WECHAT_1_APPSECRET=你的AppSecret
WECHAT_1_API_BASE=
```

键名与 `skills/aws-wechat-article-main/references/env.example.yaml` 一致。多账号递增 `WECHAT_2_*` 等。

## 权限要求

- 需要已认证的服务号或订阅号
- AppID 和 AppSecret 在「开发 → 基本配置」获取
- 调用服务器 IP 需加入白名单

## 官方文档

- [新增草稿](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add)
- [发布草稿](https://developers.weixin.qq.com/doc/subscription/api/public/api_freepublish_submit.html)
- [上传永久素材](https://developers.weixin.qq.com/doc/subscription/api/material/permanent/api_addmaterial.html)
- [上传正文图片](https://developers.weixin.qq.com/doc/subscription/en/api/material/permanent/api_uploadimage)

## 封面裁剪框 pic_crop_* 的回读

`draft/add` 接受 `pic_crop_235_1` / `pic_crop_1_1`（归一化 `X1_Y1_X2_Y2`），但
**`draft/get` 不回显这两个字段**——它把值归一化后放进 `cover_info.crop_percent_list`：

```json
"cover_info": {
  "crop_percent_list": [
    {"ratio": "2.35_1", "x1": "0.001515", "y1": "0", "x2": "0.998485", "y2": "1"},
    {"ratio": "1_1",    "x1": "0.287879", "y1": "0", "x2": "0.712121", "y2": "1"}
  ]
}
```

不知道这点会得出「微信忽略了裁剪框」的错误结论——在 `news_item[0]` 里查
`pic_crop_235_1` 只会拿到 `None`。校验请读 `cover_info.crop_percent_list`，
`ratio` 用下划线写法（`2.35_1` / `1_1`）。

实测（1584x672 封面）微信原样存下，六位小数完全一致；比例不匹配时才会报 53402。
