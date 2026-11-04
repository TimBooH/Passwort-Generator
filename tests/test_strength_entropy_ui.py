"""Offline Qt checks for exact single/batch password strength."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


@unittest.skipUnless(importlib.util.find_spec('PySide6'), 'PySide6 ist nicht installiert')
class StrengthEntropyUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        environment = mock.patch.dict(os.environ, {
            'HOME': cls.temp.name,
            'XDG_CONFIG_HOME': str(Path(cls.temp.name) / 'config'),
            'XDG_DATA_HOME': str(Path(cls.temp.name) / 'data'),
            'QT_QPA_PLATFORM': 'offscreen',
        })
        environment.start()
        cls.addClassCleanup(environment.stop)
        import main
        cls.main = main
        cls.app = main.QApplication.instance() or main.QApplication([])
        if cls.app.platformName() != 'offscreen':
            raise RuntimeError('Entropie-Tests erfordern die Offscreen-Plattform')

    def setUp(self):
        folder = tempfile.TemporaryDirectory(dir=self.temp.name)
        self.addCleanup(folder.cleanup)
        settings_class = self.main.QSettings
        root = Path(folder.name).resolve()

        class CheckedSettings(settings_class):
            def __init__(self, *args, **kwargs):
                super().__init__(str(root / 'strength.ini'), settings_class.Format.IniFormat)
                self.check_path()

            def check_path(self):
                if not Path(self.fileName()).resolve().is_relative_to(root):
                    raise AssertionError('Unsicherer QSettings-Pfad außerhalb des Temp-Verzeichnisses')

            def setValue(self, *args):
                self.check_path()
                return super().setValue(*args)

            def remove(self, *args):
                self.check_path()
                return super().remove(*args)

            def clear(self):
                self.check_path()
                return super().clear()

            def sync(self):
                self.check_path()
                return super().sync()

        with mock.patch.object(self.main, 'QSettings', CheckedSettings):
            self.window = self.main.PasswordWindow(auto_check=False)
        self.addCleanup(self.window.close)
        self.window.settings.clear()
        self.window.length.setValue(10)
        for control in (self.window.lower, self.window.upper, self.window.digits, self.window.symbols):
            control.setChecked(True)
        self.window.exclude.setChecked(False)
        self.window._advanced_rules = dict(min_digits=4, min_symbols=4, excluded_chars='')

    def assert_exact_strength(self):
        self.assertAlmostEqual(self.window._last_entropy_bits, 52.88, delta=0.01)
        self.assertEqual(self.window.strength_label.text(), '🛡  Stärke: Mittel')
        self.assertEqual(self.window.ocean_strength_value.text(), 'Mittel')
        self.assertEqual(self.window.strength_bar.value(), 50)
        with mock.patch.object(self.main.QMessageBox, 'information') as information:
            self.window.show_security_analysis()
        self.assertIn('Geschätzte Entropie: 52.9 Bit', information.call_args.args[2])

    def test_generate_single_uses_exact_entropy(self):
        self.window.batch_count_combo.setCurrentIndex(self.window.batch_count_combo.findData(1))
        self.window.generate()
        self.assertEqual(len(self.window.output.text()), 10)
        self.assert_exact_strength()

    def test_batch_selection_uses_same_entropy(self):
        self.window.batch_count_combo.setCurrentIndex(self.window.batch_count_combo.findData(5))
        self.window.generate()
        self.assertEqual(len(self.window._current_batch), 5)
        self.assert_exact_strength()
        secret = self.window._current_batch[-1]
        # Changing controls after generation must not change stored batch entropy.
        self.window._advanced_rules['min_digits'] = 0
        self.window.strength_bar.setValue(0)
        self.window._select_batch_password(secret)
        self.assertEqual(self.window.output.text(), secret)
        self.assert_exact_strength()
