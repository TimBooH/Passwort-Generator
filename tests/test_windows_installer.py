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

    def test_windows_handoff_requests_uac_elevation(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / WINDOWS_INSTALLER_NAME
            exe.write_bytes(b'MZ' + bytes(100))
            executor = mock.Mock(return_value=33)
            result = start_verified_windows_installer(
                exe, platform='nt', shell_execute=executor
            )
            self.assertEqual(result, 33)
            self.assertEqual(executor.call_count, 1)
            args = executor.call_args.args
            self.assertEqual(args[1], 'runas')
            self.assertEqual(args[2], str(exe))
            self.assertIn('/CLOSEAPPLICATIONS', args[3])
            self.assertIn('/SILENT', args[3])
            self.assertIn('/NORESTART', args[3])
            self.assertEqual(args[4], str(exe.parent))

    def test_cancelled_uac_keeps_app_running(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / WINDOWS_INSTALLER_NAME
            exe.write_bytes(b'MZ' + bytes(100))
            with self.assertRaisesRegex(OSError, 'Administratorrechten'):
                start_verified_windows_installer(
                    exe, platform='nt', shell_execute=lambda *args: 5
                )

    def test_install_script_targets_native_program_files(self):
        from pathlib import Path
        script = Path(__file__).resolve().parents[1] / 'windows' / 'PasswortGenerator.iss'
        content = script.read_text(encoding='utf-8')
        self.assertIn('DefaultDirName={autopf}\\PasswortGenerator', content)
        self.assertIn('PrivilegesRequired=admin', content)
        self.assertIn('ArchitecturesInstallIn64BitMode=x64compatible', content)
        self.assertIn('runasoriginaluser', content)
        self.assertNotIn('DefaultDirName={localappdata}', content)


if __name__ == '__main__':
    unittest.main()
