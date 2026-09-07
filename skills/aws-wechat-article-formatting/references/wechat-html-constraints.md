# 微信正文能用什么：设计模版前必读

模版设计的边界不是审美问题，是微信编辑器的过滤规则。这份文档记录**能用什么、
什么会被删掉**，设计任何新版式前先对一遍。

> 微信官方没有公开白名单。以下**优先以本仓库实测为准**，公开资料仅作补充。

## 实测结论：走 API 发布时，限制比传闻宽松得多 ⭐

2026-09-05 用探针稿实测（`draft/add` 上传 → `draft/get` 回读 → 渲染回读到的 HTML），
**11 项全部通过，微信一个字节都没删、没改写、没注入 class**：

| 项 | 结果 | 项 | 结果 |
|---|---|---|---|
| `display:flex` + `gap` | ✅ | 内联 SVG（`circle`/`text`/`polygon`） | ✅ |
| `display:inline-block` 并排 | ✅ | `box-shadow` + `border-radius` | ✅ |
| `linear-gradient` 荧光笔底纹 | ✅ | 嵌套三层 `<section>` | ✅ |
| `linear-gradient` 渐变色条 | ✅ | `transform:rotate` | ✅ |
| `<table>` 两栏 | ✅ | 纯色背景块（对照组） | ✅ |

**网上资料说 flex 不可靠、渐变支持不明——那些经验来自「在网页编辑器里粘贴」。
粘贴清洗器比 API 激进得多。我们走 `draft/add`，不经过它。** 这一条直接决定了
模版能做多复杂：卡片标题、编号角标、SVG 分隔线、双层引用框都可以做。

**两点界限**：
- 上述验证是「微信存回的 HTML 在 WebKit 浏览器里渲染」，不是微信客户端 webview。
  客户端仍可能在渲染时忽略个别属性，新版式上线前仍建议真机看一眼。
- `position` 与 `id` **没有测**（若真被删，SVG 内的 `url(#…)` 引用会整个断掉，
  混在一起测会污染其他项结论）。需要叠层效果时单独补测。

## 中文字体：指定了也没用 ⛔

**手机微信里，`font-family` 对中文完全无效。**

2026-09-06 探针稿实测：18 个字体各一行、同一句「永和九年岁在癸丑 Ag123」，发进草稿箱后

- **桌面浏览器**：中文差异非常明显——宋体横细竖粗有衬脚、楷体是手写体、黑体粗细均匀
- **iPhone 微信**：**中文一点差异都没有**，只有英文（Georgia / Menlo）看得出区别

iOS 系统本身装着 Songti SC 与 Kaiti SC，Safari 里也能渲染。所以这不是设备缺字体，
是**微信 webview 限制了中文字体**。iPhone 上都不行，就是全平台不行。

推论：

- 中文衬线 / 楷体 / 黑体的字体名，写进 `font-family` **纯属废重**。它们会被内联到
  每一个 p / h2 / li 上，本仓库 16 套原本因此多背了 9943 字节（占样式总量 16%，
  个别主题高达 41%）。已全部删除，现只保留西文与等宽（实测有效），占比降到 5%。
- **西文字体有效**：`Georgia` 能让英文变衬线，`Menlo` / `Consolas` 能让代码变等宽。
- **主题的识别特征不能依赖字形**。必须落在几何特征上——版框、双线、色块、角标、
  留白节奏。本仓库剥掉全部字体后做两两相似度比对，16 套最高 0.62，没有一对撞车，
  就是因为签名早已推到几何上。
- **预览必须与手机一致**。门户预览跑在桌面浏览器，衬线会正常显示——那是交付不了的
  承诺。删掉中文字体声明后，预览自动等于微信所得，不需要为预览特殊处理。

## 字重：中文有效，5 个档位 ⭐

和中文**字体名**完全无效正好相反，`font-weight` 对中文**有效**——它是渲染引擎按数值
选重/合成，不需要我们点名某个字体。2026-09-06 探针稿在 iPhone 微信上实测：

    100        极细
    200 ~ 300  细
    400        常规
    500 ~ 600  中粗
    700 ~ 900  粗（中文到 700 就到顶，英文还能继续变粗）

关键字 `lighter` / `bolder` 同样生效。

**`font-variant-numeric: tabular-nums` 也实测有效**（等宽数字）。几行数字竖排时，
不等宽的字形会让小数点错位，读者没法竖着比大小——这是功能性收益不是装饰。
已用在所有主题的 `table` / `td` / `th`、数据型主题的正文，以及 `stat` 数据卡组件上。

