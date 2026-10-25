"""Tiny checked-checkbox PNG for Ocean Glass, bundled as an in-memory constant.

Decode into a private temporary directory once per process so Qt's native
stylesheet engine can render it. No Python widget paintEvent, image-generation
dependency, network use, or persistent user data is involved.
"""

import base64
from pathlib import Path
from tempfile import TemporaryDirectory


_ICON_DATA = (
    'iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAAsklEQVR42rXV0Q2EIAwA'
    '0NIcE9wSbqMzOIRD3BDOoNu4hBPwwX1psGmloYUfAoSXlhIA6NQCnZiPnFugdQgP60'
    'PRbU9NEc5HziWOHigAwLanR7bogXI4WrFziew8eqAcjl6R0jF6pf/9JRusQV9hq'
    'SgaVISlotCxhLKwhGkzEGEuCu25Vo+itqm2/lo8abMGrV63C6G9GW5Fb3gdQpjG'
    'aH2PYBrj/eBj+QNY8BLt+jV1a38Z8Fq9E630IQAAAABJRU5ErkJggg=='
)
_temp_dir = None
_icon_path = None


def checkmark_png_path():
    """A stable absolute filename whose lifetime matches the app process."""
    global _temp_dir, _icon_path
    if _icon_path is not None:
        return _icon_path
    try:
        tmp = TemporaryDirectory(prefix='passwortgenerator-glass-')
        path = Path(tmp.name) / 'checked.png'
        path.write_bytes(base64.b64decode(_ICON_DATA))
        _temp_dir = tmp
        _icon_path = path.as_posix()
        return _icon_path
    except (OSError, ValueError):
        return None


# Small, precisely drawn two-state slider icons for all application switches.
# Use Qt's own rasterizer to keep rendering identical on Linux and Windows.
_switch_icons = None
_switch_dir = None


def switch_png_paths():
    """Return (off, on) image paths valid for this process' lifetime."""
    global _switch_icons, _switch_dir
    if _switch_icons is not None:
        return _switch_icons

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPen

    folder = TemporaryDirectory(prefix='passwortgenerator-switches-')
    paths = []
    for enabled in (False, True):
        image = QImage(64, 36, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(2, 2)
        painter.setPen(QPen(QColor('#5DA0D0' if enabled else '#5482B0'), 1))
        painter.setBrush(QColor('#078ED9' if enabled else '#163455'))
        painter.drawRoundedRect(QRectF(0.5, 0.5, 31, 17), 8.5, 8.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#EAFBFF' if enabled else '#AEC4DC'))
        painter.drawEllipse(QRectF(17, 3, 12, 12) if enabled else QRectF(3, 3, 12, 12))
        painter.end()
        path = Path(folder.name) / ('switch-on.png' if enabled else 'switch-off.png')
        if not image.save(str(path), 'PNG'):
            folder.cleanup()
            raise RuntimeError('Ocean Glass switch icon could not be saved.')
        paths.append(path.as_posix())
    _switch_dir = folder
    _switch_icons = tuple(paths)
    return _switch_icons
