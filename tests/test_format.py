"""format.py 回归测试：预格式化保护、表格、引用块、列表、closing.md、字号覆盖。"""
import re
import sys
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
        # 包含最后那张 alt 没有类型前缀的图。「有图注」就是有图注——作者显式写了 title，
        # 却因为 alt 里没冒号被丢掉，是判据没跟着「图注改由 title 指定」一起改。
        self.assertEqual(self._captions("有图注"),
                         ["怎么定媒介", "完美就是破绽", "改前 vs 改后", "无类型前缀"])

    def test_never(self):
        self.assertEqual(self._captions("无图注"), [])

    def test_key_images_only(self):
        """关键图有：只有信息位的图配图注，节奏位（概念隐喻等）不配。"""
        self.assertEqual(self._captions("关键图有"), ["怎么定媒介", "改前 vs 改后"])

    def test_unknown_value_falls_back_to_always(self):
        self.assertEqual(len(self._captions("随便写的")), 4)

    def test_empty_value_falls_back_to_always(self):
        self.assertEqual(len(self._captions("")), 4)

    def test_key_only_drops_caption_when_slot_is_unknown(self):
        """「关键图有」是用户主动收窄的设置，认不出图位时宁可不出。

        「有图注」下则相反——那是最宽的设置，显式写的 title 必须出。
        """
        self.assertNotIn("无类型前缀", self._captions("关键图有"))
        self.assertIn("无类型前缀", self._captions("有图注"))


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
        # 断结构不断像素：参数与正文各自成块、且参数块在前。
        # 早先这里断言的是 border-radius:15px，等于把某一版装饰的具体取值钉死在测试里，
        # 改一次设计就红一次，而红的并不是坏掉的行为。
        self.assertLess(html.index("01"), html.index("同一个模型"))
        self.assertIn("01", html)
        self.assertIn("同一个模型", html)

    def test_free_body_makes_real_paragraphs(self):
        """多段要有真正的段落间距。早先用 <br /> 连接，两段挤在一起没有气口。"""
        html = self._render(":::quote-card[出处]\n第一段\n\n第二段\n:::")
        self.assertNotIn("<br />", html)
        self.assertIn("第一段", html)
        self.assertIn("第二段", html)
        self.assertIn("margin:0 0 0.9em", html, "段间距丢了")
        self.assertIn("出处", html)

    def test_free_body_single_paragraph_has_no_extra_wrapper(self):
        """只有一句话时不该平白多包一层 section。"""
        html = self._render(":::quote-card[出处]\n只有一句\n:::")
        self.assertNotIn("margin:0 0 0.9em", html)
        self.assertIn("只有一句", html)

    def test_closing_and_lead_components_exist(self):
        """两个 100% 出现率的位置：7/7 篇文章都有导语和文末区块。"""
        for name in ("closing", "lead"):
            self.assertIn(name, self.comps, f"缺组件 {name}")
        html = self._render(":::closing[马斯]\n点个赞\n:::")
        self.assertIn("马斯", html)
        # 导语必须与引用块在视觉上分开。两者语义不同——导语是作者的开场白，
        # 引用块是别人的话——共用「带底色的卡片」这一种长相会让读者分不清。
        # 断的是「导语正文不坐在底色块上」，而不是某一版具体用了哪根边框。
        lead = self._render(":::lead\n导语内容\n:::")
        body = lead[lead.index("导语内容") - 220:lead.index("导语内容")]
        self.assertNotIn("background", body, "导语正文不该坐在底色块上，那是引用块的长相")
        self.assertIn(self.styles["primary-color"], lead, "导语需要一处主色标记")

    def test_theme_color_is_injected(self):
        html = self._render(":::section-title[01]\n标题\n:::")
        self.assertIn(self.styles["primary-ink"], html, "组件必须继承主题主色，否则和主题脱节")
        for leftover in ("{arg}", "{content}", "{primary-color}", "{primary-ink}", "{text-color}"):
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
        self.assertEqual(html.count("tabular-nums"), 2, "两行应各渲染一次")

    def test_row_template_also_gets_theme_vars(self):
        """行模板是先渲染再塞进 {content} 的，容易漏掉变量替换。"""
        html = self._render(":::stat[t]\n1 | a\n:::")
        self.assertNotIn("{primary-color}", html)
        self.assertNotIn("{text-muted}", html)
        self.assertIn(self.styles["primary-ink"], html)

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
        self.assertEqual(html.count("tabular-nums"), 2)

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
        self.assertIn(styles["primary-ink"], html)
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


