# 审稿的分支与异常处理

SKILL.md 只写主路径：环境检查 → 逐项检查 → 输出 → 修改循环 → 定稿。本文件是**走不到主路径时才读的东西**，主路径在对应位置用一行指过来。

---

## 一、往期 `{embed:link:…}` 的三种情况

文末 embed 的前三类（名片 / 小程序文字链 / 小程序卡片）规则简单：对应列表未配置、为空、或无非空关键字段 → **不追加**该类占位符，无需处理。

往期链接有三条岔路：

1. **合并后 `embeds.related_articles.manual` 已有 `name` + `url`** → 文末追加对应占位符，**最多 3 条**。超过 3 条时只保留与本文主题最相关的，或按列表顺序取前 3。
2. **`manual` 缺失或为空** → **本 skill 不自动补齐**（review 要保持纯本地、无网络、无凭证）。两条出路：
   - 首选请用户把已发表文章的 `name` + `url` 写进本篇 `article.yaml` 的 `embeds.related_articles.manual`（至多 3 条）；
   - 或在进入 [publish skill](../../aws-wechat-article-publish/SKILL.md) 时由 publish 调 `getdraft.py published-fields` 自动补齐——**只有 publish 有微信 API 凭证与网络能力**。
3. **用户声明跳过往期** → **不伪造** `manual`，审稿说明里注明「本篇跳过往期推荐」，`{embed:link:…}` 省略即可。

**全空时仍要说一声**：profiles / miniprograms / miniprogram_cards / related_articles 全为空或未配置时，审稿输出中须**显式标注**「文末 embed：无配置，已跳过」。**不得静默跳过**——静默跳过之后没人能分辨是「配置为空」还是「这一步漏了」。

字段含义与示例见 [config.example.yaml](../../aws-wechat-article-main/references/config.example.yaml) 的 `embeds` 注释，以及 [topics SKILL](../../aws-wechat-article-topics/SKILL.md) 文末「推荐链接」说明。

---

## 二、自定义检查规则

用户可在 `.aws-article/presets/review-rules.yaml` 追加检查项，它们**排在标准检查项之后**执行：

```yaml
custom_rules:
  - name: 品牌名称规范
    check: 正文中「XX公司」必须使用全称，不能简写
    level: 必须    # 必须 / 建议

  - name: 数据来源
    check: 所有引用的数据必须标注来源和日期
    level: 必须

  - name: CTA 检查
    check: 文末必须包含明确的行动号召
    level: 建议
```

`level: 必须` 命中判 🔴（进修改循环），`level: 建议` 判 🟡。

---

## 三、约束缺失时的 fallback

合并配置后仍缺关键约束时**不要中断审稿**，按缺什么降什么：

| 缺什么 | 怎么办 |
|---|---|
| `target_reader` / `tone` 等内容向约束 | 向用户说明「部分维度无法按本篇约束对齐」，建议补全 `config.yaml` / `article.yaml`，其余维度照审 |
| `.aws-article/writing-spec.md` 不存在 | 跳过「写作规范合规」整个维度，不报错 |
| `.aws-article/presets/review-rules.yaml` 不存在 | 只执行内置清单 [checklist.md](checklist.md) |
| `title_max_length` / `summary_length` 等阈值缺失 | 用微信侧硬限兜底（摘要 ≤ 128 字），并在输出里注明用的是兜底值 |

---

## 四、单独启用本 skill

用户只说「审个稿」而没走 main 的一条龙时：

- 仍须先满足 [首次引导 · 检测顺序](../../aws-wechat-article-main/references/first-time-setup.md) 的同一套环境检查，或用户按 main 约定书面声明「本次例外」。
- 第 5 步的文末 embed **仍是 BLOCKING**——单独审稿不是跳过 embed 的理由。
- 若用户只想要「挑错清单」而不要定稿产物，可在第 3 步输出后停下，**但不得写入 `article.md`**：`article.md` 一旦存在，下游会当成已定稿。

---

## 五、AI 味的两套判级不要混

[ai-flavor-check.md](ai-flavor-check.md) 里的**强 / 中 / 弱**只表示「像不像 AI」，是**诊断级**；审稿总评的 🔴 / 🟡 / 🟢 是**行动级**。

**无论强信号还是弱信号，AI 味命中一律折算为总评里的 🟡**，不阻断定稿。不要在 AI 味诊断里写 🔴/🟡/🟢，也不要把「强信号」当成「必须改」。

判定前先判体裁（长文 / 短文案 / 标题的宽严不同），并尊重 writing-spec 鼓励的口语对话与生活化类比（那不算 AI 味）。拿不准宁可不报。
