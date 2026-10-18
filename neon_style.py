"""Dark neon styling and deterministic circuit art for the Qt interface.

Circuit art is rendered once into a pixmap, not on every paintEvent/resize.
"""

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from glass_ui import is_dark_background, rgba


def circuit_texture(width=1100, height=1450):
    """Create a subtle, transparent electronic-circuit texture only once."""
    texture = QPixmap(width, height)
    texture.fill(Qt.GlobalColor.transparent)
    painter = QPainter(texture)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rng = random.Random(2026)

    # Board traces on the left and right: short connected orthogonal segments.
    for side in ('left', 'right'):
        for i in range(44):
            start_x = rng.randrange(0, 260) if side == 'left' else rng.randrange(width - 265, width)
            start_y = rng.randrange(0, height)
            sign = 1 if side == 'left' else -1
            dx = sign * rng.randrange(25, 115)
            dy = rng.choice((-1, 1)) * rng.randrange(12, 52)
            path = QPainterPath()
            path.moveTo(start_x, start_y)
            path.lineTo(start_x + dx, start_y)
            path.lineTo(start_x + dx + sign * 25, start_y + dy)
            path.lineTo(start_x + dx + sign * rng.randrange(45, 155), start_y + dy)
            painter.setPen(QPen(QColor(1, 95, 223, rng.randrange(28, 85)), 1.3))
            painter.drawPath(path)
            end = path.currentPosition()
            painter.setPen(QPen(QColor(3, 122, 253, rng.randrange(35, 130)), 1.3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(end, 2.2, 2.2)

    painter.setPen(Qt.PenStyle.NoPen)
    for i in range(80):
        x = rng.randrange(width)
        y = rng.randrange(height)
        radius = rng.choice((1.1, 1.7, 2.4, 3.5))
        painter.setBrush(QColor(0, 125, 255, rng.randrange(30, 90)))
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
    painter.end()
    return texture


def neon_stylesheet(background, foreground):
    """Accent layer; keeps Qt widget painting native and resize-safe."""
    dark = is_dark_background(background)
    fg = foreground if not dark else '#EDF6FF'
    muted = '#86A4C5' if dark else '#44637B'
    panel = 'rgba(3, 16, 32, 229)' if dark else 'rgba(230, 242, 253, 238)'
    panel_hover = 'rgba(7, 37, 69, 241)' if dark else 'rgba(196, 223, 250, 246)'
    field = 'rgba(0, 13, 27, 218)' if dark else 'rgba(247, 251, 255, 235)'
    border = '#1165A4' if dark else '#4C91C7'
    accent = '#008DFF'
    bright = '#26C8FF'
    return f"""
QMainWindow {{ background-color: #020A15; }}
QLabel#brandTitle {{
    color: {fg}; font-size: 26px; font-weight: 850;
}}
QLabel#brandSubtitle {{
    color: {bright}; font-size: 12px;
}}
QLabel#brandLock {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #09345A, stop:1 #05162D);
    color: #FFE28C; font-size: 29px;
    border: 1px solid {accent};
    border-radius: 14px; padding: 9px;
}}
QLabel#neonHint {{ color: {muted}; font-size: 11px; }}
QLabel#strengthCaption {{ color: {fg}; font-size: 12px; font-weight: 700; }}
QLabel#lengthValue {{ color: {bright}; font-size: 17px; font-weight: 750; }}
QLabel#lengthCaption {{ color: {fg}; font-weight: 700; }}
QWidget#passwordPage, QWidget#settingsPage, QWidget#updatesPage {{
    background: transparent;
}}
QTabWidget#mainTabs::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    color: {muted};
    background: {panel};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 8px 13px;
    min-width: 85px;
    margin: 0 6px 0 0;
    font-weight: 700;
}}
QTabBar::tab:selected {{
    color: #FFFFFF;
    background: #073966;
    border: 1px solid {bright};
}}
QTabBar::tab:hover:!selected {{ color: {fg}; background: {panel_hover}; }}
QPushButton {{
    color: {fg};
    background: {panel};
    border: 1px solid {border};
    border-radius: 10px;
    min-height: 29px;
    padding: 7px 13px;
    font-weight: 650;
}}
QPushButton:hover {{ border: 1px solid {bright}; background: {panel_hover}; }}
QPushButton:pressed {{ background: #0B477E; }}
QPushButton#headerSettings {{
    background: transparent; border: none;
    color: {fg}; font-weight: 700;
}}
QPushButton#headerSettings:hover {{ color: {bright}; }}
QPushButton#modeButton {{
    background: {field}; border: 1px solid {border}; border-radius: 8px;
    font-size: 13px; font-weight: 700; padding: 8px 5px;
}}
QPushButton#modeButton:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #0E3B78, stop:1 #0751A3);
    border: 2px solid {bright}; color: #FFFFFF;
}}
QPushButton#squareAction {{
    font-size: 19px; color: {bright}; padding: 5px; min-width: 42px;
}}
QPushButton#primaryButton {{
    color: #FFFFFF;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1C9CFF, stop:0.25 #0B57B5,
        stop:0.65 #05356D, stop:1 #006FD1);
    border: 2px solid {bright}; border-radius: 12px;
    min-height: 43px; font-size: 15px; font-weight: 850;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #3DBBFF, stop:1 #0955AF);
    border-color: #72E4FF;
}}
QPushButton#bottomAction {{
    border: 1px solid {border}; background: {field};
    min-height: 29px; font-size: 12px;
}}
QLineEdit, QSpinBox, QComboBox {{
    color: {fg};
    background: {field};
    border: 1px solid {border}; border-radius: 10px;
    min-height: 25px; padding: 7px 10px;
    selection-background-color: {accent};
}}
QLineEdit#passwordOutput {{
    font-size: 14px;
    padding: 9px 15px;
    min-height: 39px;
    border: 1px solid #137EBB;
}}
QLineEdit#passwordOutput:focus {{ border: 1px solid {bright}; }}
QCheckBox {{
    color: {fg}; background: transparent;
    spacing: 9px; padding: 5px 2px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {accent};
    border-radius: 4px;
    background: #061A34;
}}
QCheckBox::indicator:checked {{
    background: #0867BF;
    border: 1px solid {bright};
    image: none;
}}
QSlider::groove:horizontal {{
    height: 7px; border-radius: 3px;
    background: #294052;
}}
QSlider::sub-page:horizontal {{
    border-radius: 3px; background: {accent};
}}
QSlider::handle:horizontal {{
    width: 16px; border: 2px solid {bright};
    border-radius: 10px; background: #F0F9FF;
    margin: -6px 0;
}}
QProgressBar {{
    background: #26394D; border: none;
    border-radius: 5px; min-height: 8px;
    color: {fg};
}}
QProgressBar#strengthBar {{ max-height: 9px; min-height: 9px; }}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #057BFF, stop:1 #13DCFA);
    border-radius: 5px;
}}
QLabel#globalStatus {{
    color: {muted}; font-size: 11px; padding: 0 5px;
}}
QLabel#glassCardTitle {{ color: {fg}; font-size: 13px; font-weight: 800; }}
QLabel#supportText {{ color: {muted}; font-size: 11px; }}
QLabel {{
    color: {fg}; background: transparent;
}}
""".strip()
