"""Antialiased vector icons, independent of system/emoji glyphs."""
from functools import lru_cache
import math
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


@lru_cache(maxsize=80)
def icon_pixmap(name, size=28, color='#EDF7FF'):
    image = QPixmap(size * 2, size * 2)
    image.fill(Qt.GlobalColor.transparent)
    image.setDevicePixelRatio(2)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 32, size / 32)
    pen = QPen(QColor(color), 2.1)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    if name == 'key':
        p.drawEllipse(QRectF(17, 3, 12, 12))
        path = QPainterPath(QPointF(19, 13))
        for x, y in ((5, 27), (5, 22), (9, 22), (9, 18), (13, 18)):
            path.lineTo(x, y)
        p.drawPath(path)
    elif name == 'update':
        p.drawArc(QRectF(5, 5, 22, 22), 35 * 16, 145 * 16)
        p.drawArc(QRectF(5, 5, 22, 22), 215 * 16, 145 * 16)
        for points in (((5, 6), (5, 13), (12, 13)), ((27, 26), (27, 19), (20, 19))):
            path = QPainterPath(QPointF(*points[0]))
            for point in points[1:]:
                path.lineTo(*point)
            p.drawPath(path)
    elif name == 'settings':
        path = QPainterPath()
        for i in range(32):
            a = i * math.pi / 16
            r = 13 if i % 4 in (1, 2) else 10
            point = QPointF(16 + math.cos(a) * r, 16 + math.sin(a) * r)
            path.moveTo(point) if i == 0 else path.lineTo(point)
        path.closeSubpath()
        p.drawPath(path)
        p.drawEllipse(QRectF(11.5, 11.5, 9, 9))
    elif name == 'info':
        p.drawEllipse(QRectF(4, 4, 24, 24))
        p.drawLine(16, 14, 16, 23)
        p.drawPoint(16, 9)
    elif name == 'copy':
        p.drawRoundedRect(QRectF(10, 9, 16, 20), 2, 2)
        path = QPainterPath(QPointF(20, 5))
        for point in ((20, 3), (4, 3), (4, 23), (7, 23)):
            path.lineTo(*point)
        p.drawPath(path)
    elif name == 'document':
        path = QPainterPath(QPointF(7, 3))
        for point in ((21, 3), (27, 9), (27, 29), (7, 29), (7, 3)):
            path.lineTo(*point)
        p.drawPath(path)
        p.drawLine(21, 3, 21, 9)
        p.drawLine(21, 9, 27, 9)
        for y in (14, 19, 24):
            p.drawLine(12, y, 22, y)
    elif name in ('eye', 'eye-off'):
        path = QPainterPath(QPointF(2, 16))
        path.cubicTo(10, 4, 22, 4, 30, 16)
        path.cubicTo(22, 28, 10, 28, 2, 16)
        p.drawPath(path)
        p.drawEllipse(QRectF(12, 12, 8, 8))
        if name == 'eye-off':
            p.drawLine(4, 28, 28, 4)
    elif name == 'history':
        for y in (8, 16, 24):
            p.drawPoint(5, y)
            p.drawLine(12, y, 27, y)
    else:
        p.end()
        raise ValueError(f'Unknown icon: {name}')
    p.end()
    return image


def vector_icon(name, size=28, color='#EDF7FF'):
    return QIcon(icon_pixmap(name, size, color))


def key_icon(size=28, color='#86E5FF'):
    return icon_pixmap('key', size, color)
