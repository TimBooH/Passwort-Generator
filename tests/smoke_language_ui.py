"""Qt offscreen smoke test for live German/English UI and persisted language."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QScrollArea, QTabWidget

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
settings = QSettings('TimBooH', 'PasswortGenerator')
previous = settings.value('ui/language', None)
settings.setValue('ui/language', 'de')

window = PasswordWindow(auto_check=False)
window.resize(850, 770)
window.show()
app.processEvents()

assert window.language == 'de'
assert window.language_combo.currentData() == 'de'
assert window.nav_buttons[0].text().endswith('Passwort')
assert window.appearance_card.header.text() == 'ERSCHEINUNGSBILD'
assert window.check_button.text() == '↻ Auf Update prüfen'
assert not window.findChildren(QScrollArea)

window.tabs.setCurrentIndex(1)
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.language == 'en'
assert window.settings.value('ui/language') == 'en'
assert window.language_combo.currentData() == 'en'
assert window.appearance_card.header.text() == 'APPEARANCE'
assert window.nav_buttons[0].text().endswith('Password')
assert window.nav_buttons[1].text().endswith('Settings')
assert window.check_button.text() == '↻ Check for updates'
assert window.scheme_combo.itemText(window.scheme_combo.findData('glass')) == 'Glass (transparent)'
assert window.scheme_combo.currentData()
assert window.accent_preview.text().startswith('●  Automatic')
assert 'Development' in window.info_version.text()
assert window.background_file_label.text() == 'No background image selected'
assert window.info_help_card.header.text() == 'GUIDE & HELP'

window.tabs.setCurrentIndex(0)
window.generate()
assert window.status.text() == 'Password generated.'
assert window.strength_label.text().startswith('🛡  Strength:')
window.copy()
assert window.status.text() == 'Copied to clipboard.'
window.switch_mode(True)
assert window.length_label.text() == 'Words:'
assert window.generate_button.text().endswith('Generate passphrase')
window.generate()
assert window.status.text() == 'Passphrase generated.'
window.switch_mode(False)

window.tabs.setCurrentIndex(3)
window.show_visual_guide()
app.processEvents()
guide = window.info_detail_stack.findChild(QTabWidget, 'visualGuideTabs')
assert guide is not None
assert guide.tabText(0).endswith('Password')
assert guide.tabText(2).endswith('Update')
window.show_info_overview()

# A reopened window must use the saved English setting.
window.close()
second = PasswordWindow(auto_check=False)
second.show()
app.processEvents()
assert second.language == 'en'
assert second.nav_buttons[0].text().endswith('Password')
second.tabs.setCurrentIndex(1)
second.language_combo.setCurrentIndex(second.language_combo.findData('de'))
app.processEvents()
assert second.language == 'de'
assert second.appearance_card.header.text() == 'ERSCHEINUNGSBILD'
assert second.check_button.text() == '↻ Auf Update prüfen'
assert second.nav_buttons[0].text().endswith('Passwort')
assert not second.findChildren(QScrollArea)
second.close()
if previous is None:
    settings.remove('ui/language')
else:
    settings.setValue('ui/language', previous)
settings.sync()
app.processEvents()
print('Deutsch/English live switching, saving, labels, passphrases and visual help OK')
