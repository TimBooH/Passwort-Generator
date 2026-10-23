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
assert window.scheme_combo.currentData() == DEFAULT_SCHEME
assert window.settings.value('color_scheme') == DEFAULT_SCHEME
assert window.bg_combo.currentData() == preset_colors(DEFAULT_SCHEME)[0]
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
assert window.ocean_page_subtitle.text() == 'Sichere Passwörter und Passphrasen'
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

# The redesigned theme does not replace other available themes.
window.tabs.setCurrentIndex(1)
normal = window.scheme_combo.findData('glass_light')
assert normal >= 0
window.scheme_combo.setCurrentIndex(normal)
for _ in range(3):
    app.processEvents()
assert not window.background_surface._ocean_enabled
assert not window.background_surface._ocean.isVisible()
assert not window.glass_cards[0]._ocean_enabled

window.scheme_combo.setCurrentIndex(window.scheme_combo.findData('ocean_glass'))
for _ in range(3):
    app.processEvents()
assert window.background_surface._ocean_enabled
assert window.settings.value('color_scheme') == 'ocean_glass'

# All pages, both languages and small-window layouts still work.
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
window.tabs.setCurrentIndex(0)
assert window.ocean_page_title.text() == 'CREATE PASSWORD'
assert window.ocean_page_subtitle.text() == 'Secure passwords and passphrases'
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
assert again.scheme_combo.currentData() == 'ocean_glass'
again.language_combo.setCurrentIndex(again.language_combo.findData('de'))
app.processEvents()
again.close()
QSettings('TimBooH', 'PasswortGenerator').setValue('ui/language', 'de')
print('Ocean Glass default, themes, screenshot layout and bilingual pages OK')
