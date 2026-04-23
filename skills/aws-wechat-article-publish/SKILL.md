---
name: aws-wechat-article-publish
description: 公众号发布｜公众号草稿箱｜公众号群发｜图文推送｜微信 API｜wechat automation｜WeChat API automation｜auto publish｜scheduled publish — 公众号 API 发布工具，图文入草稿箱或直接群发，支持封面素材上传、发布前检查与 draft/published 模式切换。面向公众号运营、自动化内容团队、开发者。触发词：「发布」「提交」「群发」「推送」「发出去」「上传到公众号」「发到公众号」「可以发了吗」「发布前检查」。需要多环节串联（写+审+排+配图+发）请走 aws-wechat-article-main。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env:
        - WECHAT_1_APPID
        - WECHAT_1_APPSECRET
      bins:
        - python3
    primaryEnv: aws.env
---

# 发布

**公众号 API 直连发布** —— 图文入草稿箱或直接群发，素材上传、发布前检查一站式完成。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 调 `publish.py` **直连微信公众号官方 API** 发布图文。**会把本篇 `article.html` 与 `imgs/*` 文件作为 POST body 上传到微信服务器。** 具体行为：

- **凭证读取**：`aws.env` 的 `WECHAT_{N}_APPID` / `WECHAT_{N}_APPSECRET`（多槽位支持 N≥1）
- **凭证外发**：`APPID` / `APPSECRET` 以 query string 形式发给 `api.weixin.qq.com/cgi-bin/token` 换 `access_token`；后续请求带 `access_token` query string。微信返回的 `access_token` 在进程内存短期缓存，**不落盘**
- **内容外发**：本篇封面、正文插图以 multipart upload 发给 `material/add_material`；`article.html` 正文与标题/摘要以 JSON POST 发给 `draft/add`、`freepublish/submit`
- **网络目标**：默认 `api.weixin.qq.com`；用户可在 `WECHAT_{N}_API_BASE` / `config.yaml.wechat_api_base` 自配反代
- **文件读**：仓库内 `.aws-article/config.yaml`、`aws.env`、本篇 `article.yaml`、`article.html`、`imgs/*`
- **文件写**：仅本篇 `article.yaml` 的状态字段（`media_id`、`publish_id`、`publish_completed`）
- **shell**：仅 `python3 {baseDir}/scripts/publish.py`、`getdraft.py`、`article_init.py`

**建议**：首次运行用 `publish_method: draft` 只入草稿箱确认效果，再切 `published` 真正群发。

## 配套 skill（informational）

本 skill 是 `aws-wechat-article-*` 一条龙公众号套件的**发布环节**（入口 `aws-wechat-article-main`）。工作流中的若干步骤会读取同级 `../aws-wechat-article-main/references/*.md` 等共享文档（首次引导、articlescreening schema、env/config 示例等）。

- **套件完整装齐到同一 `skills/` 根目录**时，跨 skill 引用都能读到。
- **单独安装本 skill** 时，跨 skill 引用的步骤会在读取阶段遇到 `file not found`；但 `publish.py`、`getdraft.py`、`article_init.py` 这几个脚本本身可独立运行（只要 `aws.env` 与 `.aws-article/config.yaml` 就绪）。

完整 9 slug 清单见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

通过微信公众号 API 将排版稿写入**草稿箱**或再**提交发布**（由 **`config.yaml`** 的 **`publish_method`** 与命令行 **`--publish`** 控制）。

## 配置检查 ⛔

任何操作执行前，**必须**按 **[首次引导](../aws-wechat-article-main/references/first-time-setup.md)** 执行其中的 **「检测顺序」**。检测通过后才能进行以下操作（或用户明确书面确认「本次不检查」）：

## 脚本目录

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。发布子命令在 **`{baseDir}/scripts/publish.py`**（项目根执行）。

