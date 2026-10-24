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

# Genuine Qt app capture with the sole fixed reference design.
assert window.background_surface._ocean_enabled
assert not hasattr(window, 'appearance_card')
assert not hasattr(window, 'scheme_combo')
assert not window.background_surface.has_background_image()

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
assert window.generate_button.width() >= 600
print(f'CTA metrics: width={window.generate_button.width()}, height={window.generate_button.height()}')
assert 40 <= window.generate_button.height() <= 60
assert window.ocean_sections.height() <= 276
assert window.output.height() >= 54
assert not window.ocean_hero_icon.pixmap().isNull()
assert window.font().family() == 'Carlito'
assert all(not b.icon().isNull() for b in window.nav_buttons + [window.info_nav_button])
assert not window.copy_top_button.icon().isNull()
assert not window.regenerate_button.icon().isNull()
assert window.ocean_options_panel.isVisible()
assert window.ocean_length_panel.isVisible()
assert window.check_layout.verticalSpacing() >= 10
assert all(c.isChecked() for c in (window.upper, window.lower, window.digits, window.symbols))
assert 'QCheckBox::indicator:checked' in window.styleSheet()
assert 'checked.png' in window.styleSheet()
assert window.ocean_hero_icon.isVisible()
assert window.ocean_page_title.isVisible()
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

