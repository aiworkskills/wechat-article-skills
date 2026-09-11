# 写稿的分支与异常处理

SKILL.md 只写主路径：读约束 → 写 → 自检 → 展示。本文件是**走不到主路径时才读的东西**，主路径在对应位置用一行指过来。

---

## 一、`write.py` 退出码处理 ⛔

运行脚本后**须把终端里的具体报错原样摘要给用户**（或引用关键行），勿只说「调用失败」。

| 类型 | 判断线索 | 动作 |
|------|----------|------|
| **未配置（退出码 2）** | stderr 含 `[NO_MODEL]` | **自动降级**：跑 `write.py prompt <mode> <input>` 取回提示词 JSON → Agent 按其中的 `system_prompt` / `user_prompt` 写 → 输出到 `-o` 路径。**无须**用户确认或「本次例外」。 |
| **网络类（退出码 1）** | 超时、连接失败、`URLError`、`网络错误:`、临时 502/503 | **自动再试 1 次**（告知用户「正在重试」）。第二次仍是网络类 → 改走 `prompt` 由 Agent 代写，**必须明确告知**「第三方 API 网络不可用，本次由对话模型代写」。 |
| **配置/凭证类（退出码 1）** | 401/403、Key 无效、`未找到写作约束`、YAML 解析失败 | **不要**为省事自动降级掩盖问题。列出须检查项（`config.yaml` 的 `writing_model`、`aws.env` 的 `WRITING_MODEL_API_KEY`、本篇是否有 `article.yaml`），请用户修正后重跑。用户**明确打字**同意本次改由 Agent 代写，再按 main「本次例外」处理并留痕。 |
| **业务/内容类（退出码 1）** | 4xx 中除鉴权外（如 400 参数）、模型返回空 | 把 API 返回体摘要给用户；按提示改 `model` / 参数再试一次；仍失败则与用户商定是否 Agent 代写。 |

**无论哪条降级路径，Agent 代写前都先跑 `write.py prompt`**，取回与调第三方模型时**完全相同**的提示词，确保写作约束一致。

⚠️ `prompt` 与 `strip-citations` 都把结果输出到 **stdout**，诊断信息走 stderr——重定向时 `> out.json` 即可，不必过滤。

**禁止**：配置明显错误时静默改用 Agent 写稿却不说明；网络降级后不告知「本次未走第三方模型」。

---

## 二、用户供图分支（`image_source: user`）

- 用户图片须先放入本篇 `imgs/`；再由智能体**读图分析**生成或补全 `img_analysis.md`（可用 `user_image_prepare.py` 生成模板再填）。**未落盘 `img_analysis.md` 不得调用 `write.py`**，脚本会报错退出。
- `img_analysis.md` 是写稿时配图与章节顺序的**唯一依据**：`write.py` 会把它并入提示，按「建议章节 / 推荐用途」把每张图放到合理位置（可重排章节以匹配叙事）。
- 其中「推荐用途：封面」**必须且只能有 1 处**，否则不得写稿。
- 写稿时直接用真实路径（`imgs/xxx.png`），**不再输出 `placeholder`**。
- `image_source` 只允许 `generated` / `user`，**禁止写** `user_provided`。

### 状态切换（`article.yaml`）

- 新建默认：`image_source: generated`、`publish_completed: false`。
- 进入「用户上传图片替换/重写」流程：`image_source` 改 `user`，`publish_completed` **置回 `false`**。
- 重新发布成功且有回执后，才写回 `publish_completed: true`。

---

## 三、业务资料库的两条用法

`.aws-article/products/{产品名}/` 是用户业务的原始资料库——业务介绍 `.md` **直接挂在产品根**，`images/` 存业务配图。

**触发口径**：本篇涉及用户自身业务（对外介绍 / 教程 / 案例 / 自家安利）→ **必须**先 `ls .aws-article/products/`，相关产品根下的 `*.md` **必读**，已有同主题文档**优先增量改写**而非另起炉灶。与自身业务无关（行业资讯 / 通用教程）→ 不读，不强求。

### Agent 直接写稿时

