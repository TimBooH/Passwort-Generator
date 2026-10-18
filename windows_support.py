"""Verified Windows-setup handoff using an explicit UAC elevation request.

The caller MUST verify the published GitHub SHA-256 and byte count before
calling this module. A PE "MZ" check is additional validation, not a signature.
"""

import ctypes
import os
from pathlib import Path

WINDOWS_INSTALLER_NAME = 'PasswortGenerator-Setup-x64.exe'
SETUP_PARAMETERS = '/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS'


def verify_windows_installer(path):
    binary = Path(path)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('Der Windows-Installer fehlt.')
    with binary.open('rb') as source:
        if source.read(2) != b'MZ':
            raise ValueError('Ungültiger Windows-Installer: EXE-Header fehlt.')
    return binary


def start_verified_windows_installer(path, platform=None, shell_execute=None):
    """Prompt for admin rights via UAC; never bypass Windows security controls.

    The installer goes into Program Files and therefore needs elevation.
    Windows ShellExecuteW with the 'runas' verb displays the UAC dialog.
    If the user cancels, raise an exception and KEEP the current GUI open.
    """
    if (os.name if platform is None else platform) != 'nt':
        raise OSError('Windows-Installation kann nur unter Windows gestartet werden.')
    binary = verify_windows_installer(path)
    if shell_execute is None:
        shell_execute = ctypes.windll.shell32.ShellExecuteW
        shell_execute.argtypes = [
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int,
        ]
        shell_execute.restype = ctypes.c_void_p
    result = shell_execute(
        None, 'runas', str(binary), SETUP_PARAMETERS, str(binary.parent), 1
    )
    code = int(result or 0)
    if code <= 32:
        raise OSError(
            'Der Windows-Installer konnte nicht mit Administratorrechten '
            'gestartet werden (UAC möglicherweise abgebrochen). '
            f'Fehlercode: {code}.'
        )
    return code
