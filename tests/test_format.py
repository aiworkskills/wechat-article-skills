"""format.py 回归测试：预格式化保护、表格、引用块、列表、closing.md、字号覆盖。"""
import re
import unittest
import io
import os
import tempfile
from pathlib import Path

from tests._load import load

fmt = load("skills/aws-wechat-article-formatting/scripts/format.py", "aws_format")


def _styles(theme_name="default", overrides=None):
    return fmt._build_styles(fmt._load_theme_file(fmt._find_theme_file(theme_name)), overrides or {})


class PreformatTest(unittest.TestCase):
    def test_body_text_still_spaced_and_quoted(self):
        out = fmt._preformat_markdown('AI工具在2026年发布，他说"很好"。')
        self.assertEqual(out, 'AI 工具在 2026 年发布，他说「很好」。')

    def test_image_and_link_targets_untouched(self):
        src = "![截图：淘米图1](imgs/淘米图1.png)\n![流程](imgs/AI工具.png)\n[文](https://x.com/AI工具)"
        out = fmt._preformat_markdown(src)
        self.assertIn("(imgs/淘米图1.png)", out)
        self.assertIn("(imgs/AI工具.png)", out)
        self.assertIn("(https://x.com/AI工具)", out)
        self.assertIn("![截图：淘米图 1]", out)  # alt 文字仍按正文规则处理

    def test_code_untouched(self):
        src = '代码`print("hi")`和\n```py\ns = "x"  # 注释1\n```\n'
        out = fmt._preformat_markdown(src)
        self.assertIn('`print("hi")`', out)
        self.assertIn('s = "x"  # 注释1', out)
        self.assertNotIn("「", out)

    def test_embed_and_html_and_bare_url_untouched(self):
        src = '{embed:link:AI工具指南}\n<img src="a.png" alt="图1">\nhttps://a.com/中文1'
        out = fmt._preformat_markdown(src)
        self.assertIn("{embed:link:AI工具指南}", out)
        self.assertIn('<img src="a.png" alt="图1">', out)
        self.assertIn("https://a.com/中文1", out)

    def test_quotes_do_not_pair_across_lines(self):
        out = fmt._preformat_markdown('他说"第一句\n第二句"结束')
        self.assertNotIn("「", out)


class MdToHtmlTest(unittest.TestCase):
    def setUp(self):
        self.styles = _styles()

    def test_inline_code_escaped_and_isolated(self):
        html = fmt._md_to_html("x `a < b` 和 `<div>` 和 `**不加粗**`", self.styles)
        self.assertIn("a &lt; b</code>", html)
        self.assertIn("&lt;div&gt;</code>", html)
        self.assertIn("**不加粗**</code>", html)
        self.assertNotIn("<strong", html)

    def test_inline_image_not_turned_into_link(self):
        html = fmt._md_to_html("看 ![图](a.png) 和 [链](b)", self.styles)
        self.assertNotIn("!<a", html)
        self.assertIn('href="b"', html)

    def test_table_alignment_row_and_duplicate_headers(self):
        md = "| 方案 | 速度 |\n|:---:|---:|\n| A | 快 |\n\n| 方案 | 速度 |\n|---|---|\n| B | 慢 |\n"
        html = fmt._md_to_html(md, self.styles)
        self.assertNotIn(":---:", html)
        self.assertEqual(html.count("<table"), 2)
        self.assertEqual(html.count("<th "), 4)
        self.assertEqual(html.count("<td "), 4)

    def test_blockquote_blank_line_keeps_one_quote(self):
        html = fmt._md_to_html("> 引用\n>\n> 第二段\n", self.styles)
        self.assertEqual(html.count("<blockquote"), 1)
        self.assertNotIn("&gt;</p>", html)
        self.assertNotIn(">></p>", html)

    def test_nested_list_four_space_indent(self):
        html = fmt._md_to_html("- 一\n    - 二\n- 三\n", self.styles)
        self.assertEqual(html.count("<ul"), 2)
        self.assertNotIn("<ul style=\"padding-left:20px;\"><ul", html)

    def test_first_h1_skipped_only_for_article(self):
        self.assertNotIn("<h1", fmt._md_to_html("# 标题\n\n正文", self.styles))
        self.assertIn("<h1", fmt._md_to_html("# 关于作者\n\n正文", self.styles, skip_first_h1=False))

    def test_cover_image_excluded_from_body(self):
        html = fmt._md_to_html("![封面：x](placeholder)\n\n![流程：y](imgs/a.png)", self.styles)
        self.assertNotIn("placeholder", html)
        self.assertIn('src="imgs/a.png"', html)


