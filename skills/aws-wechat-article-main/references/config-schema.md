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

# ── 写作模型（第三方 LLM）──
writing_model:
  base_url: ""               # API 端点（任何 OpenAI 兼容接口，含中转/代理）
  api_key: ""                # API Key
  model: ""                  # 模型名
  temperature: 0.7
  max_tokens: 4000

# ── 排版 ──
default_format_preset: ""   # 默认排版预设名，空则每次询问

# ── 图片 ──
cover_aspect: "2.35:1"      # 封面比例：2.35:1、16:9、1:1
cover_style: 简约            # 封面风格：简约、插画、实拍、品牌模板
image_density: 每节一图      # 配图密度
caption_style: 有图注        # 有图注、无图注
multi_image_count: 6         # 多图推送张数偏好
# 素材（封面、品牌头尾图等）统一放在 .aws-article/assets/ 下

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
drafts_root: drafts/               # 进行中的文章
published_root: posts/published/   # 已发布的文章
series_root: series/               # 系列规划
```

> **安全提示**：config.yaml 已在 `.gitignore` 中，不会提交到仓库。请注意保管 AppSecret 和 API Key。

## 文件组织约定

### 全局目录（`.aws-article/`）

```
.aws-article/
├── config.yaml                  # 配置
├── writing-spec.md              # 写作规范
├── presets/                     # 用户自定义预设
│   ├── formatting/              #   排版主题（YAML）
│   ├── image-styles/            #   配图风格
│   ├── title-styles/            #   标题风格
│   └── review-rules.yaml        #   自定义审稿规则
├── assets/                      # 素材库
│   ├── brand/                   #   品牌元素（头图、尾图）
│   ├── covers/                  #   封面图素材
│   └── stock/                   #   通用素材
└── templates/                   # 模板覆盖
```

预设和模板的加载优先级：用户当次说法 > `.aws-article/` 用户文件 > skill 内置默认。详见 `.aws-article/README.md`。

### 文章目录（一篇文章一个目录）

```
drafts/{日期}-{标题slug}/
├── topic-card.md                # topics 产出：选题卡片
├── research.md                  # topics 产出：调研摘要
├── draft.md                     # writing 产出：初稿（含配图标记）
├── review.md                    # review 产出：审稿结果
├── article.md                   # 审稿通过后的定稿
├── article.html                 # formatting 产出：排版后 HTML
├── article.yaml                 # publish 需要的元信息
└── imgs/                        # images 产出
    ├── outline.md               #   配图方案
    ├── prompts/                 #   各图的 prompt 文件
    └── NN-type-slug.png         #   生成的图片
```

目录名格式：`{YYYY-MM-DD}-{标题slug}`，由 topics 确认选题后创建。发布后整体移动到 `published_root`。

### 系列目录

```
series/{系列slug}/
├── plan.md                      # 系列总规划
└── progress.md                  # 进度追踪
```

## 说明

- 以上为首期约定字段，可按需增删。
- 缺省时各 skill 使用自身默认值。
- 首次无配置时按 [first-time-setup.md](first-time-setup.md) 引导用户完成。
