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

EIGHT = [("块", "kuai"), ("报", "bao"), ("书", "shu"), ("艺", "yi"),
         ("彩", "cai"), ("手", "shou"), ("构", "gou"), ("码", "ma")]


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

    def test_unknown_scheme_errors(self):
        t = _theme("块")
        with self.assertRaises(SystemExit):
            fmt._apply_scheme(t, "不存在的配色")

    def test_no_scheme_is_identity(self):
        t = _theme("块")
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
