# 发布前检查清单

在审稿通过后、实际提交前执行。

## 内容侧：由终审负责，别在这里重做一遍

标题 / 摘要 / 作者、敏感词与错别字、正文占位符、原创标注、文末引导区块、配图齐全——这些是 [review skill 的终审](../../aws-wechat-article-review/SKILL.md)检查项。**两边各维护一份清单必然会漂**，这里不复制。

走一条龙时终审已经过了，直接往下。**单独触发本 skill**（用户只说「发一下」）时，先跑一遍终审再回来。

## 发布侧：只有这里能查

- [ ] `.aws-article/config.yaml` 的 `publish_method` 是 `draft` / `published` / `none` 之一 —— `publish.py check-screening`
- [ ] 目标账号槽位已由**用户选定**（不是替他挑的）—— `publish.py accounts`
- [ ] 该槽位的 `WECHAT_{N}_APPID` / `APPSECRET` 已填 —— `publish.py check-wechat-env`
- [ ] 服务器 IP 在公众号后台白名单里（`token` 报 errcode 多半是这条）
- [ ] 封面在**文章目录下**（`cover.png` / `.jpg` / `.jpeg` / `.webp`），不是 `imgs/` 里
- [ ] 正文里没有挂未群发文章的链接（微信会拒；改用永久链接或去掉超链）
- [ ] 需要 2.35:1 / 1:1 裁剪框时装了 Pillow，或已在 `article.yaml` 手填 `pic_crop_*`
- [ ] 如需开启评论 / 仅粉丝可评，已确认设置

全部勾选后执行 `full`。

发布成功后的 `publish_completed` 四项门禁见 [SKILL.md](../SKILL.md)。
