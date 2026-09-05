# 更新日志

本文档记录 wechat-article-skills 的版本变更历史。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，日期采用 ISO 8601 格式（YYYY-MM-DD）。

---

## [2026-09-05] — 配图体系重构：从模板库到推导方法

### Breaking changes

- **封面预设语义收窄**：预设只描述**视觉语言**（色板 / 光与材质 / 气质 / 适合），不再含物体、场景、构图与占位标题。此前用户选了「破土」当账号风格，每篇文章都是嫩芽——预设把画什么定死了，模型只能填空。老预设里写死的场景不再生效
- **Type × Style 体系整体移除**：删除 `styles.md` / `style-presets.md` / `auto-selection.md`，`prompt-construction.md` 中 12 个旧 Type 的 prompt 模板段一并删除（Style 维度从来不是用户可配项，实际未被使用）。依赖该维度的自建预设需按新 schema 重写
- **形态清单更换**：封面从 12 个美学词汇（简约 / 孟菲斯 / 蒸汽波…）换成 **12 个内容形态**，按 83 张真实公众号封面（11 个品类）统计重做——其中蒸汽波、孟菲斯、复古潮流、新中式、图文混排、品牌模板在样本里出现 0 次；正文配图从 12 个收敛为 **8 个**（删「手绘草图」——手绘是媒介不是形态、删「氛围留白」——出图是一片模糊，新增「金句卡片」）

### 新增

- **`references/cover-method.md`（封面七步推导）**：找核心张力（这篇文章里什么变成了什么）→ 定关系类型（并置 / 融合 / 替代 / 氛围）→ 找视觉隐喻（含机器人、发光大脑、齿轮堆等陈词滥调禁用清单与 8 条范例）→ 选形态模板 → 按 2.35:1 信息流尺寸布局 → 写成 150–300 字散文 brief → 回看五条
- **`references/image-method.md`（正文配图六步）**：先判断要不要这张图——删掉它读者会**看不懂**（信息位，必须带文章真实内容）还是**读不下去**（节奏位，不加字），都不影响就删掉图位 → 选形态 → 取文章真实内容 → 定媒介 → 套模板与可轮换维度 → 写 prompt
- **模板 schema 统一为五字段**（用于 / 主体 / 影调 / **文案** / 版式），「文案」不可缺省——旧模板缺它，所以产出的是背景图而不是成品封面
- **手绘媒介池 8 种**：马克笔白板 / 方格笔记本 / 便签手写 / 黑板粉笔 / 牛皮纸圆珠笔 / 终端等宽 / 打印稿批注 / 扁平矢量。每篇选一个、**篇内统一、篇间必换**，选定后写入本篇 `article.yaml` 的 `image_medium`，下一篇扫 `drafts/` 最近三篇避开
- **可轮换维度**：18 个模板各带若干维度，同篇多图必须错开组合，避免连着三张流程图长一个样
- **`references/cover-examples/`**：20 段概念型散文范例（是范例不是模板，给 Agent 的隐喻库）
- **`image_create.py check`**：出图后**纯代码**检查（长边 ≥900px、非近单色），不调 API，可对任意图单跑
- **`image_create.py compose` + frontmatter `title:`**：可选的标题合成（自动字号、标点处折行、按底色选深浅字并加细描边），给中文渲染弱的模型（DALL-E、旧 Flux）或有品牌字体要求的账号用；缺 Pillow 或系统中文字体时告警跳过，不阻断出图
- **publish 封面裁剪框**：按封面实际尺寸算出 `pic_crop_235_1` / `pic_crop_1_1` 两个归一化框随草稿提交，2.35:1（信息流首图）优先、1:1 作降级视图。此前两个字段都没传，微信自行居中裁切——这正是「封面标题被切掉」的成因。本篇 `article.yaml` 可手动指定，脚本不覆盖；需 Pillow，缺失或封面读不出尺寸时跳过，不阻断发布

### 变更

