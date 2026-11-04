"""GUI integration test for download -> previous AppImage -> automatic restart."""

import atexit
import hashlib
import os
import tempfile
from pathlib import Path
from unittest import mock

_settings_temp = tempfile.TemporaryDirectory()
atexit.register(_settings_temp.cleanup)
os.environ['HOME'] = _settings_temp.name
os.environ['XDG_CONFIG_HOME'] = str(Path(_settings_temp.name) / 'config')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QIODevice, QSaveFile, QSettings
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                  os.environ['XDG_CONFIG_HOME'])

import main
from main import PasswordWindow
from updater import PREVIOUS_NAME, staging_path


class FakeReply:
    def __init__(self):
        self.deleted = False

    def error(self):
        return QNetworkReply.NetworkError.NoError

    def readAll(self):
        return b''

    def deleteLater(self):
        self.deleted = True


app = QApplication([])
app.setStyle('Fusion')
def checked_settings(*args, **kwargs):
    settings = QSettings(*args, **kwargs)
    assert Path(settings.fileName()).resolve().is_relative_to(
        Path(_settings_temp.name).resolve()
    ), 'QSettings muss im Temp-Verzeichnis liegen'
    return settings


# Check before PasswordWindow performs its first settings write/removal.
with mock.patch.object(main, 'QSettings', side_effect=checked_settings):
    window = PasswordWindow(auto_check=False)
assert Path(window.settings.fileName()).resolve().is_relative_to(
    Path(_settings_temp.name).resolve()
), 'QSettings muss im Temp-Verzeichnis liegen'
window.show()
app.processEvents()
assert window.tab_names[2] == 'Update'
window.tabs.setCurrentIndex(2)
app.processEvents()
assert window.check_button.isVisible(), 'Update controls must be on the Updates tab'
assert window.progress_bar.parentWidget() is not None

with tempfile.TemporaryDirectory() as temp:
    folder = Path(temp)
    current = folder / 'PasswortGenerator.AppImage'
    previous = folder / PREVIOUS_NAME
    current.write_bytes(b'\x7fELFOLD-BINARY')
    current.chmod(0o755)
    payload = b'\x7fELFNEW-VERIFIED-APPIMAGE'
    stage = staging_path(current)
    stream = QSaveFile(str(stage))
    assert stream.open(QIODevice.OpenModeFlag.WriteOnly)
    assert stream.write(payload) == len(payload)

    window.download_reply = FakeReply()
    reply = window.download_reply
    window.save_file = stream
    window.download_installed = True
    window.download_target = current
    window.download_stage = stage
    window.download_error = None
    window.download_bytes = len(payload)
    window.download_hash = hashlib.sha256(payload)
    window.latest_version = 'v1.5.0'
    window.latest_asset = {
        'size': len(payload),
        'digest': 'sha256:' + hashlib.sha256(payload).hexdigest(),
    }

    window._download_channel = window.update_channel
    window._download_version = window.latest_version
    window._download_asset = dict(window.latest_asset)
    window.latest_asset = None
    window.channel_combo.setEnabled(False)

    with mock.patch('main.restart_updated_app') as restart:
        window.download_finished()
        restart.assert_called_once_with(current)
    assert reply.deleted
    assert window.channel_combo.isEnabled()
    assert current.read_bytes() == payload
    assert previous.read_bytes() == b'\x7fELFOLD-BINARY'
    assert current.stat().st_mode & 0o111
    assert not stage.exists()

    # A broken update must leave the running version and its backup untouched.
    bad_stage = staging_path(current)
    bad_file = QSaveFile(str(bad_stage))
    assert bad_file.open(QIODevice.OpenModeFlag.WriteOnly)
    assert bad_file.write(b'\x7fELFBAD') > 0
    window.save_file = bad_file
    window.download_reply = FakeReply()
    window.download_installed = True
    window.download_target = current
    window.download_stage = bad_stage
    window.download_error = None
    window.download_bytes = 999  # Deliberately does not match release size.
    window.download_hash = hashlib.sha256(b'broken')

    window._download_channel = window.update_channel
    window._download_version = 'failed-download'
    window._download_asset = {'size': len(payload)}
    window.channel_combo.setEnabled(False)

    with mock.patch('main.restart_updated_app') as restart, \
            mock.patch('main.QMessageBox.warning') as warning:
        window.download_finished()
        restart.assert_not_called()
        warning.assert_called_once()
    assert current.read_bytes() == payload
    assert previous.read_bytes() == b'\x7fELFOLD-BINARY'
    assert not bad_stage.exists()
    assert window.channel_combo.isEnabled()

window.close()
app.processEvents()
print('GUI update integration passed: checksum, previous backup, relaunch, failed-download rollback.')
