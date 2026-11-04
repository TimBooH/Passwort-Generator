"""Qt offscreen smoke test for the six new v0.20 features."""
import math
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from unittest import mock
from PySide6.QtCore import QEvent, QSettings
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QMessageBox

from main import PasswordWindow
from password_core import PHRASE_FIRST_EN, PHRASE_LAST_EN, SYMBOLS

app = QApplication([])
app.setStyle('Fusion')
settings = QSettings('TimBooH', 'PasswortGenerator')
saved = {}
for key in ('ui/language', 'passphrase/language',
            'password/min_digits', 'password/min_symbols',
            'password/excluded_chars', 'security/hide_on_deactivate',
            'security/confirm_history'):
    saved[key] = settings.value(key, None)
settings.setValue('ui/language', 'de')
settings.setValue('passphrase/language', 'de')
settings.setValue('security/hide_on_deactivate', True)
settings.setValue('security/confirm_history', False)
settings.setValue('password/min_digits', 0)
settings.setValue('password/min_symbols', 0)
settings.setValue('password/excluded_chars', '')

window = PasswordWindow(auto_check=False)
window.resize(850, 770)
window.show()
app.processEvents()

assert window.analysis_button.isVisible()
assert window.rules_button.isVisible()
assert window.rollback_button is not None
assert window.privacy_focus_checkbox.isChecked()
assert {s.key().toString() for s in window._shortcuts} == {
    'Ctrl+G', 'Ctrl+Shift+C', 'Ctrl+H',
    'Ctrl+1', 'Ctrl+2', 'Ctrl+3', 'Ctrl+4',
}

window._advanced_rules = {
    'min_digits': 3, 'min_symbols': 2, 'excluded_chars': '!@#'
}
for _ in range(12):
    window.generate()
    secret = window.output.text()
    assert len(secret) == window.length.value()
    assert sum(ch.isdigit() for ch in secret) >= 3
    assert sum(ch in SYMBOLS for ch in secret) >= 2
    assert not any(ch in '!@#' for ch in secret)
assert window._last_entropy_bits > 0
with mock.patch.object(QMessageBox, 'information') as inform:
    window.show_security_analysis()
    assert inform.called
    assert 'Bit' in inform.call_args.args[2]

window.show_button.setChecked(True)
assert window.output.echoMode() == window.output.EchoMode.Normal
window.changeEvent(QEvent(QEvent.Type.WindowDeactivate))
assert not window.show_button.isChecked()
window.privacy_focus_checkbox.setChecked(False)
window.show_button.setChecked(True)
window.changeEvent(QEvent(QEvent.Type.WindowDeactivate))
assert window.show_button.isChecked()
window.show_button.setChecked(False)

window.switch_mode(True)
assert window.phrase_language.isEnabled()
assert not window.rules_button.isVisible()
idx = window.phrase_language.findData('en')
window.phrase_language.setCurrentIndex(idx)
words = {a + b for a in PHRASE_FIRST_EN for b in PHRASE_LAST_EN}
window.generate()
assert all(word in words for word in window.output.text().split('-'))
assert settings.value('passphrase/language') == 'en'
window.switch_mode(False)

window.tabs.setCurrentIndex(1)
assert window.privacy_focus_checkbox.isVisible()
assert window.history_confirm_checkbox.isVisible()
assert window.security_card.isAncestorOf(window.privacy_focus_checkbox)
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
assert window.privacy_focus_checkbox.text() == 'Hide password when switching windows'
assert window.history_confirm_checkbox.text() == 'Confirm before opening password history'
window.tabs.setCurrentIndex(0)
assert window.rules_button.text().endswith('Advanced rules')
window.tabs.setCurrentIndex(2)
assert 'Restore previous version' in window.rollback_button.text()
window.close()

for key, value in saved.items():
    if value is None:
        settings.remove(key)
    else:
        settings.setValue(key, value)
settings.sync()
print('Advanced rules, two passphrase languages, analysis, shortcuts, privacy, rollback UI OK')
