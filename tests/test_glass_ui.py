"""Headless tests for palette and styling helpers (no QApplication needed)."""

import unittest

from PySide6.QtGui import QColor

from glass_ui import build_glass_stylesheet, is_dark_background, rgba


class GlassStyleTests(unittest.TestCase):
    def test_color_mode(self):
        self.assertTrue(is_dark_background('#101827'))
        self.assertFalse(is_dark_background('#F1F4F8'))

    def test_rgba_clamps_opacity(self):
        self.assertEqual(rgba('#112233', 300), 'rgba(17, 34, 51, 255)')
        self.assertEqual(rgba('#112233', -20), 'rgba(17, 34, 51, 0)')

    def test_stylesheet_dark_and_light(self):
        for bg, text_color in (('#101827', '#FFFFFF'), ('#F1F4F8', '#121820')):
            style = build_glass_stylesheet(bg, text_color, 54)
            self.assertIn('QGroupBox', style)
            self.assertIn('QPushButton#primaryButton', style)
            self.assertIn('QSlider::handle:horizontal', style)
            self.assertIn('rgba(', style)
            self.assertIn(text_color, style)

    def test_glass_opacity_changes_card_alpha(self):
        low = build_glass_stylesheet('#101827', '#FFFFFF', 30)
        high = build_glass_stylesheet('#101827', '#FFFFFF', 85)
        self.assertNotEqual(low, high)

    def test_known_palette_colors(self):
        self.assertTrue(QColor('#A1EAFF').isValid())


if __name__ == '__main__':
    unittest.main()