class AccentInkTest(unittest.TestCase):
    """强调色分成两个：面积用 primary-color，文字用压深过的 primary-ink。

    同一个颜色既要当大面积块底（h2 实心块、steps 的编号圈），又要当正文级文字
    （h3、链接、行内代码），而这两件事对明度的要求是反的。16 套里有四套
    （暖橙、马卡龙粉、薄荷绿、莫兰迪）的强调色压白底只有 3.1~3.9，当块底够用、
    当 17px 的文字就低于可读线。不分开就只能改色相，那等于把主题的身份也改了。
    """

    def test_low_contrast_accent_is_darkened_for_text(self):
        theme = {"variables": {"primary-color": "#17A398"}}     # 薄荷绿，压白底 3.12
        styles = fmt._build_styles(theme)
        self.assertEqual(styles["primary-color"], "#17A398", "面积用色不该被动")
        self.assertGreaterEqual(fmt._contrast_on_white(styles["primary-ink"]), 4.5)

    def test_already_readable_accent_is_left_alone(self):
        theme = {"variables": {"primary-color": "#14508C"}}     # 金融蓝，压白底 8.22
        styles = fmt._build_styles(theme)
        self.assertEqual(styles["primary-ink"], "#14508C", "够读的颜色不该被平白压深")

    def test_theme_can_declare_its_own_ink(self):
        theme = {"variables": {"primary-color": "#17A398", "primary-ink": "#005B54"}}
        self.assertEqual(fmt._build_styles(theme)["primary-ink"], "#005B54")




class CaptionGateTest(unittest.TestCase):
    """图注的判据必须和「图注从哪来」保持一致。

    图注早先是从 alt 的全角冒号后面切出来的，所以 `_want_caption` 里有一条
    「alt 没冒号就不出图注」。后来图注改成由 markdown 的 title 参数显式指定——
    alt 变成了给生图模型看的画面指令——那条判据就没跟着改，结果是作者明明写了
    图注，却因为 alt 里没冒号被静默丢掉。
    """

    def _render(self, md, caption_style=None):
        theme = {"styles": {"img": "max-width:100%;", "figcaption": "font-size:13px;",
                            "strong": "font-weight:700;"}}
        styles = fmt._build_styles(theme)
        kw = {"caption_style": caption_style} if caption_style else {}
        return fmt._md_to_html(md, styles, **kw)

    def test_explicit_caption_survives_plain_alt(self):
        html = self._render('![排版对比](x.png "图 1：阅读时长分布")')
        self.assertIn("图 1：阅读时长分布", html)

    def test_no_title_means_no_caption(self):
        """alt 冒号后那段是给生图模型的画面指令，拿它当图注等于复述读者已经看见的东西。

        它出现在 alt="" 属性里是应该的（图没加载出来时给读者兜底），
        断的是它没有另外变成一段图注。
        """
        html = self._render("![数据图表：开发者站在巨型分数牌前](x.png)")
        after_img = html.split("/>", 1)[1] if "/>" in html else html
        self.assertNotIn("开发者站在巨型分数牌前", after_img)

    def test_never_wins_over_explicit_title(self):
        html = self._render('![数据图表：画面指令](x.png "图 1：说明")', fmt.CAPTION_NEVER)
        self.assertNotIn("图 1：说明", html)

    def test_key_only_filters_by_slot(self):
        info = self._render('![数据图表：画面指令](x.png "图 1：说明")', fmt.CAPTION_KEY_ONLY)
        self.assertIn("图 1：说明", info)
        rhythm = self._render('![概念隐喻：画面指令](x.png "图 1：说明")', fmt.CAPTION_KEY_ONLY)
        self.assertNotIn("图 1：说明", rhythm)

    def test_key_only_drops_unknown_slot(self):
        """「关键图有」认不出图位时不出图注——不替用户放宽他刚设的限制。"""
        html = self._render('![随手写的 alt](x.png "图 1：说明")', fmt.CAPTION_KEY_ONLY)
        self.assertNotIn("图 1：说明", html)