**这是字号被基线锁死后唯一还能拉开层级的手段。** 字重差本身就是层级工具：
「标题 600 / 正文 400」差 200，「标题 800 / 正文 300」差 500——层级对比翻倍，
尺寸一个像素都不用动。

用它时两条注意：

- **正文 300 要克制**。16px 细体在低亮度屏上会发虚，只适合本来就走留白路线、
  且配了收窄行长的主题；墨色必须保持近黑（#1F1F1F 一带），不能再调浅。
- **`strong` 要跟着正文走**。正文 300 时 strong 用 600 就够醒目；正文 400 时要 700。
  差值维持在 300 左右是「看得见但不吵」的区间。

## 一条铁律：只有内联样式

`<style>` 块、外部 `<link>` 样式表**一律被剥离**。所有样式必须写在元素的
`style` 属性里。这条决定了：

- **没有伪元素**（`::before` / `::after` 需要 CSS 规则，内联写不了）。想要标题前
  的小图标、引用块的大引号，只能**真的插一个元素**进去。
- **没有伪类**（`:hover` / `:first-child` 同理）。
- **没有 `@media` / `@keyframes`**，做不了响应式断点和关键帧动画。

## 标签

| 可用 | 说明 |
|---|---|
| `<p>` `<h1>`–`<h6>` `<br>` | 基础文本 |
| `<strong>` `<b>` `<em>` `<i>` `<u>` | 行内强调 |
| `<ul>` `<ol>` `<li>` | 列表 |
| `<a>` | 外链会触发安全提示 |
| `<img>` | 自动套 `max-width:100%`；**iOS 上须带 `width` / `height` 属性** |
| `<table>` `<tr>` `<th>` `<td>` | 表格可用，也是 flex 不可靠时的降级布局手段 |
| `<section>` `<span>` | 各家编辑器（秀米 / 135）产出的主力容器，实际保留良好 |
| `<svg>` 内联 | 可用，但限制多，见下 |
| `<mpvoice>` `<mpvideo>` | 微信专有音视频 |

**会被剥离**：`<script>` `<iframe>` `<style>` `<object>` `<embed>` `<form>`
`<input>`，以及 `onclick` 等一切事件属性。

## CSS

### 能用

`font-size` `color` `font-weight` `font-style` `letter-spacing` `line-height`
`margin` `padding` `text-align` `text-decoration` `opacity`
`background`（纯色）`border` `border-radius` `box-shadow`
`display:block` / `inline-block`

### 会被删或不可靠

| 属性 | 情况 |
|---|---|
| `position`（absolute / fixed / relative） | **整条被删**。布局只能走文档流，不能做定位叠加 |
| `id` 属性 | **整个删掉**，HTML 与 SVG 内的都删。锚点、SVG 内部引用全部失效 |
| `z-index` | 依赖 position，同样失效 |
| `transform` | `rotate` **实测通过**；iOS 上 SVG 的 `transform-origin` 据资料仍不稳，谨慎使用 |
| `display:flex` | **实测通过**（含 `gap`）。资料说的不可靠来自粘贴路径，API 路径没问题。仍建议为老编辑器场景保留 `inline-block` / `<table>` 降级 |
| 渐变 `background` | **实测通过**。荧光笔底纹与渐变色条都正常渲染 |
| 百分比做位移 | 如 `margin-top:-100%` 不可靠 |
| `text-decoration-thickness` | **被删**（2026-09-07 实测）。下划线粗细控不了 |
| `text-underline-offset` | **被删**（同上）。下划线离字底的距离控不了 |
| `calc()` | **含 calc 的整条属性被删**（2026-09-07 实测）。`width:calc(100% + 32px)` 连 `width` 一起没了，`margin:0 0 0 calc(50% - 50vw)` 连 `margin` 一起没了。`100vw` / `vw` 单位本身保留。要冲出边距用固定负值 `margin:0 -16px`，不要用 calc 算 |
| `<img width="…">` 属性 | **被剥掉**，`height` 属性保留（2026-09-07 回读实测）。微信同时把 `src` 改成 `data-src` 懒加载、`http` 改 `https`、尾缀 `/0` 改 `/640`。style 里的 `width:` 不受影响 |

下划线要控粗细或位置，只能改用 `border-bottom`——它能定粗细与颜色，代价是紧贴内容框
底边、离字底的距离不可调。`text-decoration:underline` 本身可用。

