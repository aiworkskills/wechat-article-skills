# 首次引导 ⛔ BLOCKING

任何操作执行前，必须执行以下 **「检测顺序」** 中的检查步骤。

---

一条龙 / 总览流水线：**先具备仓库根 `aws.env`、`.aws-article/config.yaml`，并通过 `validate_env.py`**，再按总览 [SKILL.md](../SKILL.md) 交互顺序完成 **「2) 全局账号约束」**：**`article_category` / `target_reader` / `default_author` 须由用户确认后再写入** `config.yaml`（**禁止**从某篇 `article.yaml` 擅自抄录），再进入 **「3) 本篇准备」**。

总览规则见 [SKILL.md](../SKILL.md)「配置检查」。

---

## 检测顺序（智能体先判断 OS）

- **Linux / macOS**：下文用 Bash。
- **Windows**：下文用 PowerShell。

### 1）`.aws-article/config.yaml` 与 `aws.env` 是否存在（仓库根）

```bash
test -f .aws-article/config.yaml && test -f aws.env && echo ok || echo missing
```

```powershell
if ((Test-Path -LiteralPath ".aws-article\config.yaml") -and (Test-Path -LiteralPath "aws.env")) { "ok" } else { "missing" }
```

⛔ 若为 `missing`，按示例各建一份即可：

1. **`.aws-article/config.yaml`**：复制 **`skills/aws-wechat-article-main/references/config.example.yaml`** 为 **`.aws-article/config.yaml`**。
2. **`aws.env`**：复制 **`skills/aws-wechat-article-main/references/env.example.yaml`** 为仓库根 **`aws.env`**（内容格式为 `KEY=value`）。

**初始化约束**：新建 **`.aws-article/config.yaml`** 时，**`publish_method` 必须初始化为 `draft`**；除非用户明确指定「不接微信/不走上传」，否则禁止初始化为 `none`。

上述两个文件都创建并保存后，在仓库根运行 **`validate_env.py`**（见下节）。

### 2）`validate_env.py`

在**仓库根**执行：

```bash
python skills/aws-wechat-article-main/scripts/validate_env.py
```

（默认读取 **`.aws-article/config.yaml`** 与 **`aws.env`**；可用 `--config`、`--env` 指定路径。）

**脚本运行结果**

- **成功（退出码 0）**：输出 **`True`**、**`配置校验通过`**。写作模型、图片模型或 `wechat_N_name` 未配置时会附带警告，但不影响退出码。
- **失败（退出码 1）**：先输出 **`failed`**，再输出微信必要配置的实际缺失项。

#### 校验失败时的配置引导（必须严格执行）

`validate_env.py` 会完成全部检查后统一输出结果。**当退出码为 1** 时，按实际失败项说明：

环境检查结果：公众号必要配置不完整

1. **必填项**：`wechat_accounts`、`wechat_api_base`，以及每个槽位的 `WECHAT_N_APPID` / `WECHAT_N_APPSECRET`。
2. **配置方式（二选一，**不要把密钥粘贴到聊天里**）**：
   - **方式 A（推荐）**：在仓库根用编辑器打开 **`aws.env`** 填入 `WECHAT_1_APPID` / `WECHAT_1_APPSECRET` 等，并在 **`.aws-article/config.yaml`** 填入 `wechat_accounts` / `wechat_api_base` 等非密钥项，保存后告诉我「已填好」我来复检。
   - **方式 B**：前往平台 **`https://aiworkskills.cn/`** 在网页上配。

**原则**：Agent **不向用户索取密钥**、**不代替用户粘贴密钥到文件**。密钥只由用户在本地编辑器中写入 `aws.env`；validate_env 只做非空校验，不读值外发。

**额外操作**：若用户明确表示不配置微信账号，可将 **`config.yaml`** 中 **`publish_method`** 设为 **`none`**，重跑后跳过微信组校验。写作和图片模型均为可选项。

**⛔ 配置与写稿分两阶段（必须遵守）**

