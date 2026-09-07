# 经预设包下发的四套模版：彩 / 手 / 构 / 码

这里的 YAML **不在** `format.py` 的内置搜索路径里。内置只留四套（`../themes/`：块 / 报 / 书 / 艺），
这四套由 aiworkskills.cn 的预设包（`.aws`）下发到用户的 `.aws-article/presets/formatting/`。

放在仓库里的原因：它们和内置四套一样是网站系统预设的真源（网站仓库
`backend/scripts/build_formatting_presets.py` 读 `../themes/` + 本目录生成 fixture 与预览页），
也一起受 `tests/test_format.py` / `tests/test_schemes.py` 的守卫（八套核心层互不相同、
每套每个配色对比度过线、换配色不改版式）。

| 模版 | 骨架 | 一句话 | 配色 |
|------|------|--------|------|
| `彩` | cai | 渐变：色条、渐变标题字、渐变金句卡 | 靛青 / 玫紫 / 暮橙 |
| `手` | shou | 手作：笔锋、荧光笔、胶带贴图、手写小标 | 朱红·黄笔 / 墨蓝·粉笔 / 深绿·薄荷笔 |
| `构` | gou | 包豪斯：三色条、方块编号、圆形引号 | 蓝黄 / 赤黑 / 绿橙 |
| `码` | ma | 工程：等宽小标、灰底 chip 加粗、左竖线引用 | 蓝 / 紫 / 绿 |

本地要直接用：复制到 `.aws-article/presets/formatting/` 即可，或 `--theme` 前先把文件放进去。
`_sample.md` 是渲染样张用的稿子。
