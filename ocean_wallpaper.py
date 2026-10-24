"""Cached soft blue light behind the fixed Ocean Glass surface."""
from PySide6.QtGui import QColor, QLinearGradient, QRadialGradient, QPainter, QPainterPath, QPixmap


def ocean_texture(width=1440, height=960):
    image = QPixmap(width, height)
    image.fill(QColor('#07182F'))
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    base = QLinearGradient(0, 0, width, height)
    for position, color in ((0, '#10457B'), (.35, '#06192F'), (.7, '#092C56'), (1, '#10609B')):
        base.setColorAt(position, QColor(color))
    p.fillRect(image.rect(), base)
    for x, y, radius, color in ((.9, .02, .72, '#1878E6'), (.12, .95, .65, '#086ADD')):
        light = QRadialGradient(width*x, height*y, width*radius)
        light.setColorAt(0, QColor(color))
        light.setColorAt(1, QColor(5, 32, 67, 0))
        p.fillRect(image.rect(), light)
    for i in range(3):
        path = QPainterPath()
        y = height * (.88 + i * .08)
        path.moveTo(-100, y)
        path.cubicTo(width*.25, y-height*.38, width*.7, y+height*.4, width+100, y-height*.13)
        path.lineTo(width+100, height+100)
        path.lineTo(-100, height+100)
        path.closeSubpath()
        ribbon = QLinearGradient(0, y-height*.2, width, height)
        ribbon.setColorAt(0, QColor(21, 127, 231, 20))
        ribbon.setColorAt(.6, QColor(7, 44, 95, 5))
        ribbon.setColorAt(1, QColor(36, 153, 238, 38))
        p.fillPath(path, ribbon)
    p.end()
    return image
