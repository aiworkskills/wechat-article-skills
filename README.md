**简体中文** | [English](README_EN.md)

# 微信公众号 AI 运营助手

> 开源公众号运营数字员工。选好风格，说一句话，AI 自动完成选题、写作、排版、配图到发布的全部流程。**不用懂设计，不用会代码。**

[![License](https://img.shields.io/github/license/aiworkskills/wechat-article-skills)](LICENSE)
[![Stars](https://img.shields.io/github/stars/aiworkskills/wechat-article-skills?style=social)](https://github.com/aiworkskills/wechat-article-skills/stargazers)
[![Release](https://img.shields.io/github/v/release/aiworkskills/wechat-article-skills)](https://github.com/aiworkskills/wechat-article-skills/releases)
[![Platforms](https://img.shields.io/badge/platforms-13%2B%20Claw%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-blue)](#支持的智能体)

---

## 📚 教程与案例

- 📖 [如何用好 aiworkskills 平台？从配置到发文一文读懂](https://mp.weixin.qq.com/s/rcnq_gg3XXRwJ7ovQtBo1A) · 官方使用指南
- 🔧 [WorkBuddy 如何使用 AI Work Skills 运行公众号](https://mp.weixin.qq.com/s/GQjCY5UsArV9XI5AyoxWZQ) · WorkBuddy 组合案例
- ⚡ [QClaw + aiworkskills 一键运营公众号](https://mp.weixin.qq.com/s/xLUJBc2bbrJvgeAesbhsFA) · QClaw 组合案例
- 🔑 [小龙虾的模型怎么选](https://mp.weixin.qq.com/s/u5e7FC-QAzXaMlq36RNIJg) · 写作与配图模型选型指南

---

## 🚀 快速开始

能写公众号是一件很简单的事情，把一个公众号写好你一定有独特的见解。

我们开源的skill解决能写能发的问题，可视化配置平台解决你的个性化配置的问题。

```
① 装智能体  →  ② 安装技能  →  ③ 网页个性化化配置  →  ④ 导入 .aws  →  ⑤ 说一句话开始
```

推荐路径：在 **[aiworkskills.cn](https://aiworkskills.cn/)** 可视化配置台选好风格、填完表，一键导出配置包给 AI。

![aiworkskills 首页](https://aiworkskills.cn/images/sp/aiworkskills%E9%A6%96%E9%A1%B5.png)


### 1. 安装技能

#### 1.1 Claw 系列（QClaw / WorkBuddy 等 13+ 工具）

涵盖 QClaw · ArkClaw · JVSClaw · WorkBuddy · Linclaw · NemoClaw · AutoClaw · MaxClaw · KimiClaw · DuClaw · PowerClaw · ZeroClaw，以及开源标准底座 OpenClaw。

**方式 A · 最快**：直接在 AI 对话框发一句话——

```
帮我安装这个skill：https://github.com/aiworkskills/wechat-article-skills
```

Claw 会自动把仓库拉到本地、把 9 个技能全部挂进对话，全程不用打一条命令。

**方式 B · 第二快捷**：把下面 9 条命令一键复制到剪贴板，粘到小龙虾对话框回车即可：

```bash
clawhub install aws-wechat-article-main       # 必装 · 一条龙总控
clawhub install aws-wechat-article-assets     # 必装 · 业务资料库 / .aws 预设包
clawhub install aws-wechat-article-topics
clawhub install aws-wechat-article-writing
clawhub install aws-wechat-article-review
clawhub install aws-wechat-article-formatting
clawhub install aws-wechat-article-images
clawhub install aws-wechat-article-publish
clawhub install aws-wechat-sticker
```

> **OpenClaw**（Claw 系列的开源标准底座）直接读取仓库 `skills/` 目录——`git clone` 本仓库后即生效，无需 `clawhub install`。

#### 1.2 其他智能体（Cursor / Claude Code / Codex）

克隆仓库就行，各工具按自己的规则读取 `skills/` 目录：

```bash
git clone https://github.com/aiworkskills/wechat-article-skills.git
cd wechat-article-skills
```

| 工具 | Skill 读取路径 | 备注 |
|------|--------------|------|
| Cursor | 项目 `skills/` 或 `.cursor/skills/` | 克隆即用；也可把 `skills/aws-wechat-article-*` 和 `aws-wechat-sticker` 软链到 `.cursor/skills/` |
| Claude Code | `~/.claude/skills/` 或项目 `.claude/skills/` | 把上述 9 个目录复制或软链到对应位置 |
| Codex | 仓库根 `AGENTS.md` | 已随仓库维护，克隆即生效 |

装完后，对 AI 说「帮我写一篇公众号文章」就开始了。

### 2. 个性化配置（非必须）：不配置会使用默认的写作风格书写、排版

`.aws` 是一个配置包，把你在 [aiworkskills.cn](https://aiworkskills.cn/) 填好的账号设定、文风规范、多种视觉风格等全部打包到一起，一次导入、一次到位。

#### 2.1 两种导入方式

**方式 A · 永久下载链接（推荐）**

在配置界面点击"复制小龙虾安装指令"配置台会给你一个永久链接，形如 `https://aiworkskills.cn/xxxx/你的名字.aws`。在小龙虾对话框粘贴，格式如：

> 请用 aws-wechat-article-assets 技能，导入这份预设包：`https://aiworkskills.cn/xxxx/你的名字.aws`

这个链接**永远有效**——回配置台改了设置，链接里的内容会自动跟着更新，重新在小龙虾界面说“更新aws”就可以了。链接默认**不含** API Key；想让 AI 顺便拿到 Key，末尾加上 `?with_secrets=true` 即可。万一链接泄露，回配置台点「换链接」就能让旧链接立刻作废。

**方式 B · 手动下载安装`.aws` 文件**

在配置台直接下载 `.aws` 文件，拖给 AI 说「导入这个预设包」。

#### 2.2 预设与素材目录

首次通过 `.aws` 包导入时会自动建齐；手动建用 `mkdir -p` 即可，结构如下：

```
.aws-article/
├── config.yaml
├── writing-spec.md                 # 可选，写作规范
├── presets/                        # 7 类预设
│   ├── structures/                 #   文章结构
│   ├── closing-blocks/             #   文末区块
│   ├── title-styles/               #   标题风格
│   ├── formatting/                 #   排版主题
│   ├── cover-styles/               #   封面风格
│   ├── image-styles/               #   配图风格
│   └── sticker-styles/             #   贴图风格
├── products/                       # 用户业务资料库（按产品名分目录，AI 写第一份业务介绍时自动建）
│   └── {产品名}/                   #   每个产品一个独立目录
│       ├── 项目介绍.md             #     业务介绍 .md 直挂产品根（命名按行业）
│       └── images/                 #     业务配图（含同名说明 .md）
└── tmp/
```

---

## 🌐 支持生态

### 支持的智能体

![支持平台](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E5%B9%B3%E5%8F%B0.png)

基于 **OpenClaw 标准**，兼容 13+ Claw 系列工具：

> QClaw · ArkClaw · JVSClaw · WorkBuddy · Linclaw · NemoClaw · AutoClaw · MaxClaw · KimiClaw · DuClaw · PowerClaw · ZeroClaw

同时支持 **Claude Code · Cursor · Codex** 等主流智能体。

### 支持的大模型

> DeepSeek · 通义千问 · 智谱 GLM · Kimi · 豆包 · 文心一言 · 讯飞星火 · 腾讯混元 · MiniMax · 百川 · 阶跃星辰 · 零一万物 · GPT · Claude

兼容所有 **OpenAI 接口**大模型，API Key 本地存储不上传。

---

## ✨ 9 个 Skill 分工

| Skill | 能力 | 你这样说 |
|-------|------|---------|
| **主流程** | 串联全流程 | 「帮我写一篇公众号文章」 |
| **选题** | 调研热点，推荐 3–5 个选题卡片 | 「帮我找几个选题」 |
| **写作** | 调用大模型 / AI 直写，遵循文风规范 | 「写一篇 AI 入门」 |
| **审稿** | 敏感词 / 错别字 / 规范比对，三级结果 | 「审一下这篇」 |
| **排版** | Markdown → 微信 HTML，4 套默认主题 | 「排版」 |
| **配图** | 14 种视觉风格 × 6 种图片类型 | 「配个图」 |
| **发布** | 微信 API 直发，多账号，自动压缩 | 「发布」 |
| **贴图** | 多图推送独立流程（小绿书内侧中） | 「做一组贴图」 |
| **素材** | **业务资料库**（按产品名分目录）+ 图库 + `.aws` 预设包导入导出 | 「导入这个预设」「保存为产品介绍」 |

每一步都会暂停等你确认，不会自动跳走。全程可以打断、修改、重来。

> **业务资料库（新）**：写涉及自家业务的文章前 AI 自动查 `.aws-article/products/{产品名}/`；聊出来的产品介绍也会引导你存进去，下次直接复用——AI 不用每次重新问"你是干什么的"。

---

## 📸 可视化配置一览

所有配置在 [aiworkskills.cn](https://aiworkskills.cn/) 填表完成。

<details>
<summary><b>账号定位与目标读者</b> — 一次性说清 AI 你是谁、写给谁、写什么、怎么写</summary>

![账号与读者](https://aiworkskills.cn/images/sp/%E8%B4%A6%E5%8F%B7%E4%B8%8E%E8%AF%BB%E8%80%85%E9%85%8D%E7%BD%AE.png)

</details>

<details open>
<summary><b>视觉呈现</b> — 排版主题 + 封面 / 配图风格预设</summary>

![视觉呈现](https://aiworkskills.cn/images/sp/%E8%A7%86%E8%A7%89%E5%91%88%E7%8E%B0%E9%85%8D%E7%BD%AE.png)

</details>

<details open>
<summary><b>排版主题</b> — 4 套内置主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑），也可以 YAML 自定义</summary>

![排版主题](https://aiworkskills.cn/images/sp/%E6%8E%92%E7%89%88%E9%A3%8E%E6%A0%BC%E9%A2%84%E8%AE%BE.png)

</details>

<details open>
<summary><b>配图风格</b> — 14+ 视觉风格，对应不同内容类型</summary>

![配图风格](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E7%AB%A0%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details open>
<summary><b>封面风格</b> — 多种封面视觉语言，和内容定位一一对应</summary>

![封面风格](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E5%B0%81%E9%9D%A2%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>发布设置</b> — 微信 API、敏感词、文末嵌入元素</summary>

![发布配置](https://aiworkskills.cn/images/sp/%E5%8F%91%E5%B8%83%E9%85%8D%E7%BD%AE.png)

</details>

---

## 🛠️ 开发者路径（自己编辑配置文件）

如果你更愿意直接改 YAML、完全不走可视化配置台：

```bash
git clone https://github.com/aiworkskills/wechat-article-skills.git
cd wechat-article-skills
# 各工具按上文「🚀 快速开始 · 1.2」自动识别 skills/
cp skills/aws-wechat-article-main/references/config.example.yaml .aws-article/config.yaml
cp skills/aws-wechat-article-main/references/env.example.yaml aws.env
# 编辑 config.yaml（账号 / 文风 / 模型）和 aws.env（API Key / 微信凭证）
python skills/aws-wechat-article-main/scripts/validate_env.py
```
---

## 🔑 模型配置（可选但推荐）

整条流程里有两个地方要接大模型：一个给 AI **写稿**用，一个给 AI **画图**用。两者互相独立——只配写稿、只配画图、或两个都配，都可以。每个都支持**可视化配置**和**直接改配置文件**两种方式。

### 为什么要配？

- **配了**：AI 走你指定的专业模型（写稿：GPT / Claude，配图：香蕉、seedream 等），出稿与配图质量稳定可控，你的文风规范和敏感词策略都能严格执行。
  - **好处**： 用能力很强的模型直接跑小龙虾，我们看起来有些浪费，小龙虾配置普通模型，写稿配高级模型，好钢用到刀刃上，谁叫我们都不是土豪呢。
  - **配图可能必须**：很多coding plan的模型是不支持图片生成的，不配的话图片就出不来。 
- **不配**：默认**不放行**，除非你明确同意让 AI 自己代写 / 代画：
  - **写稿**：加 `validate_env.py --agent-writing-approved`，AI 会按同一套文风规范亲自写。
  - **配图**：加 `validate_env.py --agent-image-capable`，让有多模态能力的 AI（如 Claude / GPT）直接出图。

两个模型都走 **OpenAI 兼容接口**，**API Key 只存在你本地，不会上传任何服务器**。

### 写稿模型（`writing_model`）

**方式 A · 龙虾聊天框直接说：**

```
帮我配置个写作模型：模型api地址：https://xxxx.com APIkey:kf-xxxxxx
```

**方式 B · 可视化配置台**

在 [aiworkskills.cn](https://aiworkskills.cn/) 的「模型配置」栏填三项：**接口地址**、**模型名**、**API Key**。导出 `.aws` 时会自动带上配置；用永久链接且追加 `?with_secrets=true` 才会把 API Key 一起带过去。

**方式 C · 直接改配置文件**

在 `.aws-article/config.yaml` 里填：

```yaml
writing_model:
  base_url: https://api.openai.com/v1
  model: gpt-5                # 推荐 GPT 系列，长文稳定、文风还原度高
  provider: openai            # 可选，仅用于日志 / 诊断
```

在仓库根 `aws.env` 里填：

```
WRITING_MODEL_API_KEY=sk-...
```

改完后在仓库根跑一次 `python skills/aws-wechat-article-main/scripts/validate_env.py` 确认。

### 画图模型（`image_model`）

负责生成封面、文章配图、九宫格贴图，以及对已有图片的改写。走 OpenAI 标准的图片接口。

**方式 A · 龙虾聊天框直接说：**
```
帮我配置个配图模型：模型api地址：https://xxxx.com APIkey:kf-xxxxxx
```

**方式 B · 可视化配置台**

和写稿模型在同一个配置栏，填图片模型的**接口地址**、**模型名**、**API Key** 三项，导出 `.aws` 时一起带上。

**方式 C · 直接改配置文件**

在 `.aws-article/config.yaml` 里填：

```yaml
image_model:
  base_url: https://generativelanguage.googleapis.com/v1beta/openai
  model: gemini-3.1-pro-preview     # 推荐「香蕉」系列，封面与配图都能打
  provider: google                  # 可选
```

在 `aws.env` 里填：

```
IMAGE_MODEL_API_KEY=sk-...
```

> 想让 AI 自己的多模态能力直接代画（不接外部图片模型）：运行 `validate_env.py --agent-image-capable`（需你明确同意）。

---

## 📋 技能更新

直接在 AI 对话框发一句话：

```
帮我更新这些skills：https://github.com/aiworkskills/wechat-article-skills
```

## 📋 更新日志

完整变更历史见 [CHANGELOG.md](CHANGELOG.md)。最近几次：

- **2026-04-24** · 引入 `products/{产品名}/` 业务资料库（读+写双向流程）；`stock_image_ingest.py` → `product_image_ingest.py`（破坏性，含老用户迁移命令）
- **2026-04-22** · assets skill 支持 `.aws` 永久 URL 导入；强化 skill 描述与套件完整性校验
- **2026-04-15** · 排版 skill 目录结构整理，同步各 skill 与脚本更新
- **2026-04-03** · 新增 assets skill：图片入库 + `.aws` 预设包导入导出
- **2026-03-31** · 脚本迁移与发布入口统一
- **2026-03-20** · 四平台一键安装 + 配置校验对齐
- **2026-03-18** · 三层文件架构升级 + 嵌入元素支持

---

## 🏠 社区

- 💬 [GitHub Discussions](https://github.com/aiworkskills/wechat-article-skills/discussions) — 使用问题、最佳实践
- 🐛 [Issues](https://github.com/aiworkskills/wechat-article-skills/issues) — Bug 反馈、功能建议
- 🌐 [aiworkskills.cn](https://aiworkskills.cn/) — 可视化配置台

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=aiworkskills/wechat-article-skills&type=Date)](https://star-history.com/#aiworkskills/wechat-article-skills&Date)

---

## License

[Apache License 2.0](LICENSE)
