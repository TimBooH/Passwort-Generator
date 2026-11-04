"""Native Qt stress test for the one fixed Ocean Glass reference design.

Repeated resizes may not enable hidden theme/wallpaper controls or cause native
Qt shutdown crashes. Existing password/security/update views must still work.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QScrollArea, QSlider, QStackedWidget
from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.show()
app.processEvents()

assert len(window.glass_cards) == 2
assert len(window.secondary_cards) == 4
assert not hasattr(window, 'appearance_card')
assert not hasattr(window, 'scheme_combo')
assert not hasattr(window, 'bg_combo')
assert not hasattr(window, 'choose_background_button')
assert not hasattr(window, 'image_mode_combo')
assert not hasattr(window, 'accent_preview')
assert window.language_card.isAncestorOf(window.language_combo)
assert window.security_card.isAncestorOf(window.clear_clipboard_checkbox)
assert window.background_surface._ocean_enabled
assert window.background_surface._ocean.isVisible()
assert not window.background_surface.has_background_image()
assert isinstance(window.tabs, QStackedWidget)
assert window.tabs.count() == 4
assert not window.findChildren(QScrollArea)
assert len(window.findChildren(QSlider)) == 1
assert window.length_slider.minimum() == 8
assert window.length_slider.maximum() == 128
assert window.nav_container.y() < window.tabs.y()

# Stress the *real* application with 60 resizes, four tabs and live passwords.
widths = (530, 580, 760, 1120, 1680, 1000, 640, 1210, 740, 900)
heights = (700, 710, 820, 940, 900, 740, 750, 880, 820, 770)
for repeat in range(6):
    for width, height in zip(widths, heights):
        window.resize(width, height)
        app.processEvents()
        assert window.width() >= 510
        assert window.background_surface._ocean_enabled
        assert not window.background_surface.has_background_image()

# Generate passwords and change pages separately, avoiding concurrent
# invalidation of the same native QWidget layout during resize callbacks.
window.resize(1120, 790)
for number in range(25):
    window.length.setValue(8 + (number * 5) % 121)
    window.generate()
    app.processEvents()
    assert len(window.output.text()) == window.length.value()
for page in (0, 1, 2, 3, 2, 1, 0):
    window.tabs.setCurrentIndex(page)
    app.processEvents()
    assert window.tabs.currentIndex() == page

# Show each interactive card at desktop and narrow widths.
for size in ((1660, 900), (530, 700)):
    window.resize(*size)
    for page, widget in ((0, window.glass_cards[0]),
                         (1, window.language_card),
                         (1, window.security_card),
                         (2, window.glass_cards[1])):
        window.tabs.setCurrentIndex(page)
        app.processEvents()
        assert widget.isVisible(), f'Hidden card on page {page}'
    window.tabs.setCurrentIndex(0)
    app.processEvents()
    assert window.grab().save('glossy-preview.png')

# Give Qt its normal event-loop deferred-delete pass before Python exits.
window.close()
window.deleteLater()
from PySide6.QtCore import QCoreApplication, QEvent
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
app.processEvents()
del window
import gc
gc.collect()
print('Fixed Ocean GUI stress passed: 60 resizes, four tabs, no appearance switch.', flush=True)
