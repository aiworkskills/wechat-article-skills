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


if __name__ == "__main__":
    unittest.main()
