"""writing 侧的提示词守卫：markdown 语法规范必须是系统不变量。

markdown 语法不是用户偏好——用户不会写、也不该知道要写。所以它只能来自代码侧，
不能指望 `.aws-article/writing-spec.md` 提及；用户那份文件为空、或者写了相反的要求，
语法规范都必须照样生效。这几条测试就是钉这个性质。
"""

import importlib.util
import re
import pathlib
import unittest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WRITE = _ROOT / "skills" / "aws-wechat-article-writing" / "scripts" / "write.py"


def _load():
    spec = importlib.util.spec_from_file_location("write_mod", _WRITE)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:      # 模块里有 CLI，导入时不该真的退出
        pass
    return mod


@unittest.skipUnless(_WRITE.exists(), "writing skill 未安装")
class MarkdownSpecIsSystemInvariantTest(unittest.TestCase):

    # 实测模型最常写错的几样，逐条点名而不是笼统说「用标准 markdown」
    NAMED = ["__加粗__", "_斜体_", "裸 URL", "====", "四个空格", "HTML 标签", ":::"]

    def setUp(self):
        self.w = _load()

    def _prompt(self, **kw):
        kw.setdefault("screening", {})
        kw.setdefault("writing_spec", "")
        kw.setdefault("structure_template", "")
        return self.w.build_system_prompt(**kw)

    def test_present_when_user_spec_is_empty(self):
        """用户那份写作规范为空时，语法规范必须照样在。"""
        sp = self._prompt()
        for k in self.NAMED:
            self.assertIn(k, sp, f"用户规范为空时丢了「{k}」这条")

    def test_present_when_user_spec_is_unrelated(self):
        sp = self._prompt(writing_spec="全程用「你」称呼读者，段落不超过三行。")
        for k in self.NAMED:
            self.assertIn(k, sp)

    def test_comes_after_user_spec_and_declares_precedence(self):
        """用户规范在前、语法规范在后，且显式声明冲突时以语法规范为准。

        否则用户随手写一句「强调用 __双下划线__」就能把整条链路带歪——
        而他根本不知道这句话会让正文里冒出一串下划线。
        """
        mark = "用户规范正文XYZ"
        sp = self._prompt(writing_spec=mark)
        self.assertLess(sp.index(mark), sp.index("### Markdown 语法（硬性）"))
        self.assertIn("以本节为准", sp)

    def test_ordered_list_caveat_is_stated(self):
        """有序列表只在真有先后时用。真稿实测：三组多项有序列表里两组是并列的，
        渲染成「第一步 第二步」等于替读者断言一个不存在的顺序。"""
        self.assertIn("真有先后", self._prompt())

    def test_labeled_list_form_is_taught(self):
        """`- **标签**：说明` 是排版层会识别的形态（真稿里 62% 的列表项是这个样子），
        提示词要教，否则模型不会稳定输出它。"""
        self.assertIn("**标签**", self._prompt())

    # ── 产出配额 ────────────────────────────────────────────────
    # 只教语法不给配额，模型一处都不会写。真稿实测（10 篇）：金句卡 0 篇命中，
    # 5 篇原始模型产出里正文段落内的加粗是 0——写出来的加粗全在列表标签里。
    # 于是版式做的金句卡、重点色、荧光底在自动链路上全是死代码。

    def test_lead_paragraph_quota_is_in_the_quota_block(self):
        """摘要在「输出要求」里本来就写过，实测仍连漏 3 篇——那是一串并列项里的一条。

        配额区是唯一被稳定执行的一段（配图数、金句数都做到了），所以摘要挪进来重申。
        漏了不报错，只是第一个 `##` 之前没有 `>`，导语版式整篇不出现。
        """
        sp = self._prompt()
        quota = sp[sp.index("产出配额"):]
        self.assertIn("正文开头必须有摘要", quota)
        self.assertIn("不是**只填到别处的摘要字段", quota, "要说清它和 article.yaml 的 digest 不是一回事")

    def test_emphasis_quota_is_stated(self):
        """加粗是正文里唯一的扫读落点，且是「重点色 / 荧光底」这些主题样式的唯一入口。
        没有密度要求，模型只在列表标签里加粗，整篇正文一片平。"""
        sp = self._prompt()
        self.assertIn("每 2-3 段一处", sp, "加粗密度配额没了")
        self.assertIn("最多两处", sp, "缺上限，会变成整篇乱加粗")
        self.assertIn("每个 `##` 小节至少贡献一处", sp, "缺覆盖要求，会集中在前半篇")

    def test_emphasis_rule_says_what_to_bold_not_only_how_often(self):
        """密度达标 ≠ 有重点。

        实测四篇平均每 2.1 段就有一处加粗，读者仍然觉得「几乎没有重点」——加粗的全是
        9-11 字的抽象概括短句，平均 7.9 字，含数字的只有 4%（正文 9 个数字仅 2 个被加粗）。
        把整句复述一遍再加粗，读者扫到它等于把这段又读一次。
        """
        sp = self._prompt()
        self.assertIn("加粗是划重点", sp, "先说清用途，规则才有依据")
        self.assertIn("能独立看懂", sp, "光有长度约束会退化成裸数字或裸名词")
        self.assertIn("词云", sp, "不点名这个失败形态，收紧长度就会滑到另一个极端")
        self.assertIn("不要**加粗整句的概括", sp, "不禁掉复述，密度再高也没有落点")

    def test_emphasis_states_the_skim_test(self):
        """加粗的用途是让读者从密密麻麻的正文里一眼抓住关键信息。

        所以验收标准不是数量，是「把全文加粗抽出来连起来读，像不像一份提要」——
        `write.py check` 会把这一串打印出来交给人判断。
        """
        sp = self._prompt()
        self.assertIn("连读", sp)
        self.assertIn("能独立看懂的缩写版", sp, "验收标准要是「读得完」，不是字数")

    def test_lead_must_differ_from_the_digest_field(self):
        """实测 7 篇导语与 article.yaml 的 digest 逐字相同——读者在列表页读一遍，
        点进来第一段再读一遍。两处的读者处境不同：一个要决定点不点，一个已经点进来了。"""
        self.assertIn("不要和摘要字段写成同一句话", self._prompt())

    def test_enumerations_must_become_labeled_lists(self):
        """实测四篇「完整自然段」风格的深度分析文列表项 0 个，li-label 从不触发。
        段落偏好管的是叙述段的长短，不该把三四项并列的条件也压成散文。"""
        sp = self._prompt()
        self.assertIn("三项以上的并列", sp)
        self.assertIn("**标签**", sp)

    def test_quote_card_quota_is_exactly_one(self):
        """金句卡的价值来自稀缺——一篇两张，两张都不会被转（见 quote-card.yaml
        的 when_not_to_use）。所以配额必须是「恰好一处」，不是「可以写」。"""
        sp = self._prompt()
        self.assertIn("恰好写一处", sp)
        self.assertIn("> 金句。 —— 出处", sp)

    def test_density_word_is_defined_not_just_echoed(self):
        """`每节一图` 这些词是本套件自造的，模型不认识。

        此前提示词只把 `image_density` 的值原样拼进去，定义表躺在 images skill 的
        image-method.md 里——那份文档写稿阶段根本读不到。实测五篇真稿，正文标记数
        每篇都少于 `##` 小节数。
        """
        sp = self._prompt(screening={"image_density": "每节一图"})
        self.assertIn("每节一图", sp)
        self.assertIn("每个 `##` 小节各配一张", sp, "只回显了密度词，没给出定义")
        self.assertIn("硬配额", sp, "「尽量满足」这种软措辞会被模型当成参考值")

    def test_every_density_word_has_a_definition(self):
        for word, rule in self.w._DENSITY_RULES.items():
            sp = self._prompt(screening={"image_density": word})
            self.assertIn(rule, sp, f"{word} 没被展开成具体规则")

    def test_unknown_density_word_falls_back_without_crashing(self):
        """用户可以在 config 里写任意字符串，不能因为不在表里就崩或丢掉这行。"""
        sp = self._prompt(screening={"image_density": "每两节一图"})
        self.assertIn("每两节一图", sp)

    def test_horizontal_rule_is_taught(self):
        """`---` 是 hr-deco 的唯一触发口（书卷 / 杂志 / 硬朗 / 手账四个骨架都做了
        分隔装饰）。此前提示词根本没提过分隔线，真稿 0/10 篇出现过。"""
        self.assertIn("`---`", self._prompt())

    def test_task_list_is_not_pushed(self):
        """待办清单是低频构件——只有真正的检查项才用。提示词不点名它，避免模型
        把普通并列项写成勾选框。渲染器仍然认这个形态（手写、SKILL.md 里有说明）。"""
        self.assertNotIn("- [ ]", self._prompt())

    def test_private_block_syntax_is_not_taught(self):
        """提示词不再教 `:::` 语法。

        链路定为「markdown 语法 → 按语法输出 → 渲染器排版」：让写手同时掌握标准
        markdown 和一套私有语法就是耦合，而且那套语法只有本套件认得，稿子换个工具就废了。

        这条也挡住一种更隐蔽的回归：既教 `:::` 又禁止 `:::`，同一份提示词自相矛盾。
        """
        sp = self._prompt()
        for token in (":::steps", ":::quote-card", ":::stat", "版式组件"):
            self.assertNotIn(token, sp, f"提示词又开始教 {token} 了")
        self.assertIn("**不要**使用 `:::`", sp)

    def test_prompt_stays_lean(self):
        """空配置下的系统提示词不该失控。组件表曾经占了 4608 字符——
        提示词里每多一段，模型的注意力就薄一分。"""
        self.assertLess(len(self._prompt()), 2600)

    # 配图这一节写错，后面整条配图链路（生图、上传、排版）都接不上，
    # 但提示词本身不会报错——所以逐条钉住，不能靠「改的时候记得别碰」。
    IMAGE_RULES = [
        "![类型名：画面内容](placeholder)",   # 占位格式
        "封面**（放标题前，不进正文）",   # 类型名白名单收窄为四个，各自有下游含义
        "配图密度：",
        "不能写成 []()",                     # 少一个 ! 会被排版成链接
        "每个配图标记独占一行",
        "封面标记放在标题之前",
        "图注单独写",
    ]

    def test_image_rules_survive_empty_config(self):
        """配图规范是系统不变量，用户什么都没配也必须完整出现。"""
        sp = self._prompt()
        for rule in self.IMAGE_RULES:
            self.assertIn(rule, sp, f"配图规范丢了「{rule}」")

    def test_image_rules_survive_user_spec(self):
        sp = self._prompt(writing_spec="全程用「你」称呼读者。")
        for rule in self.IMAGE_RULES:
            self.assertIn(rule, sp)

    def test_user_supplied_image_branch_is_complete(self):
        """用户供图模式是另一条分支，规则不同但同样是硬性的：
        不得再出 placeholder、封面只能一张、不得虚构文件名。"""
        sp = self._prompt(image_source="user", img_analysis="文件名：imgs/a.png")
        for rule in ("不得再输出 placeholder", "封面只能出现 1 张",
                     "不得虚构不存在的文件名", "imgs/a.png"):
            self.assertIn(rule, sp, f"用户供图分支丢了「{rule}」")

    def test_the_two_image_branches_are_exclusive(self):
        """两条分支不能同时出现——同时说「用 placeholder」和「不得用 placeholder」
        就是又一处自相矛盾。"""
        gen = self._prompt()
        usr = self._prompt(image_source="user", img_analysis="文件名：imgs/a.png")
        self.assertIn("placeholder)", gen)
        self.assertNotIn("## 用户供图模式", gen)
        self.assertIn("## 用户供图模式", usr)
        self.assertNotIn("配图密度：", usr)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(_WRITE.exists(), "writing skill 未安装")
