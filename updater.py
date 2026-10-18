"""Safe AppImage updates: exactly one current version and one previous version.

Downloaded releases are verified by the caller, staged on the same filesystem,
then atomically renamed. A hard-link preserves the running AppImage inode
without making an 80 MB copy; copy2 is used if linking is unavailable.
"""

import os
import shutil
import subprocess
import uuid
from pathlib import Path

CURRENT_NAME = 'PasswortGenerator.AppImage'
PREVIOUS_NAME = 'PasswortGenerator-previous.AppImage'


def staging_path(installed):
    """Reserve a unique filename in the installation directory for QSaveFile."""
    target = Path(installed)
    return target.parent / ('.PasswortGenerator-update-' + uuid.uuid4().hex + '.AppImage')


def previous_path(installed):
    return Path(installed).with_name(PREVIOUS_NAME)


def verify_appimage_header(path):
    """Reject non-ELF downloads even if the release metadata looks plausible."""
    source = Path(path)
    with source.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            raise ValueError('Die heruntergeladene Datei ist kein Linux-AppImage (ELF-Header fehlt).')


def prune_owned_appimages(directory, current, previous):
    """Only prune files named for this application inside its private install dir."""
    directory = Path(directory)
    keep = {Path(current).name, Path(previous).name}
    removed = []
    for candidate in directory.glob('PasswortGenerator*.AppImage'):
        if candidate.name in keep or candidate.is_dir() or candidate.is_symlink():
            continue
        candidate.unlink()
        removed.append(candidate.name)
    # Abandoned staging files are not versions and may safely be removed.
    for candidate in directory.glob('.PasswortGenerator-update-*.AppImage'):
        if candidate.is_file() and not candidate.is_symlink():
            candidate.unlink()
            removed.append(candidate.name)
    return removed


def install_staged_appimage(staged, installed):
    """Atomically install a verified AppImage with the preceding version kept.

    Only invoked AFTER the SHA-256 digest and expected byte size were checked.
    Existing installed and previous versions are never modified in-place.
    Returns the predecessor path if an old installation existed, else None.
    """
    staged, installed = Path(staged), Path(installed)
    previous = previous_path(installed)
    if not staged.is_file() or staged.is_symlink():
        raise ValueError('Die temporäre AppImage-Datei fehlt.')
    if installed.parent.resolve() != staged.parent.resolve():
        raise ValueError('Update-Datei muss im Installationsordner liegen.')
    if installed == staged:
        raise ValueError('Update und installierte Version dürfen nicht identisch sein.')
    if installed.is_symlink() or previous.is_symlink():
        raise ValueError('Verknüpfte AppImage-Dateien werden aus Sicherheitsgründen nicht überschrieben.')
    verify_appimage_header(staged)
    os.chmod(staged, 0o755)

    # Never rename the running executable away before the replacement is ready.
    had_current = installed.is_file()
    if had_current:
        backup_tmp = installed.parent / ('.PasswortGenerator-prev-' + uuid.uuid4().hex)
        try:
            try:
                os.link(installed, backup_tmp)
            except OSError:
                shutil.copy2(installed, backup_tmp)
            os.replace(backup_tmp, previous)
        finally:
            backup_tmp.unlink(missing_ok=True)
    # If this rename fails, the original executable remains in place.
    os.replace(staged, installed)
    try:
        prune_owned_appimages(installed.parent, installed, previous)
    except OSError:
        # Cleanup of obsolete versions must never invalidate a good update.
        pass
    return previous if had_current else None


def restart_updated_app(executable):
    """Launch the downloaded binary after the original GUI has exited.

    The shell sleep gives Qt time to finish its teardown. Scrub PyInstaller
    process-private environment variables so the new AppImage starts cleanly.
    """
    executable = Path(executable).expanduser().resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise OSError('Die aktualisierte AppImage-Datei ist nicht ausführbar.')
    environment = os.environ.copy()
    for key in (
        'APPIMAGE', 'APPDIR', 'OWD', 'ARGV0', 'PYTHONHOME', 'PYTHONPATH',
        'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'QT_QPA_FONTDIR',
        'QML2_IMPORT_PATH', '_PYI_APPLICATION_HOME_DIR',
        '_PYI_PARENT_PROCESS_LEVEL', '_PYI_ARCHIVE_FILE',
    ):
        environment.pop(key, None)
    original_library_path = environment.pop('LD_LIBRARY_PATH_ORIG', None)
    if original_library_path is not None:
        environment['LD_LIBRARY_PATH'] = original_library_path
    else:
        environment.pop('LD_LIBRARY_PATH', None)
    environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    return subprocess.Popen(
        ['/bin/sh', '-c', 'sleep 1; exec "$1"', 'PasswortGenerator-Restart', str(executable)],
        cwd=str(executable.parent),
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
