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

本 skill 管理本地业务资料库与预设包，可选从 `aiworkskills.cn` 域下载 `.aws` 预设包（ZIP 格式）。

- **凭证**：无
- **网络**：可选 `https://*.aiworkskills.cn/**/*.aws` 下载预设包。**白名单强制**：仅 HTTPS + `aiworkskills.cn` 子域，非白名单会**直接报错退出**。调试参数 `--allow-any-host` 可放宽但不推荐生产使用
- **文件读**：用户指定的本地图片路径或 `.aws` 文件（脚本边界）；AI 在引导业务介绍入库时会先 `ls .aws-article/products/` 看已有产品名
- **文件写**：仓库内 `.aws-article/products/{产品名}/*.md`（业务介绍，AI 用 Write 工具直接落库）、`.aws-article/products/{产品名}/images/*`（图片 + 同名 `.md`，由脚本写）、`.aws-article/presets/<子目录>/*`（预设文件）、`.aws-article/downloads/*.aws`（下载缓存）、`.aws-article/tmp/*`（解压临时目录）；导入 `.aws` 时**仓库根 `aws.env`** 会按映射表增量写入密钥字段（覆盖现有键前自动备份为 `aws.env.bak.{ts}`，stderr 仅打印键名不打印值）
- **归档**：解压 `.aws` 扩展名的 ZIP 到 `.aws-article/tmp/`，按白名单子目录合并到 `.aws-article/presets/`。**已内置 ZIP slip 防御**：逐项校验 ZIP 成员路径，拒绝含绝对路径、`..` 段或解析后指向解压目录外的路径，任一违反立即退出不写入任何文件
- **shell**：仅 `python3 {baseDir}/scripts/product_image_ingest.py`、`import_presets_aws.py`

所有写入限制在仓库根下的 `.aws-article/` 内。

## 配套 skill（informational）

本 skill 是 `aws-wechat-article-*` 一条龙公众号套件的**业务资料库与预设环节**（入口 `aws-wechat-article-main`）。

- **单独安装可用**：业务图入库 / `.aws` 预设导入两个脚本都不依赖兄弟 skill，只要 `.aws-article/` 目录就能工作。
- 其他 skill 读取 `.aws-article/products/{产品名}/`（业务介绍 + `images/`）和 `.aws-article/presets/` 里由本 skill 管理的资源，属套件协同；需结合写稿/配图/排版等 skill 使用。

完整 9 slug 清单见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

| 能力 | 说明 |
|------|------|
| **业务介绍 .md 入库** | AI 与用户对话产出业务介绍内容时，引导/响应保存到 `products/{产品名}/<文件名>.md`（用 Write 工具直接落库，无脚本） |
| **业务图入库** | 用户业务图 → `products/{产品名}/images/`（脚本 `--product` 必填），供其它 skill 引用 |
| **预设包 `.aws`** | ZIP 包（本地文件或 `https://aiworkskills.cn/**/*.aws` URL）→ 合并 `presets/` 子目录；`config.yaml` 见下 |

---

## 〇、设计意图（必读）⛔

`.aws-article/products/{产品名}/` 是**用户自家业务**（卖货 / 卖软件 / 卖服务 / 自媒体 IP 等）的**资料库**——既是 AI 写涉及业务的内容时的**底稿来源**，也是 AI 与用户协作产出新介绍时的**保存目的地**。

### 目录约定

```
.aws-article/products/{产品名}/
├─ 项目介绍.md                # 业务介绍 .md 直挂产品根（命名按用户行业，如 服务介绍.md / 品牌介绍.md）
├─ (其他业务文档.md)
└─ images/
   ├─ 配置首页.png
   └─ 配置首页.md             # 图片说明 .md（同名）
```

### 双向触发

