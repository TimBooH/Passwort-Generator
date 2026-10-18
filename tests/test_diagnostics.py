"""Crash logs should have a session, timestamps, version, and reason."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from diagnostics import CrashReporter
from version import APP_VERSION


class DiagnosticsTests(unittest.TestCase):
    def test_versioned_timestamped_entries_and_exception_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            previous_hook = sys.excepthook
            reporter = CrashReporter(p, redirect_stderr=False)
            try:
                self.assertTrue(reporter.marker.is_file())
                reporter.note('RESIZE', 'width=1900', force=True)
                try:
                    raise RuntimeError('demonstration failure')
                except RuntimeError:
                    reporter.exception('Test failure', *sys.exc_info())
                reporter.heartbeat()
            finally:
                reporter.close()
            self.assertEqual(sys.excepthook, previous_hook)
            self.assertFalse(reporter.marker.exists())
            log = (p / 'crash.log').read_text(encoding='utf-8')
            self.assertIn('[v' + APP_VERSION + ']', log)
            self.assertIn('START', log)
            self.assertIn('STOP', log)
            self.assertIn('RESIZE', log)
            self.assertIn('RuntimeError: demonstration failure', log)
            self.assertIn('Traceback', log)
            self.assertRegex(log, r'\[20\d{2}-\d\d-\d\dT\d\d:\d\d:\d\d')

    def test_unexpected_previous_session_is_not_reported_as_certain_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            marker = p / 'session-999999999.json'
            marker.write_text(json.dumps({
                'pid': 999999999,
                'version': '1.4.0',
                'started': '2026-10-18T01:00:00+02:00',
                'last_action': 'RESIZE width=1900',
            }), encoding='utf-8')
            reporter = CrashReporter(p, redirect_stderr=False)
            reporter.close()
            log = (p / 'crash.log').read_text(encoding='utf-8')
            self.assertIn('UNEXPECTED_EXIT', log)
            self.assertIn('RESIZE width=1900', log)
            self.assertIn('cause', log)
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