| 脚本 / 子命令 | 用途 |
|--------|------|
| **`article_init.py`** | 初始化或更新本篇 **`article.yaml`**（及可选 **`closing.md`**）。用于总览 **本篇准备**（建目录后）或 **发布前** 补全元数据。仓库根执行：`python {baseDir}/scripts/article_init.py <文章目录> [--title … --author … --digest …]` |
| **`getdraft.py`** | 独立于 `publish.py`：用于正式文章查询（`published-list` / `published-fields` / `publish-get` / `article-get`，对应 `freepublish/*`），可用于 `embeds.related_articles.manual` 为空时自动补全推荐链接。注意：`freepublish/*` 需要公众号具备对应接口权限。仓库根：`python {baseDir}/scripts/getdraft.py published-fields` |
| `check-screening` | 校验 **`config.yaml`** 的 **`publish_method`**（**`draft`** / **`published`** / **`none`**） |
| `check-wechat-env` | 按 **`config.yaml` 槽位**检查 `aws.env` 的 `WECHAT_N_APPID` / `WECHAT_N_APPSECRET` 是否已填（**调用 `publish.py` 前建议跑**） |
| `check` | 环境检查：`aws.env`、各槽位、依赖、可选探测 token |
| `accounts` | 列出 **`config.yaml`** 中各微信槽位名称，并标记 `aws.env` 凭证缺项 |
| `full` / `token` / … | 调微信 API（需 **`aws.env`** 微信凭证） |

## 凭证与 `publish_method` ⛔

### `publish_method`（以仓库 **`config.yaml`** 为准）

| 值 | 含义 | 行为 |
|----|------|------|
| **`draft`**（默认） | 只进公众号**草稿箱** | **`full`** 创建草稿后**不**调用 freepublish 提交发布。 |
| **`published`** | 草稿 + **提交发布** | **`full`** 创建草稿后继续提交发布（异步）。**`full --publish`** 可**单次强制**带发布，即使当前为 **`draft`**。 |
| **`none`** | 用户明确不填微信 | **`full`** **立即退出**，不调任何微信接口（**`--publish`** 也会被忽略）。其它子命令（`token` 等）仍要凭证。 |

### 多账号时如何选槽位

1. 运行 **`python {baseDir}/scripts/publish.py accounts`**，从 **`config.yaml` 的 `wechat_accounts` + `wechat_N_name`** 向用户展示列表（例如：`您有2个账号：1."xiaoming"，2."xiaoz"`）必须询问用户选择哪个账号发布到草稿箱，然后根据用户选择发布到指定的账号。
2. 在 **`config.yaml`** 写 **`wechat_publish_slot: <整数>`**，**或**命令行 **`--account <序号或名称>`**（**CLI 优先**，见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)）。

### 全局环境

在仓库根具备 **`aws.env`**（微信密钥）与 **`config.yaml`**（微信槽位数量与名称）。写作/生图见 **`validate_env.py`**（微信未齐仍可先做内容）。**`publish_method: none`** 时 **`full`** 会跳过；**`draft`/`published`** 发布前建议 **`check-wechat-env`**。API 端点优先取 **`WECHAT_N_API_BASE`**，若槽位未配则回退 **`config.yaml.wechat_api_base`**（两者都空时使用官方）。

### 作者名回退

`full` / `create-draft` 若 **`article.yaml` 无 author**，回退 **`config.yaml`** 的 **`default_author`**。

### `publish_completed`（本篇是否已发布完成）

- 字段在**本篇** **`article.yaml`**。**`publish.py` 不读、不改**；由智能体维护。
- **`false`**：发布流程未闭环。
- **`true`**：已视为发布完成（草稿已确认 / 或 **`published`** 流程成功且运营确认）。

**本篇发布真正结束后**：将 **`publish_completed: true`** 写回 **`article.yaml`**。

**写回 `true` 的前置门禁（缺啥补啥）**：

1. `article.html` 存在；
2. 文章目录存在封面图 `cover.(png/jpg/jpeg/webp)`；
3. `article.md` 与 `article.html` 中均不含 `placeholder`；
4. 发布命令成功并拿到回执（`media_id` 或 `publish_id`）。

任一不满足：只可标记为“已提交草稿，未闭环”，**不得**写回 `publish_completed: true`。

## 用户仅说「发布」且未明确路径时 ⛔

在用户**未给出** `drafts/…` 路径、仅说「发布文章」「帮我发一下」等时：

1. **确定本篇目录**：列出仓库下 **`drafts/`** 中子目录；若**多篇**，请用户**指定一篇**或选「最新修改」的一篇再读该目录 **`article.yaml`**。**勿**在未确认目录时假定路径。
2. 读取该目录 **`article.yaml`** 中的 **`publish_completed`**（YAML 布尔：`true` / `false`；**缺省按 `false` 处理**）。