- **比例改走结构化参数**：此前把「（尺寸: 1792x1024）」当中文拼进 prompt 末尾，模型基本不理会（实测 12 张图全是 1360x784）。Gemini 系走 `extra_body.imageConfig.aspectRatio`（2.35:1 就近映射 21:9，偏差 0.7%），其余模型保持「生成后裁切」以免严格网关 400，可用 `image_model.aspect_mode`（`auto` / `imageconfig` / `none`）覆盖
- **分辨率兜底**：同一 prompt 返回过 1584px 也返回过 384px；加 `imageConfig.imageSize`（默认 2K）与出图后像素校验，低于 900px 自动重试（`CHECK_RETRIES` 1 → 3）
- **`caption_style` 三档真正生效**（有图注 / 无图注 / 关键图有）——此前 `config.example.yaml` 定义了三档，实际行为却写死成「alt 里有全角冒号就切一刀」，选「无图注」照样出图注
- **封面检查不再承诺「标题区干净度」**：默认路径的标题由模型画进图里，文字本身就是高边缘密度，硬套会把每张正确的封面判为不合格；该项只在显式给 `--title-zone` 时检查
- **各 SKILL.md 脚本命令统一为 `{python}` 占位符**：Windows 用 `py -3 -X utf8`（`python3` 在未装 Python 时会静默打开 Microsoft Store，`-X utf8` 避免中文输出在 GBK 环境乱码），macOS / Linux 用 `python3`；由 main SKILL 第 0 步探测
- `config.example.yaml` 的 `wechat_api_base` 从空串改为默认反代：官方 `api.weixin.qq.com` 有 IP 白名单，用户在自己电脑上跑必然 40164，而 `validate_env` 又要求该字段非空

### 修复

- **跑错目录被报成「模型未配置」**：配置按 cwd 解析且不向上遍历（避免在非预期工作区读到别人的凭证，该设计保留），但找不到 `config.yaml` 时一路走到 `[NO_MODEL]` + 退出码 2，而退出码 2 意味着 Agent 可以改用自身能力代生图——配置完全正常、只是 `cd` 错目录的用户会看到假的「你没配图片模型」并绕开自己配好的专用模型。现在分开报：目录 / 未引导 → 退出码 1 且点名不得据此降级；`config.yaml` 在但 `image_model` 或 key 缺失 → 仍是退出码 2
- **重跑生图会覆盖成更差的图**：新图不合格而磁盘上已有合格同名图时保留旧图——重跑只能让结果变好，不该让它变坏
- **换后缀会断引用**：端点返回格式会变（同一 prompt 这次 PNG 下次 JPEG），删同名旧后缀图从 INFO 改为 WARN 并写明引用会断；SKILL.md 第 7 步补上重跑后按文件名主干复核 `article.md` / `article.html` 引用的要求
- **自建反代下线被报成「网络抖动」**：报错带上实际端点，并区分「自配反代不可用」（重试不会好转，给出改回官方的办法）与真正的网络抖动
- 读超时不是 `URLError` 子类，此前直接抛栈——批量跑 8 条时第 3 条超时会导致后面 5 条全丢；超时纳入可重试网络错误，批量单条失败不再中断整批
- publish：`draft/get` 不回显 `pic_crop_*`（值归一化进 `cover_info.crop_percent_list`），已记入 `api-reference.md`——不知道这点会误判成「微信忽略了裁剪框」。已用真实草稿验证提交值原样存下，六位小数一致；**展示效果仍建议发一篇草稿到手机上肉眼确认**

---

## [2026-09-04] — 排版与配图脚本缺陷修复 + 回归测试

### 修复

- **`format.py`**：预格式化改为保护围栏代码块、行内代码、链接与图片目标、`{embed:…}`、HTML 标签与裸 URL——中文图片路径（`imgs/淘米图1.png`）不再被插入空格导致发布时报「正文引用了不存在的图片」，示例代码里的 ASCII 引号不再被替换成「」；行内代码内容做 HTML 转义；表格支持 `|:---:|` 对齐行且表头重复时不再被拆成两张残表；`--font-size` 覆盖正文段落；`closing.md` 不再丢失首个 h1；四空格缩进列表只加深一层；引用块内单独的 `>` 空行不再切断引用；补上 README 已承诺但未实现的 `--export-theme`
- **`image_create.py`**：`test` 子命令失败时退出码由 0 改为 1（SKILL.md 里按退出码分类的失败分支才真正生效）；封面比例真正落地（按 aspect 映射到最接近尺寸后用 Pillow 居中裁切，此前固定输出 1792x1024，实为 1.75:1）；frontmatter 中未加引号的 `aspect` 可反推（YAML 1.1 会把 `16:9` 解析成 969）；输出后缀按实际图片字节格式判定；通义 text2image 端点补上异步提交与任务轮询；Gemini 官方域名改用 `x-goog-api-key`

### 新增

- `tests/` 回归测试 24 例，覆盖预格式化保护范围、表格与引用块解析、字号覆盖、aspect 反推与裁切、图片格式探测、协议识别与退出码。运行：`python3 -m unittest discover -s tests`（随后续提交扩到 68 例）
- `.gitignore` 补齐 `aws.env.*` / `*.bak` / `*.bak_*` / `skills.zip` / `*.aws` / `.aws-article/downloads/`——此前只忽略 `aws.env`，备份文件会被当作未追踪文件暴露

---

## [2026-08-17] — 可选配置不阻断流程

### 变更

