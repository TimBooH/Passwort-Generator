"""Offline Qt regressions for safe clipboard cleanup on application exit."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


@unittest.skipUnless(importlib.util.find_spec('PySide6'), 'PySide6 ist nicht installiert')
class ClipboardExitUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.environment = mock.patch.dict(os.environ, {
            'HOME': cls.temp.name,
            'XDG_CONFIG_HOME': str(Path(cls.temp.name) / 'config'),
            'XDG_DATA_HOME': str(Path(cls.temp.name) / 'data'),
            'QT_QPA_PLATFORM': 'offscreen',
        })
        cls.environment.start()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.addClassCleanup(cls.environment.stop)
        import main
        cls.main = main
        cls.app = main.QApplication.instance() or main.QApplication([])
        if cls.app.platformName() != 'offscreen':
            raise RuntimeError('Clipboard-Tests erfordern die Offscreen-Plattform')

    def assert_temporary_settings(self, settings):
        settings_path = Path(settings.fileName()).resolve()
        if not settings_path.is_relative_to(Path(self.temp.name).resolve()):
            self.fail(f'Unsicherer QSettings-Pfad außerhalb des Temp-Verzeichnisses: {settings_path}')

    def setUp(self):
        settings_class = self.main.QSettings

        def checked_settings(*args, **kwargs):
            # An explicit file avoids Qt's process-wide native config-path cache,
            # which would otherwise affect subsequent UI test classes.
            settings = settings_class(
                str(Path(self.temp.name) / 'clipboard-exit.ini'),
                settings_class.Format.IniFormat,
            )
            self.assert_temporary_settings(settings)
            return settings

        # Check before even the window constructor can write or remove settings.
        with mock.patch.object(self.main, 'QSettings', side_effect=checked_settings):
            self.window = self.main.PasswordWindow(auto_check=False)
        self.addCleanup(self.window.close)
        self.assert_temporary_settings(self.window.settings)
        self.window.settings.clear()
        self.window.clear_clipboard_checkbox.setChecked(True)
        self.clipboard = self.app.clipboard()
        self.addCleanup(self.clipboard.clear)
        self.window.output.setText('exit-test-password')
        self.window.copy()
        self.assertTrue(self.window.clipboard_timer.isActive())

    def test_close_clears_own_password(self):
        self.assertTrue(self.window.close())
        self.assertEqual(self.clipboard.text(), '')
        self.assertIsNone(self.window._clipboard_secret)
        self.assertFalse(self.window.clipboard_timer.isActive())

    def test_close_preserves_newer_clipboard_content(self):
        self.clipboard.setText('newer user content')
        self.window.close()
        self.assertEqual(self.clipboard.text(), 'newer user content')

    def test_close_preserves_password_when_auto_clear_disabled(self):
        self.window.clear_clipboard_checkbox.setChecked(False)
        self.window.output.setText('disabled-password')
        self.window.copy()
        self.window.close()
        self.assertEqual(self.clipboard.text(), 'disabled-password')

    def test_about_to_quit_clears_without_close_and_is_idempotent(self):
        with mock.patch.object(self.window, '_set_ui') as status_update:
            self.app.aboutToQuit.emit()
            self.assertEqual(self.clipboard.text(), '')
            self.assertIsNone(self.window._clipboard_secret)
            self.assertFalse(self.window.clipboard_timer.isActive())
            self.clipboard.setText('newer user content')
            self.window.clear_clipboard_on_exit()
            self.window.clear_clipboard_on_exit()
            self.window.close()
            self.window.clear_clipboard_on_exit()
            self.app.aboutToQuit.emit()
            self.assertEqual(self.clipboard.text(), 'newer user content')
            status_update.assert_not_called()

    def test_exit_method_preserves_newer_content(self):
        self.clipboard.setText('newer user content')
        self.window.clear_clipboard_on_exit()
        self.assertEqual(self.clipboard.text(), 'newer user content')

    def test_exit_method_preserves_password_when_auto_clear_disabled(self):
        self.window.clear_clipboard_checkbox.setChecked(False)
        self.window.output.setText('disabled-password')
        self.window.copy()
        self.window.clear_clipboard_on_exit()
        self.assertEqual(self.clipboard.text(), 'disabled-password')
