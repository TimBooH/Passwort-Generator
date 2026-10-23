"""Static abstract blue ribbon background for the built-in Ocean Glass theme.

Generated once by Qt at startup and displayed via QLabel. No image synthesis,
network request, resize-time painting or extra packaged asset is required.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap


def ocean_texture(width=1440, height=960):
    """Make a cached wallpaper-like pixmap with soft blue flowing ribbons."""
    image = QPixmap(width, height)
    image.fill(QColor('#06152F'))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    background = QLinearGradient(0, 0, width, height)
    background.setColorAt(0, QColor('#0B2450'))
    background.setColorAt(0.46, QColor('#071832'))
    background.setColorAt(1, QColor('#053A80'))
    painter.fillRect(image.rect(), background)

    # Three wide, soft ribbon forms, like the reference's blue desktop curves.
    for i, (start, crest, trough, end) in enumerate((
        ('#0644C2', '#147DEA', '#063A92', '#031B45'),
        ('#0B59DC', '#22A9FC', '#0B4CAC', '#062C64'),
        ('#08337F', '#1585E3', '#075BAF', '#032459'),
    )):
        path = QPainterPath()
        y = height * (.17 + i * .21)
        path.moveTo(-120, y + 185)
        path.cubicTo(width * .20, y - 360, width * .66, y + 255,
                     width + 120, y - 125)
        path.lineTo(width + 120, height + 120)
        path.lineTo(-120, height + 120)
        path.closeSubpath()
        fill = QLinearGradient(0, y - 120, width, y + 360)
        for pos, color in ((0, start), (.38, crest), (.70, trough), (1, end)):
            fill.setColorAt(pos, QColor(color))
        painter.fillPath(path, fill)

    # Top-left cyan glimmer creates depth without distracting from the content.
    glint = QPainterPath()
    glint.moveTo(-120, height * .47)
    glint.cubicTo(width * .34, -height * .12, width * .71, height * .44,
                  width + 120, height * .09)
    painter.setPen(QColor(72, 192, 255, 65))
    painter.drawPath(glint)
    painter.end()
    return image
