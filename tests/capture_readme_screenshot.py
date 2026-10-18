"""Capture the *running* PasswortGenerator Qt window on a Linux CI runner.

This is a real QMainWindow.grab() screenshot, not an illustration or mockup.
Settings are isolated from users. The shown sample password is generated fresh
in CI, is not used as a credential, and is never saved by the application.
Network checks and update popups are disabled for a reproducible capture.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='passwort-readme-config-')

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QLineEdit
from main import PasswordWindow
from version import APP_VERSION

settings = QSettings('TimBooH', 'PasswortGenerator')
settings.setValue('ui/language', 'de')
app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(1120, 790)
window.show()
window.tabs.setCurrentIndex(0)

# Use an actual app appearance preset rather than digitally drawing a UI.
theme_index = window.scheme_combo.findData('glass_dark')
assert theme_index >= 0, 'Glass Dark must exist as a real application theme.'
window.scheme_combo.setCurrentIndex(theme_index)

# Generate a one-use demonstration password through the application itself.
# Showing it makes the real strength indicator and new compact button visible.
window.generate()
assert window.output.text()
window.show_button.setChecked(True)
for _ in range(10):
    app.processEvents()

assert window.nav_container.isVisible()
assert window.info_nav_button.isVisible()
assert window.nav_buttons[0].isChecked()
assert window.nav_buttons[0].x() > 0
assert window.output.echoMode() == QLineEdit.EchoMode.Normal
assert window.strength_bar.value() > 0
assert window.generate_button.isVisible()
assert window.generate_button.objectName() == 'generatePasswordButton'
assert window.generate_button.width() <= 360
assert window.generate_button.height() <= 40
assert window.language == 'de'

# Render actual Qt widgets directly; no image synthesis or image editing.
image = window.grab()
assert not image.isNull() and image.width() >= 1000 and image.height() >= 720
filename = Path('readme-screenshot.png')
assert image.save(str(filename), 'PNG')
assert filename.stat().st_size > 10_000

window.close()
app.processEvents()
print(
    f'ORIGINAL LINUX QT SCREENSHOT CREATED: {filename}, '
    f'PasswortGenerator v{APP_VERSION}, '
    f'{image.width()}x{image.height()}, {filename.stat().st_size} bytes'
)
