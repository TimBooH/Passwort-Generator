"""Offscreen regression: every selectable checkbox is a visual switch.

Verify actual painted states, not merely the existence of CSS fragments. The
test runs in both languages and checks Password, Passphrase and Settings.
"""
import os
import tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='passwort-switch-test-')

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QCheckBox
from main import PasswordWindow

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(1120, 790)
window.show()
app.processEvents()

checkboxes = window.findChildren(QCheckBox)
expected = [
    window.upper, window.lower, window.digits, window.symbols, window.exclude,
    window.phrase_two_digits, window.clear_clipboard_checkbox,
    window.privacy_focus_checkbox, window.history_confirm_checkbox,
]
assert len(checkboxes) == len(expected) == 9, [
    widget.objectName() or widget.text() for widget in checkboxes
]
assert set(checkboxes) == set(expected)
css = window.styleSheet()
assert 'QCheckBox::indicator:checked' in css
assert 'switch-on.png' in css and 'switch-off.png' in css
# Generic stylesheet's old square checkbox used "image: none;".
# The *final* override must explicitly provide ON/OFF switch images.
assert css.rfind('image: url(') > css.rfind('image: none;')

for language in ('de', 'en'):
    window.language_combo.setCurrentIndex(window.language_combo.findData(language))
    for page, control in [
        (0, window.upper), (0, window.lower), (0, window.digits),
        (0, window.symbols), (0, window.exclude),
        (0, window.phrase_two_digits), (1, window.clear_clipboard_checkbox),
        (1, window.privacy_focus_checkbox), (1, window.history_confirm_checkbox),
    ]:
        window.tabs.setCurrentIndex(page)
        if control is window.phrase_two_digits:
            window.switch_mode(True)
        else:
            window.switch_mode(False)
        app.processEvents()
        assert control.isVisible(), control.objectName()
        original = control.isChecked()
        control.setChecked(False)
        app.processEvents()
        off = control.grab().toImage()
        control.setChecked(True)
        app.processEvents()
        on = control.grab().toImage()
        assert not off.isNull() and not on.isNull()
        assert off.size() == on.size()
        # Painting in the left-most switch-indicator area must change.
        diff = sum(
            off.pixel(x, y) != on.pixel(x, y)
            for x in range(min(32, off.width()))
            for y in range(min(26, off.height()))
        )
        assert diff > 12, (control.objectName(), language, diff)
        control.setChecked(original)

# The settings switches must remain functional, not just decorative.
window.tabs.setCurrentIndex(1)
window.clear_clipboard_checkbox.setChecked(False)
assert not window.clipboard_timeout_combo.isEnabled()
window.clear_clipboard_checkbox.setChecked(True)
assert window.clipboard_timeout_combo.isEnabled()

window.close()
print('9 compact switches: Password/Passphrase/Settings ON/OFF rendering and settings behavior OK')
