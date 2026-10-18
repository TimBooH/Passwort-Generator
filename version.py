"""Release numbering: 99 development milestones, then 1.0.0 as full release.

The earlier 1.2.x–1.5.x tags were published before the scheme reset.
They are retained on GitHub for transparency and are treated as legacy builds.
"""

from password_core import parse_version

APP_VERSION = "0.03.0"
FULL_RELEASE_VERSION = "1.0.0"
TOTAL_RELEASE_STEPS = 100

# Releases published before introducing the 100-step development roadmap.
# Their names are never reused; otherwise GitHub update checks are ambiguous.
LEGACY_RELEASES = frozenset({
    (1, 2, 0),
    (1, 3, 0),
    (1, 3, 1),
    (1, 4, 0),
    (1, 5, 0),
    (1, 5, 1),
})


def release_step(version=APP_VERSION):
    """1..99 for v0.01.0..v0.99.x, 100 for v1.0.x, None otherwise."""
    number = parse_version(version)
    if number is None:
        return None
    major, minor, _patch = number
    if major == 0 and 1 <= minor <= 99:
        return minor
    if major == 1 and minor == 0:
        return TOTAL_RELEASE_STEPS
    return None


def version_status(version=APP_VERSION):
    """Human-friendly progress label shown in the interface."""
    step = release_step(version)
    if step is None:
        return ""
    if step >= TOTAL_RELEASE_STEPS:
        return "Vollversion"
    return f"Entwicklung {step:02d}/{TOTAL_RELEASE_STEPS}"


def is_newer_release(latest_tag, current_version=APP_VERSION):
    """Compare new-series tags while excluding historical 1.x releases.

    A previously published v1.5.1 must not appear as an upgrade from
    v0.01.0. This helper cannot retroactively change older 1.5.1 clients:
    those users must install the first 0.xx version manually once.
    """
    newest = parse_version(latest_tag)
    current = parse_version(current_version)
    if newest is None or current is None:
        return False
    if newest in LEGACY_RELEASES and current not in LEGACY_RELEASES:
        return False
    if current in LEGACY_RELEASES and newest not in LEGACY_RELEASES:
        return True
    return newest > current
