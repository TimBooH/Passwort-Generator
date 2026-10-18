"""Glossy glass components for PasswortGenerator.

The reflections are painted by Qt on the translucent cards: actual layered
gradients and specular highlights, rather than a pale CSS background. This
simulates polished glass without relying on KWin's compositor blur.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor, QBrush, QLinearGradient, QPainter, QPainterPath, QPen,
    QPolygonF, QRadialGradient,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget,
)


def is_dark_background(color):
    """Determine light or dark palette from approximate perceived luminance."""
    tone = QColor(color)
    luminance = (0.2126 * tone.redF() + 0.7152 * tone.greenF()
                 + 0.0722 * tone.blueF())
    return luminance < 0.56


def rgba(color, opacity):
    """Produce a valid Qt stylesheet RGBA color and clamp the alpha channel."""
    tone = QColor(color)
    alpha = max(0, min(255, int(opacity)))
    return f'rgba({tone.red()}, {tone.green()}, {tone.blue()}, {alpha})'


def blend(a, b, ratio):
    """Mix two Qt colors; ratio=1 yields the second color."""
    start, end = QColor(a), QColor(b)
    ratio = max(0.0, min(1.0, float(ratio)))
    return QColor(
        round(start.red() * (1 - ratio) + end.red() * ratio),
        round(start.green() * (1 - ratio) + end.green() * ratio),
        round(start.blue() * (1 - ratio) + end.blue() * ratio),
    )


def with_alpha(color, opacity):
    new_color = QColor(color)
    new_color.setAlpha(max(0, min(255, int(opacity))))
    return new_color


def build_glass_stylesheet(background, foreground, opacity=54):
    """Readability-first controls to sit on top of our custom-painted glass."""
    dark = is_dark_background(background)
    opacity = max(30, min(85, int(opacity)))
    # The background remains subtly visible in the controls; no white slabs.
    field_alpha = min(232, 146 + opacity // 2) if dark else min(246, 188 + opacity // 2)
    field = rgba('#0C1B2B' if dark else '#F2F8FF', field_alpha)
    border = rgba('#B5E5FF' if dark else '#274565', 62 if dark else 42)
    border_focus = rgba('#93E2FF' if dark else '#2669A1', 188)
    muted = rgba(foreground, 190)
    button = rgba('#243A52' if dark else '#DEE9F7', 198 if dark else 229)
    button_hover = rgba('#355574' if dark else '#C8DEF1', 227 if dark else 245)
    primary_start = '#75DDF9' if dark else '#237CBF'
    primary_end = '#338FCF' if dark else '#125489'
    primary_text = '#0B1D2E' if dark else '#FFFFFF'
    select_bg = '#14283D' if dark else '#E9F1FB'
    select_fg = '#F3F9FF' if dark else '#192B3D'
    line = rgba('#FFFFFF' if dark else '#587EA1', 70 if dark else 76)
    progress = '#68D6F6' if dark else '#257EB5'

    return f"""
