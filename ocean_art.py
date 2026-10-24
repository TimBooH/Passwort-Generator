"""Native vector icon accents for Ocean Glass.

Drawn into tiny cached QPixmaps one time, not via a widget paintEvent. This
keeps the interface portable on Linux/Windows and independent of emoji fonts.
"""
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap


@lru_cache(maxsize=8)
def key_icon(size=28, color='#86E5FF'):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    scale = size / 32.0
    p.scale(scale, scale)
    pen = QPen(QColor(color), 2.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(16, 3, 12, 12)
    p.drawLine(18, 14, 5, 27)
    p.drawLine(5, 27, 5, 21)
    p.drawLine(5, 21, 9, 21)
    p.drawLine(9, 21, 9, 17)
    p.drawLine(9, 17, 13, 17)
    p.end()
    return pixmap
