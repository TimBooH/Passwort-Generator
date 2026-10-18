"""Headless stress test: repeated resizing, palette changes, and wallpaper modes.

The CI job starts a fresh process; a native Qt crash will fail the job.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_LOGGING_RULES', 'qt.qpa.*=false')

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QScrollArea, QSlider

from main import PasswordWindow

app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.show()
app.processEvents()
assert len(window.glass_cards) == 3
assert not window.findChildren(QSlider), 'The glass-opacity slider must be removed'
assert not hasattr(window, 'glass_slider')
assert not window.settings.contains('glass_opacity'), 'Legacy opacity setting must be removed'
assert window.grab().save('glossy-preview.png'), 'Unable to render preview'

with tempfile.TemporaryDirectory() as temp:
    background = Path(temp) / 'stress-wallpaper.png'
    image = QImage(1800, 980, QImage.Format.Format_RGB32)
    image.fill(QColor('#18445A'))
    painter = QPainter(image)
    painter.fillRect(50, 50, 600, 240, QColor('#A3526C'))
    painter.end()
    assert image.save(str(background)), 'Unable to make wallpaper fixture'
    window.background_surface.set_background_image(str(background))
    assert window.background_surface.has_background_image()

    # Mimic user dragging the right and bottom edges repeatedly.
    widths = [460, 520, 760, 1120, 1700, 1020, 460, 1900, 630, 940]
    heights = [540, 690, 820, 1050, 680, 740, 590, 970, 820, 750]
    for mode_label, mode in [
        (window.image_mode_combo.itemText(i), window.image_mode_combo.itemData(i))
        for i in range(window.image_mode_combo.count())
    ]:
        idx = window.image_mode_combo.findData(mode)
        assert idx >= 0, mode
        window.image_mode_combo.setCurrentIndex(idx)
        for width, height in zip(widths, heights):
            window.resize(width, height)
            app.processEvents()
            assert window.width() >= 460
            assert window.height() >= 540
        pix = window.grab()
        assert not pix.isNull(), f'Render failed in mode {mode}'

    # Change many settings while the window is wide, like actual UI usage.
    for iteration in range(25):
        window.bg_combo.setCurrentIndex(iteration % window.bg_combo.count())
        window.fg_combo.setCurrentIndex(iteration % window.fg_combo.count())
        window.length.setValue(8 + (iteration * 5) % 121)
        window.generate()
        app.processEvents()
        assert len(window.output.text()) == window.length.value()
    # Failed files must not replace the successfully loaded background.
    try:
        window.background_surface.set_background_image(str(Path(temp) / 'missing.png'))
        raise AssertionError('A missing file was accepted')
    except ValueError:
        assert window.background_surface.has_background_image()

    # The glass tiles really resize with the window in both directions.
    window.resize(1680, 900)
    app.processEvents()
    assert window.glass_cards[0].width() >= 1500, (
        'Glass tiles must expand instead of being capped at 940 pixels'
    )
    assert window.glass_cards[1].width() == window.glass_cards[0].width()
    assert window.grab().save('glossy-wide-preview.png')
    window.resize(520, 770)
    app.processEvents()
    assert window.glass_cards[0].width() < 520
    window.resize(740, 810)
    app.processEvents()
    assert window.grab().save('glossy-wallpaper-preview.png')
    window.remove_background_image()
    app.processEvents()
    assert not window.background_surface.has_background_image()

window.close()
app.processEvents()
print('Responsive GUI stress test passed: no opacity slider, 6 image modes, 60 resizes, 25 UI changes.')
