"""Local crash diagnostics with timestamps, app version and failure context.

Python exceptions are logged with tracebacks. faulthandler and redirected native
stderr record fatal signals and Qt messages where the OS/Python can report them.
A session marker lets the next launch identify unexpected termination. This is
best-effort diagnostics, not a promise to infer unknown graphics driver faults.
"""

import atexit
import faulthandler
import json
import os
import platform
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from version import APP_VERSION


def timestamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def default_state_directory():
    root = os.environ.get('XDG_STATE_HOME')
    return (Path(root).expanduser() if root else Path.home() / '.local' / 'state') / 'passwort-generator'


def process_exists(pid):
    try:
        pid = int(pid)
        if pid < 1:
            return False
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (ValueError, TypeError, OverflowError):
        return False


class CrashReporter:
    """Append-only crash.log, local-only. Never log passwords or clipboard."""

    def __init__(self, state_directory=None, redirect_stderr=True):
        self.directory = Path(state_directory) if state_directory else default_state_directory()
        self.path = self.directory / 'crash.log'
        self.session = uuid.uuid4().hex[:12]
        self.pid = os.getpid()
        self.marker = self.directory / f'session-{self.pid}.json'
        self.started = timestamp()
        self.last_event = 'start'
        self._handle = None
        self._original_stderr_fd = None
        self._closed = False
        self._last_write = 0.0
        self._last_category = None
        self._native_reporting = False
        self._original_excepthook = None
        self._original_thread_hook = None
        self._python_hook = None
        self._thread_hook = None

        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            if self.path.is_file() and self.path.stat().st_size > 4 * 1024 * 1024:
                self.path.replace(self.directory / 'crash.log.1')
            self._handle = self.path.open('a', encoding='utf-8', buffering=1)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
            self._detect_abnormal_sessions()
            self.log('START', f'pid={self.pid}, platform={platform.platform()}, '
                              f'python={sys.version.split()[0]}, '
                              f'qt-platform={os.environ.get("QT_QPA_PLATFORM", "auto")}')
            self._save_marker()
            self._install_exception_hooks()
            # faulthandler's output includes the actual fatal signal name and
            # Python frames, where available. It must keep the file open.
            faulthandler.enable(file=self._handle, all_threads=True)
            self._native_reporting = True
            if redirect_stderr:
                self._capture_native_stderr()
            atexit.register(self.close)
        except (OSError, RuntimeError) as exc:
            # Logging must never be a reason for the app to fail to launch.
            try:
                self.log('WARNING', f'Crash diagnostics partially unavailable: {exc}')
            except Exception:
                pass

    def _detect_abnormal_sessions(self):
        for marker in self.directory.glob('session-*.json'):
            try:
                record = json.loads(marker.read_text(encoding='utf-8'))
                if process_exists(record.get('pid')):
                    continue
                self.log(
                    'UNEXPECTED_EXIT',
                    'Previous session did not close normally; '
                    f'previous-version={record.get("version", "unknown")}, '
                    f'previous-start={record.get("started", "unknown")}, '
                    f'last-action={record.get("last_action", "unknown")}. '
                    'Likely crash, forced termination or power loss; '
                    'the exact cause must be checked in the fatal traceback.',
                )
                marker.unlink(missing_ok=True)
            except (OSError, ValueError, TypeError):
                # An incomplete JSON marker must not crash the app.
                continue

    def _save_marker(self):
        try:
            content = {
                'pid': self.pid,
                'version': APP_VERSION,
                'session': self.session,
                'started': self.started,
                'last_action': self.last_event,
                'last_seen': timestamp(),
            }
            temporary = self.marker.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')
            temporary.replace(self.marker)
        except OSError:
            pass

    def _capture_native_stderr(self):
        try:
            self._original_stderr_fd = os.dup(2)
            os.dup2(self._handle.fileno(), 2)
            self.log('INFO', 'Qt/C++ stderr is now included in this logfile.')
        except OSError:
            self._original_stderr_fd = None

    def _install_exception_hooks(self):
        self._original_excepthook = sys.excepthook
        self._original_thread_hook = threading.excepthook

        def hook(etype, value, tb):
            self.exception('Uncaught Python exception', etype, value, tb)

        self._python_hook = hook
        sys.excepthook = hook

        def thread_hook(args):
            self.exception(
                f'Uncaught exception in thread {args.thread.name if args.thread else "unknown"}',
                args.exc_type, args.exc_value, args.exc_traceback,
            )

        self._thread_hook = thread_hook
        threading.excepthook = thread_hook

    def log(self, category, reason):
        if self._closed or self._handle is None:
            return
        try:
            self._handle.write(
                f'[{timestamp()}] [v{APP_VERSION}] [pid {self.pid}] '
                f'[{self.session}] [{category}] {reason}\n'
            )
            self._handle.flush()
        except (OSError, ValueError):
            pass

    def note(self, category, detail='', force=False):
        """Throttled breadcrumbs for UI actions; never include password text."""
        now = time.monotonic()
        if not force and category == self._last_category and now - self._last_write < 0.9:
            return
        self._last_category = category
        self._last_write = now
        self.last_event = f'{category} {detail}'.strip()
        self.log('ACTION', self.last_event)
        self._save_marker()

    def heartbeat(self):
        self.log('HEARTBEAT', f'last-action={self.last_event}')
        self._save_marker()

    def exception(self, category, etype, value, tb):
        name = getattr(etype, '__name__', str(etype))
        self.log('ERROR', f'{category}; reason={name}: {value}; last-action={self.last_event}')
        if self._handle is not None:
            try:
                traceback.print_exception(etype, value, tb, file=self._handle)
                self._handle.flush()
            except (OSError, ValueError):
                pass

    def error(self, category, error):
        self.log('ERROR', f'{category}; reason={type(error).__name__}: {error}; '
                          f'last-action={self.last_event}')

    def close(self):
        if self._closed:
            return
        self.log('STOP', 'Application closed normally.')
        try:
            if self.marker.exists():
                record = json.loads(self.marker.read_text(encoding='utf-8'))
                if record.get('session') == self.session:
                    self.marker.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError):
            pass
        self._closed = True
        if self._python_hook is not None and sys.excepthook is self._python_hook:
            sys.excepthook = self._original_excepthook
        if self._thread_hook is not None and threading.excepthook is self._thread_hook:
            threading.excepthook = self._original_thread_hook
        try:
            if self._native_reporting:
                faulthandler.disable()
            if self._original_stderr_fd is not None:
                os.dup2(self._original_stderr_fd, 2)
                os.close(self._original_stderr_fd)
        except OSError:
            pass
        if self._handle is not None:
            try:
                self._handle.close()
            except OSError:
                pass
