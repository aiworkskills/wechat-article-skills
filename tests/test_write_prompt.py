"""writing 侧的提示词守卫：markdown 语法规范必须是系统不变量。

markdown 语法不是用户偏好——用户不会写、也不该知道要写。所以它只能来自代码侧，
不能指望 `.aws-article/writing-spec.md` 提及；用户那份文件为空、或者写了相反的要求，
语法规范都必须照样生效。这几条测试就是钉这个性质。
"""

import importlib.util
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
        self.assertIn("每 2-3 段至少有一处", sp, "加粗密度配额没了")
        self.assertIn("最多两处", sp, "缺上限，会变成整篇乱加粗")

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
        "封面、信息图、氛围、流程图、对比、实证",  # 类型名白名单
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
