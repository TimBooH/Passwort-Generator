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
