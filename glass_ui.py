"""Glassmorphism visuals for PasswortGenerator.

The background uses a painted gradient with soft lighting. Cards are tinted
translucent surfaces, not a claim of compositor-dependent desktop blur.
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def is_dark_background(color):
    """Use luminance, not palette name, so custom user colors work."""
    tone = QColor(color)
    value = 0.2126 * tone.redF() + 0.7152 * tone.greenF() + 0.0722 * tone.blueF()
    return value < 0.56


def rgba(color, opacity):
    """Return a Qt stylesheet-safe rgba() value."""
    tone = QColor(color)
    alpha = max(0, min(255, int(opacity)))
    return f'rgba({tone.red()}, {tone.green()}, {tone.blue()}, {alpha})'


def build_glass_stylesheet(background, foreground, opacity=54):
    """Style glass cards and controls while respecting background/text choices."""
    dark = is_dark_background(background)
    opacity = max(30, min(85, int(opacity)))
    panel_opacity = round(opacity * (1.60 if dark else 2.55))
    panel = rgba('#FFFFFF', panel_opacity)
    panel_hover = rgba('#FFFFFF', min(242, panel_opacity + 18))
    field = rgba('#FFFFFF' if dark else '#F8FBFF', min(235, panel_opacity + (5 if dark else 15)))
    border = rgba('#FFFFFF' if dark else '#384960', 105 if dark else 46)
    bright_border = rgba('#FFFFFF' if dark else '#435D79', 160 if dark else 72)
    secondary_button = rgba('#FFFFFF' if dark else '#DAE9F7', 52 if dark else 160)
    accent = '#7DDCFF' if dark else '#195F92'
    primary_text = '#102536' if dark else '#FFFFFF'
    primary_start = '#A1EAFF' if dark else '#287CBF'
    primary_end = '#4B9FF3' if dark else '#16558E'
    progress = '#72D5FF' if dark else '#287FB3'
    muted = rgba(foreground, 185)
    return f"""
QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QWidget#appRoot {{
    background: transparent;
}}
QScrollArea {{
    border: none;
}}
QLabel, QCheckBox, QGroupBox {{
    color: {foreground};
}}
QLabel#heroTitle {{
    color: {foreground};
    font-size: 25px;
    font-weight: 800;
    background: transparent;
    padding: 0 0 2px 0;
}}
QLabel#heroSubtitle {{
    color: {muted};
    font-size: 13px;
    background: transparent;
}}
QLabel#glassTag {{
    color: {accent};
    background: {rgba('#FFFFFF', 36 if dark else 175)};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 7px 17px;
    font-size: 11px;
    font-weight: 700;
}}
QGroupBox {{
    background-color: {panel};
    border: 1px solid {border};
    border-top: 1px solid {bright_border};
    border-radius: 20px;
    margin-top: 18px;
    padding: 17px 14px 14px 14px;
    font-weight: 700;
    font-size: 14px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 18px;
    padding: 0 9px;
    background: transparent;
    color: {foreground};
}}
QGroupBox:hover {{
    border-color: {bright_border};
}}
QLineEdit, QSpinBox, QComboBox {{
    color: {foreground};
    background-color: {field};
    selection-background-color: {primary_end};
    border: 1px solid {border};
    border-radius: 11px;
    padding: 10px 12px;
    min-height: 21px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {accent};
    background-color: {panel_hover};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    color: {foreground};
    background-color: {QColor(background).name()};
    selection-background-color: {primary_end};
    selection-color: {primary_text};
    border: 1px solid {bright_border};
    outline: none;
}}
QPushButton {{
    color: {foreground};
    background: {secondary_button};
    border: 1px solid {border};
    border-top: 1px solid {bright_border};
    border-radius: 12px;
    padding: 10px 15px;
    min-height: 18px;
    font-weight: 650;
}}
QPushButton:hover {{
    background: {panel_hover};
    border-color: {bright_border};
}}
QPushButton:pressed {{
    background: {panel};
}}
QPushButton#primaryButton {{
    color: {primary_text};
    border: 1px solid {bright_border};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {primary_start}, stop:1 {primary_end});
    font-weight: 800;
}}
QPushButton#primaryButton:hover {{
    background: {primary_start};
}}
QPushButton:disabled {{
    color: {muted};
    background: {secondary_button};
}}
QCheckBox {{
    spacing: 9px;
    padding: 2px 1px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
}}
QSlider::groove:horizontal {{
    height: 6px;
    border-radius: 3px;
    background: {rgba('#FFFFFF', 78 if dark else 154)};
}}
QSlider::sub-page:horizontal {{
    border-radius: 3px;
    background: {progress};
}}
QSlider::handle:horizontal {{
    background: {primary_start};
    border: 2px solid {rgba('#FFFFFF', 195)};
    border-radius: 9px;
    width: 17px;
    margin: -7px 0;
}}
QProgressBar {{
    color: {foreground};
    border: 1px solid {border};
    background: {field};
    border-radius: 8px;
    text-align: center;
    min-height: 16px;
}}
QProgressBar::chunk {{
    border-radius: 7px;
    background: {progress};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 5px 0;
}}
QScrollBar::handle:vertical {{
    background: {rgba('#FFFFFF' if dark else '#34536C', 82)};
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


class GlassBackground(QWidget):
    """A painted aurora gradient visible through translucent child cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_color = '#101827'
        self.setAutoFillBackground(False)

    def set_base_color(self, value):
        color = QColor(value)
        if color.isValid():
            self._base_color = color.name()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        base = QColor(self._base_color)
        dark = is_dark_background(self._base_color)
        background = QLinearGradient(QPointF(0, 0), QPointF(self.width(), self.height()))
        background.setColorAt(0.0, base.lighter(116) if dark else base.lighter(104))
        background.setColorAt(0.52, base)
        background.setColorAt(1.0, base.darker(142) if dark else base.darker(113))
        painter.fillRect(self.rect(), background)

        # Soft glows produce depth even when the desktop compositor has no blur.
        spots = [
            (0.04, 0.02, 0.62, QColor(63, 190, 244, 103 if dark else 55)),
            (1.04, 0.41, 0.69, QColor(168, 90, 238, 83 if dark else 42)),
            (0.17, 1.03, 0.65, QColor(68, 234, 190, 69 if dark else 38)),
        ]
        scale = max(self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y, radius, center_color in spots:
            center = QPointF(self.width() * x, self.height() * y)
            size = scale * radius
            glow = QRadialGradient(center, size)
            edge = QColor(center_color)
            edge.setAlpha(0)
            glow.setColorAt(0.0, center_color)
            glow.setColorAt(1.0, edge)
            painter.setBrush(glow)
            painter.drawEllipse(center, size, size)
        painter.end()


def apply_glass_shadow(widget):
    """Subtle depth effect on a frosted card."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(30)
    shadow.setOffset(0, 7)
    shadow.setColor(QColor(0, 7, 26, 68))
    widget.setGraphicsEffect(shadow)
