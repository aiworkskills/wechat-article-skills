# 配图的分支与异常处理

SKILL.md 只写主路径：解析标记 → 定风格 → 写 prompt → 生成 → 插入。本文件是**走不到主路径时才读的东西**，SKILL.md 在对应位置用一行指过来。

这样分是有原因的：实测 `images/SKILL.md` 的 16,249 字里只有 2,520 字属于主路径，其余 85% 是分支与一次性配置。Agent 每配一篇图都要把不会发生的情况读一遍，才能确认自己该走哪条。

---

## 一、正文配图来源优先级（先查素材库再生图）⛔

**仅适用于正文插图**，封面永远走脚本生成（见 SKILL.md「封面 vs 正文」）。

**在**为正文 `placeholder` 调用 `image_create.py`、写入 `imgs/prompts/` **之前**，先判断是否可用**本地业务配图库**，避免业务相关文章（教程 / 产品介绍 / 案例 / 自家界面截图）「有现成业务配图却重新生成」：

1. **仓库业务配图库**：若本篇涉及用户业务，先 `ls .aws-article/products/`，进入相关产品的 `images/` 子目录，列出并阅读**同名 `.md`**（含路径与画面说明），按主题匹配后在 `article.md` 中直接引用对应 `.png` / `.webp`（或复制到本篇 `imgs/` 再引用）。**与正文严格相关才用**，避免硬凑。
2. **用户上传 / 本篇 `image_source: user`**：走下面的「用户供图模式」。
3. **仍缺图或须原创插画**：再按 [image-method.md](image-method.md) 选形态、写 `imgs/prompts/`、执行 `image_create.py`。

> 业务配图库属「仓库内业务资源」，**不必**等用户手动上传才查；与用户供图模式并列，而非附属于它。

---

## 二、用户供图模式（`image_source: user`）

当用户上传图片并指定主题时：

1. 确保 `{article_dir}/imgs/` 存在，把用户图片放进去。
2. 生成/维护 `{article_dir}/img_analysis.md`，每图至少含：文件名、图片内容、建议章节、推荐用途、图注建议。
3. ⛔ `img_analysis.md` 中「推荐用途：封面」**必须且只能出现 1 次**，其余为「正文」。
4. 同步把本篇 `article.yaml` 的 `image_source` 写成 `user`（取值只允许 `generated` / `user`）。
5. 写稿阶段直接用真实路径（`imgs/淘米.png`），**不再出 placeholder**。

**顺序**：`imgs/` 落图 → 写好 `img_analysis.md` → 再跑 `write.py`。写稿以 `img_analysis.md` 为准，把图插到内容匹配的章节。

可用 `{python} {baseDir}/scripts/user_image_prepare.py <article_dir>` 生成 `img_analysis.md` 模板再补全。

---

## 三、发布后换图重发

用户说「这篇配图不满意，换成我上传的新图并重新发草稿箱」时：

1. 用户指定目标目录 `drafts/YYYYMMDD-slug/`。
2. 新图放进该目录 `imgs/`，更新 `img_analysis.md`（仍须满足「封面仅 1 张」），并把 `article.yaml.image_source` 改为 `user`。
3. 按 `img_analysis.md` 重新映射图片到 `article.md` 的对应章节（允许重排章节以匹配图序）。
4. 跑 `format.py` **重新生成**整份 `article.html`，不要只改旧 HTML 的局部。
5. 终审：确认 `article.md` / `article.html` 里没有 `placeholder`，且引用的图片文件都存在。
6. 回到发布步骤 `publish.py full`（`publish_method: draft` 时写入草稿箱）。

---

## 四、`image_create.py` 调用失败（智能体必选分支）⛔

只要执行了 `image_create.py` 且**非零退出或 stderr 有 API/网络错误**，就必须走本节，**不得**只说「生图失败」而不分类、不摘要报错。

先把 stderr 的关键行摘要给用户（含 `❌`、HTTP 状态码、`【配置/认证】`、`网络错误（可重试）`、`[NO_MODEL]`）。