QMainWindow {{
    background: {QColor(background).name()};
}}
QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport {{
    background: transparent;
    border: none;
}}
QLabel {{
    color: {foreground};
    background: transparent;
}}
QLabel#heroTitle {{
    font-size: 25px;
    font-weight: 800;
    padding: 1px;
}}
QLabel#heroSubtitle {{
    font-size: 12px;
    color: {muted};
    padding: 0;
}}
QLabel#glassCardTitle {{
    font-size: 12px;
    font-weight: 750;
    color: {foreground};
    padding: 0 0 2px 0;
}}
QLabel#supportText {{
    color: {muted};
    font-size: 11px;
}}
QCheckBox {{
    color: {foreground};
    background: transparent;
    spacing: 9px;
    padding: 3px 0;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
}}
QLineEdit, QSpinBox, QComboBox {{
    color: {foreground};
    background: {field};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 9px 12px;
    selection-background-color: {primary_end};
    min-height: 22px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {border_focus};
}}
QComboBox::drop-down {{
    border: none;
    width: 25px;
}}
QComboBox QAbstractItemView {{
    color: {select_fg};
    background-color: {select_bg};
    selection-background-color: {primary_end};
    selection-color: {primary_text};
    border: 1px solid {border_focus};
    outline: 0;
}}
QPushButton {{
    color: {foreground};
    background: {button};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 9px 15px;
    min-height: 22px;
    font-weight: 650;
}}
QPushButton:hover {{
    background: {button_hover};
    border-color: {border_focus};
}}
QPushButton:pressed {{
    background: {field};
}}
QPushButton#primaryButton {{
    color: {primary_text};
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {primary_start}, stop:1 {primary_end});
    border: 1px solid {border_focus};
    font-weight: 800;
}}
QPushButton#primaryButton:hover {{
    background: {primary_start};
}}
QPushButton:disabled {{
    color: {muted};
    background: {button};
}}
QSlider::groove:horizontal {{
    height: 5px;
    border-radius: 2px;
    background: {line};
}}
QSlider::sub-page:horizontal {{
    background: {progress};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 15px;
    background: {primary_start};
    border: 2px solid {rgba('#FFFFFF', 130)};
    border-radius: 9px;
    margin: -7px 0;
}}
QProgressBar {{
    color: {foreground};
    border: 1px solid {border};
    background: {field};
    border-radius: 7px;
    min-height: 16px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {progress};
    border-radius: 6px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {line};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


class GlassBackground(QWidget):
    """Atmospheric background with soft off-center light sources."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_color = '#101827'
        self.setAutoFillBackground(False)

    def set_base_color(self, color):
        selected = QColor(color)
        if selected.isValid():
            self._base_color = selected.name()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        base = QColor(self._base_color)
        dark = is_dark_background(base)
        area = QRectF(self.rect())
        background = QLinearGradient(area.topLeft(), area.bottomRight())
        if dark:
            background.setColorAt(0.0, blend(base, '#263A59', 0.16))
            background.setColorAt(0.55, base)
            background.setColorAt(1.0, blend(base, '#060B15', 0.33))
        else:
            background.setColorAt(0.0, blend(base, '#FFFFFF', 0.15))
            background.setColorAt(0.55, base)
            background.setColorAt(1.0, blend(base, '#8F9DB6', 0.13))
        painter.fillRect(area, background)

        # Restrained illumination allows the glossy cards to be the focus.
        glow_sources = (
            (-0.09, 0.02, 0.61, QColor(55, 158, 235, 65 if dark else 31)),
            (1.11, 0.46, 0.70, QColor(109, 98, 225, 50 if dark else 29)),
            (0.07, 1.07, 0.48, QColor(20, 184, 173, 39 if dark else 21)),
        )
        diameter_scale = max(1, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y, radius, tint in glow_sources:
            center = QPointF(self.width() * x, self.height() * y)
            radial = QRadialGradient(center, diameter_scale * radius)
            radial.setColorAt(0.0, tint)
            radial.setColorAt(1.0, with_alpha(tint, 0))
            painter.setBrush(radial)
            painter.drawEllipse(center, diameter_scale * radius, diameter_scale * radius)
        painter.end()


class GlossyGlassCard(QWidget):
    """Custom painted glass tile with true specular highlights and edge lighting.

    Qt paints glass layers into its own surface: the surrounding background
    shines through the alpha-blended fill, with a glossy curved reflection
    across the top and a slim high-intensity rim around the entire tile.
    """

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._base_color = QColor('#101827')
        self._opacity = 54
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        column = QVBoxLayout(self)
        column.setContentsMargins(25, 23, 25, 25)
        column.setSpacing(7)
        self.header = QLabel(title)
        self.header.setObjectName('glassCardTitle')
        column.addWidget(self.header)
        column.addSpacing(7)
        self.body = QVBoxLayout()
        self.body.setSpacing(9)
        column.addLayout(self.body)

        depth = QGraphicsDropShadowEffect(self)
        depth.setBlurRadius(35)
        depth.setOffset(0, 9)
        depth.setColor(QColor(4, 11, 30, 82))
        self.setGraphicsEffect(depth)

    def set_glass_color(self, background, opacity):
        color = QColor(background)
        if color.isValid():
            self._base_color = color
        self._opacity = max(30, min(85, int(opacity)))
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w < 20 or h < 20:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        bounds = QRectF(5.5, 4.5, w - 11.0, h - 10.0)
        radius = 18.0
        outline = QPainterPath()
        outline.addRoundedRect(bounds, radius, radius)
        dark = is_dark_background(self._base_color)
        a = round(114 + self._opacity * 1.48)
        if dark:
            color_top = blend(self._base_color, '#426182', 0.47)
            color_bottom = blend(self._base_color, '#080F20', 0.63)
        else:
            color_top = blend(self._base_color, '#FFFFFF', 0.70)
            color_bottom = blend(self._base_color, '#B8CBDF', 0.33)

        painter.save()
        painter.setClipPath(outline)

        # Foundation: a cool glass volume that fades toward the lower edge.
        fill = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        fill.setColorAt(0.0, with_alpha(color_top, a - 18))
        fill.setColorAt(0.45, with_alpha(blend(color_top, color_bottom, .45), a))
        fill.setColorAt(1.0, with_alpha(color_bottom, min(245, a + 13)))
        painter.fillPath(outline, fill)

        # Gloss coat: brightest next to the light source, fading smoothly.
        upper = QLinearGradient(
            QPointF(bounds.left(), bounds.top()),
            QPointF(bounds.left() + bounds.width() * .18,
                    bounds.top() + min(135, bounds.height() * .53)),
        )
        upper.setColorAt(0.0, QColor(255, 255, 255, 64 if dark else 116))
        upper.setColorAt(.28, QColor(225, 245, 255, 34 if dark else 42))
        upper.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(bounds, upper)

        # A wide diagonal specular reflection: an actual reflective streak,
        # carefully kept faint so it does not obscure labels and controls.
        reflection = QPolygonF([
            QPointF(bounds.left() + bounds.width() * .03, bounds.top()),
            QPointF(bounds.left() + bounds.width() * .40, bounds.top()),
            QPointF(bounds.left() + bounds.width() * .12, bounds.bottom()),
            QPointF(bounds.left() - bounds.width() * .13, bounds.bottom()),
        ])
        streak = QLinearGradient(
            QPointF(bounds.left(), bounds.top()),
            QPointF(bounds.left() + bounds.width() * .46, bounds.top()),
        )
        streak.setColorAt(0.0, QColor(255, 255, 255, 2))
        streak.setColorAt(.46, QColor(255, 255, 255, 15 if dark else 22))
        streak.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(streak)
        painter.drawPolygon(reflection)

        # A diffuse icy highlight reflected on the upper right edge.
        glow_center = QPointF(bounds.right() - 32, bounds.top() - 40)
        shimmer = QRadialGradient(glow_center, max(95, bounds.width() * .37))
        shimmer.setColorAt(0, QColor(134, 219, 255, 39 if dark else 31))
        shimmer.setColorAt(1, QColor(134, 219, 255, 0))
        painter.fillRect(bounds, shimmer)
        painter.restore()

        # Thin Fresnel edge catches light mostly at the top-left. Darker
        # sides and a barely-visible lower edge add the sense of thickness.
        stroke = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        stroke.setColorAt(0.0, QColor(230, 249, 255, 159 if dark else 205))
        stroke.setColorAt(0.39, QColor(185, 224, 255, 65 if dark else 109))
        stroke.setColorAt(0.72, QColor(145, 185, 229, 44 if dark else 73))
        stroke.setColorAt(1.0, QColor(200, 236, 255, 81 if dark else 125))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QBrush(stroke), 1.25))
        painter.drawPath(outline)

        # Razor-fine bright line across the upper rim.
        top_light = QLinearGradient(
            QPointF(bounds.left() + 23, 0),
            QPointF(bounds.right() - 40, 0),
        )
        top_light.setColorAt(0, QColor(255, 255, 255, 0))
        top_light.setColorAt(.17, QColor(247, 254, 255, 192 if dark else 234))
        top_light.setColorAt(.58, QColor(240, 251, 255, 72 if dark else 98))
        top_light.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(QPen(QBrush(top_light), 1.3))
        painter.drawLine(
            QPointF(bounds.left() + 25, bounds.top() + 1.35),
            QPointF(bounds.right() - 36, bounds.top() + 1.35),
        )

        # Inner second rim gives the illusion of a beveled glass edge.
        inner = bounds.adjusted(2.0, 2.0, -2.0, -2.0)
        inset = QPainterPath()
        inset.addRoundedRect(inner, radius - 2, radius - 2)
        painter.setPen(QPen(QColor(255, 255, 255, 16 if dark else 35), .75))
        painter.drawPath(inset)
        painter.end()
