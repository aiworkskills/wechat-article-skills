# 选题的分支与细则

SKILL.md 只写主路径：定方向 → 调研 → 出选题卡 → 用户选 → 落盘。本文件是**主路径之外才要读的东西**，主路径在对应位置用一行指过来。

---

## 一、一条龙 vs 单独使用

**一条龙（走 [main](../../aws-wechat-article-main/SKILL.md)）**：main 在「3) 本篇准备」里已建好目录并落了 `article.yaml`，还问清了写作意图。所以：

- 第 2 步（全局三键）main 本轮已做 → **不重复**。
- 第 3 步（A/B/C/D 归类）**口头确认一句**即可。
- 第 8 步**不要改目录名**，直接往已有目录写，`article.yaml` 只**合并更新**缺失键。
- 目录已存在且含 `article.yaml` 时，**须先读它**（连同 `config.yaml`）再产出 `topic-card.md` / `research.md`。

**单独使用本 skill**：第 8 步若新建目录，须在**同目录**创建或更新 `article.yaml`（至少 `publish_completed: false`，并尽量写入已定的标题/摘要）。**不得**只留一个 `topic-card.md` 就引导用户去调 `write.py`——那样本篇元数据全是空的，后面每一步都要回来补。

单独安装（套件没装齐）时，指向 `../aws-wechat-article-main/references/*.md` 的链接会断，但本 skill 的纯本地步骤仍可用。

---

## 二、预设候选池的收敛

`title_style` / `custom_title_style` / `default_title_style` 在 `config.yaml` 里**须为 YAML 列表**，`custom_*` 非空时优先于 `default_*`。

含**多个候选**时，须按本篇选题择一，**写回本篇 `article.yaml` 同键为单元素列表** `[名]`，再往下走。**禁止盲选第一个**；判断不了就把候选和说明摆给用户选。

加载优先级：用户当次指定（「用反问型」）→ 本篇 `article.yaml` 的 `title_style` → `config.yaml` 的 `custom_title_style` > `default_title_style` → `.aws-article/presets/title-styles/` → 内置 5 种（见 [title-presets.md](title-presets.md)）。

其它预设（`default_structure`、`default_format_preset` 等）同一套规则，字段清单见 [articlescreening-schema.md](../../aws-wechat-article-main/references/articlescreening-schema.md)。

---

## 三、业务资料库

**选题涉及用户自身业务**（产品/软件/服务）时：先 `ls .aws-article/products/`，进入相关产品目录**必读**根下的 `*.md`（业务介绍），从中找契合自家业务的选题角度。

与自身业务无关的方向（行业资讯、通用教程）→ 不读、不强求。

**禁止**把业务资料里没有的能力写进选题卡当卖点。

---

## 四、系列策划（模式 D）

系列规划保存到 `{series_root}/{系列slug}/plan.md`（`series_root` 以 `config.yaml` 为准，默认 `series/`）。

`plan.md` 里写系列总线、每篇的选题与顺序、彼此的依赖关系。用户说「先写第 N 篇」时，只为**那一篇**建 `{drafts_root}/YYYYMMDD-标题slug/` 并落 `article.yaml`，不要一次性把十篇目录全建出来——没写的目录只会变成噪音。

---

## 五、文末推荐链接由谁来做

全局 `.aws-article/config.yaml` **一般不改**。`embeds.related_articles` 若在全局配了 `manual`，各篇共用同一套 `{embed:link:名称}` 即可。

**每篇要不同推荐**时，只在**本篇 `article.yaml`** 增加 `embeds.related_articles.manual`（`name` + `url` 列表）——**不要**在本篇写名片 / 小程序，那两类仍以全局为准（`format.py` 只对 `related_articles` 做深度合并）。

**但「去把已发布文章查出来」不是本 skill 的活。** 本 skill 无凭证、不联网调微信接口。查询要跑 `getdraft.py published-fields`，那需要微信 API 凭证与 `freepublish` 接口权限，归 [publish skill](../../aws-wechat-article-publish/SKILL.md) 做（见它的 branches「五」）。这里只负责：用户手上已有链接时，把 `name` + `url` **写进本篇 `article.yaml`**（至多 3 条）。

占位符 `{embed:link:…}` 由 [review 第 5 步](../../aws-wechat-article-review/SKILL.md) 写进 `article.md`，排版阶段解析——`name` 须与 `manual` 里一致。