class HighlightBlockTest(unittest.TestCase):
    """highlight 一度是只活在预览里的死样式。

    16 套主题全都给它写了样式、门户预览也一直在渲染它，但没有任何 markdown 语法
    能产出它——预览里那个提示框，真实文章根本做不出来。
    """

    def _render(self, md, styles=None):
        theme = {"styles": styles or {"highlight": "background:#EDF3F9; padding:20px;",
                                      "p": "font-size:16px;", "strong": "font-weight:800;"}}
        return fmt._md_to_html(md, fmt._build_styles(theme), components=_load_comps())

    def test_highlight_block_uses_theme_style(self):
        html = self._render(":::highlight\n先确定风格模板，再开始写作。\n:::")
        self.assertIn("background:#EDF3F9", html)
        self.assertIn("先确定风格模板", html)
        self.assertNotIn(":::", html)

    def test_note_is_an_alias(self):
        self.assertIn("background:#EDF3F9", self._render(":::note\n注意事项\n:::"))

    def test_inline_format_applies_inside(self):
        html = self._render(":::highlight\n这里有**重点**\n:::")
        self.assertIn("font-weight:800", html)

    def test_multi_paragraph_gets_real_spacing(self):
        html = self._render(":::highlight\n第一段\n\n第二段\n:::")
        self.assertIn("margin:0 0 0.8em", html)

    def test_falls_back_to_blockquote_when_theme_lacks_highlight(self):
        html = self._render(":::highlight\n内容\n:::",
                            styles={"blockquote": "border-left:3px solid #DDD;", "p": ""})
        self.assertIn("border-left:3px solid #DDD", html)

    def test_real_component_file_wins_over_the_builtin_fallback(self):
        """骨架想给提示框做结构时，放一个同名组件文件就能覆盖这条兜底。"""
        comps = dict(_load_comps())
        comps["highlight"] = {"name": "highlight", "body": "free",
                              "template": '<section style="border:2px solid red;">{content}</section>'}
        theme = {"styles": {"highlight": "background:#EDF3F9;", "p": ""}}
        html = fmt._md_to_html(":::highlight\n内容\n:::", fmt._build_styles(theme), components=comps)
        self.assertIn("border:2px solid red", html)
        self.assertNotIn("background:#EDF3F9", html)


def _load_comps():
    return fmt._load_components()


def _skeleton_files():
    """骨架 YAML。palette.yaml 与它们同目录但不是骨架，遍历时必须排除。

    骨架目前只存在于 design/skeletons 分支——那套设计还没定稿，不在主线上。
    目录不存在时返回空，相关用例整体跳过，这样两个分支共用同一份测试文件。
    """
    d = fmt.SKILL_DIR / "references" / "presets" / "skeletons"
    if not d.is_dir():
        return []
    return [f for f in sorted(d.glob("*.yaml")) if f.name != "palette.yaml"]


_HAS_SKELETONS = bool(_skeleton_files())
_SKIP_NO_SKELETON = unittest.skipUnless(_HAS_SKELETONS, "骨架只在 design/skeletons 分支上")


