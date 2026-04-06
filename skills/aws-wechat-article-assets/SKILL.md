---
name: aws-wechat-article-assets
description: 公众号素材与预设包：图片入库到 `.aws-article/assets/stock/images`（中文名 + 同名 .md）；或导入 `.aws` 预设包（ZIP）合并到 `.aws-article/presets/`；`config.yaml` 仅本地不存在时从包内复制，已存在则 stdout 输出与包内差异 JSON、不覆盖。触发词含「素材库入库」「stock images」「上传图到素材库」「.aws」「预设包」「导入预设」「主题包」。
---

# 公众号素材与预设（Assets）

| 能力 | 说明 |
|------|------|
| **图片入库** | 用户图 → `assets/stock/images/`，供其它 skill 引用 |
| **预设包 `.aws`** | ZIP 包 → 合并 `presets/` 子目录；`config.yaml` 见下 |

---

## 一、图片入库（Stock Images）

### 目录

| 路径 | 作用 |
|------|------|
| `.aws-article/assets/stock/images/` | 入库图片 + 同名 `.md`（固定：**图片路径** / **图片描述**） |

### 工作流

1. 用户上传或给出本地图片路径。
2. **Agent 读图**，确定**中文主文件名**（如 `淘米`）。
3. 在**仓库根**执行：

```bash
python skills/aws-wechat-article-assets/scripts/stock_image_ingest.py <源图片路径> --stem "中文名"
```

4. 生成 `淘米.png` + `淘米.md`（格式见下）。

### `.md` 固定格式

```markdown
**图片路径**：`.aws-article/assets/stock/images/示例.png`

**图片描述**：……
```

### 脚本 `stock_image_ingest.py`

- `source`、`--stem`（必填）、`--content`（可选）、`--repo`（可选）

---

## 二、预设包导入（`.aws`）

扩展名 **`.aws`**，实质为 **ZIP**。解压后根目录应包含与仓库一致的预设文件夹（可多出其它文件，脚本只处理下列目录）：

`closing-blocks`、`formatting`、`image-styles`、`sticker-styles`、`structures`、`title-styles`

另可有根级 **`config.yaml`**。

### 合并规则

- 每个上述目录：**递归合并**到 `.aws-article/presets/<同名>/`；**同名文件覆盖**，新路径则**新增**。
- **`config.yaml`**：若包内存在且本地**尚无** `.aws-article/config.yaml`，则从包内**复制**；若本地**已有**，则**不覆盖**，按包内字段与本地**同名键**递归比对，将差异以 **JSON 数组** 打印到 **stdout**（`{"key":"点分路径","old":…,"new":…}`），供智能体询问用户后再手改配置；说明日志在 stderr。
- 解压目录：**`.aws-article/tmp/`**（固定路径；运行前若无 `.aws-article` 会创建）。**每次执行前**若 `tmp` 已存在则**整目录删除后重建**，再解压本次 `.aws`；合并到 `presets/` 后**保留**解压结果便于核对，下次导入会再次清空 `tmp` 并覆盖为新包内容。

### 密钥与配置

- **预设包内的 `config.yaml` 不应、也不会包含** `aws.env` 中的密钥；仓库密钥始终在仓库根 **`aws.env`**。
- 本地已有 `config.yaml` 时导入不会自动改配置；请根据 stdout 差异与用户确认后再更新字段（或对照 `.aws-article/tmp/` 解压结果）。

### 工作流

1. 用户上传或提供本地 **`*.aws`** 路径。
2. 可先 **`--dry-run`** 查看将写入的路径。
3. 在**仓库根**执行：

```bash
python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws
python skills/aws-wechat-article-assets/scripts/import_presets_aws.py path/to/bundle.aws --dry-run
```

### 脚本 `import_presets_aws.py`

- 参数：`bundle`（`.aws` 文件路径）、`--dry-run`、`--repo`

---

## 脚本一览

| 脚本 | 路径 |
|------|------|
| `stock_image_ingest.py` | `skills/aws-wechat-article-assets/scripts/stock_image_ingest.py` |
| `import_presets_aws.py` | `skills/aws-wechat-article-assets/scripts/import_presets_aws.py` |

## 过程文件

| 场景 | 产出 |
|------|------|
| 图片入库 | `assets/stock/images/*.{png,...}` + 同名 `*.md` |
| `.aws` 导入 | 更新 `.aws-article/presets/**`；`config.yaml` 首次复制或 stdout 差异 JSON；解压缓存在 `.aws-article/tmp/` |