- **`validate_env.py` 退出码 1** 时：**本轮只谈环境配置**——按当前失败分支展示 **环境检查结果 + 三条 + 额外操作** 即可，**结束在该主题**；**禁止**在同一条回复（或同一轮未闭环配置前）里再接：写哪篇文章、是否继续某篇草稿、`drafts/` 路径、选题、定题、`topic-card`、审稿、排版等**任何写稿向流程**。
- **`validate_env.py` 退出码 0（含可选项警告）** 时：流程**不阻断**，可直接进入下一阶段。
- **下一阶段**：用户按上文配置引导完成落盘并重跑校验至 **退出码 0** 后，先完成总览 **「2) 全局账号约束」**，再进入 **「3) 本篇准备」**、写稿等。
  - **在不了解用户是要续写旧稿还是新开一篇时**（含刚闭环配置后接写稿）：须按总览 **「3) 本篇准备」** 开头规则**先问再动**，**禁止**直接假定某一 `drafts/…` 目录并调用写作脚本。

---

## `validate_env.py` 在做什么（摘要）

| 组别 | `config.yaml` | `aws.env` | 缺失时行为 |
|------|----------------|-----------|------------|
| 微信公众号 | `wechat_accounts`（≥1）、`wechat_api_base` | `WECHAT_{i}_APPID`、`WECHAT_{i}_APPSECRET` | **阻断**：`failed` + 退出码 1 |
| 公众号展示名 | `wechat_{i}_name` | — | **警告**，不阻断 |
| 写作模型 | `writing_model.base_url`、`model`（`provider` 可选） | `WRITING_MODEL_API_KEY` | **警告**，不阻断 |
| 图片模型 | `image_model.base_url`、`model`（`provider` 可选） | `IMAGE_MODEL_API_KEY` | **警告**，不阻断 |

模型与公众号展示名均为可选项。微信槽位与 AppID/AppSecret 保持原有必填规则；`publish_method: none` 时保持原有的跳过微信组逻辑。

---

## 阻断规则

⛔ **缺少 `.aws-article/config.yaml` 或 `aws.env`**，或 **`validate_env.py` 退出码 1**（微信必要配置不完整）：

- 禁止进入一条龙默认流水线（除非先设 **`publish_method: none`** 并重跑校验通过）。
- 禁止宣称环境已就绪或一条龙已完成。

写作/图片模型或 `wechat_N_name` 缺失只产生警告，不触发阻断。

---

## 引导流程（简版）

### 第 1 步：说明可选策略

- **环境与密钥**：写作/生图的 **URL 与模型名**在 **`config.yaml`**，**API Key** 在 **`aws.env`**；微信 **AppID/AppSecret** 在 **`aws.env`**，槽位展示名与 **`wechat_api_base`** 等在 **`config.yaml`**。  
- **`validate_env.py` 退出码 0** 表示微信必要配置已通过，或已通过 **`publish_method: none`** 跳过微信组；写作/图片模型或展示名可带警告通过。发布前建议再运行 **`check-wechat-env`**。

### 第 2 步：检查通过以后检查并创建预设目录（这个必须执行）

通过环境检查后，必须先判断以下目录是否存在；**不存在就立即创建**：

- `.aws-article/presets/structures`
- `.aws-article/presets/closing-blocks`
- `.aws-article/presets/title-styles`
- `.aws-article/presets/formatting`
- `.aws-article/presets/cover-styles`
- `.aws-article/presets/image-styles`
- `.aws-article/presets/sticker-styles`
- `.aws-article/tmp`

