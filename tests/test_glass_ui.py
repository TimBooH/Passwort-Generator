"""Headless tests for polished glass color and styling helpers."""

import unittest
from PySide6.QtGui import QColor

from glass_ui import blend, build_glass_stylesheet, is_dark_background, rgba, with_alpha


class GlassStyleTests(unittest.TestCase):
    def test_color_mode(self):
        self.assertTrue(is_dark_background('#101827'))
        self.assertFalse(is_dark_background('#F1F4F8'))

    def test_rgba_clamps_opacity(self):
        self.assertEqual(rgba('#112233', 300), 'rgba(17, 34, 51, 255)')
        self.assertEqual(rgba('#112233', -20), 'rgba(17, 34, 51, 0)')

    def test_blend_midpoint(self):
        self.assertEqual(blend('#000000', '#FFFFFF', .5).name(), '#808080')
        self.assertEqual(blend('#000000', '#FFFFFF', 0).name(), '#000000')
        self.assertEqual(blend('#000000', '#FFFFFF', 1).name(), '#ffffff')

    def test_with_alpha(self):
        self.assertEqual(with_alpha('#112233', 400).alpha(), 255)
        self.assertEqual(with_alpha('#112233', -4).alpha(), 0)

    def test_stylesheet_dark_and_light(self):
        for bg, fg in (('#101827', '#FFFFFF'), ('#F1F4F8', '#121820')):
            style = build_glass_stylesheet(bg, fg)
            self.assertIn('QPushButton#primaryButton', style)
            self.assertNotIn('QSlider::', style)
            self.assertIn('QTabBar::tab:selected', style)
            self.assertIn('QTabWidget#mainTabs::pane', style)
            self.assertIn('rgba(', style)
            self.assertIn(fg, style)

    def test_known_accent(self):
        self.assertTrue(QColor('#75DDF9').isValid())


if __name__ == '__main__':
    unittest.main()
