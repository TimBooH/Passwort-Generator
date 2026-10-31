"""Capture a genuine settings screenshot to verify visible Security switches."""
import os
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='passwort-switch-preview-')
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from main import PasswordWindow

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(730, 830)
window.show()
window.show_settings_dialog('general')
app.processEvents()
window.clear_clipboard_checkbox.setChecked(True)
window.privacy_focus_checkbox.setChecked(False)
window.history_confirm_checkbox.setChecked(True)
for _ in range(7):
    app.processEvents()
assert window.security_card.isVisible()
assert all(x.isVisible() for x in (
    window.clear_clipboard_checkbox,
    window.privacy_focus_checkbox,
    window.history_confirm_checkbox,
))
assert 'switch-on.png' in window.styleSheet()
assert 'switch-off.png' in window.styleSheet()
assert window._settings_dialog is not None and window._settings_views.currentIndex() == 0
image = window._settings_dialog.grab()
output = Path('settings-switches.png')
assert image.save(str(output), 'PNG') and output.stat().st_size > 10000
window._settings_dialog.close()
window.close()
print('Genuine Settings switches screenshot:', output)
