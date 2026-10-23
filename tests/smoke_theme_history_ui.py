"""Headless integration for theme presets, auto accent, GitHub changelog and Info."""

import json
import os
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTextBrowser, QTabWidget

from main import PasswordWindow, REPO_URL
from theme_colors import (
    accent_for_background, accessible_text_color, contrast_ratio, preset_colors
)


class FakeReleaseReply:
    def __init__(self, payload, error=None):
        self.payload = json.dumps(payload).encode('utf-8')
        self.deleted = False
        self.network_error = (
            error if error is not None else QNetworkReply.NetworkError.NoError
        )

    def error(self):
        return self.network_error

    def errorString(self):
        return 'Simulierter Netzwerkfehler'

    def readAll(self):
        return self.payload

    def deleteLater(self):
        self.deleted = True


app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.show()
window.tabs.setCurrentIndex(1)
app.processEvents()
assert window.scheme_combo.count() == 8
assert window.scheme_combo.findData('ocean_glass') >= 0
assert window.scheme_combo.findData('glass_dark') >= 0
assert window.scheme_combo.findData('glass_light') >= 0
assert window.scheme_combo.findData('custom') >= 0
initial_circuit_key = window.background_surface._circuit.pixmap().cacheKey()

def apply_scheme(scheme):
    window.scheme_combo.setCurrentIndex(window.scheme_combo.findData(scheme))
    app.processEvents()
    bg, _unused_text = preset_colors(scheme)
    assert window.bg_combo.currentData() == bg
    assert not hasattr(window, 'fg_combo')
    assert not window.settings.contains('text_color')
    assert contrast_ratio(accessible_text_color(bg), bg) >= 4.5
    assert window.settings.value('color_scheme') == scheme
    expected_accent = accent_for_background(bg)
    assert expected_accent in window.accent_preview.text()
    assert window.glass_cards[0]._accent.name().upper() == expected_accent
    assert window.background_surface._circuit.pixmap().cacheKey() == initial_circuit_key, (
        'Recreating QPainter circuit texture during color changes can crash Qt'
    )
    return expected_accent


glass_accent = apply_scheme('glass')
assert window.background_surface._clear_glass
assert all(card._clear_glass for card in window.glass_cards + window.secondary_cards)
window.glass_cards[0]._refresh_style()
assert ', 48)' in window.glass_cards[0].styleSheet()
dark_accent = apply_scheme('glass_dark')
assert not window.background_surface._clear_glass
assert all(not card._clear_glass for card in window.glass_cards + window.secondary_cards)
light_accent = apply_scheme('glass_light')
assert dark_accent != light_accent
violet_accent = apply_scheme('violet_glass')
forest_accent = apply_scheme('forest_glass')
assert violet_accent != forest_accent
assert window.background_surface._circuit.pixmap() is not None
assert window.info_nav_button.isVisible()
assert not hasattr(window, 'info_button')
assert not hasattr(window, 'open_crash_log')

# Changing a single color means it is no longer a named preset.
red_idx = window.bg_combo.findData('#351A23')
assert red_idx >= 0
window.bg_combo.setCurrentIndex(red_idx)
app.processEvents()
assert window.scheme_combo.currentData() == 'custom'
assert window.settings.value('color_scheme') == 'custom'
assert window.accent_preview.text().endswith(accent_for_background('#351A23'))

# The concise Info page is inline, with scalable illustrated help in the same tab.
window.show_info()
app.processEvents()
assert window.tabs.currentIndex() == 3
assert window.info_credit.text() == 'Made by Jon Bovi'
assert window.info_card is not window.info_help_card
assert window.info_card.isVisible()
assert window.info_help_card.isVisible()
assert window.visual_guide_button.parentWidget() is not None
assert 'v' in window.info_version.text()
assert not hasattr(window, 'build_info_dialog')
graphic_button = window.visual_guide_button
assert graphic_button is not None and 'Grafische Erklärung' in graphic_button.text()
graphic_button.click()
app.processEvents()
tabs = window.info_detail_stack.findChild(QTabWidget, 'visualGuideTabs')
assert tabs is not None and tabs.count() == 3
for i in range(3):
    label = window.info_detail_stack.findChild(QLabel, f'visualGuideImage{i}')
    assert label is not None and label.pixmap() is not None and not label.pixmap().isNull()
assert window.info_detail_stack.currentIndex() == 1
graphic_button.click()
assert window.info_detail_stack.currentIndex() == 0

# No network calls: feed a deterministic GitHub response to the real GUI.
window.tabs.setCurrentIndex(2)
app.processEvents()
payload = [
    {
        'tag_name': 'v0.05.0',
        'published_at': '2026-10-18T10:34:40Z',
        'body': '## Neue Funktionen\n- Automatische Akzentfarbe und Farbschemas',
        'html_url': f'{REPO_URL}/releases/tag/v0.05.0',
    },
    {
        'tag_name': 'v0.04.0',
        'published_at': '2026-10-18T10:16:20Z',
        'body': '## Vorherige Version\n- Neon-Design',
        'html_url': f'{REPO_URL}/releases/tag/v0.04.0',
    },
    {
        'tag_name': 'v1.5.1',
        'published_at': '2026-10-18T02:07:36Z',
        'body': '## Historische Version\n- Schnellerer Build',
        'html_url': f'{REPO_URL}/releases/tag/v1.5.1',
    },
]
reply = FakeReleaseReply(payload)
window.history_reply = reply
window.release_history_finished()
app.processEvents()
assert reply.deleted
assert window.release_combo.count() == 3
assert window.release_combo.isEnabled()
assert window._release_history_loaded
assert window.release_combo.currentIndex() == 0
assert window.release_combo.itemData(0) == 'v0.05.0'
assert window.release_combo.itemData(2) == 'v1.5.1'
assert 'Automatische Akzentfarbe' in window.changelog_view.toPlainText()
assert not hasattr(window, 'open_release_button')
assert not hasattr(window, 'reload_history_button')
assert 'neueste zuerst' in window.release_history_status.text()
window.release_combo.setCurrentIndex(2)
app.processEvents()
assert window.changelog_title.text().endswith('v1.5.1')
assert 'Schnellerer Build' in window.changelog_view.toPlainText()
assert '• ' in window.changelog_view.toPlainText()
assert '## ' not in window.changelog_view.toPlainText()
assert len(window.changelog_view.toPlainText().splitlines()) <= 5

# Invalid response must produce an informative state, not empty false data.
bad_reply = FakeReleaseReply({'message': 'rate limit'})
window.history_reply = bad_reply
window.release_history_finished()
assert 'nicht verfügbar' in window.release_history_status.text()
assert window.release_combo.count() == 3
assert bad_reply.deleted

window.close()
app.processEvents()
print('Theme/history Info integration passed: live accents, presets, legacy changelog, credit, help.')
