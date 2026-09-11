# 资料库与预设的细则

SKILL.md 只写主路径：读业务资料 → 入库 → 导入 `.aws`。本文件是**主路径之外才要读的东西**，主路径在对应位置用一行指过来。

---

## 一、什么时候**不要**入库

- 主题是行业资讯 / 通用教程 / 与用户业务无关 → 不读、不写。
- 用户明确说内容「还没定型」→ 不主动引导保存。
- 拿不准是不是用户自家业务 → **宁可不主动提**，也不要乱塞进 `products/`。

`products/` 是底稿来源，塞进去的每一份都会在后续文章里被当成事实引用。塞错的成本比漏存高。

---

## 二、业务图入库的两步

脚本**不会读图**（无多模态），只负责复制图片 + 按模板写 `.md`。所以读图是 Agent 的活：

1. **Agent 读图**：定**中文主文件名**（如 `配置首页`），写出**客观画面描述**。
2. 在仓库根执行，**带上 `--content`**：

```bash
{python} {baseDir}/scripts/product_image_ingest.py <源图片路径> \
  --product "公众号AI运营助手" --stem "配置首页" \
  --content "客观中文描述，一两句即可"
```

`--product` / `--stem` 必填；产品目录与 `images/` 不存在时自动创建。

**不传 `--content`** 时「图片描述」会写成固定占位句「请根据图片补全（客观描述画面内容即可）。」——这是**预期行为，不是脚本故障**。要么入库时带 `--content`，要么入库后编辑同名 `.md` 替换占位段。

生成的 `.md` 是固定格式：

```markdown
**图片路径**：`.aws-article/products/公众号AI运营助手/images/示例.png`

**图片描述**：……
```

---

## 三、`.aws` 的合并语义

### 预设目录：替换式

七个白名单子目录 `closing-blocks` / `cover-styles` / `formatting` / `image-styles` / `sticker-styles` / `structures` / `title-styles`，每个都是**替换式**（以服务端为准，避免旧文件残留）：

- 包内**有**该子目录 → **先清空**本地 `.aws-article/presets/<同名>/` 再写入包内内容。旧包里有、新包里删掉的文件不会残留。
- 包内**没有**该子目录 → 本地对应子目录**保持不动**，不受本次导入影响。

**不在白名单的目录会被跳过**，脚本会打一条 `【跳过】…不在预设白名单` 的日志。两个常见的：

| 路径 | 谁在用 | 为什么不由 `.aws` 管 |
|---|---|---|
| `presets/components/` | [formatting](../../aws-wechat-article-formatting/SKILL.md) 的自定义版式组件 | 组件绑骨架，随模版走，不单独下发 |
| `presets/review-rules.yaml` | [review](../../aws-wechat-article-review/SKILL.md) 的自定义检查规则 | 是用户自己写的业务规则，不该被别人的包覆盖 |

**包根优先级**：包根下同时有 `presets/<名>/` 与 `<名>/` → **优先前者**；只多套了一层 `<名>/<名>/` → 自动以内层为合并根。

### `config.yaml`：不覆盖，只报差异

- 本地**尚无** `.aws-article/config.yaml` → 从包内**复制**。
- 本地**已有** → **不覆盖**。按包内字段与本地同名键递归比对，差异以 **JSON 数组**打到 **stdout**（`{"key":"点分路径","old":…,"new":…}`），说明日志走 stderr。Agent 拿到差异后**询问用户**再手改配置。

### `writing-spec.md`：始终覆盖

与 `config.yaml` 不同，包内有就直接写入 `.aws-article/writing-spec.md`，不做差异比对。

### 解压目录

固定 `.aws-article/tmp/`。**每次执行前**若已存在则整目录删除后重建；合并完成后**保留**解压结果便于核对，下次导入再次清空。

---

## 四、密钥怎么进 `aws.env`

包内 `config.yaml` 的密钥字段按下表**增量写入**仓库根 `aws.env`：

| `config.yaml` 字段 | `aws.env` 键 |
|---|---|
| `wechat_appid` | `WECHAT_1_APPID` |
| `wechat_appsecret` | `WECHAT_1_APPSECRET` |
| `writing_model.api_key` | `WRITING_MODEL_API_KEY` |
| `image_model.api_key` | `IMAGE_MODEL_API_KEY` |

写入策略：

- 包内字段为空 → **不动** `aws.env` 现有键
- `aws.env` 无该键 → 追加
- 已有**相同值** → 跳过
- 已有**不同值** → 写入前备份 `aws.env.bak.{ts}` 后覆盖

stderr **只输出键名清单，不打印密钥值**；保留原文件的顺序、空行与注释。

当前前端导出**只支持单微信账号**（固定槽位 1），`aws.env` 里的 `WECHAT_2_*` 等其它键不受导入影响。

> 备份文件 `aws.env.bak.{ts}` 确认新配置可用后应当删掉——里面是明文密钥，留着就是多一份泄露面。

---

## 五、URL 导入的白名单

`bundle` 参数同时接受本地路径和 HTTPS URL。URL 模式的硬约束：

- 必须 `https://` 开头
- host 为 `aiworkskills.cn` **或其子域**
- 路径以 `.aws` 结尾
- 下载内容必须是 ZIP

任一不满足 → **直接报错退出**，不写入任何文件。

下载缓存落在 `.aws-article/downloads/<原文件名>`（**不在 `tmp/` 内**，不受清空影响，保留供事后核对）。

`--allow-any-host` 可跳过域名白名单（仍强制 https），**调试用，不建议生产**。

`--dry-run` 下 URL 模式**仍会实际下载**到 `downloads/` 以便校验 ZIP 结构，但不写 `presets/` 与 `config.yaml`。
