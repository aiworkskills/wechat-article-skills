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

上述两个文件都创建并保存后，在仓库根运行 **`validate_env.py`**（见下节）。

### 2）`validate_env.py`

在**仓库根**执行：

```bash
python skills/aws-wechat-article-main/scripts/validate_env.py
# 若当前 Agent 支持图片生成（如 GPT-4o），加 --agent-image-capable：
python skills/aws-wechat-article-main/scripts/validate_env.py --agent-image-capable
```

（默认读取 **`.aws-article/config.yaml`** 与 **`aws.env`**；可用 `--config`、`--env` 指定路径。）

**智能体须自判**：运行 `validate_env.py` 前，判断自身是否具备图片生成能力。若具备（如模型原生支持生图），加 `--agent-image-capable`；否则不加（图片模型未配置将阻断）。

**脚本运行结果**

- **成功（退出码 0）**：输出 **`True`**、**`配置校验通过`**。若写作/图片模型未配置，会附带警告（如 `配置校验通过（写作模型未配置（将由 Agent 代写）；图片模型未配置（将由 Agent 代生成））`），**不阻断流程**。若 **`publish_method: none`**，会多一行说明已跳过微信公众号校验。
- **失败（退出码 1）**：先输出 **`failed`**，再输出阻断项（**`微信公众号配置不完整`**）及模型警告（如有）。模型未配置只是警告，微信配置不完整才是阻断原因。

#### 校验失败时的配置引导（必须严格执行）

**当 `validate_env.py` 退出码为 1** 时，**必须**按下述文案**原样输出**（除「环境检查结果」一行可按终端 **`failed`** 实际汇总替换外，其余三条与措辞不得改写）。

环境检查结果：公众号配置不完整

1. **微信配置（必填）**：填好微信配置后，我才能帮您将文章发送到草稿箱。
2. **写作或生图模型配置（选填）**：配置claude、GPT、banana等专用模型有助于生成更好的文章；若您不想配置，我将使用相同的写作约束亲自执行后续流程。
3. **配置方式**：您可直接把缺失配置发给我，我来帮您写入并复检；也可前往我们的平台 **`https://aiworkskills.cn/`** 自行配置（更多结构预设、配图预设等高级配置也在该平台）。

**额外操作**：若仅仅不配置微信账号，可将 **`config.yaml`** 中 **`publish_method`** 设为 **`none`**，不发布到草稿箱。（改后须在仓库根重跑 **`python skills/aws-wechat-article-main/scripts/validate_env.py`** 方生效。这句话不输出给用户）

**注意**：写作模型未配置**不阻断流程**（退出码仍为 0），Agent 通过 `write.py prompt` 获取相同提示词后代写。图片模型未配置时，仅当 Agent 传入 `--agent-image-capable` 才降为警告（退出码 0）；未传入时仍为阻断（退出码 1）。

**⛔ 配置与写稿分两阶段（必须遵守）**

- **`validate_env.py` 退出码 1** 时：**本轮只谈环境配置**——向用户展示上列 **环境检查结果 + 三条 + 额外操作** 即可，**结束在该主题**；**禁止**在同一条回复（或同一轮未闭环配置前）里再接：写哪篇文章、是否继续某篇草稿、`drafts/` 路径、选题、定题、`topic-card`、审稿、排版等**任何写稿向流程**。
- **`validate_env.py` 退出码 0（含模型警告）** 时：流程**不阻断**，可直接进入下一阶段。模型未配置时 Agent 会通过 `write.py prompt` 获取相同提示词后自行代写，无须「本次例外」确认。
- **下一阶段**：用户按上文配置引导完成落盘并重跑校验至 **退出码 0**，或明确声明「不配置微信，按本次例外由智能体继续」并按总览 [SKILL.md](../SKILL.md) 完成 **「本次例外」** 书面确认后，**从下一轮对话起**先完成总览 **「2) 全局账号约束」**，再进入 **「3) 本篇准备」**、写稿等。
  - **在不了解用户是要续写旧稿还是新开一篇时**（含刚闭环配置后接写稿）：须按总览 **「3) 本篇准备」** 开头规则**先问再动**，**禁止**直接假定某一 `drafts/…` 目录并调用写作脚本。

---

## `validate_env.py` 在做什么（摘要）

