"""No-scroll layout: four pages and release dropdown must remain usable.

Qt offscreen smoke test, executed on Linux and Windows before packaging.
"""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QScrollArea

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.show()

assert window.centralWidget() is window.background_surface
assert not window.findChildren(QScrollArea)
assert not hasattr(window, 'scroll_area')
assert window.tabs.count() == 4
assert window.check_button.text() == '↻ Auf Update prüfen'
assert window.check_button.width() == 175
assert window.generate_button.objectName() == 'generatePasswordButton'
assert window.generate_button.height() == 40
assert window.generate_button.maximumWidth() == 360
assert 'QPushButton#generatePasswordButton' in window.styleSheet()
assert 'QPushButton#primaryButton' in window.styleSheet()  # Update CTA unchanged.

assert window.appearance_card.body.spacing() == 3
assert window.appearance_card.layout().contentsMargins().top() == 6
assert window.language_card.objectName() == 'glossyCard'
assert window.language_card.header.text() == 'SPRACHE'
assert window.language_card.layout().contentsMargins().top() == 5
assert window.changelog_card.body.spacing() == 3
assert window.changelog_card.layout().contentsMargins().top() == 5

controls = (
    (window.generate_button, window.history_button, window.length_slider,
     window.preset_combo, window.save_preset_button),
    (window.scheme_combo, window.bg_combo, window.choose_background_button,
     window.clear_background_button, window.image_mode_combo,
     window.language_combo, window.clear_clipboard_checkbox,
     window.clipboard_timeout_combo),
    (window.check_button, window.changelog_view, window.release_combo,
     window.release_history_status),
    (window.info_credit, window.info_version, window.visual_guide_button,
     window.repeat_tour_button),
)

for w, h in ((850, 760), (610, 700), (530, 700), (1100, 820)):
    window.resize(w, h)
    for page, widgets in enumerate(controls):
        window.tabs.setCurrentIndex(page)
        for _ in range(4):
            app.processEvents()
        assert window.tabs.currentIndex() == page
        assert window.centralWidget().rect().isValid()
        for control in widgets:
            assert control.isVisible(), f'Invisible control on page {page}: {control.objectName()}'
            top = control.mapTo(window, QPoint(0, 0))
            bottom = top.y() + control.height()
            right = top.x() + control.width()
            assert top.x() >= -2 and top.y() >= -2
            assert right <= window.width() + 2, (
                f'Horizontal clipping: {w}x{h} page={page} {control.objectName()} right={right}'
            )
            assert bottom <= window.height() + 2, (
                f'Vertical clipping: {w}x{h} page={page} {control.objectName()} bottom={bottom}'
            )
        if page == 0:
            button = window.generate_button
            assert button.height() == 40, f'Generate button too tall: {button.height()}'
            assert 235 <= button.width() <= 360, f'Wrong Generate width: {button.width()}'
            card = window.glass_cards[0]
            from PySide6.QtCore import QPoint
            center_button = button.mapTo(window, QPoint(button.width() // 2, 0)).x()
            center_card = card.mapTo(window, QPoint(card.width() // 2, 0)).x()
            assert abs(center_button - center_card) <= 3, 'Generate button not centered'
        if page == 2:
            assert not window.changelog_view.verticalScrollBar().isVisible()
            assert window.release_combo.isVisible()
            assert window.changelog_card.isAncestorOf(window.release_combo)
            assert window.changelog_card.isAncestorOf(window.changelog_view)
            assert window.check_button.width() <= 190
            assert window.check_button.mapTo(window, QPoint(0, 0)).x() < window.width() // 2

# All fifty release entries are in the dropdown; no page buttons or
# external scrollbars are needed. Selection updates the combined changelog tile.
entries = [{
    'tag': f'v0.{i:02d}.0',
    'date': '2026-10-18',
    'body': f'- Änderung Nummer {i}',
} for i in range(50, 0, -1)]
window._history_releases = {entry['tag']: entry for entry in entries}
window.tabs.setCurrentIndex(2)
window.release_combo.blockSignals(True)
window.release_combo.clear()
for entry in entries:
    window.release_combo.addItem(entry['tag'], entry['tag'])
window.release_combo.setEnabled(True)
window.release_combo.blockSignals(False)
app.processEvents()
assert window.release_combo.count() == 50
assert window.release_combo.itemData(0) == 'v0.50.0'
assert window.release_combo.itemData(49) == 'v0.01.0'
window.release_combo.setCurrentIndex(49)
app.processEvents()
assert window.changelog_title.text().endswith('v0.01.0')
assert 'Änderung Nummer 1' in window.changelog_view.toPlainText()
window.release_combo.setCurrentIndex(10)
app.processEvents()
assert window.changelog_title.text().endswith('v0.40.0')
assert 'Änderung Nummer 40' in window.changelog_view.toPlainText()

# The illustrated help is contained within Info, with no scrollable preview.
window.show_info()
window.show_visual_guide()
app.processEvents()
assert window.tabs.currentIndex() == 3
assert window.info_detail_stack.currentIndex() == 1
assert not window.info_page.findChildren(QScrollArea)
for size in ((530, 700), (850, 760)):
    window.resize(*size)
    for _ in range(4):
        app.processEvents()
    assert window.visual_guide_button.isVisible()
    rect = window.info_detail_stack.geometry()
    parent = window.info_detail_stack.mapTo(window, QPoint(0, 0))
    assert parent.y() + rect.height() <= window.height() + 2

window.close()
app.processEvents()
print('Four pages without scrolling, dropdown releases, compact check button, inline graphics OK')
