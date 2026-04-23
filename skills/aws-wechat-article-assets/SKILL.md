---
name: aws-wechat-article-assets
description: 公众号素材｜素材库｜预设包｜.aws 预设包｜主题包｜品牌包｜aiworkskills.cn — 公众号素材库与预设包管理：图片入库到 stock 目录（中文名 + 同名 .md），导入 .aws ZIP 预设包（本地文件或 `https://aiworkskills.cn/**/*.aws` URL）合并主题/配色/字体配置到 `.aws-article/presets/`；`config.yaml` 仅本地不存在时从包内复制，已存在则 stdout 输出差异 JSON 不覆盖。面向内容运营、品牌团队、设计支持岗。触发词：「素材库入库」「stock images」「上传图到素材库」「.aws」「预设包」「导入预设」「主题包」「aiworkskills.cn 链接」「.aws 下载地址」。
homepage: https://aiworkskills.cn
url: https://github.com/aiworkskills/wechat-article-skills
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 公众号素材与预设（Assets）

**素材与预设统一管理** —— 图片入库 + .aws 预设包导入，多 skill 复用同一套内容资产。

> **套件说明** · 本 skill 属 `aws-wechat-article-*` 一条龙套件（共 9 个 slug，入口 `aws-wechat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录，建议一并 `clawhub install` 全套。源码：<https://github.com/aiworkskills/wechat-article-skills>

## 能力披露（Capabilities）

本 skill 管理本地素材与预设包，可选从 `aiworkskills.cn` 域下载 `.aws` 预设包（ZIP 格式）。

- **凭证**：无
- **网络**：可选 `https://*.aiworkskills.cn/**/*.aws` 下载预设包。**白名单强制**：仅 HTTPS + `aiworkskills.cn` 子域，非白名单会**直接报错退出**。调试参数 `--allow-any-host` 可放宽但不推荐生产使用
- **文件读**：用户指定的本地图片路径或 `.aws` 文件
- **文件写**：仓库内 `.aws-article/assets/stock/images/*`（图片 + 同名 `.md`）、`.aws-article/presets/<子目录>/*`（预设文件）、`.aws-article/downloads/*.aws`（下载缓存）、`.aws-article/tmp/*`（解压临时目录）
- **归档**：解压 `.aws` 扩展名的 ZIP 到 `.aws-article/tmp/`，按白名单子目录合并到 `.aws-article/presets/`。**已内置 ZIP slip 防御**：逐项校验 ZIP 成员路径，拒绝含绝对路径、`..` 段或解析后指向解压目录外的路径，任一违反立即退出不写入任何文件
- **shell**：仅 `python3 {baseDir}/scripts/stock_image_ingest.py`、`import_presets_aws.py`

所有写入限制在仓库根下的 `.aws-article/` 内。

## 配套 skill（informational）

本 skill 是 `aws-wechat-article-*` 一条龙公众号套件的**素材与预设环节**（入口 `aws-wechat-article-main`）。

- **单独安装可用**：素材入库 / `.aws` 预设导入两个脚本都不依赖兄弟 skill，只要 `.aws-article/` 目录就能工作。
- 其他 skill 读取 `.aws-article/assets/stock/images/` 和 `.aws-article/presets/` 里由本 skill 管理的资源，属套件协同；需结合写稿/配图/排版等 skill 使用。

完整 9 slug 清单见 [源码仓库](https://github.com/aiworkskills/wechat-article-skills)。

| 能力 | 说明 |
|------|------|
| **图片入库** | 用户图 → `assets/stock/images/`，供其它 skill 引用 |
| **预设包 `.aws`** | ZIP 包（本地文件或 `https://aiworkskills.cn/**/*.aws` URL）→ 合并 `presets/` 子目录；`config.yaml` 见下 |

---

## 一、图片入库（Stock Images）

### 目录

| 路径 | 作用 |
|------|------|
| `.aws-article/assets/stock/images/` | 入库图片 + 同名 `.md`（固定：**图片路径** / **图片描述**） |

### 工作流

1. 用户上传或给出本地图片路径。
2. **Agent 读图**（多模态能力在本对话侧）：确定**中文主文件名**（如 `淘米`），并写出**客观画面描述**（供 `.md` 与后续配图检索使用）。
3. 在**仓库根**执行（**推荐**带上 `--content`，与第 2 步描述一致）：

```bash
python {baseDir}/scripts/stock_image_ingest.py <源图片路径> --stem "中文名" --content "客观中文描述，一两句即可"
```

若暂未写描述，也可只传 `--stem`（见下「图片描述与占位」）。

4. 生成 `淘米.png` + `淘米.md`（格式见下）。

### 图片描述与占位 ⛔

- **`stock_image_ingest.py` 不会读图**：无视觉/多模态，只负责**复制图片**并**按模板写 `.md`**。
- **未传 `--content`（或为空）** 时，「**图片描述**」会写入固定占位句：**「请根据图片补全（客观描述画面内容即可）。」**——这是预期行为，不是脚本故障。
- **要直接得到可用描述**：入库命令必须带 **`--content "……"`**（由 Agent 读图后填写），或入库后**手动/由 Agent 编辑**同名 `.md` 替换占位段。

### `.md` 固定格式

```markdown
**图片路径**：`.aws-article/assets/stock/images/示例.png`

**图片描述**：……
```

### 脚本 `stock_image_ingest.py`

- `source`、`--stem`（必填）、`--content`（可选，**强烈建议由 Agent 读图后传入**）、`--repo`（可选）

---

## 二、预设包导入（`.aws`）

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

- **预设包内的 `config.yaml` 不应、也不会包含** `aws.env` 中的密钥；仓库密钥始终在仓库根 **`aws.env`**。
- 本地已有 `config.yaml` 时导入不会自动改配置；请根据 stdout 差异与用户确认后再更新字段（或对照 `.aws-article/tmp/` 解压结果）。

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
| `stock_image_ingest.py` | `{baseDir}/scripts/stock_image_ingest.py` |
| `import_presets_aws.py` | `{baseDir}/scripts/import_presets_aws.py` |

## 过程文件

| 场景 | 产出 |
|------|------|
| 图片入库 | `assets/stock/images/*.{png,...}` + 同名 `*.md` |
| `.aws` 导入 | 更新 `.aws-article/presets/**`；`config.yaml` 首次复制或 stdout 差异 JSON；解压缓存在 `.aws-article/tmp/` |
| `.aws` URL 导入 | 下载缓存 `.aws-article/downloads/*.aws`；其余同本地导入 |
