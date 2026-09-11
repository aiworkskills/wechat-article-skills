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

本 skill 调 `publish.py` **直连微信公众号官方 API** 发布图文。**会把本篇 `article.html` 与 `imgs/*` 文件作为 POST body 上传到微信服务器。**

- **凭证读取**：`aws.env` 的 `WECHAT_{N}_APPID` / `WECHAT_{N}_APPSECRET`（多槽位，N≥1）
- **凭证外发**：`APPID` / `APPSECRET` 以 query string 发给 `api.weixin.qq.com/cgi-bin/token` 换 `access_token`；后续请求带 `access_token`。微信返回的 token 只在进程内存短期缓存，**不落盘**
- **内容外发**：封面与正文插图以 multipart 发给 `material/add_material`；`article.html` 正文与标题/摘要以 JSON POST 发给 `draft/add`、`freepublish/submit`
- **网络目标**：默认 `api.weixin.qq.com`；可用 `WECHAT_{N}_API_BASE` / `config.yaml.wechat_api_base` 自配反代
- **文件读**：`.aws-article/config.yaml`、`aws.env`、本篇 `article.yaml`、`article.html`、`imgs/*`
- **文件写**：
  - `publish.py` **不写 `article.yaml`**——`media_id` / `publish_id` / `publish_completed` 只打印，写回由智能体做（见下「`publish_completed` 门禁」）
  - 图片超过微信大小限制时会在源图旁生成压缩缓存 `<原名>_compressed.jpg`（需 Pillow）。这个文件**不会被自动清理**，也不会被当作正文图上传
  - `article_init.py` 写本篇 `article.yaml` 与可选 `closing.md`
- **shell**：`{python} {baseDir}/scripts/` 下的 `publish.py`、`getdraft.py`、`article_init.py`

**建议**：首次运行用 `publish_method: draft` 只入草稿箱确认效果，再切 `published` 真正群发。

## 路由

从选题到发出整条流程 → [aws-wechat-article-main](../aws-wechat-article-main/SKILL.md)。本 skill 单独触发适用于**已有 `article.html` 与封面**、只差最后一步上传的场景。

## 配置检查 ⛔

任何操作前先按 **[首次引导 · 检测顺序](../aws-wechat-article-main/references/first-time-setup.md)** 执行，通过后才继续（或用户明确书面确认「本次不检查」）。单独安装本 skill 时的口径见 [branches.md「六」](references/branches.md)。

## 脚本与子命令

`{baseDir}` = 本 SKILL.md 所在目录，所有命令在**仓库根**执行。

| 脚本 / 子命令 | 用途 |
|--------|------|
| **`article_init.py`** | 初始化或更新本篇 `article.yaml`（及可选 `closing.md`）。`{python} {baseDir}/scripts/article_init.py <文章目录> [--title … --author … --digest …]` |
| **`getdraft.py`** | 查已群发文章（`published-list` / `published-fields` / `publish-get` / `article-get`），用于补齐往期推荐链接。见 [branches.md「五」](references/branches.md) |
| `check-screening` | 校验 `config.yaml` 的 `publish_method` |
| `check-wechat-env` | 按 `config.yaml` 槽位检查 `aws.env` 的 `WECHAT_N_APPID` / `APPSECRET` 是否已填 |
| `check` | 环境检查：`aws.env`、各槽位、依赖、可选探测 token |
| `accounts` | 列出 `config.yaml` 中各槽位名称，并标记 `aws.env` 缺项 |
| `full` | 一键全流程（上传封面 → 上传正文图 → 建草稿 → 视配置提交发布） |
| `token` / `upload-thumb` / `upload-content-image` / `create-draft` / `publish` / `status` | 分步操作，见 [usage.md](references/usage.md) |

## `publish_method`（以 `.aws-article/config.yaml` 为准）⛔

