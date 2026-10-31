"""Offscreen integration test of bilingual Stable/Unstable updater UI.

No real download or release is published here; network replies are simulated.
"""
import json
import os
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication

from main import PasswordWindow, INSTALLED_APPIMAGE, UNSTABLE_APPIMAGE
from update_channels import RELEASE_PREFIX, channel_api, unstable_asset_name

class FakeReply(QObject):
    finished = Signal()
    def __init__(self, content):
        super().__init__()
        self.payload = json.dumps(content).encode()
    def error(self):
        return QNetworkReply.NetworkError.NoError
    def readAll(self):
        return self.payload
    def deleteLater(self):
        pass

class FakeNetwork:
    def __init__(self):
        self.urls = []
        self.replies = []
    def get(self, request):
        self.urls.append(request.url().toString())
        reply = FakeReply({})
        self.replies.append(reply)
        return reply

app = QApplication([])
app.setStyle('Fusion')
settings = QSettings('TimBooH', 'PasswortGenerator')
prior = settings.value('updates/channel', None)
settings.setValue('updates/channel', 'stable')
window = PasswordWindow(auto_check=False)
window.resize(850, 760)
window.show()
app.processEvents()
assert window.channel_combo.currentData() == 'stable'
assert window.update_channel == 'stable'
assert window.channel_combo.objectName() == 'updateChannelCombo'
assert UNSTABLE_APPIMAGE.parent != INSTALLED_APPIMAGE.parent
fake = FakeNetwork()
window.network = fake

# An explicit switch requests the rolling GitHub Unstable prerelease.
window.channel_combo.setCurrentIndex(window.channel_combo.findData('unstable'))
assert window.update_channel == 'unstable'
assert fake.urls[-1] == channel_api('unstable')
short = 'abcdef012345'
name = unstable_asset_name(os.name, short)
payload = {
    'tag_name': 'unstable', 'prerelease': True, 'draft': False,
    'name': 'PasswortGenerator Unstable ' + short,
    'body': '## Deutsch\\n- Neue Testfunktionen\\n## English\\n- New preview features',
    'assets': [{
        'name': name,
        'browser_download_url': RELEASE_PREFIX + 'unstable/' + name,
        'digest': 'sha256:' + 'a'*64, 'size': 100000000,
    }],
}
fake.replies[-1].payload = json.dumps(payload).encode()
fake.replies[-1].finished.emit()
app.processEvents()
assert window.latest_version == 'UNSTABLE ' + short
assert window.latest_asset['name'] == name
assert window.download_button.text() == 'Testversion installieren & starten'
assert window.check_button.isEnabled()
assert window.channel_combo.isEnabled()

# Reject attacker-provided release URLs before showing an install button.
window.check_for_updates()
bad = dict(payload, assets=[dict(payload['assets'][0], browser_download_url='https://evil.invalid/x')])
fake.replies[-1].payload = json.dumps(bad).encode()
fake.replies[-1].finished.emit()
assert window.latest_asset is None
assert not window.download_button.isVisible() or window.tabs.currentIndex() != 2

window.channel_combo.setCurrentIndex(window.channel_combo.findData('stable'))
assert fake.urls[-1] == channel_api('stable')
# Switching back never silently installs a preview over the stable app.
assert window.latest_asset is None
assert settings.value('updates/channel') == 'stable'
fake.replies[-1].payload = json.dumps({'tag_name': 'v0.21.1', 'assets': []}).encode()
fake.replies[-1].finished.emit()

window.tabs.setCurrentIndex(1)
window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
app.processEvents()
window.tabs.setCurrentIndex(2)
assert window.channel_label.text() == 'Update channel:'
assert window.channel_combo.itemText(window.channel_combo.findData('unstable')) == 'Unstable (test)'
window.close()
settings.remove('updates/channel') if prior is None else settings.setValue('updates/channel', prior)
settings.sync()
print('Stable/Unstable dropdown, bilingual labels, verified prerelease and isolation OK')
