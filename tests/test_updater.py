"""Safe-update regression tests with fake ELF/AppImage files."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import updater


def fake_image(path, version):
    Path(path).write_bytes(b'\x7fELF' + version.encode('utf-8'))
    return Path(path)


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.current = self.folder / updater.CURRENT_NAME
        self.previous = self.folder / updater.PREVIOUS_NAME

    def test_3_versions_only_latest_and_previous(self):
        fake_image(self.current, 'v1')
        stage2 = fake_image(updater.staging_path(self.current), 'v2')
        result2 = updater.install_staged_appimage(stage2, self.current)
        self.assertEqual(result2, self.previous)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFv2')
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv1')

        fake_image(self.folder / 'PasswortGenerator-v0.AppImage', 'ancient')
        stage3 = fake_image(updater.staging_path(self.current), 'v3')
        updater.install_staged_appimage(stage3, self.current)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFv3')
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv2')
        self.assertEqual(
            {p.name for p in self.folder.glob('PasswortGenerator*.AppImage')},
            {updater.CURRENT_NAME, updater.PREVIOUS_NAME},
        )
        if os.name != 'nt':  # POSIX execute bits are not meaningful on Windows.
            self.assertEqual(self.current.stat().st_mode & 0o777, 0o755)

    def test_first_install_has_no_previous(self):
        stage = fake_image(updater.staging_path(self.current), 'v1')
        self.assertIsNone(updater.install_staged_appimage(stage, self.current))
        self.assertTrue(self.current.is_file())
        self.assertFalse(self.previous.exists())

    def test_invalid_binary_never_replaces_current(self):
        fake_image(self.current, 'old')
        bad = self.folder / '.update-invalid'
        bad.write_bytes(b'NOT-AN-APPIMAGE')
        with self.assertRaisesRegex(ValueError, 'ELF-Header'):
            updater.install_staged_appimage(bad, self.current)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFold')

    def test_interrupted_rename_does_not_damage_current(self):
        fake_image(self.current, 'v1')
        stage = fake_image(updater.staging_path(self.current), 'v2')
        original_replace = updater.os.replace

        def blocked_replace(src, dst):
            if Path(src) == stage and Path(dst) == self.current:
                raise OSError('simulated filesystem failure')
            return original_replace(src, dst)

        with mock.patch('updater.os.replace', side_effect=blocked_replace):
            with self.assertRaisesRegex(OSError, 'filesystem failure'):
                updater.install_staged_appimage(stage, self.current)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFv1')
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv1')

    def test_fallback_to_copy_if_hardlinks_unavailable(self):
        fake_image(self.current, 'v1')
        stage = fake_image(updater.staging_path(self.current), 'v2')
        with mock.patch('updater.os.link', side_effect=OSError('no hardlink')):
            updater.install_staged_appimage(stage, self.current)
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv1')

    def test_dont_touch_other_appimages(self):
        fake_image(self.current, 'v1')
        other = fake_image(self.folder / 'OtherProgram.AppImage', 'foreign')
        stage = fake_image(updater.staging_path(self.current), 'v2')
        updater.install_staged_appimage(stage, self.current)
        self.assertTrue(other.exists())

    def test_verified_rollback_swaps_current_and_previous(self):
        fake_image(self.current, 'v2')
        fake_image(self.previous, 'v1')
        self.assertEqual(updater.restore_previous_appimage(self.current), self.current)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFv1')
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv2')

    def test_rollback_requires_real_verified_previous(self):
        fake_image(self.current, 'v2')
        with self.assertRaises(ValueError):
            updater.restore_previous_appimage(self.current)
        fake_image(self.previous, 'v1')
        self.current.write_bytes(b'invalid')
        with self.assertRaises(ValueError):
            updater.restore_previous_appimage(self.current)

    def test_failed_rollback_restores_current(self):
        fake_image(self.current, 'v2')
        fake_image(self.previous, 'v1')
        original_replace = updater.os.replace

        def fail_on_previous(src, dst):
            if Path(dst) == self.previous:
                raise OSError('rollback second rename failed')
            return original_replace(src, dst)

        with mock.patch('updater.os.replace', side_effect=fail_on_previous):
            with self.assertRaises(OSError):
                updater.restore_previous_appimage(self.current)
        self.assertEqual(self.current.read_bytes(), b'\x7fELFv2')
        self.assertEqual(self.previous.read_bytes(), b'\x7fELFv1')

    def test_restart_cleans_appimage_environment(self):
        fake_image(self.current, 'v2')
        self.current.chmod(0o755)
        with mock.patch.dict(os.environ, {
            'APPDIR': '/old', 'APPIMAGE': '/old/AppImage',
            'QT_PLUGIN_PATH': '/old/plugins', 'LD_LIBRARY_PATH': '/old/libs',
            'LD_LIBRARY_PATH_ORIG': '/usr/lib',
        }), mock.patch('updater.subprocess.Popen') as process:
            updater.restart_updated_app(self.current)
        arguments, kwargs = process.call_args
        self.assertEqual(arguments[0][0], '/bin/sh')
        self.assertEqual(arguments[0][-1], str(self.current.resolve()))
        self.assertEqual(kwargs['env'].get('LD_LIBRARY_PATH'), '/usr/lib')
        self.assertNotIn('APPDIR', kwargs['env'])
        self.assertNotIn('QT_PLUGIN_PATH', kwargs['env'])
        self.assertEqual(kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')
        self.assertTrue(kwargs['start_new_session'])

    def test_missing_new_binary_cannot_restart(self):
        with self.assertRaises(OSError):
            updater.restart_updated_app(self.current)


if __name__ == '__main__':
    unittest.main()