class PaletteTest(unittest.TestCase):
    """整套配色由一个强调色派生，用户只需要选一个颜色。

    此前 16 套主题里有 14 套，所有用色都能从强调色算出来——把一个只有一个自由度的
    连续参数固化成 16 个离散选项，本身就是设计错误。
    """

    def test_three_roles_have_different_requirements(self):
        """强调色有三种角色，混成一个变量必然出事。

        明黄 #FFD400 当色条完全没问题，当块底时白字对比只有 1.36，糊得看不见。
        """
        p = fmt._derive_palette("#FFD400")
        self.assertEqual(p["primary-fill"], fmt._darken_to_readable("#FFD400", target=3.0))
        self.assertGreaterEqual(fmt._contrast_with_white(p["primary-fill"]), 3.0)
        self.assertGreaterEqual(1.05 / (fmt._relative_luminance(p["primary-ink"]) + 0.05), 4.5)

    def test_ordinary_brand_colors_are_left_alone(self):
        """多数品牌色本来就够，不该平白改掉用户的颜色。"""
        for c in ("#1A6DB5", "#B01F24", "#5B4BFF"):
            p = fmt._derive_palette(c)
            self.assertEqual(p["primary-fill"], c, f"{c} 不该被压深")

    def test_accepts_loose_hex_input(self):
        for raw in ("#1a6db5", "1A6DB5", "#1A6DB5 "):
            self.assertEqual(fmt._derive_palette(raw)["primary-fill"], "#1A6DB5")
        self.assertEqual(fmt._normalize_hex("#abc"), "#AABBCC")
        self.assertIsNone(fmt._normalize_hex("红色"))

    def test_bad_input_falls_back_instead_of_crashing(self):
        self.assertEqual(fmt._derive_palette("红色")["primary-fill"],
                         fmt.DEFAULT_VARIABLES["primary-color"])

    def test_color_override_recomputes_every_derived_value(self):
        """--color 换了强调色，主题里写死的派生色就过期了，必须一并重算。

        不重算会出现「块底换了颜色、文字色还停在旧的」这种半换不换的状态。
        """
        theme = {"variables": {"primary-color": "#1A6DB5", "primary-ink": "#1A6DB5",
                               "bg-accent-color": "#EDF3F9"},
                 "styles": {"h3": "color:{primary-ink};", "p": "background:{bg-accent-color};"}}
        styles = fmt._build_styles(theme, {"primary-color": "#B01F24"})
        self.assertNotIn("#1A6DB5", styles["h3"])
        self.assertNotIn("#EDF3F9", styles["p"])
        self.assertEqual(styles["primary-ink"], fmt._derive_palette("#B01F24")["primary-ink"])

    @_SKIP_NO_SKELETON
    def test_skeletons_have_no_hardcoded_brand_color(self):
        """骨架的样式必须走变量，否则换色只换一半。"""
        import yaml
        for f in _skeleton_files():
            css = yaml.safe_dump(yaml.safe_load(f.read_text(encoding="utf-8"))["styles"],
                                 allow_unicode=True)
            self.assertNotIn("1A6DB5", css, f"{f.stem} 里还有写死的强调色")

    @_SKIP_NO_SKELETON
    def test_no_unreadable_text_on_any_background(self):
        """扫描渲染产物：所有「文字压在某个背景上」的组合，对比度都要 ≥3.0。

        必须追踪嵌套。第一版审计只比对同一个 style 属性里的前景/背景，而组件模板里
        背景在外层 section、白字在内层——整类问题被漏掉了：明黄配色下导语的白字压在
        原色 #FFD400 上，对比只有 1.43，肉眼一看就糊，审计却报「全部达标」。
        """
        import yaml
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from contrast_audit import violations
        md = (":::lead\n导语文字\n:::\n\n## 小标题\n\n正文**重点**与[链接](x)。\n\n"
              ":::stat[数据]\n3.2× | 平均阅读时长\n:::\n\n"
              ":::quote-card[出处]\n值得转发的一句\n:::\n\n:::closing[署名]\n收尾\n:::")
        for f in _skeleton_files():
            theme = yaml.safe_load(f.read_text(encoding="utf-8"))
            comps = fmt._load_components(str(theme.get("skeleton") or ""))
            for accent in ("#FFD400", "#00E676", "#1A6DB5", "#B01F24"):
                styles = fmt._build_styles(theme, {"primary-color": accent})
                bad = violations(fmt._md_to_html(md, styles, components=comps))
                self.assertEqual(bad, [], f"{f.stem} / {accent} 有读不了的文字：{bad[:3]}")


@_SKIP_NO_SKELETON
class PresetPaletteTest(unittest.TestCase):
    """预设强调色的硬标准：压白底对比 ≥4.5。

    对比度是对称的——「白字压色块」和「色块字压白底」是同一个数——所以过了 4.5 的颜色，
    在 primary-color / primary-fill / primary-ink 三个角色里取值相同：用户选什么就是
    什么，护栏一次都不介入。选不出这样的色，用户就会发现「我选的橙色，出来不是这个橙」。
    """

    def _palette(self):
        import yaml
        f = fmt.SKILL_DIR / "references" / "presets" / "skeletons" / "palette.yaml"
        return yaml.safe_load(f.read_text(encoding="utf-8"))["colors"]

    def test_every_preset_needs_no_adjustment(self):
        for c in self._palette():
            p = fmt._derive_palette(c["hex"])
            self.assertEqual(p["primary-fill"], c["hex"], f"{c['name']} 当块底会被压深")
            self.assertEqual(p["primary-ink"], c["hex"], f"{c['name']} 当文字会被压深")

    def test_presets_cover_the_hue_wheel(self):
        """至少要覆盖到冷暖两端，否则用户找不到接近自己品牌色的那一档。"""
        import colorsys
        hues = []
        for c in self._palette():
            h = c["hex"].lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
            hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
            if ss > 0.15:                      # 中性色不计入色相覆盖
                hues.append(int(hh * 360))
        self.assertGreaterEqual(len(hues), 8)
        self.assertTrue(any(h < 60 or h > 300 for h in hues), "缺暖色")
        self.assertTrue(any(120 < h < 260 for h in hues), "缺冷色")

    def test_each_skeleton_defaults_to_a_preset(self):
        """骨架的默认色必须来自预设，否则默认状态就已经不是「所见即所得」。"""
        import yaml
        presets = {c["hex"] for c in self._palette()}
        for f in _skeleton_files():
            theme = yaml.safe_load(f.read_text(encoding="utf-8"))
            self.assertIn(theme["variables"]["primary-color"], presets,
                          f"{f.stem} 的默认色不在预设里")


