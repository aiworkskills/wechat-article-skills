"""配色方案（schemes）回归测试。

一套配色 = 一组 variables 覆盖，不动 styles。守卫三件事：
1. 每套模版的每个配色都能渲染出对比度干净的整页（护栏对每个方案都成立，不只对默认色）；
2. 选了配色以后颜色真的换了（主色进了 HTML），而版式没变（组件结构一样）；
3. 不存在的配色名要报错，而不是静默用默认色。
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORMAT_PY = ROOT / "skills/aws-wechat-article-formatting/scripts/format.py"
PRESETS = ROOT / "skills/aws-wechat-article-formatting/references/presets"
sys.path.insert(0, str(ROOT / "tests"))
from contrast_audit import violations  # noqa: E402

spec = importlib.util.spec_from_file_location("fmt", FORMAT_PY)
fmt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmt)

SAMPLE = """# 样张

> 导语在第一个二级标题之前。

正文有 **加粗** 和 *强调* 和 [链接](https://example.com)，还有 `code`。

## 第一节

- **标签**：说明文字
- 普通列表项

> 金句压在这里。 —— 出处

### 小节

- [x] 做完了
- [ ] 还没做

---

结尾一段。
"""

EIGHT = [("亲和", "kuai"), ("资讯", "bao"), ("书卷", "shu"), ("杂志", "yi"),
         ("活力", "cai"), ("手账", "shou"), ("硬朗", "gou"), ("技术", "ma")]


def _theme(name: str) -> dict:
    for d in ("themes", "templates"):
        p = PRESETS / d / f"{name}.yaml"
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    raise FileNotFoundError(name)


def _render(theme: dict, skeleton: str, scheme: str | None) -> str:
    st = fmt._build_styles(fmt._apply_scheme(theme, scheme))
    return fmt._wrap_document(fmt._md_to_html(SAMPLE, st, components=fmt._load_components(skeleton)), st)


def _shape(html: str) -> str:
    """去掉颜色后的结构指纹：标签序列 + 非颜色样式。同一骨架换配色，指纹必须不变。"""
    no_color = re.sub(r"#[0-9A-Fa-f]{6}|rgba?\([^)]*\)", "C", html)
    return no_color


class SchemesTest(unittest.TestCase):
    def test_every_template_declares_schemes_with_default_first(self):
        for name, _ in EIGHT:
            t = _theme(name)
            schemes = t.get("schemes") or []
            self.assertGreaterEqual(len(schemes), 3, f"{name} 至少要有三套配色")
            names = [s["name"] for s in schemes]
            self.assertEqual(len(names), len(set(names)), f"{name} 配色名重复: {names}")
            first = schemes[0]["variables"]
            self.assertEqual(first["primary-color"].upper(), t["variables"]["primary-color"].upper(),
                             f"{name} 的第一套配色应当就是模版默认色，方便列出来选")
            for s in schemes:
                self.assertTrue(fmt._normalize_hex(s["variables"]["primary-color"]), f"{name}/{s['name']} 主色不是合法 hex")

    def test_every_scheme_renders_contrast_clean(self):
        for name, sk in EIGHT:
            t = _theme(name)
            for s in t["schemes"]:
                html = _render(t, sk, s["name"])
                self.assertEqual(violations(html), [], f"{name}/{s['name']} 对比度不过")

    def test_scheme_changes_color_but_not_layout(self):
        for name, sk in EIGHT:
            t = _theme(name)
            base = _render(t, sk, None)
            for s in t["schemes"][1:]:
                html = _render(t, sk, s["name"])
                self.assertEqual(_shape(base), _shape(html), f"{name}/{s['name']} 换配色改了版式")
                pc = fmt._normalize_hex(s["variables"]["primary-color"]).upper()
                # 主色或其派生色（fill/ink）至少有一个进了页面
                pal = fmt._derive_palette(pc, s["variables"].get("secondary-color"))
                hits = [c for c in (pc, pal["primary-fill"].upper(), pal["primary-ink"].upper()) if c in html.upper()]
                self.assertTrue(hits, f"{name}/{s['name']} 主色 {pc} 没进页面")
                self.assertNotEqual(base, html, f"{name}/{s['name']} 换配色后页面没变")


    def test_every_template_carries_selection_criteria(self):
        """模版要能被大模型选中，光有名字和「长相」不够——必须写清适合/不适合什么内容。

        决定用哪套模版的时刻在 main 的「本篇预设单选落盘」：那时手上只有候选池里的
        名字。名字带不动语义，判据得跟着模版走，并且要能被 --list-themes 打出来。
        """
        for name, _ in EIGHT:
            t = _theme(name)
            for key in ("when_to_use", "when_not_to_use"):
                text = str(t.get(key) or "").strip()
                self.assertTrue(text, f"{name} 缺 {key}")
                self.assertGreaterEqual(len(text), 20, f"{name} 的 {key} 太短，说不清场合：{text!r}")
            for sc in t["schemes"]:
                desc = str(sc.get("description") or "").strip()
                self.assertTrue(desc, f"{name}/{sc['name']} 的配色没有说明，模型只能靠名字猜色相")

    def test_list_themes_exposes_criteria_and_colors(self):
        """--list-themes 是 agent 唯一一次能同时看到判据和色值的地方。"""
        rows = {t["name"]: t for t in fmt._list_themes()}
        for name, skeleton in EIGHT[:4]:      # 内置四套一定在搜索路径里
            self.assertIn(name, rows, "内置模版没被列出来")
            row = rows[name]
            self.assertTrue(row["when_to_use"], f"{name} 的适用场景没被列出来")
            self.assertEqual(row["skeleton"], skeleton)
            for sc in row["schemes"]:
                self.assertRegex(sc["color"], r"^#[0-9A-Fa-f]{6}$", f"{name}/{sc['name']} 没带色值")
                self.assertTrue(sc["description"], f"{name}/{sc['name']} 没带说明")

    def test_preview_page_renders_every_scheme_side_by_side(self):
        """--preview 是「松绿长什么样」的答案：说不清楚的东西只能看。"""
        import tempfile
        theme = _theme("亲和")
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "p.html"
            fmt._write_preview("亲和", str(out))
            html = out.read_text(encoding="utf-8")
        for sc in theme["schemes"]:
            self.assertIn(sc["name"], html, f"对照页里没有 {sc['name']} 这一栏")
            self.assertIn(sc["variables"]["primary-color"], html, f"{sc['name']} 那一栏没用它自己的色")
        self.assertEqual(html.count('width:375px'), len(theme["schemes"]), "每套配色应各占一栏真机宽")

    def test_unknown_scheme_errors(self):
        t = _theme("亲和")
        with self.assertRaises(SystemExit):
            fmt._apply_scheme(t, "不存在的配色")

    def test_no_scheme_is_identity(self):
        t = _theme("亲和")
        self.assertIs(fmt._apply_scheme(t, None), t)
        self.assertIs(fmt._apply_scheme(t, ""), t)

    def test_secondary_soft_derived_from_secondary(self):
        pal = fmt._derive_palette("#5B4BFF", "#17A398")
        self.assertNotEqual(pal["secondary-soft"], pal["bg-accent-color"])
        # 没有次色时退回主色卡片底
        pal2 = fmt._derive_palette("#5B4BFF", None)
        self.assertEqual(pal2["secondary-soft"], pal2["bg-accent-color"])

    def test_accent_literals_absent_in_scheme_sensitive_components(self):
        """换配色后不该还有旧默认色残留：渲染非默认配色，页面里不能出现模版默认主色/次色。"""
        for name, sk in EIGHT:
            t = _theme(name)
            default_pc = fmt._normalize_hex(t["variables"]["primary-color"]).upper()
            default_sc = (fmt._normalize_hex(t["variables"].get("secondary-color") or "") or "").upper()
            for s in t["schemes"][1:]:
                html = _render(t, sk, s["name"]).upper()
                self.assertNotIn(default_pc, html, f"{name}/{s['name']} 还残留默认主色 {default_pc}")
                scheme_sc = (fmt._normalize_hex(s["variables"].get("secondary-color") or "") or "").upper()
                if default_sc and scheme_sc and scheme_sc != default_sc:
                    self.assertNotIn(default_sc, html, f"{name}/{s['name']} 还残留默认次色 {default_sc}")


if __name__ == "__main__":
    unittest.main()
