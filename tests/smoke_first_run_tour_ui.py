"""Offline regression: arrow-onboarding shown once and safe startup update popup."""

import json
import os
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from first_run_tour import TOUR_STEPS
from main import APPIMAGE_NAME, REPO, WINDOWS_INSTALLER_NAME, PasswordWindow


class FakeReply:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode('utf-8')
        self.deleted = False

    def error(self):
        return QNetworkReply.NetworkError.NoError

    def readAll(self):
        return self.payload

    def deleteLater(self):
        self.deleted = True


def wait(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


app = QApplication([])
app.setStyle('Fusion')
with tempfile.TemporaryDirectory() as state_dir:
    # Isolate the first-run flag; do not write to a normal app installation.
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, state_dir
    )
    window = PasswordWindow(auto_check=False)
    window.resize(850, 760)
    window.show()
    app.processEvents()

    assert window._first_run_tour is None
    assert not window.settings.value(
        'first_run_tour_completed', False, type=bool
    )
    window.show_first_run_tour()
    tour = window._first_run_tour
    assert tour is not None and tour.isVisible()
    assert tour.objectName() == 'firstRunTour'
    assert len(TOUR_STEPS) == 8
    for step in range(len(TOUR_STEPS)):
        tour.go_to_step(step)
        app.processEvents()
        assert tour.step_index == step
        assert window.tabs.currentIndex() == TOUR_STEPS[step][0]
        target = tour.target_widget()
        assert target.isVisible(), f'Invisible target at step {step}'
        rect = tour._highlight_rect()
        assert rect.isValid() and rect.width() > 0 and rect.height() > 0
        # The yellow arrow must actually END at the highlighted widget edge.
        start, tip = tour._arrow_line()
        assert start != tip
        assert (abs(tip.y() - rect.top()) <= 8 or
                abs(tip.y() - rect.bottom()) <= 8 or
                abs(tip.x() - rect.left()) <= 8 or
                abs(tip.x() - rect.right()) <= 8), (
                f'Arrow tip missed highlighted target: {step} {tip} {rect}'
        )
        if TOUR_STEPS[step][1] in ('phrase_two_digits', 'phrase_separator'):
            assert window._phrase_mode, 'Extras must be visible in Passphrase mode'
        assert tour.next_button.isVisible()
        assert not tour.grab().isNull(), f'Overlay failed to render at step {step}'
    assert tour.next_button.text().startswith('Fertig')
    tour.previous_step()
    assert tour.step_index == len(TOUR_STEPS) - 2
    tour.go_to_step(0)
    assert not tour.back_button.isEnabled()
    assert window.tabs.currentIndex() == 0

    # Simulate the real startup response while the arrow guide is active.
    window._startup_update_check_pending = True
    package = WINDOWS_INSTALLER_NAME if os.name == 'nt' else APPIMAGE_NAME
    from version import APP_VERSION
    from password_core import parse_version
    major, minor, patch = parse_version(APP_VERSION)
    latest = (
        f'v0.{minor + 1:02d}.0' if major == 0 and minor < 99 else
        'v1.0.0' if major == 0 else f'v{major}.{minor}.{patch + 1}'
    )
    response = {
        'tag_name': latest,
        'assets': [{
            'name': package,
            'browser_download_url':
                f'https://github.com/{REPO}/releases/download/{latest}/{package}',
            'size': 60000000,
        }],
    }
    reply = FakeReply(response)
    window.check_reply = reply
    window.check_finished()
    assert reply.deleted
    assert window._available_update == latest
    assert window._pending_update_popup == latest
    assert window._update_popup_dialog is None
    assert 'NEU' in window.nav_buttons[2].text()

    # Finishing the arrow guide persists it and shows the queued popup.
    tour.finish()
    app.processEvents()
    assert window._first_run_tour is None
    assert window.settings.value('first_run_tour_completed', False, type=bool)
    wait(225)
    popup = window._update_popup_dialog
    assert isinstance(popup, QMessageBox) and popup.isVisible()
    assert latest in popup.text()
    assert 'nichts automatisch installiert' in popup.informativeText()
    actions = {button.text(): button for button in popup.buttons()}
    assert 'Später' in actions
    assert 'Update öffnen' in actions
    actions['Update öffnen'].click()
    app.processEvents()
    assert window._settings_views.currentIndex() == 3
    assert window._update_popup_dialog is None

    # Reopening with the persisted setting must not show the introduction.
    window.show_first_run_tour()
    assert window._first_run_tour is None

    # "Tour mit Pfeilen" is a button in the fourth built-in Info page.
    window.show_info()
    assert window._settings_views.currentIndex() == 4
    restart = window.repeat_tour_button
    assert restart is not None and 'Pfeilen' in restart.text()
    restart.click()
    tour = window._first_run_tour
    assert tour is not None
    assert tour.original_page == 0
    tour.skip_button.click()
    app.processEvents()
    assert window._first_run_tour is None
    assert window.tabs.currentIndex() == 0
    assert window._update_popup_dialog is None

    # Periodic update checks must not repeat the startup popup.
    repeat_reply = FakeReply(response)
    window.check_reply = repeat_reply
    window.check_finished()
    app.processEvents()
    assert repeat_reply.deleted
    assert window._update_popup_dialog is None
    if window._settings_dialog is not None:
        window._settings_dialog.close()
    window.close()
    app.processEvents()

print('First-run arrow tour, persistent skip, re-entry and startup popup passed.')