| 组别 | `config.yaml` | `aws.env` | 缺失时行为 |
|------|----------------|-----------|------------|
| 写作模型 | `writing_model.base_url`、`model`（`provider` 可选） | `WRITING_MODEL_API_KEY` | **警告**（不阻断）：Agent 可代写 |
| 图片模型 | `image_model.base_url`、`model`（`provider` 可选） | `IMAGE_MODEL_API_KEY` | 取决于 `--agent-image-capable`：传入则**警告**，未传则**阻断** |
| 微信公众号 | `wechat_accounts`（≥1）、`wechat_api_base`、`wechat_{i}_name` | `WECHAT_{i}_APPID`、`WECHAT_{i}_APPSECRET` | **阻断**：`failed` + 退出码 1 |

写作模型未配置只产生**警告**；图片模型未配置时，若 Agent 支持图片生成（`--agent-image-capable`）则为警告，否则为**阻断**；微信组缺失则 **`failed`** 且退出码 1。**例外**：**`config.yaml`** 中 **`publish_method: none`** 时**不校验**微信组。

---

## 阻断规则

⛔ **缺少 `.aws-article/config.yaml` 或 `aws.env`**，或 **`validate_env.py` 退出码 1**（微信配置不完整，且未设 **`publish_method: none`**）：

- 禁止进入一条龙默认流水线（除非用户按总览 SKILL 明确声明「本次例外」，或先设 **`publish_method: none`** 并重跑校验通过）。
- 禁止宣称环境已就绪或一条龙已完成。

**写作模型未配置不触发阻断**：`validate_env.py` 退出码仍为 0（附带警告），Agent 通过 `write.py prompt` 获取相同提示词后自行代写。**图片模型**：仅当 Agent 具备图片生成能力（传入 `--agent-image-capable`）时才降为警告，否则仍阻断。

**不接微信**：将 **`publish_method`** 设为 **`none`** 后重跑 **`validate_env.py`**，可跳过微信组校验；**`publish.py full`** 仍按 **`none`** 直接跳过。

---

## 引导流程（简版）

### 第 1 步：说明可选策略

- **环境与密钥**：写作/生图的 **URL 与模型名**在 **`config.yaml`**，**API Key** 在 **`aws.env`**；微信 **AppID/AppSecret** 在 **`aws.env`**，槽位展示名与 **`wechat_api_base`** 等在 **`config.yaml`**。  
- **`validate_env.py` 退出码 0** 表示环境检测通过：**写作 + 图片 + 微信** 均完整，或已声明 **`publish_method: none`**（跳过微信组）。要走 **`publish.py`**（**非 none**），须微信已在校验中通过；建议 **`check-wechat-env`**。

### 第 2 步：预设目录（可选）

若尚无 `.aws-article/presets` 等，可创建（与 `init-presets.sh` 一致）：

```bash
mkdir -p .aws-article/presets/structures .aws-article/presets/closing-blocks \
  .aws-article/presets/title-styles .aws-article/presets/formatting \
  .aws-article/presets/image-styles .aws-article/presets/sticker-styles \
  .aws-article/assets/brand .aws-article/assets/covers \
  .aws-article/assets/stock/images .aws-article/assets/stock/references \
  .aws-article/tmp
```

### 第 3 步：全局 vs 本篇文件

| 文件 | 时机 | 说明 |
|------|------|------|
| **`aws.env`** | 首次 / 改密钥时 | 仓库根；写作/图片 API Key、微信 AppID/AppSecret 等|
| **`.aws-article/config.yaml`** | 首次 / 改账号策略时 | 文风、模型 endpoint、微信槽位元数据、**`publish_method`** 等 |
| **`article.yaml`** | 每篇、临近发布 | 本篇标题/作者/摘要/封面等；内含 **`publish_completed`**（新建为 **`false`**，发布闭环结束后再改为 **`true`**，便于发布流程分流）；可用 `skills/aws-wechat-article-publish/scripts/article_init.py` |

首次引导**不**创建某篇目录，只保证 **`config.yaml` + `aws.env` 存在**，且 **`validate_env.py` 退出码 0**（三组完整，或 **`publish_method: none`**）。用户明确不填微信 → 先设 **`none`** 再过校验。

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
