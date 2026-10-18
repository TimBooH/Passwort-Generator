"""Offscreen regression: top-right navigation, Info and responsive cards."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStackedWidget, QTabWidget

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(760, 810)
window.show()
app.processEvents()

tabs = window.tabs
assert isinstance(tabs, QStackedWidget)
assert tabs.currentIndex() == 0
assert tabs.count() == 4
assert tuple(window.tab_names) == ('Passwort', 'Einstellungen', 'Update', 'Info')
assert len(window.nav_buttons) == 3
assert [button.accessibleName() for button in window.nav_buttons] == list(window.tab_names[:3])
assert all(button.isVisible() for button in window.nav_buttons)
assert window.info_nav_button.isVisible()
assert window.info_nav_button.accessibleName() == 'Info'
assert window.centralWidget() is window.background_surface
assert not hasattr(window, 'scroll_area')
assert not hasattr(window, 'nav_sidebar')
assert not hasattr(window, 'settings_shortcut')
assert window.nav_container.y() < tabs.y()
assert window.nav_buttons[0].x() > 0, 'Navigation buttons should align to the right'
assert window.nav_buttons[0].isChecked()
assert len(window.secondary_cards) == 2
assert window.glass_cards[0].parentWidget() is window.password_page
assert window.nav_buttons[1].isVisible()
assert window.password_mode_button.isChecked()
assert not window.passphrase_mode_button.isChecked()
assert window.output.placeholderText() == 'Generiertes Passwort'
assert window.strength_bar.value() == 0
assert window.length_slider.value() == 20
assert window.history_button.isVisible()
assert window.info_nav_button.isVisible()
assert not hasattr(window, 'info_button')
assert not hasattr(window, 'open_crash_log')
assert not hasattr(window, 'fg_combo')
assert not window.settings.contains('text_color')
assert window.glass_cards[1].parentWidget() is window.settings_page
assert window.glass_cards[2].parentWidget() is window.updates_page
assert window.appearance_card is window.glass_cards[1]
assert window.appearance_card.header.text() == 'ERSCHEINUNGSBILD'
assert window.appearance_card.isAncestorOf(window.scheme_combo)
assert window.appearance_card.isAncestorOf(window.choose_background_button)
assert window.appearance_card.isAncestorOf(window.image_mode_combo)
assert window.changelog_card is window.secondary_cards[0]
assert window.changelog_card.parentWidget() is window.updates_page
assert window.changelog_card.header.text() == 'CHANGELOG'
assert window.changelog_card.isAncestorOf(window.release_combo)
assert window.changelog_card.isAncestorOf(window.changelog_view)
assert window.secondary_cards[1].parentWidget() is window.info_page
assert window.info_help_card.parentWidget() is window.info_page
assert window.info_card is not window.info_help_card

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
window.nav_buttons[1].click()
app.processEvents()
assert tabs.currentIndex() == 1
assert window.nav_buttons[1].isChecked()
assert window.bg_combo.isVisible()
assert window.choose_background_button.isVisible()
window.bg_combo.setCurrentIndex(1)
app.processEvents()
chosen_background = window.bg_combo.currentData()
assert window.background_surface._base_color.upper() == chosen_background.upper()

window.nav_buttons[2].click()
app.processEvents()
assert tabs.currentIndex() == 2
assert window.nav_buttons[2].isChecked()
assert window.check_button.isVisible()
assert window.update_status.isVisible()
assert not window.output.isVisible()
assert not window.bg_combo.isVisible()

# Info is now a regular fourth page, never a new window.
window.info_nav_button.click()
app.processEvents()
assert tabs.currentIndex() == 3
assert window.info_nav_button.isChecked()
assert window.info_page.isVisible()
assert window.info_credit.text() == 'Made by Jon Bovi'
assert not window.update_status.isVisible()
window.visual_guide_button.click()
app.processEvents()
assert window.info_detail_stack.currentIndex() == 1
assert window.info_detail_stack.findChild(QTabWidget, 'visualGuideTabs').count() == 3
window.visual_guide_button.click()
app.processEvents()
assert window.info_detail_stack.currentIndex() == 0

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
assert window.phrase_options_widget.isVisible()
assert not window.phrase_two_digits.isChecked()
assert window.phrase_separator.count() == 4
assert window.phrase_separator.currentData() == '-'
window.generate()
phrase = window.output.text()
assert len(phrase.split('-')) == 6
assert window._history[-1] == ('Passphrase', phrase)
base_strength = window.strength_bar.value()
window.phrase_two_digits.setChecked(True)
window.phrase_separator.setCurrentIndex(window.phrase_separator.findData('_'))
window.generate()
with_digits = window.output.text()
parts = with_digits.split('_')
assert len(parts) == 7
assert parts[-1].isdigit() and 10 <= int(parts[-1]) <= 99
assert window.strength_bar.value() > base_strength
assert window._history[-1] == ('Passphrase', with_digits)
for separator in (' ', '.', '-'):
    window.phrase_separator.setCurrentIndex(window.phrase_separator.findData(separator))
    window.generate()
    assert len(window.output.text().split(separator)) == 7
window.password_mode_button.click()
app.processEvents()
assert not window._phrase_mode
assert window.options_widget.isVisible()
assert not window.phrase_options_widget.isVisible()
assert window.length.maximum() == 128
assert not window.output.text()

# Pages follow window width; navigation stays right-aligned near the header.
for width in (460, 720, 1600, 530, 990, 470):
    window.resize(width, 790)
    for index, card in enumerate(window.glass_cards):
        tabs.setCurrentIndex(index)
        app.processEvents()
        assert card.isVisible()
        assert card.width() >= width - 120, (
            f'{window.tab_names[index]} card too narrow at {width}: {card.width()}'
        )
        assert window.nav_container.y() < tabs.y()
        assert window.nav_buttons[index].isChecked()
        if width < 720:
            assert window.nav_buttons[1].text().endswith('Design')
        else:
            assert window.nav_buttons[1].text().endswith('Einstellungen')
tabs.setCurrentIndex(0)
app.processEvents()
window.close()
app.processEvents()
print('Top-right navigation: 4 inline pages, responsive cards and no scroll container.')
