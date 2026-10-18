"""Adaptive accessible colors for the password generator's Qt interface.

The accent follows the dominant background hue, but remains high-contrast
against both light and dark surfaces, including custom wallpaper images.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

COLOR_SCHEMES = (
    ('neon_blue', 'Neon Blue', '#071322', '#FFFFFF'),
    ('glass_dark', 'Glass Dark', '#171C26', '#F0F4FC'),
    ('glass_light', 'Glass Light', '#F0F4FA', '#142436'),
    ('violet_glass', 'Violet Glass', '#2B1D3A', '#F6EDFF'),
    ('forest_glass', 'Forest Glass', '#15362E', '#F0FFF7'),
    ('custom', 'Eigene Farben', None, None),
)
SCHEME_MAP = {key: (label, bg, fg) for key, label, bg, fg in COLOR_SCHEMES}
DEFAULT_SCHEME = 'neon_blue'


def _as_color(value):
    color = QColor(value)
    if not color.isValid():
        raise ValueError('Ungültige Hintergrundfarbe.')
    return color


def relative_luminance(value):
    """WCAG relative luminance, gamma-corrected for sRGB (0..1)."""
    color = _as_color(value)
    channels = (color.redF(), color.greenF(), color.blueF())
    linear = tuple(x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4
                   for x in channels)
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def contrast_ratio(foreground, background):
    light, dark = sorted((
        relative_luminance(foreground),
        relative_luminance(background),
    ), reverse=True)
    return (light + .05) / (dark + .05)


def is_light_background(background):
    return relative_luminance(background) >= .18


def accessible_text_color(background):
    """Use legible text automatically; a separate text-color control isn't needed."""
    background = _as_color(background)
    light, dark = '#FFFFFF', '#070D15'
    return (light if contrast_ratio(light, background) >=
            contrast_ratio(dark, background) else dark)


def accent_for_background(background):
    """Match the background hue while ensuring contrast for buttons and lines.

    Neutral grays use cyan-blue; colored surfaces preserve their actual hue.
    Stronger contrast wins for medium-brightness backgrounds (WCAG graphics).
    """
    base = _as_color(background)
    hue = base.hsvHue() if base.hsvSaturationF() >= .13 else 198
    hue = max(0, hue)
    # Blue/violet/red can be dark despite a full HSV brightness value.
    # Desaturate towards a pastel shade until the color truly stands out.
    vivid = QColor.fromHsv(hue, 217, 250)
    for saturation in (217, 185, 150, 115, 80, 50, 0):
        option = QColor.fromHsv(hue, saturation, 250)
        vivid = option
        if contrast_ratio(option, base) >= 4.5:
            break
    # On light/medium surfaces choose a deeper version of the same hue.
    deep = QColor.fromHsv(hue, 211, 115)
    for value in (115, 100, 85, 70, 55, 40, 25):
        option = QColor.fromHsv(hue, 211, value)
        deep = option
        if contrast_ratio(option, base) >= 4.5:
            break
    light_contrast = contrast_ratio(vivid, base)
    dark_contrast = contrast_ratio(deep, base)
    preferred_light = not is_light_background(base)
    if preferred_light and light_contrast >= 4.5:
        chosen = vivid
    elif not preferred_light and dark_contrast >= 4.5:
        chosen = deep
    else:
        chosen = vivid if light_contrast >= dark_contrast else deep
    return chosen.name().upper()


def sample_wallpaper_color(pixmap):
    """Find a representative wallpaper color from a tiny downsampled copy.

    Does not repaint the wallpaper, create a QPainter, or read any disk data.
    Most saturated colors are weighted slightly higher to preserve image hue.
    """
    if pixmap is None or pixmap.isNull():
        return None
    image = pixmap.toImage().scaled(
        24, 24, Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )
    totals = [0.0, 0.0, 0.0]
    count = 0.0
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() < 30:
                continue
            weight = 1.0 + min(1.0, pixel.hsvSaturationF()) * .8
            totals[0] += pixel.red() * weight
            totals[1] += pixel.green() * weight
            totals[2] += pixel.blue() * weight
            count += weight
    if count <= 0:
        return None
    color = QColor(*(round(value / count) for value in totals))
    return color.name().upper()


def preset_colors(scheme):
    """Return legacy (background, text) values; UI always chooses its own text."""
    entry = SCHEME_MAP.get(scheme)
    if entry is None or entry[1] is None:
        return None
    return entry[1], entry[2]
