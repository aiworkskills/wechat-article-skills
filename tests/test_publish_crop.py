"""publish.py 封面裁剪框：微信要求裁出区域的宽高比与目标比例一致，否则 53402。"""
import unittest

from tests._load import load

pub = load("skills/aws-wechat-article-publish/scripts/publish.py", "aws_publish")


def _parse(box: str):
    x1, y1, x2, y2 = (float(v) for v in box.split("_"))
    return x1, y1, x2, y2


class CropBoxTest(unittest.TestCase):
    def _assert_ratio(self, w, h, target):
        box = pub._crop_box(w, h, target)
        x1, y1, x2, y2 = _parse(box)
        # 归一化坐标须落在 [0,1] 且有序
        for v in (x1, y1, x2, y2):
            self.assertGreaterEqual(v, 0.0, box)
            self.assertLessEqual(v, 1.0, box)
        self.assertLess(x1, x2, box)
        self.assertLess(y1, y2, box)
        got = ((x2 - x1) * w) / ((y2 - y1) * h)
        self.assertAlmostEqual(got, target, places=3, msg=f"{w}x{h} {box} -> {got}")
        return box

    def test_wide_source_for_both_ratios(self):
        """2.35:1 主图：宽幅框应取全图，方形框从中间截。"""
        box = self._assert_ratio(1408, 599, 2.35)
        x1, _, x2, _ = _parse(box)
        self.assertAlmostEqual(x2 - x1, 1.0, places=2)  # 已是 2.35:1，占满
        self._assert_ratio(1408, 599, 1.0)

    def test_square_source(self):
        self._assert_ratio(1024, 1024, 2.35)
        box = self._assert_ratio(1024, 1024, 1.0)
        self.assertEqual(box, "0.000000_0.000000_1.000000_1.000000")

    def test_tall_source(self):
        self._assert_ratio(800, 1200, 2.35)
        self._assert_ratio(800, 1200, 1.0)

    def test_various_sizes_keep_exact_ratio(self):
        for w, h in [(900, 383), (1376, 586), (704, 300), (1080, 1080), (1200, 630)]:
            for target in (2.35, 1.0):
                self._assert_ratio(w, h, target)

    def test_degenerate_size_returns_empty(self):
        self.assertEqual(pub._crop_box(0, 100, 2.35), "")
        self.assertEqual(pub._crop_box(100, 0, 1.0), "")


class CoverCropsTest(unittest.TestCase):
    def test_manual_values_win(self):
        meta = {"pic_crop_235_1": "0_0_1_1", "pic_crop_1_1": "0.2_0_0.8_1"}
        out = pub._cover_crops("/nonexistent.png", meta)
        self.assertEqual(out["pic_crop_235_1"], "0_0_1_1")
        self.assertEqual(out["pic_crop_1_1"], "0.2_0_0.8_1")

    def test_unreadable_cover_degrades_quietly(self):
        """读不到封面时不该阻断发布，交给微信自行裁切。"""
        self.assertEqual(pub._cover_crops("/nonexistent.png", {}), {})


if __name__ == "__main__":
    unittest.main()