class BuildStylesTest(unittest.TestCase):
    def test_font_size_override_hits_paragraph_and_li(self):
        for theme in ("default", "grace", "modern", "simple"):
            st = _styles(theme, {"font-size": "15px"})
            self.assertIn("font-size:15px", st["p"], theme)
            self.assertNotIn("font-size:16px", st["p"], theme)
            if "font-size" in st["li"]:
                self.assertIn("font-size:15px", st["li"], theme)

    def test_font_size_override_rewrites_hardcoded_custom_theme(self):
        st = fmt._build_styles({"styles": {"p": "font-size:14px; color:#000;"}}, {"font-size": "18px"})
        self.assertEqual(st["p"], "font-size:18px; color:#000;")

    def test_default_theme_keeps_16px(self):
        self.assertIn("font-size:16px", _styles()["p"])


if __name__ == "__main__":
    unittest.main()


class CaptionStyleTest(unittest.TestCase):
    """config.yaml 的 caption_style 原先谁也没读——图注是「alt 里有全角冒号就切一刀」写死的，
    用户在配置台选「无图注」照样出图注。"""

    def _md(self):
        # 图注写在 markdown 原生的 title 参数里；alt 冒号后那段是给生图模型的画面指令，
        # 两者用途完全不同，不能互相兼任（见 test_caption_only_from_explicit_title）。
        return (
            "正文一段。\n\n"
            '![流程步骤：白板上四个手写方框](imgs/a.png "怎么定媒介")\n\n'
            '![概念隐喻：马克笔笔尖是打印喷头](imgs/b.png "完美就是破绽")\n\n'
            '![对比两栏：左右两栏并排](imgs/c.png "改前 vs 改后")\n\n'
            '![封面：不该进正文](imgs/cover.png "封面图注")\n\n'
            '![没有冒号的alt](imgs/d.png "无类型前缀")\n'
        )

    def _captions(self, style):
        styles = fmt._build_styles(fmt._load_theme("default"))
        html = fmt._md_to_html(self._md(), styles, caption_style=style)
        return re.findall(r'<p style="text-align:center; font-size:\d+px[^>]*>([^<]*)</p>', html)

    def test_always(self):
        self.assertEqual(self._captions("有图注"),
                         ["怎么定媒介", "完美就是破绽", "改前 vs 改后"])

    def test_never(self):
        self.assertEqual(self._captions("无图注"), [])

    def test_key_images_only(self):
        """关键图有：只有信息位的图配图注，节奏位（概念隐喻等）不配。"""
        self.assertEqual(self._captions("关键图有"), ["怎么定媒介", "改前 vs 改后"])

    def test_unknown_value_falls_back_to_always(self):
        self.assertEqual(len(self._captions("随便写的")), 3)

    def test_empty_value_falls_back_to_always(self):
        self.assertEqual(len(self._captions("")), 3)

    def test_alt_without_type_prefix_never_gets_caption(self):
        """alt 没有类型前缀时判断不出图位，一律不配图注。"""
        for style in ("有图注", "关键图有"):
            self.assertNotIn("无类型前缀", self._captions(style))


