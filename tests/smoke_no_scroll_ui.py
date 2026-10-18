"""No-scroll layout: all four pages and paged release history must remain usable.

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

controls = (
    (window.generate_button, window.history_button, window.length_slider),
    (window.scheme_combo, window.bg_combo, window.choose_background_button,
     window.clear_background_button, window.image_mode_combo),
    (window.check_button, window.changelog_view, window.release_list,
     window.releases_previous, window.releases_next, window.release_page_label),
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
        if page == 2:
            assert not window.release_list.verticalScrollBar().isVisible()
            assert not window.changelog_view.verticalScrollBar().isVisible()

# Fifty versions cannot fit inside a list without scrolling: navigate pages.
entries = [{
    'tag': f'v0.{i:02d}.0',
    'date': '2026-10-18',
    'body': f'Änderung Nummer {i}',
} for i in range(50, 0, -1)]
window._release_entries = entries
window._history_releases = {entry['tag']: entry for entry in entries}
window.tabs.setCurrentIndex(2)
window.show_release_page(0)
app.processEvents()
assert window.release_list.count() == 3
assert window.release_list.item(0).data(Qt.ItemDataRole.UserRole) == 'v0.50.0'
assert window.releases_next.isEnabled()
assert not window.releases_previous.isEnabled()
assert window.release_page_label.text() == 'Seite 1/17'
window.releases_next.click()
app.processEvents()
assert window.release_page_label.text() == 'Seite 2/17'
assert window.release_list.item(0).data(Qt.ItemDataRole.UserRole) == 'v0.47.0'
window.show_release_page(16)
app.processEvents()
assert window.release_list.count() == 2
assert window.release_list.item(1).data(Qt.ItemDataRole.UserRole) == 'v0.01.0'
assert not window.releases_next.isEnabled()
assert window.releases_previous.isEnabled()
assert not window.release_list.verticalScrollBar().isVisible()
window.releases_previous.click()
assert window.release_page_label.text() == 'Seite 16/17'

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
print('All four pages accessible without scrolling; release paging + inline graphics OK')
