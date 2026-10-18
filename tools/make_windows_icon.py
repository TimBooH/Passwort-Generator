"""Render the repo's SVG logo to a multi-resolution Windows .ico file."""

import io
import os
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def create_icon():
    app = QApplication.instance() or QApplication([])
    source = Path('assets/de.timbooh.passwortgenerator.svg')
    output = Path('assets/passwortgenerator.ico')
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise RuntimeError(f'Invalid vector logo: {source}')
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError('Cannot create icon buffer')
    if not image.save(buffer, 'PNG'):
        raise RuntimeError('Could not render the project logo')
    with Image.open(io.BytesIO(bytes(buffer.data()))) as picture:
        picture.save(
            str(output), format='ICO',
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                   (64, 64), (128, 128), (256, 256)],
        )
    assert output.is_file() and output.stat().st_size > 2000
    print(f'Windows icon created: {output} ({output.stat().st_size} bytes)')


if __name__ == '__main__':
    create_icon()
