"""Visual regression of the approved compact Ocean Glass main and settings UI."""
import os
import tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='compact-ocean-')
from PySide6.QtCore import QSettings, QPoint
from PySide6.QtWidgets import QApplication, QScrollArea
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
from main import PasswordWindow
from theme_colors import DEFAULT_SCHEME

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(730, 830)
window.show()
for _ in range(5):
    app.processEvents()

assert DEFAULT_SCHEME == 'ocean_glass'
assert window.background_surface._ocean_enabled
assert not window.background_surface.has_background_image()
assert not hasattr(window,'appearance_card')
assert not hasattr(window,'scheme_combo')
assert 'QFrame#passwordOutputCard' in window.styleSheet()
assert 'QPushButton#compactNavButton' in window.styleSheet()
assert window.password_output_card.isVisible()
assert window.ocean_output_caption.isVisible()
assert window.ocean_sections.isVisible()
assert window.ocean_options_panel.isVisible()
assert window.ocean_length_panel.isVisible()
assert window.ocean_options_panel.x() < window.ocean_length_panel.x()
assert window.ocean_options_panel.height() == window.ocean_length_panel.height()
assert window.ocean_options_heading.text().endswith('Passwortoptionen')
assert window.ocean_length_heading.text().endswith('Länge & Anzahl')
assert not window.ocean_hero_icon.isVisible()
assert not window.ocean_page_title.isVisible()
assert window.findChildren(QScrollArea) == [window.batch_scroll]
assert not window.batch_scroll.isVisible()
assert all(b.isVisible() for b in window._compact_nav_buttons)
assert [b.text() for b in window._compact_nav_buttons] == [
    'Passwort','Passphrase','Verlauf','Einstellungen'
]
assert not any(b.isVisible() for b in window.nav_buttons + [window.info_nav_button])
assert len(window.batch_count_buttons)==4
assert [b.text() for b in window.batch_count_buttons]==['1','5','10','20']
assert window.batch_count_buttons[0].isChecked()
assert window.generate_button.isVisible()
assert not window.status.isVisible()
assert not window.regenerate_button.isVisible()
assert window.generate_button.parentWidget() is window.glass_cards[0]
assert window.generate_button.mapTo(window,QPoint(0,0)).y() > window.ocean_sections.mapTo(window,QPoint(0,0)).y()
assert window.show_button.isVisible()
assert window.copy_top_button.isVisible()
assert not window.rules_button.isVisible()
assert not window.ocean_preset_box.isVisible()
assert window.output.height() >= 43, (window.output.height(), window.output.minimumHeight(), window.output.maximumHeight(), window.size())
assert 'switch-on.png' in window.styleSheet()

window.generate()
assert len(window.output.text()) == window.length.value()
assert window.output.echoMode() == window.output.EchoMode.Normal
window.switch_mode(True)
assert window.passphrase_mode_button.isChecked()
window.generate()
assert window.output.text()
window.switch_mode(False)
window.show_settings_dialog('update')
app.processEvents()
assert window._settings_dialog is not None
assert window._settings_dialog.isVisible()
assert window._settings_views.currentIndex() == 3
assert window.check_button.isVisible()
assert window.channel_combo.isVisible()
assert window.tabs.count()==1
window._settings_dialog.close()
app.processEvents()
assert window._settings_dialog is None
assert window.tabs.count()==4

window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.language == 'en'
assert window.settings_button.text()=='Settings'
assert window.password_mode_button.text()=='Password'
assert window.ocean_options_heading.text().endswith('Password options')
assert window.ocean_length_heading.text().endswith('Length & quantity')
window.language_combo.setCurrentIndex(window.language_combo.findData('de'))
window.apply_colors()
assert window.background_surface._ocean_enabled
window.close()
print('Approved compact Ocean GUI, separate settings, no footer and bilingual navigation OK')
