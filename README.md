# 微信公众号 AI 运营助手

一套运行在 Cursor / OpenClaw 上的 AI Skills，覆盖公众号内容生产全流程：**选题→写稿→审稿→排版→配图→发布**。

## 安装

```bash
bash scripts/install-skills.sh
```

将 8 个 skill + 共享资源安装到 `.cursor/skills/`。

## 30 秒上手

安装后直接对 AI 说：

```
帮我写一篇公众号文章
```

AI 会：
1. 检测到没有配置 → 自动引导你完成首次配置（账号类型、目标读者、调性等）
2. 配置完成后进入选题→写稿→审稿→排版→配图→发布的完整流程
3. 每一步完成后暂停，等你确认或修改后再继续

**你不需要记住任何命令**，用自然语言说就行：

| 你说 | AI 做什么 |
|------|----------|
| 「帮我找几个选题」 | 搜索热点，推荐 3-5 个选题 |
| 「写一篇 AI 入门的文章」 | 围绕 AI 入门调研→选角度→写全文 |
| 「做个 AI 工具系列」 | 规划系列→拆分每篇→逐篇写作 |
| 「审一下这篇稿子」 | 检查敏感词/错别字/规范/配图 |
| 「排版」 | Markdown → 微信可直接粘贴的 HTML |
| 「配图」 | 自动匹配风格，生成封面和正文配图 |
| 「发布」 | 通过 API 上传到公众号草稿箱 |
| 「做一组贴图」 | 多图推送的独立创作流程 |

---

## 使用指南

### 1. 首次配置

首次使用时 AI 会自动引导你填写配置。**必填项只有 3 个**：

- 账号类型（科技/职场/情感/教育...）
- 目标读者（一线互联网人/大学生/宝妈...）
- 语气调性（轻松/正式/专业/幽默...）

其余都可以后续在 `.aws-article/config.yaml` 中补充。

如需手动配置：
```bash
cp .aws-article/config.example.yaml .aws-article/config.yaml
# 编辑 config.yaml
```

### 2. 写一篇文章（完整流程）

**一条龙模式**：说「一条龙写一篇文章」或「从选题到发布全做」

```
你：帮我一条龙写一篇 AI 相关的文章

AI：[搜索热点，推荐 5 个选题]
    请选择：输入编号选定 / 调整 / 重新选

你：选 2

AI：[调用模型写初稿，含配图标记]
    ℹ️ 使用第三方模型写作（deepseek-chat）
    文章已生成，请确认或提出修改意见。

你：开头再吸引一点

AI：[修改开头后重新展示]

你：通过，继续

AI：[审稿：检查敏感词、错别字、写作规范...]
    🔴 必须修改：第3段发现错别字「帐号」→「账号」
    🟡 建议修改：第5段 AI 味表达

你：改好继续

AI：[排版：Markdown → HTML，使用经典蓝主题]
    ✅ 已保存 article.html

AI：[配图：分析文章，生成 3 张配图]
    ℹ️ 使用专用图片模型（dall-e-3）

你：继续

AI：[发布前检查 → 上传到公众号草稿箱]
    ✅ 草稿创建成功，media_id: xxx
```

**单步模式**：只做某一步

```
你：帮这篇文章配个图        → 只跑配图
你：把这篇排版一下          → 只跑排版
你：审一下 drafts/xxx/draft.md → 只跑审稿
```

### 3. 选题

**四种场景**：

| 场景 | 你说 | AI 做什么 |
|------|------|----------|
| 有明确话题 | 「写一篇 AI Agent 的文章」 | 搜竞品文章，提供 3-4 个不同角度 |
| 有方向没话题 | 「AI 最近有什么好写的」 | 搜热点，推荐 3-5 个选题 |
| 完全没方向 | 「这周写什么」 | 按你的账号领域搜热点 |
| 系列策划 | 「做个 AI 入门系列」 | 规划系列总线 + 每篇选题 + 发布节奏 |

每个选题包含：标题候选（多种风格）、切入角度、大纲预览、工作量评估、摘要候选。

### 4. 写作

**两种写作方式**（AI 自动选择，也可指定）：

| 方式 | 条件 | 说明 |
|------|------|------|
| 第三方模型 | config 配了 `writing_model` | 调用 DeepSeek/GPT 等生成 |
| Agent 直写 | 未配置模型 | 当前 AI 直接写 |

AI 会告知你当前用的是哪种方式。

写作时自动在需要配图的位置插入标记，后续配图时直接使用。

**写作规范**：创建 `.aws-article/writing-spec.md` 可以约束 AI 的写作风格（用词、句式、品牌调性等）。参考 `writing-spec.example.md`。

### 5. 审稿

**两种模式**（自动识别）：

| 模式 | 时机 | 重点 |
|------|------|------|
| 内容审 | 写稿后 | 敏感词、错别字、写作规范、配图标记 |
| 终审 | 发布前 | 排版完整性、图片就位、发布要素 |

结果分三级：🔴 必须改 / 🟡 建议改 / 🟢 通过。有 🔴 项时自动进入修改循环。

### 6. 排版

把 Markdown 转成微信公众号可直接粘贴的 HTML。

**4 套内置主题**：

| 主题 | 风格 |
|------|------|
| `default` | 经典蓝 — 左边框小标题 |
| `grace` | 优雅紫 — 圆角色块 |
| `modern` | 暖橙 — 胶囊圆角 |
| `simple` | 极简黑 — 最少装饰 |

