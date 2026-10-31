"""Capture the real approved Compact Ocean PySide6 main-window UI in CI.

Pure Qt QMainWindow.grab(), no generated illustration, isolated preferences.
"""
import os
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['XDG_CONFIG_HOME']=tempfile.mkdtemp(prefix='compact-readme-')
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLineEdit
from main import PasswordWindow
from version import APP_VERSION

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
settings=QSettings('TimBooH','PasswortGenerator')
settings.setValue('ui/language','de')
app=QApplication([])
app.setStyle('Fusion')
window=PasswordWindow(auto_check=False)
window.resize(730,830)
window.show()
window.tabs.setCurrentIndex(0)
window.generate()
window.show_button.setChecked(True)
for _ in range(10): app.processEvents()

assert window.background_surface._ocean_enabled
assert not window.background_surface.has_background_image()
assert not hasattr(window,'appearance_card')
assert window.output.text() and window.output.echoMode()==QLineEdit.EchoMode.Normal
assert window.strength_bar.value()>0
assert window.password_output_card.isVisible()
assert window.ocean_options_panel.isVisible()
assert window.ocean_length_panel.isVisible()
assert all(b.isVisible() for b in window._compact_nav_buttons)
assert [b.text() for b in window._compact_nav_buttons]==[
    'Passwort','Passphrase','Verlauf','Einstellungen'
]
assert not window.info_nav_button.isVisible()
assert not window.nav_buttons[2].isVisible()
assert not window.status.isVisible()
assert window.generate_button.isVisible()
assert window.generate_button.width()>=480
assert window.generate_button.height()>=55
assert window.check_layout.verticalSpacing()>=5
assert not window.rules_button.isVisible()
assert not window.ocean_preset_box.isVisible()
assert window.ocean_output_caption.isVisible()
assert 'QFrame#passwordOutputCard' in window.styleSheet()
image=window.grab()
assert not image.isNull() and image.width()>=700 and image.height()>=770
filename=Path('readme-screenshot.png')
assert image.save(str(filename),'PNG')
assert filename.stat().st_size>10000
window.close()
app.processEvents()
print(f'COMPACT OCEAN REAL QT SCREENSHOT: {image.width()}x{image.height()}, {filename.stat().st_size} bytes')
