"""Secure handoff from the running Windows application to an Inno Setup installer.

The caller MUST already have verified the exact GitHub-provided SHA-256 and
file size. We separately reject non-PE payloads before launching the setup.
"""

import os
import subprocess
from pathlib import Path

WINDOWS_INSTALLER_NAME = 'PasswortGenerator-Setup-x64.exe'


def verify_windows_installer(path):
    """Basic portable-executable header check (not an Authenticode signature)."""
    binary = Path(path)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('Der Windows-Installer fehlt.')
    with binary.open('rb') as file:
        if file.read(2) != b'MZ':
            raise ValueError('Ungültiger Windows-Installer: EXE-Header fehlt.')
    return binary


def start_verified_windows_installer(path, platform=None):
    """Launch silent per-user setup; [Run] restarts the installed GUI when done."""
    if (os.name if platform is None else platform) != 'nt':
        raise OSError('Windows-Installation kann nur unter Windows gestartet werden.')
    binary = verify_windows_installer(path)
    return subprocess.Popen(
        [
            str(binary), '/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
            '/CLOSEAPPLICATIONS',
        ],
        cwd=str(binary.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