class ComponentTest(unittest.TestCase):
    """版式组件 :::name[参数] … :::

    微信只认内联样式、没有伪元素，所以「标题前的角标」「引用块的大引号」必须真的
    插元素。主题只能给标签配样式，表达不了结构——组件补的就是这一层。
    """

    def setUp(self):
        self.styles = fmt._build_styles(fmt._load_theme("default"))
        self.comps = fmt._load_components()

    def test_builtin_components_load(self):
        self.assertIn("section-title", self.comps)
        self.assertIn("quote-card", self.comps)
        for name, spec in self.comps.items():
            self.assertTrue(spec.get("template"), f"{name} 缺 template")
            for field in ("when_to_use", "when_not_to_use", "anti_pattern", "example"):
                self.assertTrue(spec.get(field), f"{name} 缺 {field}（Agent 选型要用）")

    def _render(self, md):
        return fmt._md_to_html(md, self.styles, components=self.comps)

    def test_single_body_renders_structure(self):
        html = self._render(":::section-title[01]\n同一个模型，两个分数\n:::")
        self.assertIn("border-radius:15px", html)      # 圆形角标
        self.assertIn("01", html)
        self.assertIn("同一个模型", html)

    def test_free_body_joins_paragraphs(self):
        html = self._render(":::quote-card[出处]\n第一段\n\n第二段\n:::")
        self.assertIn("第一段<br />第二段", html)
        self.assertIn("出处", html)

    def test_theme_color_is_injected(self):
        primary = self.styles["primary-color"]
        html = self._render(":::section-title[01]\n标题\n:::")
        self.assertIn(primary, html, "组件必须继承主题主色，否则和主题脱节")
        for leftover in ("{arg}", "{content}", "{primary-color}", "{text-color}"):
            self.assertNotIn(leftover, html, f"占位符 {leftover} 未被替换")

    def test_arg_is_escaped(self):
        html = self._render(':::quote-card[<b>x</b>]\n内容\n:::')
        self.assertNotIn("<b>x</b>", html, "方括号参数须转义，否则可注入标签")

    def test_unknown_component_falls_through(self):
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            html = self._render("正文\n\n:::no-such[x]\n内容\n:::")
        self.assertIn("内容", html, "未知组件不能把正文吞掉")
        self.assertIn("未知版式组件", err.getvalue())

    def test_unclosed_component_falls_through(self):
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            html = self._render(":::quote-card[x]\n没有结尾")
        self.assertIn("没有结尾", html, "缺少闭合时不能把正文吞掉")
        self.assertIn("缺少结尾", err.getvalue())

    def test_no_components_means_plain_text(self):
        """未加载组件时按原文走，不能报错。"""
        html = fmt._md_to_html(":::quote-card[x]\n内容\n:::", self.styles, components=None)
        self.assertIn("内容", html)

    def test_user_dir_overrides_builtin(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            try:
                os.chdir(d)
                p = Path(".aws-article/presets/components")
                p.mkdir(parents=True)
                (p / "quote-card.yaml").write_text(
                    "name: quote-card\ntemplate: '<section>用户版</section>'\n", encoding="utf-8")
                comps = fmt._load_components()
                self.assertIn("用户版", comps["quote-card"]["template"])
            finally:
                os.chdir(cwd)

    def test_rows_body_renders_each_line(self):
        html = self._render(
            ":::stat[标题]\n62.7% | 标准 harness\n99.9% | Provider Adapter\n:::")
        self.assertIn("62.7%", html)
        self.assertIn("Provider Adapter", html)
        self.assertEqual(html.count("border-bottom:1px solid"), 2, "两行应各渲染一次")

    def test_row_template_also_gets_theme_vars(self):
        """行模板是先渲染再塞进 {content} 的，容易漏掉变量替换。"""
        html = self._render(":::stat[t]\n1 | a\n:::")
        self.assertNotIn("{primary-color}", html)
        self.assertNotIn("{text-muted}", html)
        self.assertIn(self.styles["primary-color"], html)

    def test_missing_column_does_not_break_row(self):
        """作者少写一列时补空串，不能整块渲染失败。"""
        html = self._render(":::steps[t]\n只有步骤名\n:::")
        self.assertIn("只有步骤名", html)
        self.assertNotIn("{c1}", html)

    def test_extra_columns_are_dropped(self):
        html = self._render(":::stat[t]\n1 | a | 多余的 | 更多\n:::")
        self.assertIn("1", html)
        self.assertNotIn("多余的", html, "超出 row_columns 的列应丢弃而不是溢出版式")

    def test_arg_split_for_two_column_header(self):
        html = self._render(":::compare[左边 / 右边]\na | b\n:::")
        self.assertIn("左边", html)
        self.assertIn("右边", html)

    def test_blank_rows_ignored(self):
        html = self._render(":::stat[t]\n1 | a\n\n2 | b\n:::")
        self.assertEqual(html.count("border-bottom:1px solid"), 2)

    def test_row_map_maps_enum_to_symbol(self):
        """枚举列必须能映射成符号：直接打 done 会被窄列截成 don。"""
        html = self._render(":::checklist[t]\ndone | 事项一\ntodo | 事项二\n:::")
        self.assertNotIn(">done<", html)
        self.assertNotIn(">todo<", html)
        self.assertIn("&#10003;", html)      # done → ✓
        self.assertIn("&#9675;", html)       # todo → ○

    def test_row_map_unknown_value_falls_back_to_raw(self):
        """写错状态值时原样输出，不能整行消失。"""
        html = self._render(":::checklist[t]\n完成 | 事项\n:::")
        self.assertIn("完成", html)
        self.assertIn("事项", html)

    def test_component_color_inferred_when_theme_has_no_variables(self):
        """网站导出的主题只有字面色的 styles、没有 variables 块。

        不反推的话，{primary-color} 会落到 DEFAULT_VARIABLES 的兜底蓝，
        16 套主题的组件全是同一个 #0F4C81——用户原话「我看到的小标题都是蓝色」。
        """
        theme = {"styles": {
            "strong": "color:#C0392B; font-weight:700;",
            "blockquote": "background:#FDF2F0; padding:20px;",
            "p": "font-size:16px; line-height:1.95; color:#1F1F1F; margin:0 0 28px;",
        }}
        styles = fmt._build_styles(theme)
        self.assertEqual(styles["primary-color"], "#C0392B")
        self.assertEqual(styles["bg-accent-color"], "#FDF2F0")
        html = fmt._md_to_html(":::section-title[01]\n标题\n:::", styles, components=self.comps)
        self.assertIn("#C0392B", html)
        self.assertNotIn(fmt.DEFAULT_VARIABLES["primary-color"], html)

    def test_explicit_variables_win_over_inference(self):
        theme = {"variables": {"primary-color": "#123456"},
                 "styles": {"strong": "color:#C0392B;"}}
        self.assertEqual(fmt._build_styles(theme)["primary-color"], "#123456")

    def test_cli_color_override_still_wins(self):
        theme = {"styles": {"strong": "color:#C0392B;"}}
        styles = fmt._build_styles(theme, {"primary-color": "#00FF00"})
        self.assertEqual(styles["primary-color"], "#00FF00")

    def test_inference_falls_back_to_default_when_no_color_anywhere(self):
        styles = fmt._build_styles({"styles": {"p": "font-size:16px;"}})
        self.assertEqual(styles["primary-color"], fmt.DEFAULT_VARIABLES["primary-color"])

    def test_caption_only_from_explicit_title(self):
        """alt 里冒号后那段是给生图模型的画面指令，不能兼任图注。

        实例：![氛围：开发者站在巨型99.9分数牌前，视线越过分数望向复杂而开放的城市]
        —— 拿它当图注是把读者眼睛已经看见的东西复述一遍，零信息。
        """
        styles = fmt._build_styles(fmt._load_theme("default"))
        html = fmt._md_to_html('![氛围：开发者站在巨型99.9分数牌前](a.png)', styles)
        self.assertIn("<img", html)
        self.assertNotIn("开发者站在巨型99.9分数牌前</p>", html)

    def test_caption_rendered_when_title_given(self):
        styles = fmt._build_styles(fmt._load_theme("default"))
        html = fmt._md_to_html('![信息图：画面指令](a.png "同一模型两个分数，差 37 个百分点")', styles)
        self.assertIn("同一模型两个分数", html)
        self.assertNotIn("画面指令</p>", html)

    def test_title_does_not_leak_into_src(self):
        """title 必须从 src 里摘干净，否则图片路径带上引号会直接 404。"""
        styles = fmt._build_styles(fmt._load_theme("default"))
        html = fmt._md_to_html('![x：y](imgs/a.png "图注")', styles)
        self.assertIn('src="imgs/a.png"', html)

    def test_single_quoted_and_curly_quoted_title(self):
        styles = fmt._build_styles(fmt._load_theme("default"))
        for mark in ('"图注A"', "'图注B'", '“图注C”'):
            html = fmt._md_to_html(f'![x：y](a.png {mark})', styles)
            self.assertIn(mark.strip('"\'“”'), html)
