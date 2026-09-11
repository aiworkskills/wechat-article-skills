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

    def test_wrong_directory_is_not_no_model(self):
        """空目录（没有 .aws-article/config.yaml）是「跑错目录 / 没做首次引导」，不是「模型未配置」。

        原先这两种情况都走 [NO_MODEL] + 退出码 2，而 SKILL.md 规定退出码 2 意味着
        Agent 可以改用自身能力代生图——于是配置完全正常、只是 cd 错了目录的用户，
        会看到一句假的「你没配图片模型」并同意降级，绕开自己配好的专用模型。
        """
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(SCRIPT), "test"], cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertNotIn("[NO_MODEL]", r.stderr, "不得触发 Agent 降级生图")
            self.assertIn(".aws-article/config.yaml", r.stderr)

    def test_no_model_exit_2(self):
        """config.yaml 在、但 image_model 没配 —— 这才是真正的未配置，允许降级。"""
        with tempfile.TemporaryDirectory() as d:
            Path(d, ".aws-article").mkdir()
            Path(d, ".aws-article/config.yaml").write_text("tone: x\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), "test"], cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("[NO_MODEL]", r.stderr)

    def test_missing_api_key_is_still_no_model(self):
        """image_model 填了但 aws.env 没有 key —— 仍属未配置。"""
        with tempfile.TemporaryDirectory() as d:
            Path(d, ".aws-article").mkdir()
            Path(d, ".aws-article/config.yaml").write_text(
                'image_model:\n  base_url: "https://x/v1/images/generations"\n  model: "m"\n',
                encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), "test"], cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("[NO_MODEL]", r.stderr)


