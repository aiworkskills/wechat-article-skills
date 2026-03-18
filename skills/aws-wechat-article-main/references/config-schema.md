# 配置字段说明

配置文件路径：项目 `.aws-article/config.yaml` 或用户 `~/.aws-article/config.yaml`。各子 skill 读取同一份配置；优先级：用户当次说法 > 配置文件 > skill 内默认值。

## 完整字段

```yaml
# ── 账号与定位 ──
account_type: 科技          # 领域：科技、职场、情感、教育、品牌号、个人IP 等
target_reader: ""           # 目标读者画像，如「一线互联网人」
tone: 轻松                  # 调性：正式、轻松、专业、幽默、犀利
update_frequency: 周更      # 更新频率：日更、周更、双周、月更
default_author: ""          # 默认作者名

# ── 选题与标题 ──
topic_direction: ""         # 选题方向或禁区说明
title_style: 干货型         # 悬念型、干货型、数字型、反问型、故事型
title_max_length: 25        # 标题最大字数
summary_length: "80-150"    # 摘要字数范围
forbidden_title_phrases: [] # 禁用标题套路，如：浅谈、万字长文、建议收藏

# ── 写作 ──
article_style: 口语化       # 口语化、书面、故事型、方法论、清单体
paragraph_preference: 短段为主
heading_density: 每节必有小标题
closing_block: ""           # 文末固定引导语模板
forbidden_words: []         # 禁用词/敏感词表
original_attribution: ""    # 原创/转载标注习惯

# ── 排版 ──
default_format_preset: ""   # 默认排版预设名，空则每次询问

# ── 图片与素材 ──
cover_aspect: "2.35:1"      # 封面比例：2.35:1、16:9、1:1
cover_style: 简约            # 封面风格：简约、插画、实拍、品牌模板
image_density: 每节一图      # 配图密度
caption_style: 有图注        # 有图注、无图注
multi_image_count: 6         # 多图推送张数偏好
assets_root: imgs/           # 素材根目录
header_image: ""             # 品牌头图路径
footer_image: ""             # 品牌尾图路径

# ── 审稿 ──
review_required:             # 必检项列表
  - 敏感词
  - 错别字
  - 链接
  - 原创标注
custom_sensitive_words: []   # 自定义敏感词
review_output_format: 分块详细  # 简要清单、分块详细

# ── 发布 ──
wechat_appid: ""               # 公众号 AppID
wechat_appsecret: ""           # 公众号 AppSecret
publish_method: api            # api、manual
need_open_comment: 1           # 开启评论：0=否 1=是
only_fans_can_comment: 0       # 仅粉丝可评：0=否 1=是

# ── 路径 ──
posts_root: posts/
drafts_root: drafts/
published_root: posts/published/
```

> **安全提示**：config.yaml 已在 `.gitignore` 中，不会提交到仓库。但请注意保管好你的 AppSecret。

## 说明

- 以上为首期约定字段，可按需增删。
- 缺省时各 skill 使用自身默认值。
- 首次无配置时按 [first-time-setup.md](first-time-setup.md) 引导用户完成。
