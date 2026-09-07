# 经预设包下发的四套模版：活力 / 手账 / 硬朗 / 技术

这里的 YAML **不在** `format.py` 的内置搜索路径里。内置只留四套（`../themes/`：亲和 / 资讯 / 书卷 / 杂志），
这四套由 aiworkskills.cn 的预设包（`.aws`）下发到用户的 `.aws-article/presets/formatting/`。

放在仓库里的原因：它们和内置四套一样是网站系统预设的真源（网站仓库
`backend/scripts/build_formatting_presets.py` 读 `../themes/` + 本目录生成 fixture 与预览页），
也一起受 `tests/test_format.py` / `tests/test_schemes.py` 的守卫（八套核心层互不相同、
每套每个配色对比度过线、换配色不改版式、每套都带 `when_to_use` 与配色说明）。

| 模版 | 骨架 | 适合 | 配色 |
|------|------|------|------|
| `活力` | cai | 产品发布、增长复盘、年轻读者 | 靛青 / 玫紫 / 暮橙 |
| `手账` | shou | 个人笔记、复盘、学习记录 | 朱红·黄笔 / 墨蓝·粉笔 / 深绿·薄荷笔 |
| `硬朗` | gou | 观点、宣言、立场鲜明 | 蓝黄 / 赤黑 / 绿橙 |
| `技术` | ma | 工程实践、技术文档、代码讲解 | 蓝 / 紫 / 绿 |

本地要直接用：复制到 `.aws-article/presets/formatting/` 即可。
样张在 `../_sample.md`（配 `../_sample-image.svg`），`--preview` 用的就是它。