@unittest.skipIf(Image is None, "Pillow 未安装")
class MinSizeRetryTest(unittest.TestCase):
    """端点返回尺寸波动大（实测 384~1584px），过小需重试而非直接采用。"""

    def _png(self, w, h):
        # 用噪声图而不是纯色：纯色会触发「近单色」检查，这里只想测尺寸一项
        buf = io.BytesIO()
        Image.effect_noise((w, h), 64).convert("RGB").save(buf, "PNG")
        return buf.getvalue()

    def _run(self, sizes, retries=None, check_resolution=True):
        """按 sizes 顺序依次返回图片，记录实际调用次数。"""
        calls = []

        def gen():
            wh = sizes[min(len(calls), len(sizes) - 1)]
            calls.append(wh)
            return self._png(*wh)

        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            data = ic._generate_with_checks("t.md", gen, retries=retries,
                                            check_resolution=check_resolution)
        return data, calls, err.getvalue()

    def test_no_retry_when_large_enough(self):
        data, calls, err = self._run([(1376, 586)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(err, "")
        self.assertEqual(Image.open(io.BytesIO(data)).size, (1376, 586))

    def test_default_does_not_retry(self):
        """默认零重试。**每一次重试都是一次付费生成，而被丢弃的候选图不落盘**——
        目录里一张废图都看不见，钱已经花了。曾经默认 3 次，一篇五图的文章期望要
        烧掉十次生成，只为把正文图从 683px 换成 1376px。"""
        self.assertEqual(ic.CHECK_RETRIES, 0)
        data, calls, err = self._run([(384, 163)])
        self.assertEqual(len(calls), 1, "默认不该自动重跑")
        self.assertIn("384", err)
        self.assertIn("--retries", err, "要告诉用户怎么显式重试")

    def test_retries_when_explicitly_asked(self):
        """机制本身保留：显式传 --retries 时照旧重跑并取更好的一张。"""
        data, calls, err = self._run([(384, 163), (1376, 586)], retries=1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(Image.open(io.BytesIO(data)).size, (1376, 586))
        self.assertEqual(err, "")

    def test_keeps_larger_when_retry_is_worse(self):
        """重试可能更差，须保留较大的一张而不是最后一张。"""
        data, calls, err = self._run([(704, 300), (384, 163)], retries=1)
        self.assertEqual(Image.open(io.BytesIO(data)).size, (704, 300))
        self.assertIn("704", err)

    def test_warns_after_exhausting_retries(self):
        data, calls, err = self._run([(384, 163)], retries=2)
        self.assertEqual(len(calls), 3)
        self.assertIn("384", err)
        self.assertIn("4K", err)  # 提醒不要设 4K

    def test_body_image_skips_resolution_check(self):
        """900px 是**封面**的线（官方推荐 900x383）。正文插图在微信里只有 375pt 宽，
        683px 和 1376px 读者分不出来——为这个差别重生成是白花钱。"""
        data, calls, err = self._run([(683, 384)], retries=3, check_resolution=False)
        self.assertEqual(len(calls), 1, "正文图不该因为分辨率被重跑")
        self.assertEqual(err, "")

    def test_cover_detection(self):
        self.assertTrue(ic._is_cover("01-cover"))
        self.assertTrue(ic._is_cover("01-封面"))
        self.assertTrue(ic._is_cover("02-对比", {"role": "cover"}))
        self.assertFalse(ic._is_cover("02-对比两栏"))
        self.assertFalse(ic._is_cover("01-cover", {"role": "body"}))

    def test_threshold_matches_wechat_cover_minimum(self):
        self.assertGreaterEqual(ic.MIN_LONG_EDGE, 900)

    def test_default_image_size_is_not_4k(self):
        """实测 4K 会让端点连 aspectRatio 一起忽略。"""
        self.assertNotEqual(ic.DEFAULT_IMAGE_SIZE, "4K")

    def test_no_crash_without_pillow_or_bad_bytes(self):
        self.assertIsNone(ic._image_long_edge(b"not an image"))


@unittest.skipIf(Image is None, "Pillow 未安装")
class CoverChecksTest(unittest.TestCase):
    """出图后的纯代码检查只剩两项：分辨率与近单色。

    「标题区干净度」那一项已随标题合成一起删除——它是为「先出底图、再用 Pillow 往
    留白区贴中文标题」那条路存在的，而那条路的前提（模型画不好中文）已经不成立。
    """

    def test_monochrome_flagged(self):
        buf = io.BytesIO(); Image.new("RGB", (1400, 600), (10, 10, 10)).save(buf, "PNG")
        probs = ic._cover_problems(buf.getvalue())
        self.assertTrue(any("近单色" in p for p in probs), probs)

    def test_normal_image_passes(self):
        im = Image.linear_gradient("L").resize((1400, 600)).convert("RGB")
        buf = io.BytesIO(); im.save(buf, "PNG")
        self.assertEqual(ic._cover_problems(buf.getvalue()), [])

    def test_title_compositing_is_gone(self):
        """中文出错那条线上的东西不该再留在代码里。"""
        for gone in ("_compose_title", "_split_title", "_find_cjk_font",
                     "_zone_edge_density", "_parse_zone", "_resolve_title",
                     "ZONE_BUSY_THRESHOLD", "DEFAULT_TITLE_ZONE"):
            self.assertFalse(hasattr(ic, gone), f"{gone} 还在")


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


@unittest.skipUnless(Image is not None, "缺少 Pillow")
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


@unittest.skipIf(Image is None, "Pillow 未安装")
class CropGuillotineTest(unittest.TestCase):
    """裁掉一小条是正常的，裁掉一大半说明端点根本没理 aspectRatio。

    实测四张封面里三张返回 1024x1024 方图，被裁成 1024x436。模型是**按方画布构图**
    的（「左侧四成…右侧六成…字高 28%」），上下砍掉 58% 等于把构图腰斩。这一步此前
    只打一行 INFO，看着像正常流程，没人知道封面为什么难看。
    """

    def _png(self, w, h):
        buf = io.BytesIO()
        Image.effect_noise((w, h), 64).convert("RGB").save(buf, "PNG")
        return buf.getvalue()

    def _crop(self, w, h, aspect="2.35:1"):
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            data = ic._crop_to_aspect(self._png(w, h), aspect)
        return Image.open(io.BytesIO(data)).size, err.getvalue()

    def test_square_from_endpoint_is_warned(self):
        size, err = self._crop(1024, 1024)
        self.assertEqual(size, (1024, 436))
        self.assertIn("WARN", err)
        self.assertIn("腰斩", err)
        self.assertIn("--retries", err, "要告诉用户这种情况值得重跑")

    def test_normal_nearest_ratio_crop_is_silent(self):
        """21:9 → 2.35:1 这类就近映射只裁掉几个百分点，不该报警。"""
        _, err = self._crop(1584, 672)
        self.assertEqual(err, "")

    def test_moderate_crop_is_silent(self):
        _, err = self._crop(1600, 900)
        self.assertNotIn("WARN", err)

    def test_threshold_leaves_room_for_real_ratio_mapping(self):
        self.assertLess(ic.CROP_KEEP_MIN, 16 / 9 / (2.35) + 0.01)
        self.assertGreater(ic.CROP_KEEP_MIN, 1 / 2.35, "方图裁 2.35:1 只剩 43%，必须被拦住")


class StyleNameValidationTest(unittest.TestCase):
    """形态名此前没有任何脚本校验过。

    image_create.py 压根不读候选池，全靠 Agent 自觉。实测 2026-09-12：网站导出的
    config 里写着「对比说明 / 板书白板 / 氛围烘托」，三个都不存在（真名是 对比两栏 /
    概念隐喻 / 场景还原，而「板书白板」根本是**媒介**不是形态）。Agent 挑中它只能
    自己编，整套形态方法论静默失效——而且不报错。
    """

    def _run_in(self, cfg: dict | None):
        import os, tempfile, yaml as _y
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                if cfg is not None:
                    os.makedirs(".aws-article")
                    with open(".aws-article/config.yaml", "w", encoding="utf-8") as f:
                        _y.safe_dump(cfg, f, allow_unicode=True)
                return ic._cmd_styles()
            finally:
                os.chdir(cwd)

    def test_real_names_pass(self):
        self.assertEqual(0, self._run_in(
            {"custom_article_image_style": ["对比两栏", "概念隐喻", "金句卡片"]}))

    def test_bogus_names_fail(self):
        self.assertEqual(1, self._run_in(
            {"custom_article_image_style": ["对比说明", "板书白板", "氛围烘托"]}))

    def test_medium_name_is_not_a_style(self):
        """「板书白板」是媒介，不是形态——最容易混的一类，单独钉住。"""
        self.assertEqual(1, self._run_in({"custom_article_image_style": ["板书白板"]}))

    def test_empty_pool_is_fine(self):
        self.assertEqual(0, self._run_in({"custom_article_image_style": []}))

    def test_no_config_still_lists(self):
        self.assertEqual(0, self._run_in(None))

    def test_builtin_style_files_exist(self):
        """内置形态目录不能是空的，否则上面所有校验都会变成「全都不存在」。"""
        self.assertGreaterEqual(len(ic._list_style_names("image-styles")), 8)
        self.assertGreaterEqual(len(ic._list_style_names("cover-styles")), 10)
