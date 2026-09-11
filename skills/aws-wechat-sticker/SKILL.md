---
name: aws-wechat-sticker
description: 公众号贴图｜九宫格｜多图推送｜图片消息｜表情包 — 贴图与多图推送：从创意构思、规划图序、AI 生图到整组图审核，产出一组风格统一的图片 + 每张配文。发布走常规图文链路（拼成图文后 formatting + publish），微信原生「图片消息」需在公众号后台手动发。面向公众号运营、自媒体、IP 账号。触发词：「贴图」「多图推送」「发组图」「图片消息」「九宫格」「做一组图」「图片帖子」「发几张图」「不写正文发图」「只发图不写字」。是文章内配图/封面请走 aws-wechat-article-images；需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env:
        - IMAGE_MODEL_API_KEY
        - WECHAT_1_APPID
        - WECHAT_1_APPSECRET
      bins:
        - python3
---

# 贴图 / 多图推送

**一组风格统一的图 + 每张配文** —— 构思、排图序、生图、审图。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 编排贴图流程，调用同套件的 `image_create.py`（images）生图；可选调用 `publish.py` 发布。**会把图片 prompt 发给外部图像 API；若走发布路径，会把图片作为 POST body 上传到微信 API。**

- **凭证读取**：`aws.env` 的 `IMAGE_MODEL_API_KEY`；走发布时额外读 `WECHAT_{N}_APPID` / `WECHAT_{N}_APPSECRET`
- **凭证外发**：`IMAGE_MODEL_API_KEY` 以 `Authorization: Bearer` 头发给 `image_model.base_url`；微信凭证用于换 `access_token`
- **内容外发**：图片 prompt 发给图像 API；图片文件发给微信 `material/add_material` / `draft/add`
- **文件读**：`.aws-article/config.yaml`、本篇 `article.yaml`、`imgs/prompts/*.md`
- **文件写**：本篇 `imgs/*.{png,webp}`、`imgs/outline.md`、`article.yaml`
- **shell**：`{python} {baseDir}/../aws-wechat-article-images/scripts/image_create.py`；可选 `../aws-wechat-article-publish/scripts/publish.py`

**至少要同时装 `aws-wechat-article-images`**（生图能力在那边）；要走发布再装 `aws-wechat-article-publish`。

## 路由

长文图文（标题+正文+插图+后台发文）→ [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)；长文内单篇插图 → [aws-wechat-article-images](../aws-wechat-article-images/SKILL.md)。本 skill 做**以图片为主**的内容：多张图 + 每张配文，整组统一风格。

## 产出目标（先看这个）

- **输入**：主题 / 选题卡 / 用户素材图（任选其一）
- **输出**：`imgs/`（`outline.md` + `prompts/` + 图片），整组风格统一，不漂移
- **发布**：⛔ 微信原生「图片消息」本套件**未实现**。要么把整组图拼成一篇图文走常规链路，要么只交付图由用户在后台手发——两条路径见 [branches.md「一」](references/branches.md)

## 配置检查 ⛔

任何操作前先按 **[首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)** 执行，通过后才继续（或用户明确书面确认「本次不检查」）。

**图片模型**：`image_model`（`provider`、`base_url`、`model`）在 `.aws-article/config.yaml`；`IMAGE_MODEL_API_KEY` 在仓库根 `aws.env`。键名对照 [env.example.yaml](../aws-wechat-article-main/references/env.example.yaml)。

须遵守 main 的**智能体行为约束**：未通过环境校验且未获用户明确「本次例外」时，**不得假装已走专用生图 API**。

## 工作流

```
贴图进度：
- [ ] 第1步：⛔ 环境检查 + 合并本篇约束
- [ ] 第2步：确定选题
- [ ] 第3步：确定风格（全组统一）
- [ ] 第4步：规划图序 → imgs/outline.md
- [ ] 第5步：⛔ 展示方案并等用户确认
- [ ] 第6步：生成图片
- [ ] 第7步：审图
- [ ] 第8步：交付（拼图文发 或 交给用户后台手发）
```

### 第1步：合并本篇约束

本篇在 `drafts/…/` 下时，按 **`.aws-article/config.yaml` → 本篇 `article.yaml`** 合并读取（同键本篇优先）。重点字段：`multi_image_count`、`tone`、`target_reader`、`custom_sticker_style` > `default_sticker_style`。

无有效 YAML 时，用用户口述主题 + skill 默认值。

### 第2步：确定选题

topics 产出的贴图卡片 / 用户直接给主题 / 用户提供素材图。

### 第3步：确定风格

加载优先级与九个形态的分类（信息位 5 个 / 节奏位 3 个）见 [branches.md「三」](references/branches.md)。

**全组图统一一个形态** —— 组图的价值就在整齐，每张换一个等于没有风格。

### 第4步：规划图序

产出 `imgs/outline.md`：每张图的用途、配文、文件名。模板见 [references/workflow.md](references/workflow.md)；贴图类型与叙事线见 [branches.md「四」](references/branches.md)。

**张数 ≤ 9**（微信限制）。

### 第5步：展示方案并等用户确认 ⛔

把 `outline.md` 整张表摆给用户，**等确认再生图**——生图要花钱，方案错了每张都得重来。

### 第6步：生成图片

**优先调 `image_create.py`**（依赖 `image_model` + `IMAGE_MODEL_API_KEY`）；环境未就绪或用户接受 main 的「本次例外」时才降级为 Agent 生图 / 只出 prompts。

**必须告知用户当前用的是哪种**：

- `ℹ️ 使用 image_create.py 调用专用生图模型（{model}）`
- `ℹ️ 本次未走 image_create.py（原因：…）`

在**仓库根**执行（路径按本篇 `imgs/` 调整）：

```bash
# 整批
{python} {baseDir}/../aws-wechat-article-images/scripts/image_create.py batch drafts/YYYYMMDD-slug/imgs/prompts/ -o drafts/YYYYMMDD-slug/imgs/

# 单张
{python} {baseDir}/../aws-wechat-article-images/scripts/image_create.py generate imgs/prompts/01.md -o imgs/01.png

# 连通性自检
{python} {baseDir}/../aws-wechat-article-images/scripts/image_create.py test
```

图片内文字与 prompt 构建规则与长文配图完全一致，见 [images SKILL](../aws-wechat-article-images/SKILL.md) 与 [prompt-construction.md](../aws-wechat-article-images/references/image-styles/prompt-construction.md)。调用失败的四分类处理见 [branches.md「二」](references/branches.md)。

### 第7步：审图

贴图专用清单：[references/checklist.md](references/checklist.md)。重点是**整组看**：风格是否统一、第一张缩略图下是否仍可辨、图序是否读得通。

### 第8步：交付

⛔ **不要在贴图目录上直接跑 `publish.py full`** —— 它硬性要求 `article.yaml` + `article.html` + `cover.*`，贴图目录没有这三样，跑了必然报错。

两条落地路径（拼成图文自动发 / 只交付图由用户后台手发）见 [branches.md「一」](references/branches.md)。走第二条时**不要声称发布闭环完成**。

## 分支与细则

发布路径的真实边界、生图失败四分类、风格与形态优先级、贴图类型与叙事线、「九宫格」指什么、单独安装 → [references/branches.md](references/branches.md)。

## 过程文件

| 读取 | 产出 |
|------|------|
| `topic-card.md`（可选）、`.aws-article/config.yaml` + 本篇 `article.yaml` | `imgs/outline.md`、`imgs/prompts/*.md`、`imgs/*.png` |
