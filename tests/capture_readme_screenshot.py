"""Capture a real screenshot of the running Linux/Qt UI for README.md.

CI runs this in its own process so screenshot settings cannot affect tests.
No password is shown unmasked or stored in the generated PNG.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='passwort-readme-config-')

from PySide6.QtWidgets import QApplication
from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(1040, 780)
window.show()
window.tabs.setCurrentIndex(0)
for _ in range(5):
    app.processEvents()
assert window.nav_container.isVisible()
assert window.info_nav_button.isVisible()
assert window.nav_buttons[0].isChecked()
assert window.nav_buttons[0].x() > 0
assert window.output.echoMode() == window.output.EchoMode.Password
image = window.grab()
assert not image.isNull() and image.width() >= 900 and image.height() >= 680
filename = Path('readme-screenshot.png')
assert image.save(str(filename), 'PNG')
assert filename.stat().st_size > 8_000
window.close()
app.processEvents()
print(f'Real screenshot created: {filename}, {image.width()}x{image.height()}, '
      f'{filename.stat().st_size} bytes')
