---
name: aws-wechat-article-assets
description: 公众号素材｜业务资料库｜预设包｜.aws 预设包｜主题包｜品牌包｜aiworkskills.cn — 用户业务资料库与预设包管理：业务资料按产品名组织在 `.aws-article/products/{产品名}/`（介绍 .md 直挂产品根 + 配图归 `images/` 子目录含同名说明 .md），AI 与用户对话产出业务介绍内容时引导用户保存；图片入库走 `product_image_ingest.py --product <产品名> --stem <中文名>`。导入 .aws ZIP 预设包（本地文件或 `https://aiworkskills.cn/**/*.aws` URL）合并主题/配色/字体配置到 `.aws-article/presets/`；`config.yaml` 仅本地不存在时从包内复制，已存在则 stdout 输出差异 JSON 不覆盖。面向内容运营、品牌团队、设计支持岗。触发词：「素材库入库」「stock images」「上传图到素材库」「.aws」「预设包」「导入预设」「主题包」「aiworkskills.cn 链接」「.aws 下载地址」。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 用户业务资料库与预设（Assets）

**业务资料按产品名分目录** — `.aws-article/products/{产品名}/` 直挂业务介绍 `.md`、`images/` 存配图（含同名说明 `.md`）。**写涉及用户自身业务的文章/配图前必须先查这里；新生成的业务介绍内容应引导用户保存到这里**。预设包合并到 `.aws-article/presets/`。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 管理本地业务资料库与预设包，可选从 `aiworkskills.cn` 域下载 `.aws` 预设包（ZIP）。

- **凭证**：无（但**导入 `.aws` 会把包内密钥写进仓库根 `aws.env`**，见下）
- **网络**：可选 `https://*.aiworkskills.cn/**/*.aws` 下载预设包。**白名单强制**：仅 HTTPS + `aiworkskills.cn` 及其子域，非白名单**直接报错退出**。`--allow-any-host` 可放宽，调试用
- **文件读**：用户指定的本地图片或 `.aws` 文件；引导入库前会 `ls .aws-article/products/` 看已有产品名
- **文件写**：
  - `.aws-article/products/{产品名}/*.md`（业务介绍，AI 用 Write 工具直接落库）
  - `.aws-article/products/{产品名}/images/*`（图片 + 同名 `.md`，由脚本写）
  - `.aws-article/presets/<白名单子目录>/*`、`.aws-article/downloads/*.aws`、`.aws-article/tmp/*`
  - **仓库根 `aws.env`**：导入 `.aws` 时按映射表增量写入密钥（覆盖现有键前自动备份 `aws.env.bak.{ts}`，stderr 只打印键名不打印值）
- **归档安全**：解压 `.aws`（ZIP）到 `.aws-article/tmp/`。**已内置 ZIP slip 防御**——逐项校验成员路径，拒绝绝对路径、`..` 段、或解析后指向解压目录外的路径，任一违反立即退出且不写入任何文件
- **shell**：仅 `{python} {baseDir}/scripts/` 下的 `product_image_ingest.py`、`import_presets_aws.py`

除 `aws.env` 外，所有写入都限制在仓库根的 `.aws-article/` 内。

**单独安装可用**：两个脚本都不依赖兄弟 skill，只要有 `.aws-article/` 目录就能工作。

## 三件事

| 能力 | 说明 |
|------|------|
| **业务介绍 .md 入库** | 对话中产出的业务介绍 → `products/{产品名}/<文件名>.md`（Write 工具直接落库，无脚本） |
| **业务图入库** | 用户业务图 → `products/{产品名}/images/` + 同名说明 `.md`（脚本，`--product` 必填） |
| **预设包 `.aws`** | ZIP（本地文件或 `https://aiworkskills.cn/**/*.aws`）→ 合并 `presets/` 白名单子目录 |

## 设计意图（必读）⛔

`.aws-article/products/{产品名}/` 是**用户自家业务**（卖货 / 卖软件 / 卖服务 / 自媒体 IP）的资料库——既是 AI 写业务相关内容时的**底稿来源**，也是 AI 与用户协作产出新介绍时的**保存目的地**。

```
.aws-article/products/{产品名}/
├─ 项目介绍.md                # 业务介绍 .md 直挂产品根（命名按用户行业：服务介绍.md / 品牌介绍.md…）
├─ (其他业务文档.md)
└─ images/
   ├─ 配置首页.png
   └─ 配置首页.md             # 图片说明 .md（同名）
```

**双向触发**：

| 方向 | 触发条件 | 行为 |
|------|---------|------|
| **读** | 当前任务涉及用户自家业务（对外介绍 / 教程 / 案例 / 自家安利 / 业务配图） | 先 `ls .aws-article/products/`，识别相关产品，读它根下的 `*.md`、查 `images/` 同名 `.md`，把已有素材当底稿与配图候选 |
| **写** | AI 刚生成或改写的内容**语义属于用户业务介绍** | 走下面「业务介绍 .md 入库」；用户说「保存为产品介绍」等也走这条 |