class OutputQuotaCheckTest(unittest.TestCase):
    """`write.py check` —— 把产出配额从一张靠人肉数的表变成能跑的检查。

    这些项实测漏得很稳定：连着三篇没写摘要、四篇一个列表都没有、加粗密度够了但
    全是复述整句。都是能直接数出来的，不该靠眼睛。
    """

    def setUp(self):
        self.w = _load()

    GOOD = (
        "# 标题\n\n> 摘要，交代这篇讲什么、按什么顺序讲，和列表页那句不一样。\n\n"
        "## 一节\n\n开头一段，讲清背景和来龙去脉，交代清楚上下文。\n\n"
        "这一段里有 **省 88% Token** 这个数。\n\n"
        "第三段继续说，把前面的判断展开一层，给出理由。\n\n"
        "- **标签**：说明文字\n\n"
        "又一段，这里提到 **按问题找证据** 这个说法。\n\n"
        "> 金句压在这里。 —— 马斯\n"
    )

    def test_good_draft_passes(self):
        bad, warn, digest = self.w.check_output(self.GOOD)
        self.assertEqual(bad, [], f"合格稿被判不合格: {bad}")
        self.assertIn("省 88% Token", digest)

    def test_missing_lead_is_a_hard_failure(self):
        bad, _, _ = self.w.check_output(self.GOOD.replace("> 摘要，交代这篇讲什么、按什么顺序讲，和列表页那句不一样。\n\n", ""))
        self.assertTrue(any("没有 `>` 摘要" in b for b in bad))

    def test_missing_quote_card_is_a_hard_failure(self):
        bad, _, _ = self.w.check_output(self.GOOD.replace(" —— 马斯", ""))
        self.assertTrue(any("金句" in b for b in bad))

    def test_thin_emphasis_is_a_hard_failure(self):
        """正文段落数够多而加粗太少 —— 手机上扫过去没有落点。"""
        thin = "# t\n\n> 摘要摘要摘要摘要摘要摘要摘要摘要。\n\n## 一\n\n" + "\n\n".join(
            f"第{i}段正文，没有任何强调。" for i in range(12)) + "\n\n> 金句。 —— 马斯\n"
        bad, _, _ = self.w.check_output(thin)
        self.assertTrue(any("加粗" in b for b in bad), bad)

    def test_paraphrase_length_is_warned(self):
        """9-11 字的抽象概括是实测最常见的失败形态：扫到它等于把这段重读一遍。"""
        _, warn, _ = self.w.check_output(
            self.GOOD.replace("**省 88% Token**", "**成果来自工程能力的扩张**"))
        self.assertTrue(any("偏长" in w for w in warn), warn)

    def test_unbolded_numbers_are_warned(self):
        _, warn, _ = self.w.check_output(
            self.GOOD.replace("**省 88% Token**", "省 88% Token，另有 37 分与 2 倍"))
        self.assertTrue(any("关键数字" in w for w in warn), warn)

    def test_digest_line_lets_a_human_judge_the_skim(self):
        """加粗的用途是让读者一眼抓住关键信息，验收标准是「只读加粗能否串成提要」。
        机器判不了读不读得通，所以把它打印出来交给人。"""
        _, _, digest = self.w.check_output(self.GOOD)
        self.assertIn(" / ", digest, "多处加粗要串成一行给人读")


    def test_check_flags_both_emphasis_failure_modes(self):
        """两头都要拦。只拦长的那次，模型转头去写 2-4 字裸名词——48 处平均 3.6 字、
        94% 在 4 字以内，机械指标全绿而串起来是个词云，工具报了假绿灯。"""
        w = _load()
        base = ("# t\n\n> 摘要交代本篇讲什么按什么顺序讲与列表页那句不同。\n\n## 一\n\n"
                "第一段正文说明背景与来龙去脉。\n\n第二段有 {b} 这个重点。\n\n"
                "第三段继续展开理由。\n\n第四段再有 {b} 一处。\n\n"
                "> 金句。 —— 马斯\n")
        _, warn_short, _ = w.check_output(base.replace("{b}", "**透明度**"))
        self.assertTrue(any("裸名词" in x for x in warn_short), warn_short)
        _, warn_long, _ = w.check_output(base.replace("{b}", "**成果来自工程能力的扩张**"))
        self.assertTrue(any("偏长" in x for x in warn_long), warn_long)
        # 中英混排的理想加粗不能被任何一头误伤：按字符数它有 11 个，按显示单位是 3 个
        _, warn_ok, _ = w.check_output(base.replace("{b}", "**省 88% Token**"))
        self.assertFalse([x for x in warn_ok if "裸名词" in x or "偏长" in x], warn_ok)

    def test_emphasis_length_counts_display_units_not_characters(self):
        """按字符数会误伤中英混排——`省 88% Token` 正是我们要的样子（数字连着它的
        意思），len() 却是 11，会被当成「复述整句」拦下来。"""
        w = _load()
        self.assertEqual(w._emph_units("省 88% Token"), 3)
        self.assertEqual(w._emph_units("成果来自工程能力的扩张"), 11)
        self.assertTrue(w._is_bare_noun("透明度"))
        self.assertFalse(w._is_bare_noun("省 88% Token"))
        self.assertFalse(w._is_bare_noun("按问题找证据"))


