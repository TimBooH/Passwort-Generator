"""Windows installer handoff tests runnable on every platform."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from windows_support import (
    WINDOWS_INSTALLER_NAME,
    start_verified_windows_installer,
    verify_windows_installer,
)


class WindowsInstallerTests(unittest.TestCase):
    def test_installer_name_and_header_validation(self):
        self.assertEqual(WINDOWS_INSTALLER_NAME, 'PasswortGenerator-Setup-x64.exe')
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / WINDOWS_INSTALLER_NAME
            exe.write_bytes(b'not an exe')
            with self.assertRaisesRegex(ValueError, 'EXE-Header'):
                verify_windows_installer(exe)
            exe.write_bytes(b'MZ' + bytes(80))
            self.assertEqual(verify_windows_installer(exe), exe)

    def test_refuses_missing_file(self):
        with self.assertRaises(ValueError):
            verify_windows_installer(Path(tempfile.gettempdir()) / 'missing-setup-9876.exe')

    def test_only_windows_may_launch_windows_update(self):
        if os.name != 'nt':
            with self.assertRaises(OSError):
                start_verified_windows_installer('any-file.exe')

    def test_windows_handoff_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / WINDOWS_INSTALLER_NAME
            exe.write_bytes(b'MZ' + bytes(100))
            with mock.patch('windows_support.subprocess.Popen') as popen:
                start_verified_windows_installer(exe, platform='nt')
                args = popen.call_args.args[0]
                self.assertEqual(args[0], str(exe))
                self.assertIn('/CLOSEAPPLICATIONS', args)
                self.assertIn('/SILENT', args)


if __name__ == '__main__':
    unittest.main()
