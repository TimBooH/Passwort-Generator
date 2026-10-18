"""Crash-resistant Qt glass widgets and selectable background images.

No QGraphicsDropShadowEffect: shadows are painted directly to avoid expensive
offscreen widget-effect buffers on every resize. Images are decoded once at a
bounded resolution; resize uses only source/destination geometry.
"""

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, QTimer, Qt
from PySide6.QtGui import (
    QColor, QBrush, QImageReader, QPalette, QPixmap,
)
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


IMAGE_MODES = (
    ('Ausfüllen (ohne Rand)', 'cover'),
    ('Einpassen (ganzes Bild)', 'contain'),
    ('Gestreckt', 'stretch'),
    ('Zentriert (100 %)', 'center'),
    ('Original (links oben)', 'original'),
    ('Gekachelt', 'tile'),
)
MODE_IDS = frozenset(mode for _, mode in IMAGE_MODES)
MAX_IMAGE_FILE = 30 * 1024 * 1024
MAX_DECODE_EDGE = 4096
MAX_IMAGE_PIXELS = 110_000_000


def is_dark_background(color):
    tone = QColor(color)
    luminosity = 0.2126 * tone.redF() + 0.7152 * tone.greenF() + 0.0722 * tone.blueF()
    return luminosity < 0.56


def rgba(color, opacity):
    tone = QColor(color)
    alpha = max(0, min(255, int(opacity)))
    return f'rgba({tone.red()}, {tone.green()}, {tone.blue()}, {alpha})'


def blend(a, b, ratio):
    start, end = QColor(a), QColor(b)
    factor = max(0.0, min(1.0, float(ratio)))
    return QColor(
        round(start.red() * (1 - factor) + end.red() * factor),
        round(start.green() * (1 - factor) + end.green() * factor),
        round(start.blue() * (1 - factor) + end.blue() * factor),
    )


def with_alpha(color, opacity):
    colored = QColor(color)
    colored.setAlpha(max(0, min(255, int(opacity))))
    return colored


def image_rectangles(mode, canvas_w, canvas_h, image_w, image_h):
    """Compute stable Qt drawPixmap(target, pixmap, source) geometry.

    Returns (targetRect, sourceRect). Tile is handled separately using QBrush.
    Decoded images larger than 4096px are intentionally scaled down for safety.
    """
    w, h, iw, ih = map(float, (canvas_w, canvas_h, image_w, image_h))
    if min(w, h, iw, ih) <= 0:
        return None
    source = QRectF(0.0, 0.0, iw, ih)
    if mode == 'stretch':
        return QRectF(0.0, 0.0, w, h), source
    if mode == 'contain':
        factor = min(w / iw, h / ih)
        out_w, out_h = iw * factor, ih * factor
        return QRectF((w - out_w) / 2, (h - out_h) / 2, out_w, out_h), source
    if mode == 'cover':
        factor = max(w / iw, h / ih)
        crop_w, crop_h = w / factor, h / factor
        crop = QRectF((iw - crop_w) / 2, (ih - crop_h) / 2, crop_w, crop_h)
        return QRectF(0.0, 0.0, w, h), crop
    if mode == 'center':
        return QRectF((w - iw) / 2, (h - ih) / 2, iw, ih), source
    if mode == 'original':
        return QRectF(0.0, 0.0, iw, ih), source
    return None


def read_background_image(path):
    """Read an image once with a strict pixel budget; raise for invalid files."""
    candidate = Path(path).expanduser()
    try:
        size_bytes = candidate.stat().st_size
    except OSError as exc:
        raise ValueError(f'Bilddatei nicht gefunden: {candidate.name}') from exc
    if size_bytes < 1 or size_bytes > MAX_IMAGE_FILE:
        raise ValueError('Das Bild ist leer oder größer als 30 MB.')
    reader = QImageReader(str(candidate))
    reader.setAutoTransform(True)
    if not reader.canRead():
        raise ValueError('Bildformat ungültig. Bitte PNG, JPG, WEBP oder BMP verwenden.')
    size = reader.size()
    if not size.isValid() or size.width() <= 0 or size.height() <= 0:
        raise ValueError('Das Bild hat keine gültigen Abmessungen.')
    if size.width() * size.height() > MAX_IMAGE_PIXELS:
        raise ValueError('Das Bild ist extrem groß. Bitte ein kleineres Bild verwenden.')
    factor = min(1.0, MAX_DECODE_EDGE / max(size.width(), size.height()))
    if factor < 1.0:
        reader.setScaledSize(
            QSize(max(1, round(size.width() * factor)), max(1, round(size.height() * factor)))
        )
    image = reader.read()
    if image.isNull():
        raise ValueError('Bild konnte nicht gelesen werden: ' + reader.errorString())
    pixmap = QPixmap.fromImage(image)
    if pixmap.isNull():
        raise ValueError('Bild konnte nicht als Hintergrund verwendet werden.')
    return pixmap


