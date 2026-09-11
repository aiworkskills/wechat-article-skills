# 排版的分支与细则

SKILL.md 只写主路径：选模版 → 跑 `format.py` → 得 `article.html`。本文件是**主路径之外才要读的东西**，主路径在对应位置用一行指过来。

---

## 一、`:::` 版式组件（手写可用，写手不产出）

**写作提示词里不再有 `:::` 语法**（`write.py::build_components_block` 已移除），writing SKILL 明令禁止写手输出它。排版侧仍然认——存量草稿不会废，用户手写也有效。

代价是 `stat`（大数字对）和 `layers`（层级图）这两个 markdown 表达不了的组件，**除非手写否则不会出现**。这是「写作侧只产出标准 markdown」这个取舍明确付出的成本，不是遗漏。

主题只能给标签配内联样式，表达不了结构——而微信没有伪元素，「标题前的角标」「引用块的大引号」必须**真的插元素**。组件补的就是这一层：

```
:::section-title[01]
同一个模型，两个分数
:::

:::quote-card[AWS 团队]
基准分数衡量的是你缺哪个 harness，不是模型的能力上限。
:::
```

`lead`（导语）与 `closing`（文末区块）几乎每篇都该有——实测本账号 7/7 篇开头都有导语、结尾都有互动引导与署名，此前一律是裸文本或借用引用块的样式。导语**刻意不做成带底色的卡片**，就是为了和 `blockquote` 分开：作者的开场白和引用别人的话语义不同，此前共用样式导致长得一模一样。

### 查找顺序

内置组件在 [components/](components/)，用户自定义放 `.aws-article/presets/components/<名>.yaml`。组件还可**按骨架整套替换**：`components/<骨架名>/<组件名>.yaml`。

查找顺序：**内置基础版 → 骨架专属 → 用户自定义**，后者覆盖前者。

每个组件 YAML 里带 `when_to_use` / `when_not_to_use` / `anti_pattern`——**选组件前先读这三项**，它们和配图方法里的判据是同一个作用：拦住「因为好看所以用」。

模板里的 `{primary-color}` `{text-color}` 等占位符从当前主题取值，所以组件与任何主题组合都不会脱节。未知组件名或缺少结尾 `:::` 时按原文输出并告警，**不吞内容**。

### `:::highlight` / `:::note`（提示框）

```
:::highlight
先确定行高、段距、留白这三个数，再考虑换模板。顺序反了，换多少套都没用。
:::
```

它不是组件文件，而是套用主题里的 `highlight` 样式键。**但目前四套内置模版都没有定义 `highlight`**，代码里会退回 `blockquote` 的样式——也就是说现在 `:::highlight` 和普通引用块长得一样。想让它有自己的长相，两条路：在模版 YAML 里加 `highlight:` 样式键，或放一个同名组件文件覆盖这条兜底。

---

## 二、主题解析的完整顺序

`format.py` 自己的行为只有两条：

1. 命令行 `--theme <名称>` 显式指定时**始终优先**。
2. 未传 `--theme` 时，**只读**与 `article.md` 同目录的 `article.yaml` 的 `default_format_preset`（**须为 YAML 列表**：`[]` 或单元素 `[主题名]`，多候选会报错）；为空则用内置默认模版 **`亲和`**。

脚本**不直接读** `.aws-article/config.yaml`——全局的 `custom_format_preset` / `default_format_preset` 候选池由 main 在「本篇准备」阶段收敛后写回 `article.yaml`。

智能体在对话里帮用户选主题时按：用户口述 → 本篇 `article.yaml.default_format_preset` → `.aws-article/presets/formatting/` 自定义 → 内置 `亲和`。

主题名须对应内置模版或 `.aws-article/presets/formatting/<名>.yaml`。字段说明见 [articlescreening-schema.md](../../aws-wechat-article-main/references/articlescreening-schema.md)。

配色同理：`--scheme` 优先，其次本篇 `default_format_scheme`（单元素列表），再无则用模版 YAML 里 `schemes` 的默认项（由 `default_scheme` 字段声明）。

---

## 三、自定义主题

在 `.aws-article/presets/formatting/` 下新建主题文件即可。快速起步是导出一套现成的改：

```bash
{python} {baseDir}/scripts/format.py --export-theme 亲和 > .aws-article/presets/formatting/my-brand.yaml
```

`format.py` 还会检查用户家目录 `~/.aws-article/presets/formatting/`（跨项目共享的自定义主题，**只读预设文件，不读凭证**）。不需要这个能力可清空 / 不创建该目录。

主题文件格式与扩展方式详见 [presets/README.md](presets/README.md)。

---

## 四、嵌入元素 `{embed:…}` 的合并规则

- **名片 / 小程序**的 `embeds` 以 `.aws-article/config.yaml` 为准。
- **仅「往期链接」例外**：本篇 `article.yaml` 可写 `embeds.related_articles`，与全局 `related_articles` **深度合并**（用于每篇不同的推荐）。
- 合并结果中 `embeds` 非空时才解析 `{embed:profile|miniprogram|miniprogram_card|link:名称}`；否则不对占位符做替换（视为无配置）。

占位符由 [review 第 5 步](../../aws-wechat-article-review/SKILL.md) 写入 `article.md`，与 [writing 结构模板](../../aws-wechat-article-writing/references/structure-template.md) 的说明一致。**占位符与配置对不上时排版阶段会失败**。

---

## 五、输出 HTML 的细节

- 所有样式 inline（微信编辑器兼容）。
- **正文不含文章标题**：`article.md` 的第一个 `#`（h1）在转换时被跳过，标题在公众号后台单独填，正文不重复。
- 配图标记 `![类型：描述](placeholder)` 保留为 `<img>` 标签，待 images skill 替换。
- 同目录存在 **`closing.md`** 时会追加到文末；`closing.md` 自己的首个 `#` 会保留，**只有 `article.md` 的首个 `#`** 被当作文章标题跳过。
- **预格式化**（中英文间加空格、ASCII 引号转「」、合并空行）只作用于正文文字：围栏代码块、行内代码、链接/图片目标、`{embed:…}`、原生 HTML 标签与裸 URL 原样保留，行内代码内容做 HTML 转义。不需要时加 `--no-preformat`。
- 表格支持 `|:---:|` 这类对齐行。

---

## 六、设计新版式前必读 ⛔

微信正文只认**内联样式**，没有伪元素、没有伪类，`position` 与 `id` 会被整条删掉。这决定了「装饰必须作为真实元素插进 HTML」，而不能靠 CSS 变出来。

能用什么、什么会被剥离，见 [wechat-html-constraints.md](wechat-html-constraints.md)。

另：微信 `draft/add` 偶发把 `style=""` 清空，**非确定性**——同样的内容重新上传一次通常就好了。不要据此反推「某个标签的样式不被支持」。
