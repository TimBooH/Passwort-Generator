"""Verify window position and size survive a real close/reopen cycle.

Runs without network or startup onboarding on Linux and Windows. The settings
location is isolated so CI cannot alter anyone's desktop preferences.
"""

import os
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QByteArray, QPoint, QSettings, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')

with tempfile.TemporaryDirectory(prefix='passwort-window-geometry-') as directory:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory
    )
    saved = QSettings('TimBooH', 'PasswortGenerator')
    saved.clear()
    saved.sync()

    first = PasswordWindow(auto_check=False)
    first.show()
    first.resize(700, 700)
    first.move(32, 38)
    for _ in range(4):
        app.processEvents()

    original_size = first.size()
    original_position = first.pos()
    assert original_size.width() == 700 and original_size.height() == 700
    first.generate()
    secret = first.output.text()
    assert secret
    first.close()
    app.processEvents()
    saved.sync()
    geometry = saved.value('window/geometry')
    assert isinstance(geometry, QByteArray)
    assert not geometry.isEmpty()
    assert secret not in str(saved.allKeys())

    second = PasswordWindow(auto_check=False)
    second.show()
    for _ in range(5):
        app.processEvents()
    assert second.size() == original_size, (
        f'Window size not restored: {original_size} vs {second.size()}'
    )
    pos = second.pos()
    assert abs(pos.x() - original_position.x()) <= 12, (
        f'X-position changed: {original_position} -> {pos}'
    )
    assert abs(pos.y() - original_position.y()) <= 12, (
        f'Y-position changed: {original_position} -> {pos}'
    )
    assert second.output.text() == '', 'Passwords must not be persisted'
    second.close()
    app.processEvents()

print('Restored exact window size and prior position after restart; no saved secrets.')
