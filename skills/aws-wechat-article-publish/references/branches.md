# 发布的分支与异常处理

SKILL.md 只写主路径：选账号 → 查 → `full` → 确认回执 → 写回状态。本文件是**走不到主路径时才读的东西**，主路径在对应位置用一行指过来。

---

## 一、用户只说「发布」、没给路径 ⛔

用户说「发布文章」「帮我发一下」而**没给** `drafts/…` 路径时：

1. **先确定本篇目录**：列出仓库 `drafts/` 下的子目录。有多篇则请用户**指定一篇**或选「最新修改」的那篇，再读该目录的 `article.yaml`。**勿在未确认目录时假定路径。**
2. 读 `article.yaml` 的 `publish_completed`（YAML 布尔；**缺省按 `false` 处理**），按下表分流：

| `publish_completed` | 怎么说（可口语化，勿改含义） |
|---|---|
| **`true`** | 告知「项目里本篇文档已按记录成功发布」；问「您是否需要编写新文章？」。要写 → 转交 [main](../../aws-wechat-article-main/SKILL.md) / [writing](../../aws-wechat-article-writing/SKILL.md) 从本篇准备或选题起走。 |
| **`false`** 或缺省 | 读 `title`（无则用目录名简述），说明「《{title}》尚未执行完成（发布流程未闭环）」；问「是否继续并完成发布？还是编写新文章？」。继续本篇 → 再核对 `publish_method`、跑 `check-screening` 与 `check-wechat-env`。 |

---

## 二、发布失败的四类处理

失败类型由脚本 stderr 与微信 `errcode` 判断。

| 类型 | 线索 | 动作 |
|---|---|---|
| **网络类** | 超时、连接失败、5xx | 脚本对单次请求**已自动重试 1 次**。仍失败 → 告知「网络不可用，请稍后重试或检查代理」，不要反复重跑。 |
| **凭证/配置类** | token 失败带 errcode、缺字段 | 提示**第几槽位**，检查 APPID / APPSECRET / **IP 白名单**，用户改正后再跑 `full`。 |
| **封面裁剪 53402** | 「封面裁剪失败」 | 手填的 `pic_crop_*` 宽高比与目标比例不一致。删掉手填值让脚本自动算，或改对比例。见下方第三节。 |
| **中间产物缺失** | 封面缺失、正文有 `placeholder` | **先补产物再发**。用户坚持先发草稿 → 必须明确告知「正文配图未完成」，且 `publish_completed` 保持 `false`。 |

正文里挂着未群发文章的链接也会被微信拒——改用已群发文章的永久链接（后台对该文「复制链接」），或从正文去掉相关超链。

---

## 三、封面裁剪框

微信只收一张封面（`thumb_media_id`），但 `draft/add` 可附带两个裁剪框，分别决定 **2.35:1**（订阅号信息流首图）与 **1:1**（分享卡片、公众号主页、历史列表）怎么裁。不传时微信自行居中裁切。

`publish.py` 会按封面实际尺寸自动算出两个框并随草稿提交（**需 Pillow**；未安装则跳过，交给微信默认行为）。

**设计取向是 2.35:1 优先**——信息流那一眼决定点不点，1:1 作降级视图。所以封面按 2.35:1 构图即可，不必为迁就方形而牺牲主视图。

需要手动指定时，在本篇 `article.yaml` 写 `pic_crop_235_1` / `pic_crop_1_1`（`X1_Y1_X2_Y2` 归一化 0~1），**脚本不再覆盖那一项**。注意裁出区域的宽高比须与目标比例一致，否则返回 **53402**。

---

## 四、几处回退

| 项 | 回退顺序 |
|---|---|
| **作者名** | 本篇 `article.yaml` 的 `author` → `config.yaml` 的 `default_author` |
| **API 端点** | `aws.env` 的 `WECHAT_{N}_API_BASE` → `config.yaml.wechat_api_base` → 官方 `https://api.weixin.qq.com` |
| **账号槽位** | 命令行 `--account`（**CLI 优先**）→ `config.yaml` 的 `wechat_publish_slot` |

**槽位的数量与名称只来自 `config.yaml`**（`wechat_accounts` + `wechat_{i}_name`）；`aws.env` 里只有凭证（`WECHAT_{i}_APPID` / `APPSECRET` / 可选 `API_BASE`）。

---

## 五、往期推荐链接的自动补齐

[review](../../aws-wechat-article-review/SKILL.md) 在 `embeds.related_articles.manual` 为空时不会自己补——它没有网络和凭证。补齐在这一步做：

```bash
{python} {baseDir}/scripts/getdraft.py published-fields
```

`getdraft.py` 与 `publish.py` 相互独立，走 `freepublish/*` 接口（`published-list` / `published-fields` / `publish-get` / `article-get`）。**需要公众号具备对应接口权限**，没权限时直接告诉用户手填。

拿到 `name` + `url` 后写入本篇 `article.yaml` 的 `embeds.related_articles.manual`（**至多 3 条**），再重新跑排版生成 `article.html`，然后才发布——`{embed:link:…}` 占位符是排版阶段解析的。

---

## 六、单独安装本 skill

`publish.py`、`getdraft.py`、`article_init.py` 三个脚本**可独立运行**，只要 `aws.env` 与 `.aws-article/config.yaml` 就绪。

文档里指向 `../aws-wechat-article-main/references/*.md` 的链接在套件未装齐时会断，但发布功能本身可用。仍建议先按 [首次引导 · 检测顺序](../../aws-wechat-article-main/references/first-time-setup.md) 走一遍环境检查。
