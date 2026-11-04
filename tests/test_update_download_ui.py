"""Offline Qt regressions for a channel-safe update download lifecycle."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


@unittest.skipUnless(importlib.util.find_spec('PySide6'), 'PySide6 ist nicht installiert')
class UpdateDownloadUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.environment = mock.patch.dict(os.environ, {
            'HOME': cls.temp.name,
            'XDG_CONFIG_HOME': str(Path(cls.temp.name) / 'config'),
            'QT_QPA_PLATFORM': 'offscreen',
        })
        cls.environment.start()
        # Import only after redirecting paths; main defines installation paths at import.
        import main
        cls.main = main
        cls.app = main.QApplication.instance() or main.QApplication([])
        cls.main.QSettings.setDefaultFormat(cls.main.QSettings.Format.IniFormat)
        cls.main.QSettings.setPath(
            cls.main.QSettings.Format.IniFormat,
            cls.main.QSettings.Scope.UserScope,
            str(Path(cls.temp.name) / 'config'),
        )

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.files = tempfile.TemporaryDirectory(dir=self.temp.name)
        self.addCleanup(self.files.cleanup)
        self.folder = Path(self.files.name)
        main = self.main
        settings_class = main.QSettings

        def checked_settings(*args, **kwargs):
            # The organization/application overload always uses NativeFormat.
            # An explicit INI filename also isolates settings on Windows.
            settings = settings_class(
                str(self.folder / 'download.ini'), settings_class.Format.IniFormat
            )
            self.assert_temporary_settings(settings)
            return settings

        # Validate before the constructor can remove or write any settings.
        with mock.patch.object(main, 'QSettings', side_effect=checked_settings):
            self.window = main.PasswordWindow(auto_check=False)
        self.addCleanup(self.window.close)
        self.assert_temporary_settings(self.window.settings)
        self.window.settings.clear()
        self.assert_temporary_settings(self.window.settings)
        self.window.settings.setValue('updates/channel', 'stable')
        self.window.update_channel = 'stable'
        blocked = self.window.channel_combo.blockSignals(True)
        self.window.channel_combo.setCurrentIndex(self.window.channel_combo.findData('stable'))
        self.window.channel_combo.blockSignals(blocked)
        self.window.reporter = mock.Mock()
        self.payload = b'\x7fELF' + bytes(100000)
        self.asset = {
            'name': main.WINDOWS_INSTALLER_NAME,
            'size': len(self.payload),
            'digest': 'sha256:' + hashlib.sha256(self.payload).hexdigest(),
            'browser_download_url': 'https://example.invalid/update',
        }
        self.window.latest_asset = self.asset
        self.window.latest_version = 'snapshot-version'
        self.reply = mock.Mock()
        self.reply.error.return_value = main.QNetworkReply.NetworkError.NoError
        self.reply.readAll.side_effect = [self.payload, b'']
        self.window.network = mock.Mock()
        self.window.network.get.return_value = self.reply
        patches = [
            mock.patch.object(main, 'INSTALLED_APPIMAGE', self.folder / 'installed.AppImage'),
            mock.patch.object(main, 'UNSTABLE_APPIMAGE', self.folder / 'unstable.AppImage'),
            mock.patch.object(main.QStandardPaths, 'writableLocation', return_value=str(self.folder)),
            mock.patch.object(main.QMessageBox, 'warning'),
            mock.patch.object(main.QMessageBox, 'question', return_value=main.QMessageBox.StandardButton.Yes),
            mock.patch.object(main, 'persist_installed_update_channel'),
            mock.patch.object(main, 'restart_updated_app'),
            mock.patch.object(main, 'start_verified_windows_installer'),
            mock.patch.object(main.QTimer, 'singleShot'),
            mock.patch.object(main, 'os', SimpleNamespace(
                name='posix', access=os.access, W_OK=os.W_OK, chmod=os.chmod,
            )),
        ]
        self.mocks = [self.enterContext(patch) for patch in patches]

    def assert_temporary_settings(self, settings):
        settings_path = Path(settings.fileName()).resolve()
        if not settings_path.is_relative_to(Path(self.temp.name).resolve()):
            self.fail(f'Unsicherer QSettings-Pfad außerhalb des Temp-Verzeichnisses: {settings_path}')

    def test_save_file_open_failure_clears_snapshot(self):
        with mock.patch.object(self.main, 'QSaveFile') as save_file:
            save_file.return_value.open.return_value = False
            save_file.return_value.errorString.return_value = 'mock open failure'
            self.window.download_update()
        self.assertIsNone(self.window._download_channel)
        self.assertIsNone(self.window._download_asset)
        self.assertIsNone(self.window._download_version)
        self.assertIsNone(self.window.download_reply)
        self.assertTrue(self.window.channel_combo.isEnabled())
        self.window.network.get.assert_not_called()
        self.mocks[3].assert_called_once()

    def start_download(self):
        self.window.download_update()
        self.assertIs(self.window.download_reply, self.reply)
        self.assertFalse(self.window.channel_combo.isEnabled())
        self.assertEqual(self.window._download_asset, self.asset)
        self.assertIsNot(self.window._download_asset, self.asset)

    def test_success_uses_snapshot_even_when_latest_asset_is_none(self):
        self.start_download()
        self.asset['size'] = -1
        self.asset['digest'] = 'changed'
        self.window.latest_asset = None
        self.window.latest_version = 'changed-version'
        self.window.update_channel = 'unstable'  # Simulate an unrelated state mutation.
        self.window.read_download_data()
        self.window.download_finished()
        self.mocks[5].assert_called_once_with('stable')
        self.assertEqual(self.window.settings.value('updates/channel'), 'stable')
        self.assertIn('snapshot-version', self.window.update_status.text())
        self.assertIn('snapshot-version', self.window.reporter.note.call_args_list[1].args[1])
        self.mocks[3].assert_not_called()
        self.assertEqual(self.window.download_target.read_bytes(), self.payload)
        self.assertTrue(self.window.channel_combo.isEnabled())
        self.assertIsNone(self.window.download_reply)
        self.reply.deleteLater.assert_called_once()

    def test_channel_switch_is_rejected_without_settings_or_asset_changes(self):
        self.start_download()
        with mock.patch.object(self.window.settings, 'setValue') as write:
            self.window.channel_combo.setCurrentIndex(self.window.channel_combo.findData('unstable'))
            self.assertEqual(self.window.channel_combo.currentData(), 'stable')
            self.assertEqual(self.window.update_channel, 'stable')
            self.assertEqual(self.window.settings.value('updates/channel'), 'stable')
            self.assertIs(self.window.latest_asset, self.asset)
            write.assert_not_called()
        self.assertFalse(self.window.channel_combo.signalsBlocked())
        self.assertEqual(self.window.network.get.call_count, 1)
        self.window.download_finished()

    def test_failures_release_combo_and_hide_progress(self):
        for failure in ('network', 'size', 'digest', 'read'):
            with self.subTest(failure=failure):
                self.reply.readAll.side_effect = [self.payload, b'']
                self.reply.error.return_value = self.main.QNetworkReply.NetworkError.NoError
                self.start_download()
                if failure == 'network':
                    self.reply.error.return_value = self.main.QNetworkReply.NetworkError.ConnectionRefusedError
                    self.reply.errorString.return_value = 'mock network error'
                elif failure == 'size':
                    self.window._download_asset['size'] += 1
                elif failure == 'digest':
                    self.window._download_asset['digest'] = 'sha256:' + '0' * 64
                else:
                    self.reply.readAll.side_effect = OSError('mock read failure')
                self.window.download_finished()
                self.assertTrue(self.window.channel_combo.isEnabled())
                self.assertTrue(self.window.progress_bar.isHidden())
                self.assertIsNone(self.window.download_reply)
                self.assertIsNone(self.window.save_file)
        self.assertEqual(self.mocks[3].call_count, 4)
        self.mocks[5].assert_not_called()
        self.mocks[6].assert_not_called()

    def test_other_operations_keep_combo_locked_until_they_finish(self):
        for operation in ('check_reply', '_rollback_reply'):
            with self.subTest(operation=operation):
                self.reply.readAll.side_effect = [self.payload, b'']
                self.start_download()
                setattr(self.window, operation, object())
                self.window.download_finished()
                self.assertFalse(self.window.channel_combo.isEnabled())
                setattr(self.window, operation, None)
                self.window._refresh_update_channel_enabled()
                self.assertTrue(self.window.channel_combo.isEnabled())

    def test_windows_rollback_download_has_same_lock_and_snapshot(self):
        main = self.main
        tag = 'v0.01.0'
        asset = dict(self.asset, browser_download_url=(
            main.RELEASE_DOWNLOAD_PREFIX + tag + '/' + main.WINDOWS_INSTALLER_NAME
        ))
        metadata = mock.Mock()
        metadata.error.return_value = main.QNetworkReply.NetworkError.NoError
        metadata.readAll.return_value = json.dumps({'tag_name': tag, 'assets': [asset]}).encode()
        self.window._rollback_reply = metadata
        self.window._rollback_tag = tag
        self.window.channel_combo.setEnabled(False)
        with mock.patch.object(main, 'os', SimpleNamespace(name='nt')):
            self.window.rollback_release_finished()
            self.assertTrue(self.window._rollback_pending)
            self.assertFalse(self.window.channel_combo.isEnabled())
            self.assertEqual(self.window._download_version, tag)
            self.window.latest_asset = None
            self.window.latest_version = 'changed'
            self.window.download_finished()
        self.mocks[7].assert_called_once_with(self.window.download_target, rollback=True)
        self.mocks[5].assert_called_once_with('stable')
        self.assertTrue(self.window.channel_combo.isEnabled())
        self.assertFalse(self.window._rollback_pending)

    def test_rollback_metadata_error_releases_combo(self):
        reply = mock.Mock()
        reply.error.return_value = self.main.QNetworkReply.NetworkError.ConnectionRefusedError
        reply.errorString.return_value = 'mock rollback error'
        self.window._rollback_reply = reply
        self.window.channel_combo.setEnabled(False)
        self.window.rollback_release_finished()
        self.assertTrue(self.window.channel_combo.isEnabled())
        self.assertFalse(self.window._rollback_pending)