1. 写稿前先 `ls .aws-article/products/`，涉及某产品就必读它根下的 `*.md`。
2. 把业务资料**转化为账号文风**后引用；无关或无文档时不引用，**不阻断写稿**。
3. `draft.md` 里凡**实际引用或依据**了某份业务介绍的，在该处表述之后用括号附上**该文件的仓库相对路径**（路径须真实存在）；未引用则不加。

### 走 `write.py` 时

1. 同样先 `ls .aws-article/products/` 判断有无相关文档。
2. **有** → 执行时传 `--reference <路径>`（可重复，**最多 5 个**；路径须形如 `.aws-article/products/<产品名>/<文件名>.md`，**直接挂在产品根**，**不接受** `images/` 下的图片说明 `.md`）。脚本将全文注入系统提示的「参考资料库」，并要求模型在依据处标注资料路径。
3. **无** → 不传 `--reference`。
4. 若因上下文 / token 超限失败，减少 `--reference` 篇数或换更短文档重试。

### 写后回写

本次写作产生的内容若**语义属于业务介绍**（侧重产品/服务自介而非文章主体），按 [assets skill](../../aws-wechat-article-assets/SKILL.md) 引导用户存回 `.aws-article/products/{产品名}/`，下次涉及业务的文章会自动用上。

**禁止**：把与主题无关的文档硬塞进正文；伪造业务资料中不存在的事实。

---

## 四、结构 / 文末预设的多候选处理

`default_structure`、`default_closing_block` 在本篇 `article.yaml` 中必须是**单元素列表** `[名]`（或 `[]`）。`write.py` 只读本篇 `article.yaml`，**不会**在执行阶段从 `custom_*` / `default_*` 候选池推断。

含**多个候选**时 Agent 须：

1. 读取每个候选预设文件（如 `.aws-article/presets/structures/<名>.md`），了解适用场景；
2. 结合本篇主题 / 选题卡判断最匹配的一个；
3. 写入 `article.yaml` 同键为单元素列表；
4. 再调用 `write.py`。

**禁止盲选第一个**。无法判断时，向用户展示候选与说明请其选择。

### 加载优先级

**文章结构**：用户当次指定 → 本篇 `default_structure` → `.aws-article/presets/structures/` → 内置 [structure-template.md](structure-template.md)。

**文末区块**：本篇 `default_closing_block` → 合并约束里非空的 `closing_block` → 内置兜底（`---` + 一句关注引导）。

---

## 五、发布意图（`publish_method`）

在调用 `write.py` 或进入写作之前确认 `.aws-article/config.yaml` 的 `publish_method`：

| 取值 | 向用户怎么说 |
|------|------|
| **`draft`**（默认） | 定稿后走 `publish.py full` 只写入**公众号草稿箱**，不自动发出去 |
| **`published`** | 创建草稿后**再提交发布**（异步）；也可用 `full --publish` 单次强制 |
| **`none`** | 用户明确不填微信：`full` 直接跳过不调微信，写稿/审稿/排版照常 |

**已是三者之一（小写）时不重复盘问。** 默认保持 `draft`，除非用户明确要对外发布或明确不填微信。用户拒绝填微信 → 写 `none`，不要代跑 `publish.py full`。

**禁止**：`publish_method` 非法时调用 `write.py`；未经同意默认 `published`。

---

## 六、确认轮次优化

- **全局三键**已非空 → 静默通过，不再确认。
- **`publish_method`** 已是合法值 → 静默通过。
- 需要同时确认「新篇 / 续写」和「发布意图」时，**合并为一轮提问**。
- 用户已给明确主题且无风格要求时，配图按默认风格自动执行，不单独确认。

用户意图明确时（给出主题 + 「写一篇文章」），理想轮次为 **1 轮**（确认标题/摘要）+ 写完展示。

---

## 七、续写时的中间产物门禁

- 续写新增 `![...](placeholder)` 时，必须把该占位计入「待配图清单」，供 images 步骤生成替换。
- 进入发布相关步骤前复核：`article.md` / `article.html` 若仍含 `placeholder`，只能标记为「正文配图未完成」，**禁止**宣称发布闭环完成。
