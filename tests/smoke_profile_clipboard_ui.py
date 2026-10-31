"""End-to-end offscreen smoke for presets, clipboard safety and nav ordering."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from main import PasswordWindow
from password_presets import decode_profile

app = QApplication([])
app.setStyle('Fusion')
settings = QSettings('TimBooH', 'PasswortGenerator')
keys = ('security/clipboard_auto_clear', 'security/clipboard_seconds',
        'profiles/custom_password', 'ui/language')
old = {key: settings.value(key, None) for key in keys}
settings.setValue('ui/language', 'de')
settings.setValue('security/clipboard_auto_clear', True)
settings.setValue('security/clipboard_seconds', 60)
settings.remove('profiles/custom_password')
window = PasswordWindow(auto_check=False)
window.resize(850, 760)
window.show()
app.processEvents()

# Button labels and order: Password -> Update -> Settings -> Info.
assert [window.nav_buttons[i].text() for i in (0, 2, 1)] == [
    'Passwort', 'Update', 'Einstellungen'
]
assert window.nav_buttons[0].x() < window.nav_buttons[2].x()
assert window.nav_buttons[2].x() < window.nav_buttons[1].x()
assert window.nav_buttons[1].x() < window.info_nav_button.x()
window.nav_buttons[1].click()
assert window.tabs.currentIndex() == 1
window.nav_buttons[2].click()
assert window.tabs.currentIndex() == 2
window.nav_buttons[0].click()
assert window.tabs.currentIndex() == 0

assert window.preset_combo.currentData() == 'standard'
window.preset_combo.setCurrentIndex(window.preset_combo.findData('strong'))
assert window.length.value() == 32
assert window.upper.isChecked() and window.symbols.isChecked()
window.preset_combo.setCurrentIndex(window.preset_combo.findData('simple'))
assert window.length.value() == 16
assert not window.symbols.isChecked()
window.length.setValue(28)
window.upper.setChecked(False)
assert window.preset_combo.currentData() == 'manual'
window.save_preset_button.click()
assert window.preset_combo.currentData() == 'custom'
saved = decode_profile(settings.value('profiles/custom_password', ''))
assert saved['length'] == 28 and not saved['upper']
assert set(saved) == {'length', 'upper', 'lower', 'digits', 'symbols', 'exclude'}
window.preset_combo.setCurrentIndex(window.preset_combo.findData('standard'))
assert window.length.value() == 20 and window.upper.isChecked()
window.preset_combo.setCurrentIndex(window.preset_combo.findData('custom'))
assert window.length.value() == 28 and not window.upper.isChecked()
window.switch_mode(True)
assert not window.preset_combo.isEnabled()
window.switch_mode(False)
assert window.preset_combo.isEnabled()

# Only erase an unchanged, app-copied secret; do not clear a newer user copy.
clipboard = QApplication.clipboard()
window.generate()
secret = window.output.text()
window.copy()
assert window.clipboard_timer.isActive()
assert clipboard.text() == secret
clipboard.setText('ordinary text')
window.clear_copied_password()
assert clipboard.text() == 'ordinary text'
assert window._clipboard_secret is None
window.copy()
assert window.clipboard_timer.isActive()
assert clipboard.text() == secret
window.clear_copied_password()
assert clipboard.text() == ''
assert window._clipboard_secret is None
window.tabs.setCurrentIndex(1)
assert window.language_card.isAncestorOf(window.language_combo)
assert window.clipboard_timeout_combo.currentData() == 60
window.clipboard_timeout_combo.setCurrentIndex(window.clipboard_timeout_combo.findData(30))
assert settings.value('security/clipboard_seconds', type=int) == 30
window.tabs.setCurrentIndex(0)
window.copy()
assert window.clipboard_timer.interval() == 30000
window.tabs.setCurrentIndex(1)
window.clear_clipboard_checkbox.setChecked(False)
assert not window.clipboard_timer.isActive()
assert window._clipboard_secret is None
window.tabs.setCurrentIndex(0)
window.copy()
assert clipboard.text() == secret
assert not window.clipboard_timer.isActive()
window.tabs.setCurrentIndex(1)
window.clear_clipboard_checkbox.setChecked(True)
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.security_card.header.text() == 'SECURITY'
assert window.language_card.header.text() == 'LANGUAGE'
assert window.clear_clipboard_checkbox.text() == 'Clear clipboard automatically'
assert window.preset_combo.itemText(window.preset_combo.findData('strong')) == 'Very secure'
assert window.nav_buttons[1].text().endswith('Settings')
assert window.nav_buttons[2].text().endswith('Update')
window.tabs.setCurrentIndex(0)
assert window.save_preset_button.text() == 'Save profile'
window.generate()
assert window.status.text() == 'Password generated.'
window.close()

for key, value in old.items():
    if value is None:
        settings.remove(key)
    else:
        settings.setValue(key, value)
settings.sync()
print('Profiles, safe clipboard timer, bilingual controls, and navigation order OK')