| 类型 | 判断线索 | 动作 |
|------|----------|------|
| **未配置** | 退出码 2、`[NO_MODEL]` | Agent 支持生图**且用户明确同意代生图** → 读 `imgs/prompts/*.md` 的 prompt + frontmatter，用自身多模态能力按**相同 prompt** 生图，继续第 7 步。不支持或代生图失败 → 明确告知「我当前不能完成生图」，给二选一：配置图片模型后重试，或本篇不配图继续（保留 prompts 并标注无配图）。 |
| **网络类** | `URLError`、`网络错误（可重试）`、超时、临时 502/503 | **自动再试 1 次**。第二次仍是网络类 → 可降级为 Agent 生图或仅保留 prompts，**须明确告知**本次未走专用 API。 |
| **配置/凭证类** | 401/403、`【配置/认证】`、配置不完整 | **不要静默降级**。列出须检查项（`config.yaml` 的 `image_model`、`aws.env` 的 `IMAGE_MODEL_API_KEY`、端点、权限），请用户改正后重跑。用户**明确打字**接受仅用 Agent / 仅 prompts 时，按 main「本次例外」处理。 |
| **业务/参数类** | `【请求参数】`、400、返回体提示 model/size 不支持 | 响应摘要给用户；可改 model / 尺寸后再试；仍失败则与用户商定是否 Agent 生图。 |

**必须告知用户当前用的是哪条路**：

- 走脚本 → `ℹ️ 使用 image_create.py 调用专用生图模型（{model}）`
- 退出码 2 降级 → `ℹ️ 图片模型未配置，本次由当前对话模型直接生图（使用相同配图方案）`
- 故障降级 → `ℹ️ 本次未走 image_create.py（原因：…）`

**禁止**：配置明显错误时静默改用 Agent 却不说明；网络降级后不告知「本次未走专用生图」。

### 故障降级（退出码 1）时的终点 ⛔

只做到第 4 步（或第 5 步）：产出 `imgs/prompts/*.md` 与方案，**不执行**「替换 placeholder」或「修复 HTML」。`imgs/README.md` 不存在或需补充时可创建/更新（如何配 `aws.env` / `config.yaml`、如何跑 `batch`、如何在 `article.html` 中替换）；已涵盖当前方案则不必重写。

**例外**：退出码 2（未配置）且已获用户同意 Agent 代生图时，不受此终点限制，生成后继续第 7 步。

---

## 五、重跑生图后必须复核引用 ⛔

端点返回的格式会变（同一 prompt 这次 PNG 下次 JPEG），脚本会删掉同名旧后缀的图并打 `[WARN]`，而 `article.md` / `article.html` 里的 `imgs/xxx.png` 就指向了不存在的文件。

实测踩过：补跑两张分辨率不达标的图，其中一张换成了 `.jpg`，正文引用当场断掉**且不报错**。

重跑后按文件名主干（`05-金句卡片`）重新匹配实际存在的文件，`article.md` 与 `article.html` 两个文件一起改。

批量重跑时加 `--skip-existing`，已生成合格的不会重复付费。

---

## 六之前：端点连着两次腰斩就别再试了 ⛔

`[WARN] … 只剩 43%……腰斩` 值得重跑**一次**（`--retries 1`）。但**连着两次都被腰斩，就停手**。

实测 2026-09-12：同一端点、同一模型、同一天——一边连出 6 张方图（封面重跑 3 次、正文重跑 3 次，**全中**，改了 prompt 也没用），另一边正常返回 1584×672 / 1408×768，一次没裁。这说明端点是**成阵子**地忽略 `aspectRatio`，不是每张独立掷骰子。它不灵的时候，第三次第四次只是接着付钱。

这时两条路：接受这张，或者在 `config.yaml` 的 `image_model.default_size` 里写死目标尺寸再跑。

每次调用都会打印 `本次调用生图 API N 次（按张计费）`——**单张模式也打**，重跑时盯着这行看花了多少。

---

## 六、端点差异与比例怎么传

`base_url` 须为**完整端点路径**，脚本据此判断调用模式：

| 端点 | 模式 | 比例怎么传 |
|---|---|---|
| `…/v1/images/generations` | DALL-E / gpt-image 等 | `size` 像素串 |
| `…/v1/chat/completions` | Gemini 等多模态（含中转站） | `extra_body.imageConfig`（比例 + 分辨率档位） |

`imageConfig` 是 Gemini 特有结构，**只对识别为 Gemini 系的模型发送**（模型名含 gemini / nano-banana / imagen），其余模型保持「尺寸并入提示 + 生成后裁切」，以免严格网关报 400。可用 `image_model.aspect_mode`（`auto` / `imageconfig` / `none`）显式覆盖。

无论走哪条路径，最终都会按 `aspect` 校正到目标比例——**但端点会间歇性忽略它**，这时脚本打「腰斩」告警，见 SKILL.md 第 6 步。

连通性自检：`{python} {baseDir}/scripts/image_create.py test`（**会真的生成一张图，按张计费**）。
