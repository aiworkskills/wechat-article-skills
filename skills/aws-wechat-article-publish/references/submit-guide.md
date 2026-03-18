# 提交到公众号后台

## 方式一：API 提交（推荐）

使用 `scripts/publish.py` 脚本，通过微信公众号 API 完成发布。

### 前置准备

1. 在 `config.yaml` 中填写凭证：
   ```yaml
   wechat_appid: "你的AppID"
   wechat_appsecret: "你的AppSecret"
   ```

2. 在公众平台「开发 → 基本配置」中将服务器 IP 加入白名单

3. 准备文章目录：
   ```
   article/
   ├── article.yaml    # 标题、作者、摘要等元信息
   ├── content.html    # 排版后的正文 HTML
   ├── cover.jpg       # 封面图
   └── images/         # 正文内图片
   ```

### 一键发布

```bash
# 创建草稿（不发布，可在后台预览）
python shared/scripts/publish.py full article/

# 创建草稿并立即发布
python shared/scripts/publish.py full article/ --publish
```

### 分步操作

```bash
# 获取 token
python shared/scripts/publish.py token

# 上传封面图
python shared/scripts/publish.py upload-thumb cover.jpg

# 上传正文图片
python shared/scripts/publish.py upload-content-image images/img1.png

# 创建草稿（需要先准备好 article.yaml）
python shared/scripts/publish.py create-draft article.yaml

# 发布
python shared/scripts/publish.py publish <media_id>

# 查询状态
python shared/scripts/publish.py status <publish_id>
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
