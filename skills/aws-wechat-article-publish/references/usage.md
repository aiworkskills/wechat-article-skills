# 发布脚本用法

脚本路径：**`skills/aws-wechat-article-publish/scripts/publish.py`**（在**仓库根**执行）。

- **微信凭证**来自仓库根 **`aws.env`**：`NUMBER_ACCOUNTS`、`WECHAT_1_NAME`、`WECHAT_1_APPID`、`WECHAT_1_APPSECRET`、`WECHAT_1_API_BASE`（1..N 槽位）。`WECHAT_N_API_BASE` 可空（空则官方 `https://api.weixin.qq.com`）。
- **`publish_method`** 在 **`config.yaml`**：**`draft`**（默认）= **`full`** 只进**草稿箱**；**`published`** = 再**提交发布**；**`none`** = **`full`** **不调接口**（用户不填微信）。**`full --publish`** 可在 **`draft`** 下单次强制发布（**`none`** 下仍跳过）。

## `publish_method` 检查

```bash
python skills/aws-wechat-article-publish/scripts/publish.py check-screening
python skills/aws-wechat-article-publish/scripts/publish.py check-screening --config .aws-article/config.yaml
```

## 微信槽位检查

```bash
python skills/aws-wechat-article-publish/scripts/publish.py check-wechat-env
python skills/aws-wechat-article-publish/scripts/publish.py accounts
```

## 一键全流程

```bash
python skills/aws-wechat-article-publish/scripts/publish.py full path/to/article-dir/

python skills/aws-wechat-article-publish/scripts/publish.py full path/to/article-dir/ --publish

python skills/aws-wechat-article-publish/scripts/publish.py --account 2 full path/to/article-dir/
```

## 正式文章读取（`getdraft.py`）

与 **`publish.py` 独立**，用于 **`freepublish/batchget`** / **`freepublish/get`** / **`freepublish/getarticle`**（仓库根执行）：

```bash
python skills/aws-wechat-article-publish/scripts/getdraft.py published-fields
python skills/aws-wechat-article-publish/scripts/getdraft.py publish-get <publish_id>
python skills/aws-wechat-article-publish/scripts/getdraft.py article-get <article_id>
```

## 分步操作

```bash
python skills/aws-wechat-article-publish/scripts/publish.py token
python skills/aws-wechat-article-publish/scripts/publish.py upload-thumb cover.jpg
python skills/aws-wechat-article-publish/scripts/publish.py upload-content-image img.png
python skills/aws-wechat-article-publish/scripts/publish.py create-draft path/to/article.yaml
python skills/aws-wechat-article-publish/scripts/publish.py publish <media_id>
```
