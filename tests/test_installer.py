"""Installer / uninstaller smoke tests without network access."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class InstallScriptTests(unittest.TestCase):
    def test_installer_rotates_only_previous_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            source = home / 'candidate.AppImage'
            env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / '.data'))
            directory = home / '.local' / 'opt' / 'passwort-generator'
            current = directory / 'PasswortGenerator.AppImage'
            previous = directory / 'PasswortGenerator-previous.AppImage'

            for version in ('1', '2', '3'):
                source.write_bytes(b'\x7fELF' + version.encode())
                subprocess.run(
                    ['bash', str(ROOT / 'install.sh'), '--file', str(source)],
                    env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                self.assertEqual(current.read_bytes(), b'\x7fELF' + version.encode())
                if version == '1':
                    self.assertFalse(previous.exists())
                else:
                    self.assertEqual(
                        previous.read_bytes(),
                        b'\x7fELF' + str(int(version) - 1).encode(),
                    )

            self.assertEqual(
                {p.name for p in directory.glob('PasswortGenerator*.AppImage')},
                {'PasswortGenerator.AppImage', 'PasswortGenerator-previous.AppImage'},
            )
            desktop = home / '.data' / 'applications' / 'de.timbooh.passwortgenerator.desktop'
            self.assertTrue(desktop.exists())
            subprocess.run(
                ['bash', str(ROOT / 'uninstall.sh')],
                env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertFalse(current.exists())
            self.assertFalse(previous.exists())
            self.assertFalse(desktop.exists())


if __name__ == '__main__':
    unittest.main()