**单位**：优先 `px`；`vw` / `vh` 可用；**不要用百分比做定位**。

**正文宽度**：约 375px（手机逻辑像素）。所有版式决定都要在这个宽度下成立。

## 行内元素加底色：别用 padding ⚠️

给 `<strong>` 这类行内元素加底色，最直觉的写法是 `background:#E9EFF6; padding:1px 5px;`。
**padding 会撑高行盒**——带底色的那一行比周围行距明显大，整页出现波浪。而 strong 一篇里
出现几十次，波浪就是几十道。

规避办法有两个，都实测可用：

```
/* 半高高亮笔：像用马克笔划过，最轻 */
background:linear-gradient(transparent 58%, #BBD0E4 58%);

/* 满高色块：视觉上是「块包住文字」，但不参与盒模型 */
background:linear-gradient(#E9EFF6, #E9EFF6); box-shadow:0 0 0 3px #E9EFF6;
```

渐变是背景、box-shadow 是绘制层，两者都不进盒模型，所以行距不变。

## 核心层的三条约束 ⭐

正文里**每篇出现几十次**的元素只有三个能加装饰：加粗、链接、列表符号
（正文段落本身只能动字号/行高/段距/缩进/对齐，那是排版不是装饰）。
标签层不能插子元素，所以 SVG、角标这类手法在这里一律不可用。

1. **加粗与链接的「手法集合」必须不同**。两者都用底线时读者分不清哪个能点。
   手法维度：线 / 底 / 彩字 / 重字 / 字距。一个用「线」另一个用「彩字」即可，
   不必两者都花哨。
2. **列表符号不能取 `none`**。两条列表项在页面上就是两个普通段落，读者认不出是列表。
   可选值远不止 disc / circle / square / decimal——桌面浏览器实测这些也都生效：

       cjk-ideographic / simp-chinese-informal   一、二、三   中文数字，比 1. 2. 地道
       decimal-leading-zero                      01. 02.     编辑部气质
       lower-alpha / upper-alpha / lower-roman   a. / A. / i.
       hiragana / katakana                       あ、い、

   **2026-09-07 探针稿实测微信保留**（cjk-ideographic / simp-chinese-informal /
   decimal-leading-zero / lower-alpha 逐项核对，四个全部原样存回）。
3. **装饰要「轻但持续」**。出现几十次的元素，重一点就是灾难——这也是上面那条
   「别用 padding」为什么要紧的原因。

### 强调不止「加粗」⭐

中文的正统强调手法有两个是加粗之外的，**2026-09-07 探针稿实测微信保留**：

    text-emphasis:filled circle 色         着重号，逐字加点。中文书刊里比加粗更正统
    text-emphasis-position:under right     点在字下（默认在字上）
    letter-spacing:3px; font-weight:500    疏排（铅字时代的 Sperrsatz），把字撑开而不加重

着重号三种写法（点 / 实心圆 / 芝麻）连同 `-webkit-` 前缀和 `position` 全部原样保留。
疏排 2px 偏弱，3px 配 500 字重才明显可辨。两者都「轻但持续」，正好适合核心层。

**这一条把核心层的可选写法扩出了一整个维度**——此前只想到「加粗 / 变色 / 加线 / 加底」
四种，着重号与疏排是完全不同的第五、第六种，而且是中文特有的。

## 标题 + SVG：能做什么，什么会塌 ⭐

h2 的样式是一串 CSS，SVG 塞不进去。骨架目录里放一个 `h2-deco.yaml`（模板含 `{content}`），
标题就会被它包起来——这是给内联 SVG 开的口子。`h3-deco` 同理。

值得开这个口子，是因为 SVG 能做的形状 CSS 一个都做不出来：

    笔刷底线      两端不齐、中段有粗细变化的手绘线
    折角块        右上角切掉一块的底
    渐隐色带      linear-gradient 填的 rect（左实右虚）
    编号环        描边圆 + 居中的 <text>，SVG 里的 text 能正常渲染
    角标括号      「」形的两笔
    双线          一粗一细、长短不一

**但 SVG 不会跟着文字换行，高度是写死的。** 375px 下 h2 经常折两行，所以：

    ✅ SVG 在标题的上方 / 下方 / 旁边（flex 并排）——各自独立，几行都不影响
    ❌ 文字压在 SVG 上（负 margin 垫上去）——实测两行时，笔刷只盖住第一行，
       折角块的第二行直接漏到白底外面

