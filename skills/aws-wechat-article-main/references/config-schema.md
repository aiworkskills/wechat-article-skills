# 配置 Schema（首期）

配置文件名与路径优先级：项目 `.aws-article/config.yaml` 或 `.aws-article/EXTEND.md` → 用户 `~/.aws-article/config.yaml` 或 `~/.aws-article/EXTEND.md`。各子 skill 读取同一份配置；读取顺序：用户当次说法 > 配置文件 > skill 内默认。

## 首期必选项（YAML 示例）

```yaml
# 账号与定位
account_type: 科技          # 领域：科技、职场、情感、教育、品牌号、个人 IP 等
target_reader: 一线互联网人
tone: 轻松                  # 正式、轻松、专业、幽默、犀利
update_frequency: 周更      # 日更、周更、双周、月更
default_author: ""          # 默认作者名

# 选题与标题
topic_direction: ""        # 选题方向/禁区说明
title_style: 干货型        # 悬念型、干货型、数字型、反问型、故事型
title_max_length: 25
summary_length: "80-150"
forbidden_title_phrases: [] # 如：浅谈、万字长文、建议收藏、震惊

# 写作
article_style: 口语化      # 口语化、书面、故事型、方法论、清单体
paragraph_preference: 短段为主
heading_density: 每节必有小标题
closing_block: ""          # 文末固定引导语模板
forbidden_words: []        # 禁用词/敏感词表（业务相关）
original_attribution: ""   # 原创/转载标注习惯

# 排版（若用默认预设名）
default_format_preset: ""  # 默认排版预设名，空则每次选

# 图片与素材
cover_aspect: "2.35:1"     # 2.35:1、16:9、1:1
cover_style: 简约
image_density: 每节一图
caption_style: 有图注
multi_image_count: 6       # 多图推送张数偏好
assets_root: imgs/         # 素材根目录
header_image: ""           # 品牌头图路径
footer_image: ""           # 品牌尾图路径

# 审稿
review_required: [敏感词, 错别字, 链接, 原创标注]
custom_sensitive_words: []
review_output_format: 分块详细  # 简要清单、分块详细（可当 brief）

# 路径与存储
posts_root: posts/
drafts_root: drafts/
published_root: posts/published/
```

## 说明

- 以上键名与示例值为首期约定，实现时可按需增删；缺省时各 skill 使用自身默认值。  
- 首次无配置时，按 [first-time-setup.md](first-time-setup.md) 做引导并写入。