| 值 | 含义 | `full` 的行为 |
|----|------|------|
| **`draft`**（默认） | 只进**草稿箱** | 创建草稿后**不**调 freepublish |
| **`published`** | 草稿 + **提交发布** | 创建草稿后继续提交发布（异步）。`full --publish` 可在 `draft` 下**单次强制**带发布 |
| **`none`** | 用户明确不填微信 | **立即退出**，不调任何微信接口（`--publish` 也被忽略）。其它子命令仍要凭证 |

## 多账号选槽位 ⛔

1. 跑 `{python} {baseDir}/scripts/publish.py accounts`，把 `config.yaml` 的 `wechat_accounts` + `wechat_{i}_name` 列给用户（例如「您有 2 个账号：1. xiaoming，2. xiaoz」）。**必须请用户选一个**，不要替他挑。
2. 选定后写 `config.yaml` 的 `wechat_publish_slot: <整数>`，**或**命令行 `--account <序号或名称>`（**CLI 优先**）。

**槽位的数量与名称只来自 `config.yaml`**；`aws.env` 里只有凭证。字段说明见 [articlescreening-schema.md](../aws-wechat-article-main/references/articlescreening-schema.md)。

## `publish_completed` 门禁 ⛔

字段在**本篇 `article.yaml`**。**`publish.py` 不读、不改**，由智能体维护：`false` = 发布流程未闭环，`true` = 已视为发布完成。

**写回 `true` 之前，四项缺一不可：**

1. `article.html` 存在；
2. 文章目录下存在封面 `cover.(png|jpg|jpeg|webp)`（**不在 `imgs/` 里**）；
3. `article.md` 与 `article.html` 中均**不含 `placeholder`**；
4. 发布命令成功并拿到回执（`media_id` 或 `publish_id`）。

任一不满足：只可标记为「已提交草稿，未闭环」，**不得**写回 `publish_completed: true`。

封面裁剪框（2.35:1 / 1:1）的细则见 [branches.md「三」](references/branches.md)。

## 工作流

```
发布进度：
- [ ] 第0步：⛔ 配置检查；用户未给路径 → 先定目录并读 publish_completed 分流
- [ ] 第1步：读 config.yaml 的 publish_method（及是否 full --publish）
- [ ] 第2步：accounts 列账号 → ⛔ 请用户选槽位 → check-wechat-env 校验凭证
- [ ] 第3步：发布前检查（pre-publish-checklist + check-screening + check）
- [ ] 第4步：确认本篇目录产物齐全（article.html、cover.*、无 placeholder）
- [ ] 第5步：full（仅草稿或含发布，视第 1 步）
- [ ] 第6步：确认回执并向用户说明
- [ ] 第7步：⛔ 四项门禁全过 → 写回 publish_completed: true
```

第 0 步的分流表见 [branches.md「一」](references/branches.md)；第 3 步清单见 [references/pre-publish-checklist.md](references/pre-publish-checklist.md)；第 5/6 步失败时的四类处理见 [branches.md「二」](references/branches.md)。

## 命令示例（仓库根）

```bash
{python} {baseDir}/scripts/publish.py check-screening
{python} {baseDir}/scripts/publish.py check-wechat-env
{python} {baseDir}/scripts/publish.py accounts
{python} {baseDir}/scripts/publish.py check
{python} {baseDir}/scripts/publish.py --account 1 full drafts/YYYYMMDD-标题slug/
{python} {baseDir}/scripts/getdraft.py published-fields
```

注意 `--account` 是**全局选项，放在子命令之前**。

## 分支与异常

未给路径的分流、发布失败四分类、封面裁剪框、几处回退、往期链接补齐、单独安装 → [references/branches.md](references/branches.md)。

更多用法：[usage.md](references/usage.md)、[submit-guide.md](references/submit-guide.md)、[api-reference.md](references/api-reference.md)。

## 过程文件

| 读取 | 产出 |
|------|------|
| `article.html`、`cover.*`、`imgs/`、本篇 `article.yaml`、`.aws-article/config.yaml`、`aws.env` | 公众号草稿或已提交发布；**成功后**由智能体把 `publish_completed: true` 写回 `article.yaml`（`publish.py` 不改此键） |
