# 提交到公众号后台

## 方式一：API 提交（推荐）

使用 `skills/aws-wechat-article-publish/scripts/publish.py`，通过微信公众号 API 完成发布。

### 前置准备

1. 在仓库根 **`aws.env`** 中填写微信槽位（与 `skills/aws-wechat-article-main/references/env.example.yaml` 键名一致），例如单账号：
   ```env
   NUMBER_ACCOUNTS=1
   WECHAT_1_NAME=主号
   WECHAT_1_APPID=你的AppID
   WECHAT_1_APPSECRET=你的AppSecret
   WECHAT_1_API_BASE=
   ```
   多账号递增 `WECHAT_2_*` 等；发布前可运行 `python skills/aws-wechat-article-publish/scripts/publish.py check-wechat-env` 检查缺项。

2. 在公众平台「开发 → 基本配置」中将服务器 IP 加入白名单

3. 准备文章目录：
   ```
   article/
   ├── article.yaml    # 标题、作者、摘要等元信息
   ├── article.html    # 排版后的正文 HTML
   ├── cover.jpg       # 封面图
   └── imgs/           # 正文内图片
   ```

### 一键发布

```bash
# 创建草稿（不发布，可在后台预览）
python skills/aws-wechat-article-publish/scripts/publish.py full article/

# 创建草稿并立即发布
python skills/aws-wechat-article-publish/scripts/publish.py full article/ --publish
```

### 分步操作

```bash
# 获取 token
python skills/aws-wechat-article-publish/scripts/publish.py token

# 上传封面图
python skills/aws-wechat-article-publish/scripts/publish.py upload-thumb cover.jpg

# 上传正文图片
python skills/aws-wechat-article-publish/scripts/publish.py upload-content-image imgs/img1.png

# 创建草稿（需要先准备好 article.yaml）
python skills/aws-wechat-article-publish/scripts/publish.py create-draft article.yaml

# 发布
python skills/aws-wechat-article-publish/scripts/publish.py publish <media_id>

# 查询状态
python skills/aws-wechat-article-publish/scripts/publish.py status <publish_id>
```

接口详情与错误码：[api-reference.md](api-reference.md)

## 方式二：手动提交

1. 登录微信公众平台（mp.weixin.qq.com）
2. 进入「素材管理」或「草稿箱」→ 新建图文消息
3. 填写标题、作者、摘要
4. 将排版后的正文粘贴到正文编辑区
5. 上传封面图，设置封面
6. 逐一上传正文内图片并插入对应位置
7. 设置评论权限（开启/仅粉丝可评）
8. 保存为草稿或直接群发