| `publish_completed` | 智能体对用户说明（可略作口语化，勿改含义） |
|---------------------|---------------------------------------------|
| **`true`** | 告知：**项目里本篇文档已按记录成功发布**；问：**您是否需要编写新文章？** 若需要 → 转交 [main](../aws-wechat-article-main/SKILL.md) / [writing](../aws-wechat-article-writing/SKILL.md) 从本篇准备或选题起走。 |
| **`false`** 或缺省 | 读取 **`article.yaml`** 的 **`title`**（若无则用目录名简述），说明：**《{title}》尚未执行完成（发布流程未闭环）**；问：**是否需要继续并完成发布？** 或 **编写新文章？** 若继续本篇 → 再核对 **`config.yaml`** 的 **`publish_method`**、**`check-screening`**、**`check-wechat-env`** 等。 |

## 工作流

```
发布进度：
- [ ] 前置：配置检查（见本节「配置检查」）⛔
- [ ] 第0步：若用户未给路径 → 选本篇目录 → 读 publish_completed → 按上表分流（true/false）
- [ ] 第1步：读 **`config.yaml`** → **`draft` / `published`**（及是否 **`full --publish`**）
- [ ] 第2步：读取 **`config.yaml`** 的 `wechat_accounts` + `wechat_N_name` 向用户展示账号列表并询问目标槽位；随后跑 **`check-wechat-env`** 校验 `aws.env` 凭证 → **`wechat_publish_slot` 或 `--account`**
- [ ] 第3步：发布前检查（checklist + **`check-screening`** + **`check`**）
- [ ] 第4步：准备文章目录
- [ ] 第5步：**`full`**（仅草稿或含发布，视上步）
- [ ] 第6步：确认结果与用户说明
- [ ] 第7步：成功后写回 **`article.yaml`** 的 **`publish_completed: true`**；按需归档
```

## 交互顺序（最小提问）

0) **未给路径时**：先按上文 **「用户仅说发布」** 处理 **`publish_completed`**；用户选 **继续本篇** 后再做下列步骤。  
1) **先看 `config.yaml` 的 `publish_method`**：**`draft`** = 默认只进草稿箱；**`published`** 或 **`full --publish`** = 再提交发布。  
2) **多槽位**：展示账号列表（来源：`config.yaml` 的 `wechat_accounts` + `wechat_N_name`），**必须请用户选槽位** → **`wechat_publish_slot`** 或 **`--account`**。  
3) 缺微信字段：运行 **`check-wechat-env`**，补全 **`aws.env`** 后再发。  
4) **发布失败**（由脚本 stderr / 微信 errcode 判断）：  
   - **网络类**（超时、连接失败、5xx）：脚本已对单次请求 **自动重试 1 次**；仍失败 → 告知「网络不可用，请稍后重试或检查代理」。  
   - **凭证/配置类**（如 token 失败带 errcode、缺字段）→ 提示 **第几槽位**、检查 **APPID/SECRET、IP 白名单**，用户改正后再执行 **`full`** / **`publish`**。
5) **中间产物缺失**（封面缺失 / 存在 `placeholder`）：先补产物再发；若用户坚持先发草稿，必须明确告知“正文配图未完成”，且保持 `publish_completed: false`。

## 命令示例（仓库根）

```bash
python {baseDir}/scripts/publish.py check-screening
python {baseDir}/scripts/publish.py check-wechat-env
python {baseDir}/scripts/publish.py accounts
python {baseDir}/scripts/publish.py check
python {baseDir}/scripts/publish.py --account 1 full drafts/YYYYMMDD-标题slug/
python {baseDir}/scripts/getdraft.py published-fields
```

详见 [references/usage.md](references/usage.md)、[references/submit-guide.md](references/submit-guide.md)、[references/api-reference.md](references/api-reference.md)。

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.html`、`imgs/`、**`article.yaml`**（含 **`publish_completed`** 等）、**`.aws-article/config.yaml`**、**`aws.env`**（微信槽位） | 发布到公众号草稿或提交发布；**成功后**由智能体将 **`publish_completed: true`** 写回 **`article.yaml`**（`publish.py` 不改此键） |
