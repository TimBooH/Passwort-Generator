"""Dark neon styling and deterministic circuit art for the Qt interface.

Circuit art is rendered once into a pixmap, not on every paintEvent/resize.
"""

import random

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from glass_ui import is_dark_background, rgba
from theme_colors import accent_for_background, accessible_text_color


def circuit_texture(width=1100, height=1450, accent='#178CFF'):
    """Create a subtle, transparent electronic-circuit texture only once."""
    texture = QPixmap(width, height)
    texture.fill(Qt.GlobalColor.transparent)
    painter = QPainter(texture)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rng = random.Random(2026)
    circuit_color = QColor(accent)
    if not circuit_color.isValid():
        circuit_color = QColor('#178CFF')

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
            painter.setPen(QPen(QColor(circuit_color.red(), circuit_color.green(), circuit_color.blue(), rng.randrange(28, 85)), 1.3))
            painter.drawPath(path)
            end = path.currentPosition()
            painter.setPen(QPen(QColor(circuit_color.red(), circuit_color.green(), circuit_color.blue(), rng.randrange(35, 130)), 1.3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(end, 2.2, 2.2)

    painter.setPen(Qt.PenStyle.NoPen)
    for i in range(80):
        x = rng.randrange(width)
        y = rng.randrange(height)
        radius = rng.choice((1.1, 1.7, 2.4, 3.5))
        painter.setBrush(QColor(circuit_color.red(), circuit_color.green(), circuit_color.blue(), rng.randrange(30, 90)))
        painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
    painter.end()
    return texture


def neon_stylesheet(background, foreground, accent=None):
    """Auto-accent styling, matching the background or a sampled wallpaper."""
    dark = is_dark_background(background)
    fg = QColor(foreground).name() if QColor(foreground).isValid() else ('#EDF6FF' if dark else '#142436')
    base = QColor(background)
    accent = accent or accent_for_background(background)
    color = QColor(accent)
    accent_text = accessible_text_color(accent)
    bright = color.lighter(125).name() if dark else color.darker(110).name()
    border = color.darker(160).name() if dark else color.lighter(145).name()
    muted = '#A3B2CC' if dark else '#536479'
    panel = rgba(base.darker(121) if dark else base.lighter(102), 229 if dark else 238)
    panel_hover = rgba(base.lighter(167) if dark else base.darker(107), 241)
    field = rgba(base.darker(146) if dark else base.lighter(106), 225 if dark else 236)
    primary_top = color.lighter(145).name() if dark else color.lighter(110).name()
    primary_bottom = color.darker(172).name()
    tab_selected = color.darker(205).name() if dark else color.lighter(200).name()
    return f"""
QMainWindow {{ background-color: {background}; }}
QLabel#brandTitle {{
    color: {fg}; font-size: 23px; font-weight: 850;
}}
QLabel#brandSubtitle {{
    color: {bright}; font-size: 11px;
}}
QLabel#brandLock {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {tab_selected}, stop:1 {background});
    color: #FFE28C; font-size: 24px;
    border: 1px solid {accent};
    border-radius: 12px; padding: 5px;
}}
QLabel#neonHint {{ color: {muted}; font-size: 11px; }}
QLabel#strengthCaption {{ color: {fg}; font-size: 12px; font-weight: 700; }}
QLabel#lengthValue {{ color: {bright}; font-size: 17px; font-weight: 750; }}
QLabel#lengthCaption {{ color: {fg}; font-weight: 700; }}
QWidget#passwordPage, QWidget#settingsPage, QWidget#updatesPage, QWidget#infoPage {{
    background: transparent;
}}
QStackedWidget#mainPages {{
    background: transparent;
    border: none;
}}
QFrame#topNav {{
    background: transparent;
    border: none;
}}
QPushButton#navButton {{
    color: {fg};
    background: {panel};
    border: 1px solid {border};
    border-radius: 8px;
    min-height: 22px;
    padding: 4px 7px;
    font-size: 11px;
    font-weight: 700;
}}
QPushButton#navButton[updateAvailable="true"] {{
    border: 2px solid {bright};
    color: {accent_text};
    background: {accent};
    font-weight: 850;
}}
QPushButton#navButton[updateAvailable="true"]:hover {{
    border-color: {accent};
    background: {bright};
    color: {accent_text};
}}
QPushButton#navButton:hover:!checked {{
    color: {bright};
    background: {panel_hover};
    border-color: {bright};
}}
QPushButton#navButton:checked {{
    color: {accent_text};
    background: {accent};
    border: 1px solid {bright};
}}
QPushButton#infoNavButton {{
    color: {fg};
    background: {panel};
    border: 1px solid {border};
    border-radius: 8px;
    min-height: 22px;
    padding: 4px 7px;
    font-size: 11px;
    font-weight: 700;
}}
QPushButton#infoNavButton:hover {{
    color: {bright};
    border-color: {bright};
}}
QPushButton {{
    color: {fg};
    background: {panel};
    border: 1px solid {border};
    border-radius: 10px;
    min-height: 23px;
    padding: 5px 10px;
    font-weight: 650;
}}
QPushButton:hover {{ border: 1px solid {bright}; background: {panel_hover}; }}
QPushButton:pressed {{ background: {tab_selected}; }}
QPushButton:focus {{ border: 1px solid {bright}; }}
QComboBox:hover, QComboBox:focus {{ border: 1px solid {bright}; }}
QPushButton#savePresetButton {{ min-height: 22px; font-size: 11px; padding: 3px 7px; }}
QLabel#updateVersionCompare {{ color: {bright}; font-weight: 800; font-size: 12px; }}
QLabel#updatePreview {{ color: {fg}; font-size: 11px; padding: 3px 6px; }}
QPushButton#modeButton {{
    background: {field}; border: 1px solid {border}; border-radius: 8px;
    font-size: 12px; font-weight: 700; padding: 5px 5px;
}}
QPushButton#modeButton:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {tab_selected}, stop:1 {accent});
    border: 2px solid {bright}; color: {accent_text};
}}
QPushButton#squareAction {{
    font-size: 18px; color: {bright}; padding: 4px; min-width: 33px;
}}
QPushButton#primaryButton {{
    color: {accent_text};
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {primary_top}, stop:0.25 {accent},
        stop:0.65 {color.darker(130).name()}, stop:1 {primary_bottom});
    border: 2px solid {bright}; border-radius: 12px;
    min-height: 37px; font-size: 14px; font-weight: 850;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {primary_top}, stop:1 {accent});
    border-color: {bright};
}}
QPushButton#checkUpdateButton {{
    min-height: 20px;
    max-height: 25px;
    padding: 2px 7px;
    border-radius: 8px;
    font-size: 11px;
}}
QComboBox#releaseVersionCombo {{
    font-size: 12px;
    min-height: 26px;
    padding: 5px 10px;
}}
QPushButton#bottomAction {{
    border: 1px solid {border}; background: {field};
    min-height: 23px; font-size: 11px;
}}
QLineEdit, QSpinBox, QComboBox {{
    color: {fg};
    background: {field};
    border: 1px solid {border}; border-radius: 10px;
    min-height: 23px; padding: 5px 8px;
    selection-background-color: {accent};
}}
QLineEdit#passwordOutput {{
    font-size: 14px;
    padding: 7px 12px;
    min-height: 32px;
    border: 1px solid {border};
}}
QLineEdit#passwordOutput:focus {{ border: 1px solid {bright}; }}
QCheckBox {{
    color: {fg}; background: transparent;
    spacing: 7px; padding: 2px 1px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {accent};
    border-radius: 4px;
    background: {field};
}}
QCheckBox::indicator:checked {{
    background: {accent};
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
    background: {panel_hover}; border: none;
    border-radius: 5px; min-height: 8px;
    color: {fg};
}}
QProgressBar#strengthBar {{ max-height: 9px; min-height: 9px; }}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {accent}, stop:1 {bright});
    border-radius: 5px;
}}
QLabel#accentPreview {{
    color: {accent};
    background: {field};
    border: 1px solid {accent};
    border-radius: 9px;
    padding: 8px 11px;
    font-weight: 800;
}}
QTextBrowser#changelogView {{
    background: {field};
    color: {fg};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 10px;
    selection-background-color: {accent};
}}
QListWidget#releaseList {{
    background: {field};
    color: {fg};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 4px;
}}
QListWidget#releaseList::item {{
    padding: 8px 7px;
    border-radius: 6px;
}}
QListWidget#releaseList::item:selected {{
    color: {accent_text};
    background: {accent};
}}
QPushButton#visualGuideButton {{
    background: {accent};
    color: {accent_text};
    border: 1px solid {bright};
    border-radius: 8px;
    font-weight: 750;
}}
QLabel#visualGuideTitle {{
    color: {bright};
    font-size: 14px;
    font-weight: 800;
}}
QLabel#visualGuideDescription {{
    color: {fg};
    font-size: 12px;
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
