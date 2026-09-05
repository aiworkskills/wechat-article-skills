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

**单位**：优先 `px`；`vw` / `vh` 可用；**不要用百分比做定位**。

**正文宽度**：约 375px（手机逻辑像素）。所有版式决定都要在这个宽度下成立。

## SVG 的坑

内联 SVG 可用，但：

- **不能有 `id`**（会被删，导致内部 `url(#…)` 引用全断）
- 不能含 `<style>` `<script>` `<a>`
- `background` 的 `url()` 里**地址不能加引号**，单双引号都会被过滤
- `<image>` 标签的图片**必须是微信素材库地址**，外链和 Base64 都不行
- iOS 上 `transform-origin` 不可靠

所以 SVG 适合做**静态装饰**（分隔线、角标、引号），不适合做需要内部引用或变换的图形。

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
3. 微信客户端 webview 与桌面浏览器的渲染差异

探针稿的做法：手写 `article.html`（每块一个特性、自带判定标准）→ `publish.py full`
进草稿箱 → `getdraft.py get` 回读 → 渲染回读到的 HTML 逐项核对。