class QuoteCardParityTest(unittest.TestCase):
    """write.py check 与 format.py 对「什么算金句卡」必须判得一样。

    2026-09-11 全流程实测：出处写成论文全名（68 字符），check 报「金句 ✓」放行，
    format.py 的锚定匹配失配，渲出来是普通引用块——作者拿到绿灯，文章静悄悄少了
    一张可截图转发的卡。工具之间判据不一致比没有工具更糟，它给的是假绿灯。
    """

    # 与 format.py 里那条逐字相同；两边一分叉这个测试就会红
    FMT_RE = re.compile(r"^(.*?)\s*(?:——|—|--)\s*([^\s—][^—]{0,24})$")
    LONG = "决定你的不是你的头衔，是你的节奏。 —— Murphy-Hill 等，《Adoption and Impact of Command-Line AI Coding Agents》"
    SHORT = "决定你的不是你的头衔，是你的节奏。 —— Murphy-Hill 等"

    def setUp(self):
        self.w = _load()

    def test_format_py_still_uses_this_regex(self):
        """把 format.py 里那条正则抠出来比对，防止只改了一边。"""
        src = pathlib.Path("skills/aws-wechat-article-formatting/scripts/format.py").read_text(encoding="utf-8")
        self.assertIn(r'^(.*?)\s*(?:——|—|--)\s*([^\s—][^—]{0,24})$', src,
                      "format.py 的金句卡判据变了，write.py 的 QUOTE_CARD_RE 要同步")

    def test_same_verdict_on_both_sides(self):
        for q in (self.LONG, self.SHORT):
            self.assertEqual(bool(self.w.QUOTE_CARD_RE.match(q)), bool(self.FMT_RE.match(q)),
                             f"两边判据不一致：{q[:40]}")

    def test_long_source_is_rejected_at_write_time(self):
        md = f"# T\n\n> 导语。\n\n## 一\n\n正文**重点**一段。\n\n> {self.LONG}\n"
        bad, _warn, _ = self.w.check_output(md)
        self.assertTrue(any("出处太长" in b for b in bad),
                        f"出处 68 字符应被拦下，实际 bad={bad}")

    def test_short_source_passes(self):
        md = f"# T\n\n> 导语。\n\n## 一\n\n正文**重点**一段。\n\n> {self.SHORT}\n"
        bad, _warn, _ = self.w.check_output(md)
        self.assertFalse(any("金句" in b or "出处" in b for b in bad), bad)