- 写作 / 配图模型未配置时 `validate_env.py` 只警告、不中断——Agent 可按同一套文风规范代写，配图则用自身生图能力
- README 与 README_EN 的 Star History 图表迁移到 `star-history.dera.page`（原数据源受 GitHub stargazer API 限制已无法渲染）

---

## [2026-07-08] — Autohand Code 安装说明

### 新增

- README 补充 Autohand Code 的 skill 读取路径（`~/.autohand/skills/` 或项目 `.autohand/skills/`）

---

## [2026-06-20] — 排版正文字号统一

### 变更

- 内置 4 套主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑）正文字号统一到 16px（`p` / `li` 的 14px / 15px → 16px，标题不动）

---

## [2026-06-17] — 在线改写入口

### 新增

- 教程与案例新增「在线试用改写功能」入口：不装智能体、不配 Key，贴段稿子就能体验网感改写

---

## [2026-06-16] — 写作护栏：抑制 AI 味露馅

### 变更

- `write.py` 与 `structure-template.md` 禁止「互动话题」式栏目标签与「发自北京」新闻电头——这两处是公众号读者最容易一眼认出 AI 代笔的地方

---

## [2026-06-01] — 审稿引入 AI 味诊断方法论

### 新增

- **review skill「AI 味自检」维度**：新增 `references/ai-flavor-check.md` 诊断方法论 —— 核心理念（AI 味的本质是「太完美」、不以「去 AI 味」为目标、改写须基于作者意图）+ 15 条公众号体裁化指纹库 + 防误判阈值 + 与 `writing-spec.md` 的豁免边界 + 体裁差异。内容审多一个「AI 味自检」维度
- **校准样例** `references/ai-flavor-check-samples.md`：用仓库内两篇真实 `draft.md` 跑出的诊断结果，作为「该报什么 / 该放过什么」的回归锚点
- 配套挂载：review 的 `SKILL.md` / `checklist.md` / `output-format.md` 接入新维度，`skill.json` 升至 0.4.0

### 设计原则

- AI 味命中**默认 🟡 建议修改，不 blocking、不影响定稿**——只诊断、给方向，不擅自代改
- 信号强度用「强/中/弱」文字，与总评 🔴🟡🟢 不撞色；尊重 `writing-spec` 鼓励的口语化（口语对话、生活化类比不当 AI 味扣分）
- 纯本地、零网络、零凭证、不新增脚本

---

## [2026-04-24] — 业务资料库结构（Breaking）

### Breaking changes

- **目录结构**：`.aws-article/assets/` 整体废除（含 `stock/`、`brand/`、`covers/`），改用 `.aws-article/products/{产品名}/`：业务介绍 `.md` 直挂产品根，业务配图归 `images/` 子目录。语义从"通用素材库"收窄为"用户自家业务资料库"
- **脚本重命名**：`stock_image_ingest.py` → `product_image_ingest.py`；新增**必填**参数 `--product <产品名>`，写入路径为 `.aws-article/products/{产品名}/images/`，产品目录不存在自动创建
- **`write.py --reference` 路径白名单收紧**：仅接受 `.aws-article/products/<产品名>/<文件名>.md`（直接挂在产品根，不在 `images/` 下）；老路径 `assets/stock/references/*.md` 直接报错

### 新增

- **业务介绍 .md 双向流程**：AI 与用户对话产出业务介绍内容时，主动引导用户保存到 `products/{产品名}/`；用户说"保存为产品介绍"等也直接保存。无需新脚本，AI 用 Write 工具直接落库（详见 [assets skill](skills/aws-wechat-article-assets/SKILL.md)「一、业务介绍 .md 入库」）
- **assets SKILL.md** 新增「设计意图」与「业务介绍 .md 入库」两章节
- **writing / topics / images / main SKILL.md + CLAUDE.md** 一致地补强"涉及用户业务必查 `products/`"读规则；writing 额外补"写后识别"双向回写

### 老用户迁移

```bash
# 1. 确认产品名
PRODUCT="你的产品名"

# 2. 创建新结构
mkdir -p ".aws-article/products/$PRODUCT/images"

# 3. 迁移老内容（按需）
mv .aws-article/assets/stock/references/*.md ".aws-article/products/$PRODUCT/" 2>/dev/null || true
mv .aws-article/assets/stock/images/* ".aws-article/products/$PRODUCT/images/" 2>/dev/null || true

# 4. 删空目录
rm -rf .aws-article/assets/

# 5. 更新 .gitignore：把 .aws-article/assets/ 改为 .aws-article/products/

# 6. 同名 .md 内的图片路径批量替换
find ".aws-article/products/$PRODUCT" -name "*.md" -exec \
  sed -i.bak "s|.aws-article/assets/stock/images/|.aws-article/products/$PRODUCT/images/|g; \
              s|.aws-article/assets/stock/references/|.aws-article/products/$PRODUCT/|g" {} +
find ".aws-article/products/$PRODUCT" -name "*.md.bak" -delete
```

