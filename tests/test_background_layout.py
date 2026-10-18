"""Unit tests for background image geometry and safe renderer choices."""

import unittest
from glass_ui import (
    IMAGE_MODES, MODE_IDS, MAX_DECODE_EDGE, image_rectangles, is_dark_background,
)


class BackgroundGeometryTests(unittest.TestCase):
    def test_all_modes_are_unique(self):
        self.assertEqual(len(IMAGE_MODES), len(MODE_IDS))
        self.assertTrue({'cover', 'contain', 'stretch', 'center', 'original', 'tile'} <= MODE_IDS)

    def test_cover_crops_and_fills(self):
        target, source = image_rectangles('cover', 800, 600, 1200, 600)
        self.assertEqual((target.width(), target.height()), (800.0, 600.0))
        self.assertAlmostEqual(source.width(), 800)
        self.assertAlmostEqual(source.left(), 200)
        self.assertAlmostEqual(source.height(), 600)

    def test_contain_preserves_aspect_ratio(self):
        target, source = image_rectangles('contain', 800, 600, 1200, 600)
        self.assertEqual((target.width(), target.height()), (800.0, 400.0))
        self.assertEqual(target.top(), 100.0)
        self.assertEqual(source.width(), 1200)

    def test_center_keeps_native_size(self):
        target, source = image_rectangles('center', 800, 600, 1200, 600)
        self.assertEqual(target.left(), -200)
        self.assertEqual(target.top(), 0)
        self.assertEqual(target.width(), source.width())

    def test_original_starts_top_left(self):
        target, source = image_rectangles('original', 800, 600, 1200, 600)
        self.assertEqual((target.left(), target.top()), (0.0, 0.0))
        self.assertEqual(target.size(), source.size())

    def test_stretch_ignores_aspect_ratio(self):
        target, source = image_rectangles('stretch', 800, 600, 1200, 900)
        self.assertEqual((target.width(), target.height()), (800.0, 600.0))
        self.assertEqual((source.width(), source.height()), (1200.0, 900.0))

    def test_invalid_dimensions_do_not_draw(self):
        for mode in MODE_IDS:
            self.assertIsNone(image_rectangles(mode, 0, 800, 1200, 900))
            self.assertIsNone(image_rectangles(mode, 100, 800, 0, 900))

    def test_loading_limit(self):
        self.assertLessEqual(MAX_DECODE_EDGE, 4096)
        self.assertTrue(is_dark_background('#101827'))


if __name__ == '__main__':
    unittest.main()
