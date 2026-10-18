"""Stable color presets and automatically derived, contrasting accent colors.

No secrets, persistent state or GUI widgets are used here; QColor is sufficient.
"""

from PySide6.QtGui import QColor

# The last preset is a manual scheme: it retains colors saved in QSettings.
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


def is_light_background(background):
    color = QColor(background)
    if not color.isValid():
        raise ValueError('Ungültige Hintergrundfarbe.')
    # Account for perceived brightness rather than just raw HSV "value".
    brightness = .2126 * color.redF() + .7152 * color.greenF() + .0722 * color.blueF()
    return brightness >= .56


def accent_for_background(background):
    """Return an eye-catching accent that follows the background hue.

    Unsaturated backgrounds receive a modern cyan/blue accent. For colored
    backgrounds the accent hue shifts slightly away from the surface color.
    Dark surfaces get bright accents; light surfaces get deeper accents.
    """
    base = QColor(background)
    if not base.isValid():
        raise ValueError('Ungültige Hintergrundfarbe.')
    if base.hsvSaturationF() < .13:
        hue = 201
    else:
        hue = (base.hsvHue() + 26) % 360
    if is_light_background(base):
        # Saturated but dark enough to remain legible on white backgrounds.
        candidate = QColor.fromHsv(hue, 212, 137)
    else:
        candidate = QColor.fromHsv(hue, 218, 249)
    return candidate.name().upper()


def preset_colors(scheme):
    """Return (background, foreground), or None for custom/unknown schemes."""
    entry = SCHEME_MAP.get(scheme)
    if entry is None or entry[1] is None:
        return None
    return entry[1], entry[2]
