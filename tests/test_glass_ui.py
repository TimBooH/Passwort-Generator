"""Headless tests for polished glass color and styling helpers."""

import unittest
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import QApplication

from glass_ui import (GlossyGlassCard, GlassBackground, blend, build_glass_stylesheet,
                      is_dark_background, rgba, with_alpha)
from neon_style import circuit_texture, neon_stylesheet
from theme_colors import (COLOR_SCHEMES, accent_for_background, accessible_text_color,
                          contrast_ratio, preset_colors, sample_wallpaper_color)


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
            self.assertIn('QStackedWidget#mainPages', style)
            self.assertNotIn('QTabBar::tab', style)
            self.assertIn('rgba(', style)
            self.assertIn(fg, style)

    def test_neon_theme_and_circuit_texture(self):
        style = neon_stylesheet('#071322', '#FFFFFF')
        self.assertIn('QPushButton#modeButton:checked', style)
        self.assertIn('QPushButton#navButton:checked', style)
        self.assertIn('QFrame#topNav', style)
        self.assertIn('QPushButton#infoNavButton', style)
        self.assertNotIn('QFrame#navSidebar', style)
        self.assertNotIn('QPushButton#headerSettings', style)
        self.assertIn('QSlider::handle:horizontal', style)
        self.assertIn('QProgressBar#strengthBar', style)
        # QPixmap requires a GUI application, even in headless CI.
        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)
        pixmap = circuit_texture(220, 300)
        self.assertFalse(pixmap.isNull())
        self.assertEqual((pixmap.width(), pixmap.height()), (220, 300))

    def test_accent_follows_background(self):
        self.assertEqual(len(COLOR_SCHEMES), 7)
        self.assertEqual(preset_colors('glass'), ('#142638', '#F6FAFF'))
        self.assertEqual(preset_colors('glass_dark'), ('#171C26', '#F0F4FC'))
        self.assertEqual(preset_colors('glass_light'), ('#F0F4FA', '#142436'))
        self.assertIsNone(preset_colors('custom'))
        dark = accent_for_background('#171C26')
        light = accent_for_background('#F0F4FA')
        red = accent_for_background('#351A23')
        green = accent_for_background('#15362E')
        self.assertTrue(QColor(dark).isValid())
        self.assertTrue(QColor(light).isValid())
        nearby = accent_for_background('#20242C')
        self.assertLessEqual(abs(QColor(dark).hsvHue() - QColor(nearby).hsvHue()), 1)
        self.assertGreaterEqual(contrast_ratio(nearby, '#20242C'), 3.0)
        self.assertNotEqual(dark, light)
        self.assertNotEqual(red, green)
        self.assertNotEqual(red, dark)
        self.assertIn(dark.lower(), neon_stylesheet('#171C26', '#F0F4FC').lower())
        with self.assertRaises(ValueError):
            accent_for_background('not-a-color')

    def test_accessible_accents_and_automatic_text(self):
        for background in (
            '#071322', '#20242C', '#351A23', '#15362E', '#2B1D3A',
            '#FFFFFF', '#F0F4FA', '#F5EDDB', '#8C806F', '#2196F3',
            '#E35B6D', '#185F74', '#D2C3E8',
        ):
            accent = accent_for_background(background)
            self.assertGreaterEqual(
                contrast_ratio(accent, background), 3.0,
                f'Insufficient accent contrast: {background} -> {accent}',
            )
            self.assertGreaterEqual(
                contrast_ratio(accessible_text_color(background), background),
                4.5, f'Unreadable text color on {background}',
            )
        self.assertNotEqual(accent_for_background('#351A23'),
                            accent_for_background('#15362E'))

    def test_wallpaper_sample_adapts_accent(self):
        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)
        image = QImage(50, 50, QImage.Format.Format_RGB32)
        image.fill(QColor('#276F45'))
        sample = sample_wallpaper_color(QPixmap.fromImage(image))
        self.assertEqual(sample, '#276F45')
        self.assertNotEqual(accent_for_background(sample),
                            accent_for_background('#351A23'))
        self.assertIsNone(sample_wallpaper_color(QPixmap()))

    def test_pure_glass_reveals_wallpaper(self):
        app = QApplication.instance() or QApplication([])
        root = GlassBackground()
        card = GlossyGlassCard('Vorschau')
        card.set_glass_color('#142638')
        card.set_glass_mode(True)
        card._refresh_style()
        self.assertTrue(card._clear_glass)
        self.assertIn(', 48)', card.styleSheet())
        root.set_transparent_glass(True)
        self.assertTrue(root._clear_glass)
        self.assertIn(', 8)', root._shade.styleSheet())
        card.set_glass_mode(False)
        card._refresh_style()
        self.assertFalse(card._clear_glass)
        self.assertNotIn(', 48)', card.styleSheet())
        root.set_transparent_glass(False)
        self.assertFalse(root._clear_glass)
        card.close()
        root.close()

    def test_known_accent(self):
        self.assertTrue(QColor('#75DDF9').isValid())
        # Alpha 158/147 is distinctly less opaque than the previous 231/174.
        import inspect
        from glass_ui import GlossyGlassCard
        source = inspect.getsource(GlossyGlassCard._refresh_style)
        self.assertIn('alpha = 158 if dark else 147', source)


if __name__ == '__main__':
    unittest.main()