class NoLeftoverBracesTest(unittest.TestCase):
    """渲染产物里不该剩下任何花括号。

    起因是一处双大括号：模板里写成 `{{primary-color}}`，替换后变成 `{#3B4CC0}`——
    无效 CSS，背景直接不生效，那条色带在页面上是隐形的。而按 `\{[a-z-]+\}` 去找残留
    的检查完全抓不到它，因为剩下的是 `{#3B4CC0}`。

    判据要改成「一个花括号都不许剩」，这样双写、错写、漏定义的变量全都会被抓住。
    """

    @_SKIP_NO_SKELETON
    def test_no_braces_in_rendered_output(self):
        import yaml
        md = ("正文一段。\n\n## 小标题\n\n带**重点**与[链接](x)的一段。\n\n"
              "- 列表\n\n> 引用\n\n:::lead\n导语\n:::\n\n:::quote-card[出处]\n金句\n:::\n\n"
              ":::steps[标题]\n第一步 | 说明\n:::\n\n:::stat[数据]\n3.2× | 说明\n:::\n\n"
              ":::checklist[清单]\ndone | 事项\n:::\n\n:::compare[左|右]\na|b\n:::\n\n"
              ":::highlight\n提示\n:::\n\n:::closing[署名]\n收尾\n:::")
        for f in _skeleton_files():
            theme = yaml.safe_load(f.read_text(encoding="utf-8"))
            comps = fmt._load_components(str(theme.get("skeleton") or ""))
            html = fmt._md_to_html(md, fmt._build_styles(theme), components=comps)
            self.assertNotIn("{", html, f"{f.stem} 的产物里有残留花括号")
            self.assertNotIn("}", html, f"{f.stem} 的产物里有残留花括号")

    def test_component_templates_have_no_double_braces(self):
        """双大括号在模板里就该拦住，不用等到渲染。"""
        import re as _re
        d = fmt.SKILL_DIR / "references" / "components"
        for f in sorted(d.rglob("*.yaml")):
            s = f.read_text(encoding="utf-8")
            self.assertIsNone(_re.search(r"\{\{[a-z][a-z0-9-]*\}\}", s),
                              f"{f.parent.name}/{f.name} 里有双大括号")