**需要「有形状又能长高」时拆两段**：SVG 只做有形状的那一截（固定高度的顶边），
会长高的部分交给 CSS `background` 接住。实测一行两行都撑得住：

    <section>
      <svg height="20">…右上角切一刀的路径…</svg>   ← 固定高度，只管形状
      <section style="background:同色; padding:…">{content}</section>  ← 自动长高
    </section>

## 参照设计手法的能力表 ⭐（2026-09-07 探针稿 · 25 条 · 手机微信实测）

对着两组杂志风参照图（满版照片、文字压图、描边字、竖排、Didot 大字）把用到的手法
逐条发进草稿箱，回读 HTML 比对 + 手机微信逐条看渲染。**HTML 层 25 条只删了 calc()**，
但手机上又倒了 3 条——第二次证实「HTML 里活着 ≠ 渲得出来」（第一次是中文字体）。

### 能用（手机实测渲染正确）

| 手法 | 写法 | 意味着什么 |
|---|---|---|
| **文字压在照片上** | `section` 的 `background:url(微信CDN) center/cover` + 内部文字 | position 死了，但这条活着，**杂志风最核心的手法可用** |
| 文字叠图底部 | `<img>` 后接 `section` 用 `margin-top:-64px` 拉上去 | 第二条叠图路径 |
| 半透明色带压图 | 同上 + `background:rgba(0,0,0,.45)` | 图上标注条 |
| **描边空心字** | `-webkit-text-stroke:2px #111; color:transparent` | 「Hot」空心 +「Spring」实心那种 |
| **竖排** | `writing-mode:vertical-rl` | 竖排英文/中文标题 |
| **iOS 自带西文字体** | `font-family:Didot` / `Baskerville` / `"Snell Roundhand"` / `"Avenir Next"` / `Futura` | 全部渲染出真字形。**Didot 可做高对比衬线 masthead**。带数字的名字必须加引号（`"Bodoni 72"`，不加引号整条失效——这是 CSS 语法不是微信限制） |
| 渐变填充文字 | `background:linear-gradient(...)` + `-webkit-background-clip:text` + `color:transparent` | 渐变色大字 |
| 巨号字 + 紧行距 | `font-size:96px; line-height:.85` + `vertical-align:top; margin-left:-30px` | 2023/4 叠数字那种 |
| `text-shadow` | `0 2px 8px rgba(0,0,0,.7)` | 白字压浅图的可读性 |
| **`object-fit:cover`** | 配固定 `height` | 裁成横条/方块不变形。微信剥掉 `width` 属性也不影响 |
| **`mask-image` 渐隐** | `-webkit-mask-image:linear-gradient(#000 45%, transparent)` | 图下缘淡进白底，「Light」沙丘那种 |
| **`clip-path`** | `polygon(0 0,100% 0,100% 70%,0 100%)` | 斜切、异形裁图 |
| 圆形裁图 | `border-radius:50%` + `object-fit:cover` | 头像/圆图 |
| `mix-blend-mode` | `overlay` | 能渲染，效果依赖图片明暗，偏弱 |
| `overflow:hidden` + 固定高 | | 裁切容器 |
| `white-space:nowrap` | | 展示字不折行 |
| `opacity` / `aspect-ratio` / `text-transform:uppercase` / `letter-spacing:6px` | | 全部正常 |

### HTML 活着、手机不渲染（第二类陷阱）

| 手法 | 现象 |
|---|---|
| **`filter:grayscale()` / `filter:blur()`** | 属性原样在 HTML 里，图片仍是彩色/清晰。**灰度和模糊做不了**，要黑白图就传黑白图 |
| **`float:left`** | 图在左，但文字不绕图、从图下方开始。**文字绕图做不了** |

### 满版 / 冲出边距（部分成立，见下一条探针）

- 微信自己的正文左右边距 **≈ 20px**（iPhone 实测：文字左缘距屏 20px）
- `margin:0 -16px` 能把元素往左拉到距屏 4px——**左侧冲边可行**
- 但 `calc()` 被删，`width:calc(100% + 32px)` 没了，元素只是平移不变宽——右侧留白
- `width:100vw` 保留但被微信注入的 `max-width:100%` 压回容器宽，**vw 满版无效**
- `<section>` 两侧负 margin 只平移不拉伸（不是 `width:auto` 的行为，微信可能也给 section 套了 max-width）