> **业务资料库 `.aws-article/products/{产品名}/`**：**不在首次引导创建**——产品名由用户在写第一份业务介绍时决定，AI 用 Write 工具落库时同时 `mkdir -p` 包括 `images/`，详见 [assets skill 一、业务介绍 .md 入库](../../aws-wechat-article-assets/SKILL.md#一业务介绍-md-入库product-intro)。

可按操作系统执行：

```bash
# Linux / macOS
mkdir -p .aws-article/presets/structures .aws-article/presets/closing-blocks \
  .aws-article/presets/title-styles .aws-article/presets/formatting \
  .aws-article/presets/cover-styles .aws-article/presets/image-styles \
  .aws-article/presets/sticker-styles \
  .aws-article/tmp
```

```powershell
# Windows PowerShell
$dirs = @(
  ".aws-article/presets/structures",
  ".aws-article/presets/closing-blocks",
  ".aws-article/presets/title-styles",
  ".aws-article/presets/formatting",
  ".aws-article/presets/cover-styles",
  ".aws-article/presets/image-styles",
  ".aws-article/presets/sticker-styles",
  ".aws-article/tmp"
)
foreach ($d in $dirs) {
  if (-not (Test-Path -LiteralPath $d)) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
  }
}
```

### 第 3 步：全局 vs 本篇文件

| 文件 | 时机 | 说明 |
|------|------|------|
| **`aws.env`** | 首次 / 改密钥时 | 仓库根；写作/图片 API Key、微信 AppID/AppSecret 等|
| **`.aws-article/config.yaml`** | 首次 / 改账号策略时 | 文风、模型 endpoint、微信槽位元数据、**`publish_method`** 等 |
| **`article.yaml`** | 每篇、临近发布 | 本篇标题/作者/摘要/封面等；内含 **`publish_completed`**（新建为 **`false`**，发布闭环结束后再改为 **`true`**，便于发布流程分流）；可用 `skills/aws-wechat-article-publish/scripts/article_init.py` |

首次引导**不**创建某篇目录，只保证 **`config.yaml` + `aws.env` 存在**，且 **`validate_env.py` 退出码 0**（微信必要配置完整，或 **`publish_method: none`**；可选项可带警告通过）。

### 第 4 步：确认并继续

摘要提示用户（勿打印完整密钥）：

- **`validate_env.py` 退出码 0**：环境检测通过，可按总览进入流水线。**要走 `publish.py`（非 none）** 前建议 **`check-wechat-env`**。  

可提示：写作规范可复制 **`skills/aws-wechat-article-main/references/writing-spec.example.md`** → **`.aws-article/writing-spec.md`**；预设见 **`.aws-article/presets/`**。

---

## 非首次运行

**每次**进入一条龙、或**仅**触发写作 / 配图 / 发布检查前，都须在仓库根执行：

```bash
python skills/aws-wechat-article-main/scripts/validate_env.py
```

**智能体**：若退出码非 0，根据终端 **`failed`** 下列出的汇总句，按上文 **「校验失败时的配置引导」** 文案**原样输出**（含三条配置引导 + **额外操作**）；用户补全并落盘后重跑 **`validate_env.py`**。若用户**明确声明本次例外**，按总览 [SKILL.md](../SKILL.md)「智能体行为约束」处理。**禁止**未获补全或明确例外确认就宣称已通过环境校验或一条龙已完成。**禁止**因「上次已通过」而跳过本节命令。

---

## 每次发文目录与顺序（摘要）

- 目录：`drafts/YYYYMMDD-标题slug/`（`drafts_root` 以 **`config.yaml`** 为准时从其读取，否则默认 `drafts/`）。  
- 建议内含：`draft.md`、`article.md`、`article.html`、`article.yaml`、`imgs/`、`out/` 等（按需生成）。  
- 流程：定题 → 选题 → 写稿 → 审 → 排版 → 配图 → 终审 → **按需发布**：**`draft`** / **`published`** / **`none`** 见 schema；**`none`** 时 **`full`** 直接跳过；**`draft`/`published`** 须微信就绪（**`check-wechat-env`**）。  

本篇 **`article.yaml`** 必填项：`title`、`author`、`digest`、`content_source`（默认 `article.html`）、**`publish_completed`**（新建 **`false`**，发布成功后再改为 **`true`**）；**`cover_image`** 强烈建议填写。
