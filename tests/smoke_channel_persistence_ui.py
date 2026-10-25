"""Regression: choosing Unstable survives the cross-installation restart.

Stable and Unstable have separate QSettings namespaces; preserve only the
explicitly selected update channel across the binary handoff, leaving private
settings isolated.
"""
import os
import tempfile
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from main import PasswordWindow, persist_installed_update_channel

app = QApplication([])
app.setStyle('Fusion')
with tempfile.TemporaryDirectory(prefix='password-channel-test-') as directory:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, directory)

    stable_store = QSettings('TimBooH', 'PasswortGenerator')
    unstable_store = QSettings('TimBooH', 'PasswortGenerator-Unstable')
    stable_store.setValue('updates/channel', 'stable')
    unstable_store.setValue('updates/channel', 'stable')  # stale old setting
    stable_store.setValue('ui/language', 'en')
    unstable_store.setValue('ui/language', 'de')
    stable_store.sync()
    unstable_store.sync()

    with mock.patch.object(PasswordWindow, 'check_for_updates'):
        # Select Unstable inside Stable and download the separate test build.
        with mock.patch('main.CHANNEL', 'stable'):
            stable = PasswordWindow(auto_check=False)
            assert stable.update_channel == 'stable'
            stable.channel_combo.setCurrentIndex(
                stable.channel_combo.findData('unstable'))
            assert stable.update_channel == 'unstable'
            assert stable.settings.value('updates/channel') == 'unstable'
            assert stable.settings.status() == QSettings.Status.NoError
            # Called by verified installer/download handoff after file.commit.
            persist_installed_update_channel('unstable')
            stable.close()

        # The newly installed Unstable app loads its OWN settings namespace.
        # It must not revert to the outdated 'stable' entry stored there.
        with mock.patch('main.CHANNEL', 'unstable'):
            preview = PasswordWindow(auto_check=False)
            assert preview.settings.applicationName() == 'PasswortGenerator-Unstable'
            assert preview.update_channel == 'unstable'
            assert preview.channel_combo.currentData() == 'unstable'
            assert preview.language == 'de'  # keep independent preferences
            preview.close()
            preview_reopened = PasswordWindow(auto_check=False)
            assert preview_reopened.update_channel == 'unstable'
            assert preview_reopened.channel_combo.currentData() == 'unstable'
            preview_reopened.close()

        # Switching back to Stable hands only that chosen channel to Stable.
        with mock.patch('main.CHANNEL', 'unstable'):
            preview = PasswordWindow(auto_check=False)
            preview.channel_combo.setCurrentIndex(
                preview.channel_combo.findData('stable'))
            assert preview.update_channel == 'stable'
            persist_installed_update_channel('stable')
            preview.close()

        with mock.patch('main.CHANNEL', 'stable'):
            returned = PasswordWindow(auto_check=False)
            assert returned.update_channel == 'stable'
            assert returned.channel_combo.currentData() == 'stable'
            assert returned.language == 'en'  # stable preferences not lost
            returned.close()

    # Never alter the other app's language or security settings.
    assert QSettings('TimBooH', 'PasswortGenerator').value('ui/language') == 'en'
    assert QSettings('TimBooH', 'PasswortGenerator-Unstable').value('ui/language') == 'de'
    for channel in ('nightly', '../other', ''):
        with mock.patch('main.QMessageBox.warning'):
            try:
                persist_installed_update_channel(channel)
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid channel accepted: ' + channel)

print('Stable to Unstable and back: selected channel persists across restart.')