要真满版得绕开 calc，见后续探针（padding 撑宽法）。

### 对四套模版意味着什么

杂志风参照图里的手法，**除了「文字绕图」「灰度/模糊滤镜」「真满版」三样，其余全部可用**。
文字压图、描边字、竖排、Didot、渐隐、斜切——这一整套此前一个都没用过。

## SVG 的坑

内联 SVG 可用，但：

- **不能有 `id`**（会被删，导致内部 `url(#…)` 引用全断）
- 不能含 `<style>` `<script>` `<a>`
- `background` 的 `url()` 里**地址不能加引号**，单双引号都会被过滤
- `<image>` 标签的图片**必须是微信素材库地址**，外链和 Base64 都不行
- iOS 上 `transform-origin` 不可靠

### 这条 `id` 限制定义了整个设计空间

要 `id` 才能用的东西**全部不可用**——这不是「少一个特性」，是砍掉了一整片：

    ❌ linearGradient / radialGradient    渐变
    ❌ pattern                            网点、斜线、纸纹底纹
    ❌ clipPath / mask                    文字形状的窗口、图片裁成异形
    ❌ filter                             feTurbulence 做真纸纹、模糊、投影
    ❌ <use> / marker                     复用图形、箭头端点

渐变归 CSS 管——`style` 里的 `linear-gradient` 是活的（涂 的高亮笔就在用）。
SVG 只管 CSS 做不出的那件事：**不规则的形状**。

能用的就这些，但够了：

    ✅ path / rect / circle / polygon / polyline / line   字面色填充与描边
    ✅ <text>                     实测能渲染（编号环、印章里验过）
    ✅ opacity / fill-opacity / stroke-opacity
    ✅ stroke-dasharray           ⭐ 画弧、画进度环、画长短不一的断线，全靠它
    ✅ stroke-linecap / linejoin
    ✅ transform                  但 iOS 上 transform-origin 不可靠

### SVG 不会长高——凡是要跟着内容长的，交给 CSS

这条踩过两次，都是同一个形状：

1. 标题装饰把 h2 用负 margin 垫到 SVG 上 → 标题折两行时，第二行漏到形状外面
2. 时间轴用 SVG 画竖线串起步骤 → 步骤文案一长，线就接不上，断成几截

**做法**：SVG 只做固定尺寸的那一部分（圆点、角标、顶边的形状），会长高的部分
（竖线、底色、边框）交给 CSS 的 `border-left` / `background`。

### 三层用法：别只在装饰层里打转

    信息层  条形图 · 火花线 · 环形进度 · 对比条 · 评分点阵
            图形本身承载信息，不是装饰。「45s vs 14s」画成两根不等长的条，
            读者不用心算。这一层最容易被忽略，价值也最大——它服务「带来阅读的
            轻松」，却完全不「喧宾夺主」，因为它根本不是装饰。

    结构层  时间轴 · 配图四角标 · 流程连接线
            把元素之间的关系画出来。步骤组件现在每步各自独立，看不出「这是一条线」。

    装饰层  笔锋底线 · 引号 · 落款印章 · 装饰分隔
            纯装饰。做得再好也只是这一层。

所有这些都在「任意形状 + 平涂色」的范围内，不需要 `id`。

## 对模版设计意味着什么

**能做的比想象中多**：嵌套 `<section>` 容器、纯色/边框/圆角/阴影、`inline-block`
并排、居中对齐、内联 SVG 静态装饰——够做出卡片式标题、编号角标、带框引用、
装饰分隔线这类「设计过」的版式。

**做不到的**：任何依赖定位的叠层效果、hover 交互、动画、响应式断点。

**最关键的一条**：因为没有伪元素，**装饰必须作为真实元素插进 HTML**。这意味着
模版不能只是「给每个标签配一段内联样式」——那样最多只能改颜色和间距，永远做不出
带角标的标题或带引号的引用块。想要设计感，模版得能声明**元素模板**（即这个标签
渲染成什么样的 HTML 结构），而不只是样式串。

## 还没测的

1. `position` / `id`（关系到能否做叠层效果，需单独探针）
2. 嵌套超过三层的 `<section>`
3. 微信客户端 webview 与桌面浏览器的其它渲染差异（中文字体一项已实测，见开头）

探针稿的做法：手写 `article.html`（每块一个特性、自带判定标准）→ `publish.py full`
进草稿箱 → `getdraft.py get` 回读 → 渲染回读到的 HTML 逐项核对。