def build_glass_stylesheet(background, foreground):
    """Style fields and buttons once per palette change, never on resize."""
    dark = is_dark_background(background)
    field = rgba('#0C1B2B' if dark else '#F2F8FF', 174 if dark else 215)
    border = rgba('#B5E5FF' if dark else '#274565', 62 if dark else 45)
    focus = rgba('#93E2FF' if dark else '#2669A1', 188)
    muted = rgba(foreground, 195)
    button = rgba('#243A52' if dark else '#DEE9F7', 195 if dark else 225)
    hover = rgba('#355574' if dark else '#C8DEF1', 222 if dark else 241)
    primary_start = '#75DDF9' if dark else '#237CBF'
    primary_end = '#338FCF' if dark else '#125489'
    primary_text = '#0B1D2E' if dark else '#FFFFFF'
    selection_bg = '#14283D' if dark else '#E9F1FB'
    selection_fg = '#F3F9FF' if dark else '#192B3D'
    line = rgba('#FFFFFF' if dark else '#587EA1', 70)
    progress = '#68D6F6' if dark else '#257EB5'
    return f"""
QMainWindow {{ background-color: {QColor(background).name()}; }}
QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport {{
    border: none;
    background: transparent;
}}
QWidget#contentColumn {{ background: transparent; }}
QLabel {{
    color: {foreground};
    background: transparent;
}}
QLabel#heroTitle {{ font-size: 25px; font-weight: 800; padding: 1px; }}
QLabel#heroSubtitle {{ color: {muted}; font-size: 12px; padding: 0; }}
QLabel#glassCardTitle {{ color: {foreground}; font-size: 12px; font-weight: 700; }}
QLabel#supportText {{ color: {muted}; font-size: 11px; }}
QLabel#globalStatus {{ color: {muted}; font-size: 11px; padding: 0 4px; }}
QWidget#passwordPage, QWidget#settingsPage, QWidget#updatesPage {{
    background: transparent;
}}
QTabWidget#mainTabs::pane {{
    border: none;
    background: transparent;
    top: 0;
}}
QTabBar::tab {{
    color: {muted};
    background: {button};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 9px 14px;
    margin-right: 5px;
    min-width: 82px;
    font-weight: 700;
}}
QTabBar::tab:selected {{
    color: {foreground};
    background: {field};
    border-color: {focus};
    border-bottom: 3px solid {primary_start};
}}
QTabBar::tab:hover:!selected {{
    background: {hover};
    color: {foreground};
}}
QCheckBox {{ color: {foreground}; background: transparent; spacing: 9px; padding: 3px 0; }}
QCheckBox::indicator {{ width: 17px; height: 17px; }}
QLineEdit, QSpinBox, QComboBox {{
    color: {foreground};
    background: {field};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 8px 11px;
    min-height: 21px;
    selection-background-color: {primary_end};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {focus}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    color: {selection_fg};
    background: {selection_bg};
    selection-background-color: {primary_end};
    selection-color: {primary_text};
    border: 1px solid {focus};
    outline: none;
}}
QPushButton {{
    color: {foreground};
    background: {button};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 8px 12px;
    min-height: 22px;
    font-weight: 650;
}}
QPushButton:hover {{ background: {hover}; border-color: {focus}; }}
QPushButton:pressed {{ background: {field}; }}
QPushButton#primaryButton {{
    color: {primary_text};
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {primary_start}, stop:1 {primary_end});
    border: 1px solid {focus};
    font-weight: 800;
}}
QPushButton#primaryButton:hover {{ background: {primary_start}; }}
QPushButton:disabled {{ color: {muted}; background: {button}; }}
QProgressBar {{
    color: {foreground};
    border: 1px solid {border};
    background: {field};
    border-radius: 7px;
    min-height: 16px;
    text-align: center;
}}
QProgressBar::chunk {{ background: {progress}; border-radius: 6px; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 4px 0; }}
QScrollBar::handle:vertical {{
    background: {line};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


class GlassBackground(QWidget):
    """Stable, native Qt background: no Python paintEvent during window resize.

    The image is rendered by an ordinary QLabel, and color gradients by QSS.
    Scaling happens after a short resize debounce instead of every resize event.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('appRoot')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._base_color = '#101827'
        self._image = QPixmap()
        self._mode = 'cover'

        self._backdrop = QLabel(self)
        self._backdrop.setObjectName('wallpaperPixmap')
        self._backdrop.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._backdrop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._backdrop.hide()
        self._shade = QFrame(self)
        self._shade.setObjectName('wallpaperShade')
        self._shade.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._shade.hide()
        self._apply_color_style()

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(85)
        self._resize_timer.timeout.connect(self._render_image)

    def _apply_color_style(self):
        base = QColor(self._base_color)
        dark = is_dark_background(base)
        first = blend(base, '#263A59', .15) if dark else base.lighter(107)
        last = blend(base, '#070C17', .25) if dark else base.darker(108)
        self.setStyleSheet(
            'QWidget#appRoot { '
            'background: qlineargradient(x1:0, y1:0, x2:1, y2:1, '
            f'stop:0 {first.name()}, stop:0.58 {base.name()}, '
            f'stop:1 {last.name()}); }}'
        )
        self._shade.setStyleSheet(
            'QFrame#wallpaperShade { '
            f'background: {rgba("#050912" if dark else "#FAFCFF", 79 if dark else 39)}; '
            'border: none; }'
        )

    def set_base_color(self, value):
        color = QColor(value)
        if color.isValid() and color.name() != self._base_color:
            self._base_color = color.name()
            self._apply_color_style()

    def set_background_image(self, path):
        loaded = read_background_image(path)
        self._image = loaded
        self._backdrop.show()
        self._shade.show()
        self._render_image()

    def clear_background_image(self):
        self._image = QPixmap()
        self._resize_timer.stop()
        self._backdrop.clear()
        self._backdrop.hide()
        self._shade.hide()

    def has_background_image(self):
        return not self._image.isNull()

    def set_image_mode(self, mode):
        if mode in MODE_IDS and self._mode != mode:
            self._mode = mode
            if self.has_background_image():
                self._render_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._backdrop.setGeometry(self.rect())
        self._shade.setGeometry(self.rect())
        self._backdrop.lower()
        if self.has_background_image():
            self._resize_timer.start()

    def _render_image(self):
        if self._image.isNull() or self.width() <= 0 or self.height() <= 0:
            return
        size = self.size()
        self._backdrop.setGeometry(self.rect())
        if self._mode == 'tile':
            # QPalette fills the QLabel using a native texture brush.
            pal = self._backdrop.palette()
            pal.setBrush(QPalette.ColorRole.Window, QBrush(self._image))
            self._backdrop.setPalette(pal)
            self._backdrop.setAutoFillBackground(True)
            self._backdrop.clear()
        else:
            self._backdrop.setAutoFillBackground(False)
            self._backdrop.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                if self._mode == 'original' else Qt.AlignmentFlag.AlignCenter
            )
            if self._mode == 'contain':
                image = self._image.scaled(
                    size, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            elif self._mode == 'cover':
                image = self._image.scaled(
                    size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            elif self._mode == 'stretch':
                image = self._image.scaled(
                    size, Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            else:
                image = self._image
            self._backdrop.setPixmap(image)
        self._backdrop.show()
        self._shade.show()
        self._backdrop.lower()


class GlossyGlassCard(QWidget):
    """Glossy tile drawn by Qt's native style engine, not Python paintEvent.

    A QSS gradient and narrow highlight rim mimic polished glass. In particular
    no custom Python painter and no QGraphicsEffect are involved in resizing.
    """

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName('glossyCard')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._base_color = QColor('#101827')
        self._last_style = None

        column = QVBoxLayout(self)
        column.setContentsMargins(22, 19, 22, 22)
        column.setSpacing(7)
        self.highlight = QFrame(self)
        self.highlight.setObjectName('glassRim')
        self.highlight.setFixedHeight(2)
        column.addWidget(self.highlight)
        column.addSpacing(4)
        self.header = QLabel(title)
        self.header.setObjectName('glassCardTitle')
        column.addWidget(self.header)
        column.addSpacing(4)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        column.addLayout(self.body)

        # Coalesce rapid background color changes into a single Qt style update.
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(75)
        self._refresh_timer.timeout.connect(self._refresh_style)
        self._refresh_style()

    def set_glass_color(self, background):
        candidate = QColor(background)
        if not candidate.isValid() or candidate.name() == self._base_color.name():
            return
        self._base_color = candidate
        self._refresh_timer.start()

    def _refresh_style(self):
        dark = is_dark_background(self._base_color)
        base = self._base_color
        top = blend(base, '#4B6988' if dark else '#FFFFFF', .43 if dark else .65)
        mid = blend(base, '#223851' if dark else '#E8F2FA', .42 if dark else .58)
        end = blend(base, '#080F20' if dark else '#C4D3DF', .6 if dark else .31)
        alpha = 174  # Consistent glossy finish; no adjustable opacity.
        top_rgba = rgba(top, alpha - 20)
        mid_rgba = rgba(mid, alpha)
        end_rgba = rgba(end, min(248, alpha + 12))
        edge = rgba('#E3F5FF' if dark else '#7E9AB2', 92 if dark else 101)
        light_edge = rgba('#F3FBFF', 157 if dark else 189)
        white_spot = rgba('#FFFFFF', 168 if dark else 209)
        css = f"""
QWidget#glossyCard {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {top_rgba}, stop:0.47 {mid_rgba}, stop:1 {end_rgba});
    border: 1px solid {edge};
    border-top: 1px solid {light_edge};
    border-radius: 18px;
}}
QFrame#glassRim {{
    border: none;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(255,255,255,0),
        stop:0.24 {white_spot},
        stop:0.70 rgba(220,245,255,75),
        stop:1 rgba(255,255,255,0));
}}
"""
        if css != self._last_style:
            self._last_style = css
            self.setStyleSheet(css)