| 方向 | 触发条件 | 行为 |
|------|---------|------|
| **读** | 当前任务涉及用户自家业务（对外介绍 / 教程 / 案例 / 自家业务安利 / 业务相关配图） | 先 `ls .aws-article/products/`，识别本篇相关产品，读该产品根下 `*.md`、查 `images/` 同名 `.md`，把已有素材作为底稿/配图候选 |
| **写** | AI 在会话中刚生成或改写的内容**语义属于用户业务介绍** | 走 [一、业务介绍 .md 入库](#一业务介绍-md-入库product-intro)；用户主动说"保存为产品介绍"等也走此流程 |

### 反例（不要触发）

- 主题是行业资讯 / 通用教程 / 与用户业务无关 → 不读、不写
- 用户明确表示内容"还没定型" → 不主动引导保存
- AI 不确定是不是用户自家业务时 → 宁可不主动提，也不要乱塞进 `products/`

---

## 一、业务介绍 .md 入库（Product Intro）

无需脚本，AI 用 Write 工具直接落库。

### 触发模式 A：AI 主动识别 + 引导

AI 在任意会话中刚生成或刚改写了一段内容，**其语义明确属于用户自家业务介绍**（产品 / 服务 / 品牌 / 项目 / 团队 / 业务范围介绍）时，主动提示用户：

> "这段是 [产品名] 的业务介绍，要不要保存到产品资料库？我可以存到 `.aws-article/products/{产品名}/{文件名}.md`，下次写涉及业务的文章时会自动用上。"

用户确认 → 走「保存流程」。

### 触发模式 B：用户主动指令

用户说类似 "保存为产品介绍 / 业务介绍 / 服务介绍 / 自家介绍 / 入库到产品 / 存到产品资料库" 时，AI 把当前会话中的目标内容（用户指定段落或最近相关产出）走「保存流程」。

### 保存流程

1. **确认产品名**：`ls .aws-article/products/`，已有目录则提示复用；新产品则向用户拿名字
2. **确认文件名**：默认 `项目介绍.md`；可改为 `产品介绍.md` / `服务介绍.md` / `品牌介绍.md` / `业务介绍.md` 等贴用户行业的命名
3. **创建目录**：`mkdir -p .aws-article/products/{产品名}/images/`（即便暂为空，把骨架建齐）
4. **写入文件**：用 Write 工具落到 `.aws-article/products/{产品名}/{文件名}.md`
5. **反馈**：「已存到 `<完整路径>`，下次涉及 [产品名] 业务的文章会自动用上」

---

## 二、业务图入库（Product Images）

### 目录

| 路径 | 作用 |
|------|------|
| `.aws-article/products/{产品名}/images/` | 入库图片 + 同名 `.md`（固定：**图片路径** / **图片描述**） |

### 工作流

1. 用户上传或给出本地图片路径，并指明**所属产品**（与 `products/` 下某个目录对应；新产品则脚本会自动创建）。
2. **Agent 读图**（多模态能力在本对话侧）：确定**中文主文件名**（如 `配置首页`），并写出**客观画面描述**（供 `.md` 与后续配图检索使用）。
3. 在**仓库根**执行（**推荐**带上 `--content`，与第 2 步描述一致）：

```bash
python {baseDir}/scripts/product_image_ingest.py <源图片路径> \
  --product "公众号AI运营助手" --stem "配置首页" \
  --content "客观中文描述，一两句即可"
```

`--product` **必填**；产品目录与 `images/` 子目录不存在时**自动创建**。

4. 生成 `配置首页.png` + `配置首页.md`（格式见下）。

### 图片描述与占位 ⛔

- **`product_image_ingest.py` 不会读图**：无视觉/多模态，只负责**复制图片**并**按模板写 `.md`**。
- **未传 `--content`（或为空）** 时，「**图片描述**」会写入固定占位句：**「请根据图片补全（客观描述画面内容即可）。」**——这是预期行为，不是脚本故障。
- **要直接得到可用描述**：入库命令必须带 **`--content "……"`**（由 Agent 读图后填写），或入库后**手动/由 Agent 编辑**同名 `.md` 替换占位段。

### `.md` 固定格式

```markdown
**图片路径**：`.aws-article/products/公众号AI运营助手/images/示例.png`

**图片描述**：……
```

### 脚本 `product_image_ingest.py`

- `source`、`--product`（**必填**）、`--stem`（必填）、`--content`（可选，**强烈建议由 Agent 读图后传入**）、`--repo`（可选）

---

## 三、预设包导入（`.aws`）

扩展名 **`.aws`**，实质为 **ZIP**。解压后根目录应包含与仓库一致的预设文件夹（可多出其它文件，脚本只处理下列目录）：

`closing-blocks`、`cover-styles`、`formatting`、`image-styles`、`sticker-styles`、`structures`、`title-styles`

另可有根级 **`config.yaml`**、**`writing-spec.md`**。

### 输入来源（本地 / URL）

`bundle` 参数同时接受两种形态：

- **本地路径**：`./brand-a.aws` 或绝对路径
- **HTTPS URL**：仅限 `aiworkskills.cn` 及其子域，必须 `https://` 开头、路径以 `.aws` 结尾
  - 示例：`https://aiworkskills.cn/bundles/brand-a.aws`
  - 下载缓存：`.aws-article/downloads/<原文件名>`（**不在 `tmp/` 内**，不受清空影响，保留供事后核对）
  - 不在白名单、非 https、或下载内容非 ZIP → **直接报错退出**
  - 调试放宽：`--allow-any-host` 可跳过域名白名单（仍强制 https）；不建议生产使用

### 合并规则

- 每个上述目录采用**「替换式」语义**（以服务端为准，避免旧文件残留）：
  - 若**包内存在**该子目录 → **先清空本地 `.aws-article/presets/<同名>/` 再写入包内内容**（旧包里有、新包里删掉的文件不会残留）；
  - 若**包内不存在**该子目录 → 本地对应子目录**保持不动**（不受本次导入影响）。
  - 包根优先级：若包根下**同时**存在 **`presets/<名>/`** 与 **`<名>/`**，脚本**优先合并前者**；若目录内仅有一层多余 **`<名>/<名>/`**，脚本会自动以内层为合并根。
- **`config.yaml`**：若包内存在且本地**尚无** `.aws-article/config.yaml`，则从包内**复制**；若本地**已有**，则**不覆盖**，按包内字段与本地**同名键**递归比对，将差异以 **JSON 数组** 打印到 **stdout**（`{"key":"点分路径","old":…,"new":…}`），供智能体询问用户后再手改配置；说明日志在 stderr。
- **`writing-spec.md`**：若包内存在，**始终覆盖**写入 **`.aws-article/writing-spec.md`**（与 `config.yaml` 不同，不做差异比对）。
- 解压目录：**`.aws-article/tmp/`**（固定路径；运行前若无 `.aws-article` 会创建）。**每次执行前**若 `tmp` 已存在则**整目录删除后重建**，再解压本次 `.aws`；合并到 `presets/` 后**保留**解压结果便于核对，下次导入会再次清空 `tmp` 并覆盖为新包内容。

### 密钥与配置

- **`config.yaml` 中的密钥字段会被增量写入仓库根 `aws.env`**。包内 `config.yaml` 顶层 `wechat_appid` / `wechat_appsecret`、嵌套 `writing_model.api_key` / `image_model.api_key` 在导入时按下表映射写入：

  | `config.yaml` 字段 | `aws.env` 键 |
  |---|---|
  | `wechat_appid` | `WECHAT_1_APPID` |
  | `wechat_appsecret` | `WECHAT_1_APPSECRET` |
  | `writing_model.api_key` | `WRITING_MODEL_API_KEY` |
  | `image_model.api_key` | `IMAGE_MODEL_API_KEY` |

- 写入策略：包内字段为空 → 不动 `aws.env` 现有键；`aws.env` 无该键 → 追加；已有相同值 → 跳过；已有不同值 → 写入前备份 `aws.env.bak.{ts}` 后覆盖。stderr 仅输出键名清单，不打印密钥值；保留原文件顺序、空行与注释。当前前端导出仅支持单微信账号（固定槽位 1），`aws.env` 中的 `WECHAT_2_*` 等其他键不受导入影响。
- `config.yaml`（运营配置）：本地无则首次复制；本地有则差异 JSON 输出到 stdout 不覆盖（与原行为一致），由 Agent 询问用户确认后手改。

### 工作流

1. 准备 `*.aws` 来源：**(a)** 本地文件（上传或已有路径），或 **(b)** 符合白名单的 **HTTPS URL**。
2. 可先 **`--dry-run`** 查看将写入的路径（URL 模式下仍会实际下载到 `downloads/` 以便校验 ZIP 结构，但不写入 `presets/` 与 `config.yaml`）。
3. 在**仓库根**执行：

```bash
# 本地路径
python {baseDir}/scripts/import_presets_aws.py path/to/bundle.aws
python {baseDir}/scripts/import_presets_aws.py path/to/bundle.aws --dry-run

# URL（仅 aiworkskills.cn 及子域）
python {baseDir}/scripts/import_presets_aws.py https://aiworkskills.cn/bundles/brand-a.aws
python {baseDir}/scripts/import_presets_aws.py https://aiworkskills.cn/x/y.aws --dry-run
```

### 脚本 `import_presets_aws.py`

- 参数：`bundle`（`.aws` 路径 或 `https://*.aiworkskills.cn` URL）、`--dry-run`、`--repo`、`--allow-any-host`（调试）

---

## 脚本一览

| 脚本 | 路径 |
|------|------|
| `product_image_ingest.py` | `{baseDir}/scripts/product_image_ingest.py` |
| `import_presets_aws.py` | `{baseDir}/scripts/import_presets_aws.py` |

## 过程文件

| 场景 | 产出 |
|------|------|
| 业务介绍 .md 入库 | `.aws-article/products/{产品名}/{文件名}.md`（AI 用 Write 工具落库；目录不存在时同时 mkdir 包括 `images/`） |
| 业务图入库 | `.aws-article/products/{产品名}/images/*.{png,...}` + 同名 `*.md` |
| `.aws` 导入 | 更新 `.aws-article/presets/**`；`config.yaml` 首次复制或 stdout 差异 JSON；密钥增量写入仓库根 `aws.env`（覆盖前备份 `aws.env.bak.{ts}`）；解压缓存在 `.aws-article/tmp/` |
| `.aws` URL 导入 | 下载缓存 `.aws-article/downloads/*.aws`；其余同本地导入 |
