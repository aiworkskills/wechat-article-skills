"""image_create.py 回归测试：比例解析、裁切、格式探测、协议识别、test 退出码。"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._load import ROOT, load

ic = load("skills/aws-wechat-article-images/scripts/image_create.py", "aws_image_create")
SCRIPT = ROOT / "skills/aws-wechat-article-images/scripts/image_create.py"

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class AspectTest(unittest.TestCase):
    def test_coerce_unquoted_yaml_sexagesimal(self):
        self.assertEqual(ic._coerce_aspect(969), "16:9")
        self.assertEqual(ic._coerce_aspect(61), "1:1")
        self.assertEqual(ic._coerce_aspect(243), "4:3")
        self.assertEqual(ic._coerce_aspect(" 2.35:1 "), "2.35:1")
        self.assertIsNone(ic._coerce_aspect(None))
        self.assertIsNone(ic._coerce_aspect(""))

    def test_resolve_size(self):
        self.assertEqual(ic._resolve_size(None, {"aspect": "2.35:1"}), ("1792x1024", "2.35:1"))
        self.assertEqual(ic._resolve_size(None, {"aspect": 969}), ("1792x1024", "16:9"))
        self.assertEqual(ic._resolve_size(None, {"size": "1024x1024"}), ("1024x1024", None))
        self.assertEqual(ic._resolve_size("4:3", {"aspect": "1:1"}), ("1024x768", "4:3"))
        self.assertEqual(ic._resolve_size(None, {"aspect": "3:1"}), ("1792x1024", "3:1"))
        self.assertEqual(ic._resolve_size(None, {}), (None, None))


@unittest.skipIf(Image is None, "Pillow 未安装")
class CropTest(unittest.TestCase):
    def _png(self, w, h):
        buf = io.BytesIO()
        Image.new("RGB", (w, h), (1, 2, 3)).save(buf, "PNG")
        return buf.getvalue()

    def test_crop_wide_to_2_35(self):
        out = ic._crop_to_aspect(self._png(1792, 1024), "2.35:1")
        self.assertEqual(Image.open(io.BytesIO(out)).size, (1792, 763))

    def test_crop_noop_when_close(self):
        data = self._png(1024, 768)
        self.assertIs(ic._crop_to_aspect(data, "4:3"), data)

    def test_crop_tall(self):
        out = ic._crop_to_aspect(self._png(1024, 1792), "9:16")
        self.assertEqual(Image.open(io.BytesIO(out)).size, (1008, 1792))


class ImageConfigSupportTest(unittest.TestCase):
    """imageConfig 是 Gemini 特有结构，误发给别的端点可能触发 400。"""

    def _cfg(self, model, mode=None):
        c = {"model": model}
        if mode is not None:
            c["aspect_mode"] = mode
        return c

    def test_auto_detects_gemini_family(self):
        for m in ("gemini-3.1-flash-image-preview", "gemini-3-pro-image",
                  "nano-banana-pro", "imagen-4"):
            self.assertTrue(ic._supports_image_config(self._cfg(m)), m)

    def test_auto_rejects_other_models(self):
        for m in ("dall-e-3", "gpt-image-1", "seedream-5.0", "qwen-image", "flux.2", ""):
            self.assertFalse(ic._supports_image_config(self._cfg(m)), m)

    def test_explicit_modes_override_detection(self):
        self.assertTrue(ic._supports_image_config(self._cfg("dall-e-3", "imageconfig")))
        self.assertFalse(ic._supports_image_config(self._cfg("gemini-3-pro-image", "none")))
        self.assertTrue(ic._supports_image_config(self._cfg("gemini-3-pro-image", "auto")))

    def test_missing_mode_defaults_to_auto(self):
        self.assertTrue(ic._supports_image_config({"model": "gemini-3-pro-image"}))

    def test_invalid_mode_exits(self):
        with self.assertRaises(SystemExit):
            ic._supports_image_config(self._cfg("gemini-3-pro-image", "bogus"))


class NearestAspectTest(unittest.TestCase):
    def test_exact_matches_pass_through(self):
        for a in ("1:1", "16:9", "9:16", "4:3", "21:9"):
            self.assertEqual(ic._nearest_supported_aspect(a), a)

    def test_cover_ratio_maps_to_21_9(self):
        self.assertEqual(ic._nearest_supported_aspect("2.35:1"), "21:9")
        # 偏差须小于裁切函数的 1% 阈值，否则等于白映射
        got = ic._aspect_value("21:9")
        self.assertLess(abs(got - 2.35) / 2.35, 0.01)

    def test_unparseable_returns_none(self):
        for a in ("", "abc", "1024x1024"):
            self.assertIsNone(ic._nearest_supported_aspect(a))


class ImageSizeTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(ic._normalize_image_size("2k"), "2K")
        self.assertEqual(ic._normalize_image_size("4K"), "4K")
        self.assertEqual(ic._normalize_image_size("512"), "512")
        self.assertIsNone(ic._normalize_image_size("huge"))
        self.assertIsNone(ic._normalize_image_size(None))

    def test_default_is_large_enough_for_wechat_cover(self):
        """封面长边需 ≥900px，默认档位不能太低。"""
        self.assertIn(ic.DEFAULT_IMAGE_SIZE, ("2K", "4K"))


class DetectTest(unittest.TestCase):
    def test_image_ext(self):
        self.assertEqual(ic._detect_image_ext(b"\x89PNG\r\n\x1a\n" + b"0" * 8), ".png")
        self.assertEqual(ic._detect_image_ext(b"\xff\xd8\xff\xe0" + b"0" * 8), ".jpg")
        self.assertEqual(ic._detect_image_ext(b"RIFF\x00\x00\x00\x00WEBPVP8 "), ".webp")
        self.assertIsNone(ic._detect_image_ext(b"{}"))

    def test_qwen_text2image_detected(self):
        cfg = {"provider": "", "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"}
        self.assertEqual(ic._detect_api_type(cfg), "qwen")
        cfg["base_url"] = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        self.assertEqual(ic._detect_api_type(cfg), "qwen")


class TestCommandExitCodeTest(unittest.TestCase):
    def test_test_subcommand_fails_with_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, ".aws-article").mkdir()
            Path(d, ".aws-article/config.yaml").write_text(
                'image_model:\n  base_url: "http://127.0.0.1:9/v1/images/generations"\n  model: "m"\n', encoding="utf-8")
            Path(d, "aws.env").write_text("IMAGE_MODEL_API_KEY=k\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), "test"], cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("网络错误", r.stderr)

    def test_no_model_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(SCRIPT), "test"], cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("[NO_MODEL]", r.stderr)


@unittest.skipIf(Image is None, "Pillow 未安装")
class MinSizeRetryTest(unittest.TestCase):
    """端点返回尺寸波动大（实测 384~1584px），过小需重试而非直接采用。"""

    def _png(self, w, h):
        # 用噪声图而不是纯色：纯色会触发「近单色」检查，这里只想测尺寸一项
        buf = io.BytesIO()
        Image.effect_noise((w, h), 64).convert("RGB").save(buf, "PNG")
        return buf.getvalue()

    def _run(self, sizes):
        """按 sizes 顺序依次返回图片，记录实际调用次数。"""
        calls = []

        def gen():
            wh = sizes[min(len(calls), len(sizes) - 1)]
            calls.append(wh)
            return self._png(*wh)

        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            data = ic._generate_with_checks("t.md", gen)
        return data, calls, err.getvalue()

    def test_no_retry_when_large_enough(self):
        data, calls, err = self._run([(1376, 586)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(err, "")
        self.assertEqual(Image.open(io.BytesIO(data)).size, (1376, 586))

    def test_retries_once_when_undersized(self):
        data, calls, err = self._run([(384, 163), (1376, 586)])
        self.assertEqual(len(calls), 2)
        self.assertEqual(Image.open(io.BytesIO(data)).size, (1376, 586))
        self.assertEqual(err, "")

    def test_keeps_larger_when_retry_is_worse(self):
        """重试可能更差，须保留较大的一张而不是最后一张。"""
        data, calls, err = self._run([(704, 300), (384, 163)])
        self.assertEqual(Image.open(io.BytesIO(data)).size, (704, 300))
        self.assertIn("704", err)

    def test_warns_after_exhausting_retries(self):
        data, calls, err = self._run([(384, 163)])
        self.assertEqual(len(calls), 1 + ic.CHECK_RETRIES)
        self.assertIn("384", err)
        self.assertIn("4K", err)  # 提醒不要设 4K

    def test_threshold_matches_wechat_cover_minimum(self):
        self.assertGreaterEqual(ic.MIN_LONG_EDGE, 900)

    def test_default_image_size_is_not_4k(self):
        """实测 4K 会让端点连 aspectRatio 一起忽略。"""
        self.assertNotEqual(ic.DEFAULT_IMAGE_SIZE, "4K")

    def test_no_crash_without_pillow_or_bad_bytes(self):
        self.assertIsNone(ic._image_long_edge(b"not an image"))


@unittest.skipIf(Image is None, "Pillow 未安装")
class CoverChecksTest(unittest.TestCase):
    """出图后的纯代码检查：标题区干净度与近单色。"""

    def _img(self, w, h, busy_right=False):
        from PIL import ImageDraw
        # 平滑渐变：有足够方差不被判单色，又没有逐像素噪声那种假边缘（真实留白区是平滑的）
        im = Image.linear_gradient("L").resize((w, h)).convert("RGB")
        if busy_right:
            d = ImageDraw.Draw(im)
            for i in range(0, w // 2, 6):  # 右半密集竖线，模拟主体画进标题区
                d.line([(w // 2 + i, 0), (w // 2 + i, h)], fill=(0, 0, 0), width=2)
        buf = io.BytesIO(); im.save(buf, "PNG"); return buf.getvalue()

    def test_clean_zone_passes(self):
        self.assertEqual(ic._cover_problems(self._img(1400, 600), ic.DEFAULT_TITLE_ZONE), [])

    def test_busy_zone_flagged(self):
        probs = ic._cover_problems(self._img(1400, 600, busy_right=True), ic.DEFAULT_TITLE_ZONE)
        self.assertTrue(any("标题区不干净" in p for p in probs), probs)

    def test_monochrome_flagged(self):
        buf = io.BytesIO(); Image.new("RGB", (1400, 600), (10, 10, 10)).save(buf, "PNG")
        probs = ic._cover_problems(buf.getvalue(), None)
        self.assertTrue(any("近单色" in p for p in probs), probs)

    def test_no_zone_skips_zone_check(self):
        self.assertEqual(ic._cover_problems(self._img(1400, 600, busy_right=True), None), [])


class TitleHelpersTest(unittest.TestCase):
    def test_parse_zone(self):
        self.assertEqual(ic._parse_zone("0.55,0.30,0.92,0.70"), (0.55, 0.30, 0.92, 0.70))
        self.assertEqual(ic._parse_zone([0.1, 0.2, 0.3, 0.4]), (0.1, 0.2, 0.3, 0.4))
        for bad in ("0.9,0,0.5,1", "0,0,1", "a,b,c,d", "0,0,1.5,1", None):
            self.assertIsNone(ic._parse_zone(bad), bad)

    def test_split_title(self):
        self.assertEqual(ic._split_title("规矩一次填清楚"), ["规矩一次填清楚"])
        self.assertEqual(ic._split_title("网页配置台：把公众号规矩一次填清楚"), ["网页配置台", "把公众号规矩一次填清楚"])
        self.assertEqual(len(ic._split_title("一二三四五六七八九十")), 2)


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(Image is None, "Pillow 未安装")
class WriteIfNotWorseTest(unittest.TestCase):
    """重跑只能让结果变好，不该让它变坏。

    实测踩过：跑完整篇文章后补跑两张，端点这一轮返回的更小，
    把上一轮已经合格的图覆盖成了 683px。
    """

    def _png(self, w, h):
        buf = io.BytesIO()
        Image.effect_noise((w, h), 64).convert("RGB").save(buf, "PNG")
        return buf.getvalue()

    def _capture(self, out, data):
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            wrote = ic._write_if_not_worse(out, data)
        return wrote, err.getvalue()

    def test_writes_when_new_image_is_fine(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "02-x.png"
            wrote, err = self._capture(out, self._png(1365, 768))
            self.assertTrue(wrote)
            self.assertEqual(Image.open(out).size, (1365, 768))
            self.assertEqual(err, "")

    def test_keeps_existing_good_image_when_new_one_is_undersized(self):
        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / "02-x.jpg"
            Image.effect_noise((1365, 768), 64).convert("RGB").save(good, "JPEG")
            out = Path(d) / "02-x.png"
            wrote, err = self._capture(out, self._png(683, 384))
            self.assertFalse(wrote)
            self.assertFalse(out.exists(), "不合格的新图不该落盘")
            self.assertTrue(good.exists(), "磁盘上合格的旧图必须保留")
            self.assertIn("保留旧图", err)

    def test_overwrites_when_existing_is_also_bad(self):
        """两张都不合格时照常覆盖——否则永远卡在第一次的坏图上。"""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "02-x.png"
            out.write_bytes(self._png(400, 225))
            wrote, err = self._capture(out, self._png(683, 384))
            self.assertTrue(wrote)
            self.assertEqual(Image.open(out).size, (683, 384))

    def test_ignores_non_image_siblings(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "02-x.png"
            (Path(d) / "02-x.md").write_text("prompt", encoding="utf-8")
            wrote, _ = self._capture(out, self._png(683, 384))
            self.assertTrue(wrote, "同名 .md 不是图，不该拦住写入")


class StaleSiblingTest(unittest.TestCase):
    """返回格式会变（PNG/JPEG 交替），同名旧后缀残留会让后续 glob 取到旧图。"""

    def _write(self, d, name):
        p = Path(d) / name
        buf = io.BytesIO(); Image.new("RGB", (40, 20), (1, 2, 3)).save(buf, "PNG")
        p.write_bytes(buf.getvalue())
        return p

    def test_removes_other_extensions(self):
        with tempfile.TemporaryDirectory() as d:
            keep = self._write(d, "05-x.png")
            old = self._write(d, "05-x.jpg")
            ic._clear_stale_siblings(keep)
            self.assertTrue(keep.exists())
            self.assertFalse(old.exists())

    def test_keeps_other_names_and_non_images(self):
        with tempfile.TemporaryDirectory() as d:
            keep = self._write(d, "05-x.png")
            other = self._write(d, "06-y.jpg")
            md = Path(d) / "05-x.md"; md.write_text("prompt", encoding="utf-8")
            ic._clear_stale_siblings(keep)
            self.assertTrue(other.exists())
            self.assertTrue(md.exists(), "同名 .md 是 prompt 源文件，不能删")
