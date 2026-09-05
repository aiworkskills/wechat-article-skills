"""format.py 回归测试：预格式化保护、表格、引用块、列表、closing.md、字号覆盖。"""
import re
import unittest

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
        return (
            "正文一段。\n\n"
            "![流程步骤：怎么定媒介](imgs/a.png)\n\n"
            "![概念隐喻：完美就是破绽](imgs/b.png)\n\n"
            "![对比两栏：改前 vs 改后](imgs/c.png)\n\n"
            "![封面：不该进正文](imgs/cover.png)\n\n"
            "![没有冒号的alt](imgs/d.png)\n"
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

    def test_alt_without_colon_never_gets_caption(self):
        for style in ("有图注", "关键图有"):
            self.assertNotIn("没有冒号的alt", self._captions(style))