想用自己的主题？在 `.aws-article/presets/formatting/` 下创建 YAML 文件即可。

### 7. 配图

**AI 自动匹配风格**，也可以指定。生成方式同写作：优先用专用图片模型，未配则用当前 AI。

14 种视觉风格 + 6 种图片类型（信息图/氛围/流程图/对比/框架/封面），自由组合。

信息图支持 10 种高级布局：九宫格、漏斗、冰山、金字塔、时间线等。

### 8. 发布

```
你：发布

AI：[发布前检查 → 上传封面 → 上传正文图 → 创建草稿]
    ✅ 草稿创建成功
    → 去公众号后台草稿箱预览确认
```

图片上传前自动压缩（封面 ≤10MB，正文 ≤1MB）。

**多账号**：管多个公众号时，config 里配 `wechat_accounts` 数组，发布时用 `--account` 指定。

**固定 IP**：公众号 API 有 IP 白名单限制，可配 `wechat_api_base` 指向你的转发代理。

### 9. 贴图 / 多图推送

独立于长文的创作流程：

```
你：做一组程序员摸鱼的贴图

AI：[确定风格 → 规划 6 张图序 → 展示方案]
    请确认或调整

你：第 3 张换个场景

AI：[调整后逐张生成 → 审稿 → 发布]
```

### 10. 嵌入元素

文章中可以插入公众号名片和小程序卡片。

先在 config 里配好：
```yaml
embeds:
  profiles:
    - name: 我的公众号
      alias: gh_xxxxxxxxx
  miniprograms:
    - name: 我的小程序
      appid: wx123456
```

然后在文章里写 `{embed:profile:我的公众号}`，排版时自动替换为微信特殊标签。

---

## 自定义预设

Skills 内置了基础预设（标题风格、文章结构、排版主题等），但你可以创建自己的预设覆盖或扩展。

**所有预设放在 `.aws-article/presets/` 下**：

| 目录 | 用途 | 格式 |
|------|------|------|
| `structures/` | 文章结构（清单体、教程型、故事型...） | .md |
| `closing-blocks/` | 文末区块（关注引导、作者介绍...） | .md |
| `title-styles/` | 标题风格 | .md |
| `formatting/` | 排版主题 | .yaml |
| `image-styles/` | 配图风格 | .md |
| `sticker-styles/` | 贴图风格 | .md |

**创建方式**：
1. 进入对应目录，读 `README.md` 了解格式要求
2. 按格式创建文件
3. 在 config 里设为默认（可选），或对话时说「用 XX 预设」

每种预设都有 README.md 作为 schema 文档，读完就知道怎么写。

---

## 目录结构

```
项目根目录
├── .aws-article/                    ← 配置、预设、素材（用户自定义）
│   ├── config.yaml                  # 配置
│   ├── writing-spec.md              # 写作规范
│   ├── presets/                     # 自定义预设
│   └── assets/                      # 素材
│
├── skills/                          ← Skill 源码
│   ├── shared/                      # 共享资源
│   │   ├── image-styles/            #   Type×Style 体系
│   │   └── scripts/                 #   publish.py + image-gen.py
│   ├── aws-wechat-article-main      # 路由
│   ├── aws-wechat-article-topics    # 选题
│   ├── aws-wechat-article-writing   # 写作
│   ├── aws-wechat-article-review    # 审稿
│   ├── aws-wechat-article-formatting # 排版
│   ├── aws-wechat-article-images    # 配图
│   ├── aws-wechat-article-publish   # 发布
│   └── aws-wechat-sticker           # 贴图
│
├── drafts/                          ← 进行中的文章（一篇一目录）
├── posts/published/                 ← 已发布的文章
└── series/                          ← 系列规划
```

每篇文章的过程文件集中在一个目录下：

```
drafts/2025-03-18-ai-agent-入门/
├── topic-card.md          ← 选题卡片
├── research.md            ← 调研摘要
├── draft.md               ← 初稿
├── review.md              ← 审稿结果
├── article.md             ← 定稿
├── article.html           ← 排版后 HTML
├── article.yaml           ← 发布元信息
└── imgs/                  ← 配图
```

---

## 配置参考

完整配置字段见 `skills/aws-wechat-article-main/references/config-schema.md`。

核心配置速览：

```yaml
# 账号定位
account_type: 科技
target_reader: ""
tone: 轻松

# 写作模型（任何 OpenAI 兼容端点）
writing_model:
  base_url: "https://api.deepseek.com"
  api_key: ""
  model: "deepseek-chat"

# 图片生成模型
image_model:
  base_url: ""
  api_key: ""
  model: ""

# 发布
wechat_appid: ""
wechat_appsecret: ""
```

---

## 脚本工具

| 脚本 | 位置 | 用途 |
|------|------|------|
| `format.py` | formatting/scripts/ | Markdown → 微信 HTML |
| `write.py` | writing/scripts/ | 调用 LLM 写文章 |
| `image-gen.py` | shared/scripts/ | 调用 LLM 生图 |
| `publish.py` | shared/scripts/ | 微信 API 发布 + 压缩 + 环境检查 |

通常你不需要直接调用这些脚本——AI 会自动使用。

环境检查：
```bash
python skills/shared/scripts/publish.py check
```

---

## 设计参考

- [baoyu-skills](https://github.com/JimLiu/baoyu-skills) — Type×Style 体系、排版转换、封面生成
- [article-writer](https://github.com/wordflowlab/article-writer) — 调研驱动选题、强制等待机制

## License

MIT
