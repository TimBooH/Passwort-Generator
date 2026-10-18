"""Offscreen UI navigation regression: three top-left tabs with persistent state."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTabWidget

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(760, 810)
window.show()
app.processEvents()

tabs = window.tabs
assert isinstance(tabs, QTabWidget)
assert tabs.tabPosition() == QTabWidget.TabPosition.North
assert tabs.currentIndex() == 0
assert not tabs.tabBar().expanding()
assert tabs.tabBar().geometry().left() <= 25
assert [tabs.tabText(i) for i in range(tabs.count())] == [
    'Passwort', 'Einstellungen', 'Updates',
]
assert window.glass_cards[0].parentWidget() is window.password_page
assert window.settings_shortcut.isVisible()
assert window.password_mode_button.isChecked()
assert not window.passphrase_mode_button.isChecked()
assert window.output.placeholderText() == 'Generiertes Passwort'
assert window.strength_bar.value() == 0
assert window.length_slider.value() == 20
assert window.history_button.isVisible()
assert window.info_button.isVisible()
assert window.glass_cards[1].parentWidget() is window.settings_page
assert window.glass_cards[2].parentWidget() is window.updates_page

# Password options remain intact when moving to settings and back.
window.length.setValue(44)
assert window.length_slider.value() == 44
window.generate()
password = window.output.text()
assert len(password) == 44
assert window.strength_bar.value() > 0
assert window._history[-1] == ('Passwort', password)
window.show_button.setChecked(True)
app.processEvents()
assert window.output.echoMode() == window.output.EchoMode.Normal
window.show_button.setChecked(False)
assert window.output.echoMode() == window.output.EchoMode.Password
window.copy()
assert app.clipboard().text() == password
tabs.setCurrentIndex(1)
app.processEvents()
assert window.bg_combo.isVisible()
assert window.fg_combo.isVisible()
assert window.choose_background_button.isVisible()
window.bg_combo.setCurrentIndex(1)
app.processEvents()
chosen_background = window.bg_combo.currentData()
assert window.background_surface._base_color.upper() == chosen_background.upper()

tabs.setCurrentIndex(2)
app.processEvents()
assert window.check_button.isVisible()
assert window.update_status.isVisible()
assert not window.output.isVisible()
assert not window.bg_combo.isVisible()

tabs.setCurrentIndex(0)
app.processEvents()
assert window.output.text() == password
assert window.length.value() == 44
assert window.glass_cards[0].isVisible()
assert not window.glass_cards[1].isVisible()
assert not window.glass_cards[2].isVisible()

# Passphrase mode generates six words, then returns to original password mode.
window.passphrase_mode_button.click()
app.processEvents()
assert window._phrase_mode
assert window.length.minimum() == 4
assert window.length.maximum() == 10
assert window.length_slider.value() == 6
assert not window.options_widget.isVisible()
window.generate()
phrase = window.output.text()
assert len(phrase.split('-')) == 6
assert window._history[-1] == ('Passphrase', phrase)
window.password_mode_button.click()
app.processEvents()
assert not window._phrase_mode
assert window.options_widget.isVisible()
assert window.length.maximum() == 128
assert not window.output.text()

# Every page follows the window width with the tab bar still at upper left.
for width in (460, 720, 1600, 530, 990, 470):
    window.resize(width, 790)
    for index, card in enumerate(window.glass_cards):
        tabs.setCurrentIndex(index)
        app.processEvents()
        assert card.isVisible()
        assert card.width() >= width - 130, (
            f'{tabs.tabText(index)} card too narrow at {width}: {card.width()}'
        )
        assert tabs.tabBar().geometry().left() <= 25
tabs.setCurrentIndex(0)
app.processEvents()
window.close()
app.processEvents()
print('Three top-left tabs: responsive, independent, settings preserved, no update-network needed.')