**什么时候不要触发**见 [branches.md「一」](references/branches.md)。

## 一、业务介绍 .md 入库

无需脚本，AI 用 Write 工具直接落库。两种触发：

- **AI 主动识别**：刚生成/改写的内容明确属于用户自家业务介绍（产品 / 服务 / 品牌 / 项目 / 团队 / 业务范围）时提示用户：
  > 「这段是 [产品名] 的业务介绍，要不要保存到产品资料库？我可以存到 `.aws-article/products/{产品名}/{文件名}.md`，下次写涉及业务的文章时会自动用上。」
- **用户主动指令**：「保存为产品介绍 / 业务介绍 / 服务介绍 / 入库到产品 / 存到产品资料库」等。

**保存流程**：

1. **确认产品名**：`ls .aws-article/products/`，已有目录提示复用；新产品向用户拿名字。
2. **确认文件名**：默认 `项目介绍.md`；可改成贴用户行业的 `产品介绍.md` / `服务介绍.md` / `品牌介绍.md`。
3. **建目录**：`mkdir -p .aws-article/products/{产品名}/images/`（即便暂时为空也把骨架建齐）。
4. **写入**：Write 工具落到 `.aws-article/products/{产品名}/{文件名}.md`。
5. **反馈**：「已存到 `<完整路径>`，下次涉及 [产品名] 业务的文章会自动用上」。

## 二、业务图入库

**脚本不会读图**——读图定文件名、写画面描述是 Agent 的活，入库命令要带 `--content`：

```bash
{python} {baseDir}/scripts/product_image_ingest.py <源图片路径> \
  --product "公众号AI运营助手" --stem "配置首页" \
  --content "客观中文描述，一两句即可"
```

`--product` / `--stem` 必填，产品目录与 `images/` 不存在时自动创建。产出 `配置首页.png` + `配置首页.md`。

不传 `--content` 会写占位句（**预期行为，不是故障**）、`.md` 的固定格式，见 [branches.md「二」](references/branches.md)。

## 三、预设包导入（`.aws`）

扩展名 `.aws`，实质是 **ZIP**。包根应含与仓库一致的预设文件夹（可以多出别的文件，脚本只处理白名单）：

`closing-blocks`、`cover-styles`、`formatting`、`image-styles`、`sticker-styles`、`structures`、`title-styles`

另可有根级 `config.yaml`、`writing-spec.md`。**不在白名单的目录会被跳过并打日志**——`components/` 与 `review-rules.yaml` 就不由 `.aws` 管理，原因见 [branches.md「三」](references/branches.md)。

**工作流**：

1. 准备来源：本地 `.aws` 文件，或符合白名单的 HTTPS URL。
2. 先 `--dry-run` 看将写入哪些路径。
3. 在**仓库根**执行：

```bash
# 本地路径
{python} {baseDir}/scripts/import_presets_aws.py path/to/bundle.aws
{python} {baseDir}/scripts/import_presets_aws.py path/to/bundle.aws --dry-run

# URL（仅 aiworkskills.cn 及子域）
{python} {baseDir}/scripts/import_presets_aws.py https://aiworkskills.cn/bundles/brand-a.aws
```

**三条要先知道的语义** ⛔：

- **预设目录是替换式**：包内有该子目录 → 先清空本地同名目录再写；包内没有 → 本地保持不动。
- **`config.yaml` 不覆盖**：本地已有时只把差异以 JSON 打到 **stdout**，须**问过用户**再手改。本地没有才复制。
- **密钥会进 `aws.env`**：包内 `wechat_appid` / `wechat_appsecret` / `writing_model.api_key` / `image_model.api_key` 按映射增量写入，覆盖前备份 `aws.env.bak.{ts}`。

完整规则（映射表、写入策略、包根优先级、URL 白名单、`tmp` 语义）见 [branches.md「三～五」](references/branches.md)。

## 脚本

| 脚本 | 参数 |
|------|------|
| `product_image_ingest.py` | `source`、`--product`（必填）、`--stem`（必填）、`--content`、`--repo` |
| `import_presets_aws.py` | `bundle`（路径或白名单 URL）、`--dry-run`、`--repo`、`--allow-any-host`（调试） |

## 分支与细则

不该入库的情况、业务图入库两步、`.aws` 合并语义、密钥映射、URL 白名单 → [references/branches.md](references/branches.md)。

## 过程文件

| 场景 | 产出 |
|------|------|
| 业务介绍 .md 入库 | `.aws-article/products/{产品名}/{文件名}.md`（同时 mkdir `images/`） |
| 业务图入库 | `.aws-article/products/{产品名}/images/*.{png,…}` + 同名 `*.md` |
| `.aws` 导入 | `.aws-article/presets/**` 更新；`config.yaml` 首次复制或 stdout 差异 JSON；密钥增量写入 `aws.env`（覆盖前备份）；解压缓存在 `.aws-article/tmp/` |
| `.aws` URL 导入 | 下载缓存 `.aws-article/downloads/*.aws`；其余同本地导入 |