@_SKIP_NO_SKELETON
class DesignTokenTest(unittest.TestCase):
    """所有数值必须落在设计 token 上。

    定过规则（4px 网格、圆角每套一档、线宽两档、字号 1.2 音阶），然后一路手写数值把
    规则忘光了：块的圆角有 2/12/14/16 四档，场的线宽七种，间距里到处是 6/10/14/18/22。
    「不精致」的技术原因就在这——不是设计想法不对，是执行时手里没有一把尺。

    修法不是再手调一遍（那还会漂），是把尺做成测试。
    """

    GRID = 4
    SCALE = {13, 16, 19, 23, 28, 34, 40}
    # name → (线宽两档, 圆角, SVG 描边)。和 scripts/dev_apply_tokens.py 保持一致
    TOKENS = {"kan": ((1, 2), "0", "1.5"), "kuai": ((2, 4), "16", "2"),
              "bai": ((1, 2), "0", "1.5"), "chang": ((4, 12), "0", "1.5")}

    def _css(self, name):
        import yaml
        d = fmt.SKILL_DIR / "references"
        out = yaml.safe_dump(
            yaml.safe_load((d / "presets" / "skeletons" / f"{name}.yaml").read_text(encoding="utf-8"))["styles"],
            allow_unicode=True)
        for f in sorted((d / "components" / name).glob("*.yaml")):
            spec = yaml.safe_load(f.read_text(encoding="utf-8"))
            out += str(spec.get("template", "")) + str(spec.get("row_template", "")) + str(spec.get("row_map", ""))
        return out

    def test_spacing_is_on_the_grid(self):
        for name in self.TOKENS:
            css = self._css(name)
            vals = set()
            for m in re.findall(r"(?:margin|padding|gap)[a-z-]*:\s*([^;]+)", css):
                vals |= {float(x) for x in re.findall(r"(?<![-\d.])(\d+(?:\.\d+)?)px", m)}
            # 0~2px 是光学微调（如 padding-bottom:1px 让下划线离开基线），不计
            off = sorted(v for v in vals if v > 2 and v % self.GRID != 0)
            self.assertEqual(off, [], f"{name} 的间距离开 {self.GRID}px 网格：{off}")

    def test_only_two_rule_widths_per_skeleton(self):
        for name, (rules, _, _) in self.TOKENS.items():
            css = self._css(name)
            # border-radius 也匹配 border[a-z-]*，要排掉
            got = {float(m.group(1)) for m in re.finditer(r"border(?!-radius)[a-z-]*:\s*([\d.]+)px", css)}
            self.assertTrue(got <= set(map(float, rules)),
                            f"{name} 的线宽超出档位 {rules}：{sorted(got)}")

    def test_one_radius_per_skeleton(self):
        for name, (_, radius, _) in self.TOKENS.items():
            got = set(re.findall(r"border-radius:\s*([\d]+)", self._css(name)))
            self.assertTrue(got <= {radius}, f"{name} 的圆角不止一档：{sorted(got)}")

    def test_font_sizes_are_on_the_scale(self):
        for name in self.TOKENS:
            got = {float(x) for x in re.findall(r"font-size:\s*([\d.]+)px", self._css(name))}
            off = sorted(x for x in got if x not in self.SCALE)
            self.assertEqual(off, [], f"{name} 的字号不在 1.2 音阶上：{off}")

    def test_one_svg_stroke_width_per_skeleton(self):
        for name, (_, _, stroke) in self.TOKENS.items():
            got = set(re.findall(r'stroke-width="([\d.]+)"', self._css(name)))
            self.assertTrue(got <= {stroke}, f"{name} 的 SVG 描边不止一档：{sorted(got)}")

    def test_color_bands_use_a_rule_width(self):
        """色带的粗细不自动吸（吸过一版，把装饰方块也当色带压扁了），改由测试拦。

        要能区分「带」和「块」：白的分隔符是一枚 8×8 旋转 45° 的方块，宽高相同，
        那是图形不是带；带的特征是宽度撑满（100% 或没写 width）而高度很小。
        """
        for name, (rules, _, _) in self.TOKENS.items():
            css = self._css(name)
            bad = []
            for m in re.finditer(r"height:\s*([\d.]+)px\s*;\s*background", css):
                h = float(m.group(1))
                # 往前看一段找同一条声明里的 width。前缀里可能隔着分号
                # （`border:none; width:8px; height:8px; background:…`），所以不能用 [^;]*
                w = re.search(r"width:\s*([\d.]+)px(?!.*width:\s*[\d.]+px)",
                              css[max(0, m.start() - 90):m.start()])
                if w and abs(float(w.group(1)) - h) < h:      # 宽高相近 → 是方块，不是带
                    continue
                if h not in set(map(float, rules)):
                    bad.append(h)
            self.assertEqual(sorted(set(bad)), [],
                             f"{name} 的色带粗细超出档位 {rules}：{sorted(set(bad))}")


class BuiltinThemeContrastTest(unittest.TestCase):
    """内置 7 套主题也要过可读性这一关。

    它们的样式是写死的十六进制色，不走 primary-fill 那套护栏——`modern` 的 h2 是白字
    压在 #EF7060 上，对比度只有 2.93，卡在 3.0 线下。这类问题不看渲染产物发现不了：
    主题文件本身没有任何异常，是「白字」和「块底」两个声明凑在一起才出事。
    """

    def test_no_unreadable_text_in_builtin_themes(self):
        import yaml
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from contrast_audit import violations
        md = ("## 小标题\n\n正文**重点**与[链接](x)。\n\n> 引用\n\n- 列表\n\n"
              ":::lead\n导语\n:::\n\n:::steps[标题]\n第一步 | 说明\n:::\n\n"
              ":::stat[数据]\n3.2× | 说明\n:::\n\n:::closing[署名]\n收尾\n:::")
        comps = fmt._load_components()
        d = fmt.SKILL_DIR / "references" / "presets" / "themes"
        for f in sorted(d.glob("*.yaml")):
            theme = yaml.safe_load(f.read_text(encoding="utf-8"))
            html = fmt._md_to_html(md, fmt._build_styles(theme), components=comps)
            bad = violations(html)
            self.assertEqual(bad, [], f"{f.stem} 有读不了的文字：{bad[:3]}")


