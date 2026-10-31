"""The same bundled font on Linux and Windows, including frozen builds."""
from functools import lru_cache
from pathlib import Path
import sys
from PySide6.QtGui import QFont, QFontDatabase


@lru_cache(maxsize=1)
def reference_font_family():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    families = []
    for name in ('Carlito-Regular.ttf', 'Carlito-Bold.ttf', 'DejaVuSansMono.ttf'):
        font_id = QFontDatabase.addApplicationFont(str(root / 'assets' / 'fonts' / name))
        if font_id < 0:
            raise RuntimeError(f'Bundled interface font is missing or invalid: {name}')
        families.extend(QFontDatabase.applicationFontFamilies(font_id))
    return families[0]


def reference_font():
    font = QFont(reference_font_family(), 11)
    font.setWeight(QFont.Weight.Normal)
    return font
