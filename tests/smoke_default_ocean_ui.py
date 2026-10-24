"""Real offscreen GUI regression: Ocean Glass is the default, not a preview.

This process uses isolated Qt settings so user preferences and Windows registry
are not changed by the smoke test.
"""
import os
import tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='ocean-glass-ui-')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QScrollArea

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
from main import PasswordWindow
from theme_colors import DEFAULT_SCHEME, preset_colors

app = QApplication([])
app.setStyle('Fusion')
# An earlier GUI test must never leave English active for other smoke tests.
QSettings('TimBooH', 'PasswortGenerator').setValue('ui/language', 'de')
window = PasswordWindow(auto_check=False)
window.resize(1120, 790)
window.show()
for _ in range(5):
    app.processEvents()

assert DEFAULT_SCHEME == 'ocean_glass'
assert not hasattr(window, 'scheme_combo')
assert not hasattr(window, 'bg_combo')
assert not hasattr(window, 'appearance_card')
assert not hasattr(window, 'choose_background_button')
assert not hasattr(window, 'image_mode_combo')
assert not window.background_surface.has_background_image()
assert window.settings.value('color_scheme') is None
assert window.settings.value('background_image_path') is None
assert window.background_surface._ocean_enabled
assert window.background_surface._ocean.isVisible()
assert not window.background_surface._circuit.isVisible()
assert window.glass_cards[0]._ocean_enabled
assert window.ocean_page_title.isVisible()
assert window.ocean_hero_icon.isVisible()
assert window.ocean_options_panel.x() < window.ocean_length_panel.x()
assert window.ocean_options_panel.height() == window.ocean_length_panel.height()
assert 'QCheckBox::indicator:checked' in window.styleSheet()
assert 'checked.png' in window.styleSheet()
assert window.ocean_page_title.text() == 'PASSWORT ERSTELLEN'
assert window.ocean_page_subtitle.text() == 'Erstelle sichere und zufällige Passwörter oder Passphrasen.'
assert window.ocean_sections.height() <= 276
assert window.ocean_length_panel.height() <= 276
assert window.output.height() >= 54
assert window.generate_button.height() >= 55
assert window.ocean_hero_icon.text() == '🔑'
assert window.symbols.mapTo(window.ocean_options_panel, window.symbols.rect().topLeft()).y() > window.digits.mapTo(window.ocean_options_panel, window.digits.rect().topLeft()).y()
assert 'Ocean Glass' in window.styleSheet()
assert '#18B7F7' in window.styleSheet()
assert not window.findChildren(QScrollArea)
assert window.generate_button.width() > 360
assert window.ocean_options_panel.isVisible()
assert window.ocean_length_panel.isVisible()
assert window.ocean_output_caption.isVisible()
assert window.ocean_strength_caption.isVisible()
assert not window.strength_label.isVisible()
assert window.ocean_options_heading.text() == 'Optionen'
assert window.ocean_length_heading.text() == 'Passwort-Länge'

# This is the real interactive program, including passwords, modes and settings.
window.generate()
assert len(window.output.text()) == window.length.value()
window.switch_mode(True)
assert window.ocean_page_title.text() == 'PASSPHRASE ERSTELLEN'
window.generate()
assert window.output.text()
window.switch_mode(False)

# Even saved legacy color/background choices cannot alter the fixed theme.
window.settings.setValue('color_scheme', 'glass_light')
window.settings.setValue('background_color', '#FFFFFF')
window.settings.setValue('background_image_path', '/tmp/no-longer-allowed.png')
window.apply_colors()
assert window.background_surface._ocean_enabled
assert not window.background_surface.has_background_image()
window.settings.remove('color_scheme')
window.settings.remove('background_color')
window.settings.remove('background_image_path')
window.tabs.setCurrentIndex(1)
assert window.language_card.isVisible()
assert window.security_card.isVisible()

# All pages, both languages and small-window layouts still work.
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
window.tabs.setCurrentIndex(0)
assert window.ocean_page_title.text() == 'CREATE PASSWORD'
assert window.ocean_page_subtitle.text() == 'Create secure random passwords or passphrases.'
assert window.ocean_options_heading.text() == 'Options'
assert window.ocean_length_heading.text() == 'Password length'
for width, height in ((530, 700), (850, 760), (1100, 820)):
    window.resize(width, height)
    for index in (0, 1, 2, 3):
        window.tabs.setCurrentIndex(index)
        app.processEvents()
        assert window.tabs.currentIndex() == index
    window.tabs.setCurrentIndex(0)
    app.processEvents()
    assert window.ocean_page_title.isVisible() == (width >= 780)
    assert window.generate_button.isVisible()
assert window.grab().width() >= 1100
window.close()
app.processEvents()

# Preferences remain selected after a new window is created.
again = PasswordWindow(auto_check=False)
assert again.background_surface._ocean_enabled
assert not hasattr(again, 'scheme_combo')
assert not hasattr(again, 'appearance_card')
again.language_combo.setCurrentIndex(again.language_combo.findData('de'))
app.processEvents()
again.close()
QSettings('TimBooH', 'PasswortGenerator').setValue('ui/language', 'de')
print('Ocean Glass default, themes, screenshot layout and bilingual pages OK')
