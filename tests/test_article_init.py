"""article_init.py 的预设字段补齐。

「必须用 article_init 初始化，不要手写 article.yaml」这条规则的全部意义，就是不依赖
Agent 记性。所以但凡有一个字段它不建、而下游又要求本篇必须落盘，这条规则就漏了。

排版那两项是典型：模版与配色都是**本篇的选择**，网站导出的 config.yaml 里可以整个
没有这两个键。缺了不报错——format.py 读不到 default_format_preset 就退回内置默认
模版，一篇本该用「资讯」的稿子会长成「亲和」的样子。
"""
import os
import tempfile
import unittest
from pathlib import Path

import yaml

from tests._load import load

init = load("skills/aws-wechat-article-publish/scripts/article_init.py", "aws_article_init")

PRESET_FIELDS = (
    "default_structure",
    "default_closing_block",
    "default_title_style",
    "default_format_preset",
    "default_format_scheme",
    "default_cover_image_style",
    "default_article_image_style",
    "default_sticker_style",
)


class PresetFieldTest(unittest.TestCase):
    def _run(self, cfg: dict | None, article: dict | None = None) -> dict:
        """在一个临时仓库里跑 _ensure_preset_fields，返回写完后的 article.yaml。"""
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                if cfg is not None:
                    Path(".aws-article").mkdir()
                    Path(".aws-article/config.yaml").write_text(
                        yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
                art = Path("article.yaml")
                art.write_text(yaml.safe_dump(article or {"title": "t"},
                                              allow_unicode=True), encoding="utf-8")
                init._ensure_preset_fields(art)
                return yaml.safe_load(art.read_text(encoding="utf-8")) or {}
            finally:
                os.chdir(cwd)

    def test_formatting_fields_appear_even_when_config_omits_them(self):
        """网站导出的 config 里没有模版/配色这两个键——它们仍须建出来。

        这是 2026-09-11 跑全流程时真实撞到的：config.yaml 两个键都没有，
        建出来的 article.yaml 也就两个都缺，排版于是静默退回默认模版。
        """
        out = self._run({"article_category": "AI", "default_structure": ["x"]})
        self.assertIn("default_format_preset", out)
        self.assertIn("default_format_scheme", out)
        self.assertEqual(out["default_format_preset"], [])
        self.assertEqual(out["default_format_scheme"], [])

    def test_declared_fields_are_created_too(self):
        cfg = {k: [] for k in PRESET_FIELDS if k not in init.ALWAYS_PRESET_FIELDS}
        out = self._run(cfg)
        for k in PRESET_FIELDS:
            self.assertIn(k, out, f"{k} 没被建出来")

    def test_existing_values_are_never_overwritten(self):
        """只补缺，不覆盖——本篇已经选好的模版不能被清成 []。"""
        out = self._run({"article_category": "AI"},
                        article={"title": "t", "default_format_preset": ["资讯"]})
        self.assertEqual(out["default_format_preset"], ["资讯"])

    def test_no_config_means_no_touch(self):
        """没有 config.yaml 时保持 article.yaml 原样，不要凭空造字段。"""
        out = self._run(None, article={"title": "t"})
        self.assertNotIn("default_format_preset", out)


if __name__ == "__main__":
    unittest.main()
