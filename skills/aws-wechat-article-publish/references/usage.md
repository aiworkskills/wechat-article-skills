# 发布脚本用法

脚本位于 `shared/scripts/publish.py`。

## 一键全流程（推荐）

```bash
# 创建草稿（不发布，可在后台预览）
python shared/scripts/publish.py full article/

# 创建草稿并立即发布
python shared/scripts/publish.py full article/ --publish

# 指定账号（多账号时）
python shared/scripts/publish.py --account main full article/
```

## 分步操作

```bash
python shared/scripts/publish.py token                       # 获取 access_token
python shared/scripts/publish.py upload-thumb cover.jpg      # 上传封面图
python shared/scripts/publish.py upload-content-image img.png # 上传正文图片
python shared/scripts/publish.py create-draft article.yaml   # 创建草稿
python shared/scripts/publish.py publish <media_id>          # 发布草稿
python shared/scripts/publish.py status <publish_id>         # 查询状态
```

## 管理命令

```bash
python shared/scripts/publish.py check      # 环境检查
python shared/scripts/publish.py accounts   # 列出已配置账号
```

## 文章目录结构

```
article/
├── article.yaml    # 文章元信息
├── content.html    # 排版后的正文 HTML
├── cover.jpg       # 封面图
└── images/         # 正文内图片（可选）
```

## article.yaml 格式

```yaml
title: "文章标题"
author: "作者名"
digest: "摘要，不超过128字"
content_source_url: ""
need_open_comment: 1
only_fans_can_comment: 0
```

## 多账号

```yaml
# config.yaml 中配置
wechat_accounts:
  - name: 主号
    alias: main
    default: true
    appid: ""
    appsecret: ""
  - name: 副号
    alias: sub
    appid: ""
    appsecret: ""
```

使用：`python shared/scripts/publish.py --account sub full article/`