---

## [2026-04-03] — 素材管理与预设包导入

### 新增

- **assets skill**：用户图片批量入库（自动生成元数据描述文件）
- `.aws` 预设包一键导入：将主题、风格、结构模板打包分享给其他账号
- 导入时自动合并到 `.aws-article/presets/`，已有 config 不覆盖而是输出差异

### 更新

- 同步更新 config 示例和各 skill 文档

---

## [2026-04-02] — 技能与脚本维护

### 修复

- 更新各 skill 指令细节
- 忽略本地 `config.yaml`，避免误提交
- 清理脚本兼容性问题

---

## [2026-03-31] — 脚本迁移与发布入口统一

### 变更

- 完成所有 Python 脚本从 `shared/` 到各 skill 目录的迁移
- 统一发布配置入口——`article_init.py` 迁入 publish skill
- 消除脚本散落在多处的问题

---

## [2026-03-20] — 多平台安装 + 配置校验

### 新增

- `install-skills.sh` 支持 OpenClaw / Cursor / Claude Code / Codex 四平台一键安装
- 新增 ClawHub manifests

### 更新

- 预设目录规范化
- 配置校验流程与发布、写作模块对齐
- 优化主技能与子技能的路由逻辑，减少误触发

---

## [2026-03-18] — 架构升级与体验优化

### 新增

- **sticker skill**（贴图 / 多图推送）
- 嵌入元素支持：公众号名片 + 小程序卡片 + 往期文章，排版时自动转为微信标签
- 6 种预设类型的 schema + 自动发现机制（放入目录即生效）

### 变更

- 统一三层文件架构：全局 `config.yaml` → 本篇 `article.yaml` → 对话中临时指定
- 提取共享层，消除 Skill 间重复逻辑
- 渐进式披露重构：精简 SKILL.md 只保留核心指令，详细说明移入 references
- 所有 skill 加入配置检查阻断，无 config 时必须先完成首次引导
- 优化全部 8 个 skill 的触发词，减少误触发

---

## [2026-03-17] — 发布能力完善

### 新增

- publish skill 的微信公众号 API 发布，凭证从 `config.yaml` 读取
- 支持自定义 API 转发地址，解决公众号固定 IP 白名单限制
- 多账号发布支持，发布时指定账号即可

### 变更

- 封面标记不进正文 HTML，封面通过 API 单独上传
- 图片上传前自动压缩（封面 ≤ 10 MB，正文 ≤ 1 MB）

---

## [2026-03-16] — 审稿 skill 重写

### 新增

- 写作规范联动检查
- 敏感词 / 错别字 / 配图完整性逐项扫描
- 结果分三级（🔴 必须改 / 🟡 建议改 / 🟢 通过），必改项触发修改循环
- 支持自定义审稿规则

---

## [2026-03-15] — 排版 skill 重写

### 新增

- `format.py` 实现 Markdown → 微信 HTML 转换
- 4 套内置主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑）
- 支持用户自定义主题导入，YAML 文件放入目录即刻可用

### 变更

- 脚本不再硬编码主题，全部从 YAML 动态读取

---

## [2026-03-14] — 配图 skill 重写

### 新增

- 14 种视觉风格 × 6 种图片类型的 Type × Style 二维体系
- 写作阶段自动标记配图位置，配图时直接使用
- 信息图支持 10 种高级布局（九宫格、漏斗、冰山、金字塔、时间线等）
- 图片生成后端对接，优先专用图片模型

---

## [2026-03-13] — 写作 skill 重写

### 新增

- 接入 DeepSeek / GPT / Qwen / Gemini 等第三方模型
- 也支持当前 AI 直写（无需第三方模型）
- 支持用户自定义写作规范（`.aws-article/writing-spec.md`）

### 变更

- 简化配置为 `base_url` + `api_key` + `model` 三项，去掉 provider 概念
- 优先用专用写作 API，未配置则降级为当前模型并告知用户

---

## [2026-03-12] — 选题 skill 重写

### 新增

- 四种输入模式：有明确话题 / 有方向没话题 / 完全没方向 / 系列策划
- 调研驱动，搜索热点和竞品文章后再推荐选题

---

## [2026-03-01] — 项目优化

### 变更

- 优化 8 个 skill 基础框架
- 全面优化各 skill 的中文描述、OpenClaw 元数据
- 优化「一条龙模式」路由

---

[2026-04-03]: https://github.com/aiworkskills/wechat-article-skills/releases/tag/v1.0.13
[2026-04-02]: https://github.com/aiworkskills/wechat-article-skills/releases/tag/v1.0.12
