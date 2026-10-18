"""Offline UI regressions for update badge, scheduled checks, and compact Info.

All requests are faked. This test runs unchanged on Linux and Windows.
"""

import json
import os
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from main import (
    APPIMAGE_NAME, APP_VERSION, REPO, UPDATE_CHECK_INTERVAL_MS,
    PasswordWindow, WINDOWS_INSTALLER_NAME,
)


class FakeReply(QObject):
    finished = Signal()

    def __init__(self, response, error=None):
        super().__init__()
        self._data = json.dumps(response).encode('utf-8')
        self._error = (error if error is not None
                       else QNetworkReply.NetworkError.NoError)
        self.deleted = False

    def error(self):
        return self._error

    def errorString(self):
        return 'Simulierte Verbindung fehlgeschlagen'

    def readAll(self):
        return self._data

    def deleteLater(self):
        self.deleted = True


class FakeNetwork:
    def __init__(self):
        self.requests = []
        self.replies = []

    def get(self, request):
        self.requests.append(request.url().toString())
        reply = FakeReply({})
        self.replies.append(reply)
        return reply


def complete_check(window, version):
    asset_name = WINDOWS_INSTALLER_NAME if os.name == 'nt' else APPIMAGE_NAME
    response = {
        'tag_name': version,
        'assets': [{
            'name': asset_name,
            'browser_download_url':
                f'https://github.com/{REPO}/releases/download/{version}/{asset_name}',
            'size': 30000000,
        }],
    }
    fake = FakeReply(response)
    window.check_reply = fake
    window.check_finished()
    assert fake.deleted


app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(850, 760)
window.show()
app.processEvents()

assert window.update_timer.interval() == 2 * 60 * 60 * 1000
assert UPDATE_CHECK_INTERVAL_MS == 7200000
assert not window.update_timer.isActive()
assert window.scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
assert window.scroll_area.verticalScrollBar().maximum() == 0, (
    f'Password page must not scroll at 850x760: '
    f'{window.scroll_area.verticalScrollBar().maximum()}'
)

# Narrow yet supported window, with a single column of checkbox options.
for width, height in ((610, 700), (530, 700), (850, 760)):
    window.resize(width, height)
    app.processEvents()
    assert window.scroll_area.verticalScrollBar().maximum() == 0, (
        f'Unexpected password scrolling at {width}x{height}: '
        f'{window.scroll_area.verticalScrollBar().maximum()}'
    )
    assert window.generate_button.isVisible()
    assert window.history_button.isVisible()

window.resize(850, 760)
app.processEvents()
top_labels = [button.text() for button in window.nav_buttons]
assert all(len(label) <= 23 for label in top_labels)
assert window.info_nav_button.height() <= 42
assert all(button.height() <= 42 for button in window.nav_buttons)

fake_network = FakeNetwork()
window.network = fake_network
window.update_timer.start()
assert window.update_timer.isActive()
window.update_timer.timeout.emit()
assert len(fake_network.requests) == 1
assert 'releases/latest' in fake_network.requests[0]
assert not window.check_button.isEnabled()
# Complete the mocked timer-triggered request with an actual newer release.
reply = fake_network.replies[-1]
asset_name = WINDOWS_INSTALLER_NAME if os.name == 'nt' else APPIMAGE_NAME
latest = 'v0.09.0'
reply._data = json.dumps({
    'tag_name': latest,
    'assets': [{
        'name': asset_name,
        'browser_download_url':
            f'https://github.com/{REPO}/releases/download/{latest}/{asset_name}',
        'size': 30000000,
    }],
}).encode()
reply.finished.emit()
app.processEvents()
assert window._available_update == latest
assert 'NEU' in window.nav_buttons[2].text()
assert window.nav_buttons[2].property('updateAvailable') is True
assert latest in window.nav_buttons[2].toolTip()
assert window.check_button.isEnabled()
assert not window.download_button.isVisible(), 'The parent Updates page is hidden'
# Note: QWidget.hide() set before its parent page is shown; show() afterwards
# must remain available once the Updates page is opened.
window.tabs.setCurrentIndex(2)
app.processEvents()
assert 'NEU' in window.nav_buttons[2].text()
assert window.download_button.isVisible()
window.tabs.setCurrentIndex(0)
window.resize(620, 720)
app.processEvents()
assert 'NEU' in window.nav_buttons[2].text()
assert window._available_update == latest

# A later successful check that says current must remove the indicator.
complete_check(window, f'v{APP_VERSION}')
app.processEvents()
assert window._available_update is None
assert window.nav_buttons[2].property('updateAvailable') is False
assert 'NEU' not in window.nav_buttons[2].text()
window.update_timer.stop()

# Info contains no written or illustrated instructions.
info = window.build_info_dialog()
assert info.windowTitle().startswith('Info')
assert info.findChild(QLabel, 'infoCredit').text() == 'Made by Jon Bovi'
assert not info.findChild(QPushButton, 'visualGuideButton')
assert not hasattr(window, 'build_visual_guide_dialog')
assert not info.findChild(QLabel, 'visualGuideTitle')
info.close()
window.close()
app.processEvents()
print('UI update-badge / 2h timer / compact navigation / no-scroll password / minimal Info OK')