def _template_files():
    """三套模版（涂 / 画 / 省）。README 不是模版。"""
    d = fmt.SKILL_DIR / "references" / "presets" / "templates"
    return [f for f in sorted(d.glob("*.yaml"))] if d.is_dir() else []


_HAS_TEMPLATES = bool(_template_files())
_SKIP_NO_TEMPLATE = unittest.skipUnless(_HAS_TEMPLATES, "三套模版尚未落地")


@_SKIP_NO_TEMPLATE
class ThreeTemplateTest(unittest.TestCase):
    """涂 / 画 / 省 三套模版的守卫。

    上一轮做四个骨架失败，根因之一是没有尺——定了规则却一路手写把规则忘了。
    这些用例把「实验里撞出来的硬规则」钉死，改坏了会直接红。
    """

    SAMPLE = ("## 小标题\n\n正文**加粗**与[链接](x)。\n\n- 列表项\n\n> 引用\n\n"
              "![对比图：说明](x.png \"图 1：图注\")\n\n:::lead\n导语\n:::\n\n"
              ":::quote-card[出处]\n金句\n:::\n\n:::steps[标题]\n第一步 | 说明\n:::\n\n"
              ":::stat[数据]\n3.2× | 说明\n:::\n\n:::compare[左|右]\na|b\n:::\n\n"
              ":::checklist[清单]\ndone | 事项\n:::\n\n:::closing[署名]\n收尾\n:::")

    def _theme(self, f):
        import yaml
        return yaml.safe_load(f.read_text(encoding="utf-8"))

    def _render_with(self, theme, accent):
        comps = fmt._load_components(str(theme.get("skeleton") or ""))
        styles = fmt._build_styles(theme, {"primary-color": accent})
        return fmt._md_to_html(self.SAMPLE, styles, components=comps)

    def _render(self, theme):
        comps = fmt._load_components(str(theme.get("skeleton") or ""))
        return fmt._md_to_html(self.SAMPLE, fmt._build_styles(theme), components=comps)

    @staticmethod
    def _techniques(css):
        """一段样式用了哪些手法。判据是集合，不是布尔对——
        「底色 + 彩字」和「彩字」差在底色上，实际分得开。"""
        t = set()
        if "border-bottom" in css or "underline" in css:
            t.add("线")
        if "background" in css:
            t.add("底")
        m = re.search(r"(?<!-)color:\s*(#[0-9A-Fa-f]{6})", css)
        if m and m.group(1).upper() != "#111318":
            t.add("彩字")
        w = re.search(r"font-weight:\s*(\d+)", css)
        if w and int(w.group(1)) >= 800:
            t.add("重字")
        return t

    def test_bold_and_link_use_different_techniques(self):
        """两者都用底线时读者分不清哪个能点。这个坑撞过两次，钉死。"""
        for f in _template_files():
            st = self._theme(f)["styles"]
            a, b = self._techniques(st["strong"]), self._techniques(st["a"])
            self.assertNotEqual(a, b, f"{f.stem}：加粗与链接手法相同 {sorted(a)}")

    def test_list_marker_is_never_none(self):
        """list-style:none 会让列表项看起来就是普通段落。撞过三次。"""
        for f in _template_files():
            self.assertNotIn("list-style:none", self._theme(f)["styles"]["ul"], f.stem)

    def test_templates_differ_at_the_core_layer(self):
        """身份必须落在每篇出现几十次的元素上，而不是可能一个都不出现的组件上。"""
        seen = {}
        for f in _template_files():
            st = self._theme(f)["styles"]
            key = (frozenset(self._techniques(st["strong"])),
                   frozenset(self._techniques(st["a"])),
                   re.search(r"list-style:\s*([\w-]+)", st["ul"]).group(1))
            self.assertNotIn(key, seen, f"{f.stem} 与 {seen.get(key)} 的核心层完全相同")
            seen[key] = f.stem

    def test_inline_background_never_uses_padding(self):
        """行内 background 配 padding 会撑高行盒，带底色那行的行距明显大于周围。"""
        for f in _template_files():
            for k in ("strong", "a", "em"):
                css = self._theme(f)["styles"].get(k, "")
                if "background" in css:
                    self.assertNotIn("padding", css, f"{f.stem} 的 {k} 用 padding 撑了行盒")

    def test_every_template_renders_cleanly(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from contrast_audit import violations
        for f in _template_files():
            html = self._render(self._theme(f))
            self.assertNotIn("{", html, f"{f.stem} 有残留花括号")
            self.assertEqual(violations(html), [], f"{f.stem} 有读不了的文字")

    def test_accent_colors_are_variables_not_literals(self):
        """模版和组件不许写死强调色，否则 --color 完全失效。

        这不是假想的洁癖：涂 最初七个组件加模版一共写死了 11 处 #14508C / #EAF0F6 /
        #BBD0E4，换色时整篇纹丝不动。字面色只允许出现在中性灰和纯白上——那两类不随
        强调色变。
        """
        import yaml
        d = fmt.SKILL_DIR / "references" / "components"
        for f in _template_files():
            paths = [f]
            sk = str(self._theme(f).get("skeleton") or "")
            if sk and (d / sk).is_dir():
                paths += sorted((d / sk).glob("*.yaml"))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                if path == f:  # variables 块里的字面值是唯一真源，跳过
                    text = text.split("styles:", 1)[-1]
                for lit in set(re.findall(r"#[0-9A-Fa-f]{6}", text)):
                    self.assertFalse(
                        fmt._is_accent(lit),
                        f"{path.name} 写死了强调色 {lit}，换色时这里不会变")

    def test_changing_the_accent_changes_the_render(self):
        """换个强调色，产出必须真的不同——上一版写死色值时这条会红。"""
        for f in _template_files():
            theme = self._theme(f)
            a = self._render_with(theme, "#14508C")
            b = self._render_with(theme, "#8C3A2E")
            self.assertNotEqual(a, b, f"{f.stem}：换色后产出完全一样")

    def test_every_accent_stays_readable(self):
        """派生护栏要对任意用户色都成立，包括亮橙、柠檬黄这种压白底本来就读不了的。"""
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from contrast_audit import violations
        for f in _template_files():
            theme = self._theme(f)
            for hexc in ("#FF8C00", "#EFE000", "#2B2F36", "#1F5C4A", "#5B3E8C"):
                html = self._render_with(theme, hexc)
                self.assertEqual(violations(html), [], f"{f.stem} 用 {hexc} 时有读不了的文字")
                self.assertNotIn("{", html, f"{f.stem} 用 {hexc} 时有花括号残留")

    def test_no_semantic_reuses_another_semantics_form(self):
        """同一套里七个语义七种形态。上一轮「块」五个语义共用一张圆角卡就是这条没守住。

        形态签名取「用了哪些视觉手段」——底色、各边框、是否 flex、字号集合、
        字重集合、字距。只取容器和边框会漏掉「省」：那一套按设计就没有底色和边框，
        它的七种形态全靠排版本身分开（flex 加序号列 vs 上下排加箭头），
        签名看不见排版就会误判成雷同。
        """
        import yaml
        COMPS = ["lead", "quote-card", "steps", "stat", "compare", "checklist", "closing"]
        d = fmt.SKILL_DIR / "references" / "components"
        for f in _template_files():
            sk = str(self._theme(f).get("skeleton") or "")
            if not sk or not (d / sk).is_dir():
                continue
            shapes = {}
            for c in COMPS:
                p = d / sk / f"{c}.yaml"
                if not p.exists():
                    continue
                spec = yaml.safe_load(p.read_text(encoding="utf-8"))
                body = str(spec.get("template", "")) + str(spec.get("row_template", ""))
                body = re.sub(r"#[0-9A-Fa-f]{3,8}|\{[a-z][a-z0-9-]*\}", "C", body)
                sig = tuple(sorted(set(
                    re.findall(r"background(?:-color)?|display:\s*flex|text-align:\s*\w+"
                               r"|border-(?:top|bottom|left|right):\s*\d+px"
                               r"|font-size:\s*\d+px|font-weight:\s*\d+"
                               r"|letter-spacing|border-radius", body))))
                self.assertNotIn(sig, shapes,
                                 f"{f.stem}：{c} 与 {shapes.get(sig)} 用了完全一样的手段 {sig}")
                shapes[sig] = c


if __name__ == "__main__":
    unittest.main()
