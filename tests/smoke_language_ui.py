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
assert not hasattr(window, 'appearance_card')
assert window.language_card.header.text() == 'SPRACHE'
assert window.check_button.text() == '↻ Auf Update prüfen'
assert not window.findChildren(QScrollArea)

window.tabs.setCurrentIndex(1)
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.language == 'en'
assert window.settings.value('ui/language') == 'en'
assert window.language_combo.currentData() == 'en'
assert not hasattr(window, 'appearance_card')
assert window.language_card.header.text() == 'LANGUAGE'
assert window.nav_buttons[0].text().endswith('Password')
assert window.nav_buttons[1].text().endswith('Settings')
assert window.check_button.text() == '↻ Check for updates'
assert window.background_surface._ocean_enabled
assert not hasattr(window, 'scheme_combo')
assert 'Development' in window.info_version.text()
assert not window.background_surface.has_background_image()
assert window.info_help_card.header.text() == 'GUIDE & HELP'
# Changelog local loading and failure texts also obey the one global setting.
window._set_changelog_ui('Keine veröffentlichten Versionen gefunden.')
assert window.changelog_view.toPlainText() == 'No published releases found.'
window._set_changelog_ui(
    'Die Versionshistorie konnte nicht geladen werden. '
    'Bitte die Internetverbindung prüfen und erneut versuchen.'
)
assert window.changelog_view.toPlainText().startswith('Could not load release history.')
assert window.language_card.isAncestorOf(window.language_combo)
assert not hasattr(window, 'appearance_card')
assert window.updates_page.findChild(type(window.language_combo), 'languageCombo') is None

# The entire application shares ONE language setting, including GitHub notes
# that were downloaded before the language was changed.
bilingual = ('## Deutsch\n- Vollständige Sprachumstellung\n'
             '## English\n- Full application language support')
historic = '# PasswortGenerator v0.16.0\n- Nur deutsche Änderungen'
window._history_releases = {
    'v0.17.0': {'tag': 'v0.17.0', 'body': bilingual},
    'v0.16.0': {'tag': 'v0.16.0', 'body': historic},
}
window.release_combo.blockSignals(True)
window.release_combo.clear()
window.release_combo.addItem('v0.17.0', 'v0.17.0')
window.release_combo.addItem('v0.16.0', 'v0.16.0')
window.release_combo.setEnabled(True)
window.release_combo.blockSignals(False)
window.tabs.setCurrentIndex(2)
window.select_release_history(0)
assert 'Full application' in window.changelog_view.toPlainText()
assert 'Sprachumstellung' not in window.changelog_view.toPlainText()
window.release_combo.setCurrentIndex(1)
assert 'Shortened and streamlined' in window.changelog_view.toPlainText()
assert 'Nur deutsche' not in window.changelog_view.toPlainText()
window._set_ui(window.update_status, 'Installiert: v0.17.0 · Prüfe GitHub …')
assert window.update_status.text().startswith('Installed:')
window._set_ui(window.release_history_status,
               'Versionshistorie nicht verfügbar: GitHub hat keine gültige Release-Liste geliefert.')
assert window.release_history_status.text() == (
    'Release history unavailable: GitHub returned an invalid release list.'
)
window.tabs.setCurrentIndex(1)
window.language_combo.setCurrentIndex(window.language_combo.findData('de'))
app.processEvents()
assert window.language == 'de'
assert 'Nur deutsche Änderungen' in window.changelog_view.toPlainText()
assert window.update_status.text().startswith('Installiert:')
assert 'nicht verfügbar' in window.release_history_status.text()
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.language == 'en'
assert 'Shortened and streamlined' in window.changelog_view.toPlainText()
assert window.update_status.text().startswith('Installed:')

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
assert not hasattr(second, 'appearance_card')
assert second.language_card.header.text() == 'SPRACHE'
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
