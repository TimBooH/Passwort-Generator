"""Offline UI regressions for update badge, scheduled checks, and compact Info.

All requests are faked. This test runs unchanged on Linux and Windows.
"""

import json
import os
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget

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
# Compute a genuinely newer version, independent of the release milestone.
from password_core import parse_version
major, minor, _patch = parse_version(APP_VERSION)
latest = (
    f'v0.{minor + 1:02d}.0' if major == 0 and minor < 99 else
    'v1.0.0' if major == 0 else f'v{major}.{minor}.{_patch + 1}'
)
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

# Info keeps the on-demand graphical guide (without a long written manual).
info = window.build_info_dialog()
assert info.windowTitle().startswith('Info')
assert info.findChild(QLabel, 'infoCredit').text() == 'Made by Jon Bovi'
button = info.findChild(QPushButton, 'visualGuideButton')
assert button is not None and 'Grafische Erklärung' in button.text()
guide = window.build_visual_guide_dialog(info)
screens = guide.findChild(QTabWidget, 'visualGuideTabs')
assert screens is not None and screens.count() == 3
for i in range(3):
    screenshot = guide.findChild(QLabel, f'visualGuideImage{i}')
    assert screenshot is not None and screenshot.pixmap() is not None
    assert not screenshot.pixmap().isNull()
guide.close()
info.close()
window.close()
app.processEvents()
print('UI update-badge / 2h timer / compact navigation / graphical Info guide OK')
