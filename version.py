"""Release numbering: 99 development milestones, then 1.0.0 as full release.

Version 0.18.0 unifies the language choice across every page, translates
cached Changelog content, supports bilingual notes, and provides faithful
English summaries of historical German-only releases.
Version 0.17.0 adds a persistent German/English language switch for the entire
Qt interface and onboarding, plus a matching English GitHub README.
Version 0.16.0 simplifies README documentation while preserving app behavior.
Version 0.15.0 compacts the appearance and Changelog card spacing and
renames the update checker action to Auf Update prüfen.
Version 0.14.1 preserves the Glass styling of both combined tiles and
checks the appearance layout on both platforms.
Version 0.14.0 restores the Update navigation and merges the release history
and notes into one Changelog glass tile, and appearance settings into one tile.
Version 0.13.0 renames the Updates navigation to Changelog while retaining
update checks and release history on Linux and Windows.
Version 0.12.0 provides release history in a newest-first dropdown,
a separate changelog glass tile, distinct creator/help cards, compact
left-aligned update checks, and persistent size/position via QSettings.
Version 0.11.0 preloads all graphical explanation previews so hidden tabs
are immediately illustrated on Windows and Linux.
Version 0.11.0 keeps three navigation action labels with a separate fourth
Info action and validates that page without legacy modal assumptions.
Version 0.11.0 precisely targets real widgets with the arrow tour, embeds
Info and graphical guidance as a fourth page, and replaces scrolling with
compact layouts and paginated release history on Windows and Linux.
Version 0.10.0 checks widget transparency in a dedicated GUI smoke process,
not during unittest interpreter teardown, to avoid native Qt refcount crashes.
Version 0.10.0 restores the pure Glass palette and transparency engine
in both Linux and Windows release builds.
Version 0.10.0 adds a once-per-startup update popup, pure see-through Glass
cards, and a persisted first-run arrow-guided tour (replayable from Info).
Version 0.09.0 uses milestone-independent mock releases for GUI regression tests.
Version 0.09.0 adds test syntax prechecks and requires a one-time manual
Windows installer run when migrating from per-user AppData to Program Files.
Version 0.09.0 restores the graphical explanation, adds passphrase number/separator
options, and moves Windows setup to protected 64-bit Program Files with UAC.
Version 0.08.1 removed the written tutorial while retaining author and version.
Version 0.08.0 sizes each page independently so the Updates screen cannot
force a scrollbar onto the Password screen.
Version 0.08.0 adds two-hour update checks, visible badge, compact pages,
and an in-memory illustrated guide for Linux and Windows.
Version 0.07.0 chooses accessible automatic text even on medium-tone backgrounds
and preserves the accent hue rather than reusing the exact accent brightness.
Version 0.07.0 verifies adaptive accent contrast across violet and muted themes.
Version 0.07.0 returns navigation to the top-right, lowers glass opacity,
and uses readable auto-contrasting accents, including wallpaper previews.
Version 0.06.0 streamlined sidebar navigation, responsive cards, and release history.
The GUI smoke test checks concise release notes rather than obsolete headings.
Version 0.05.0 added configurable glass schemes and release-history browsing.
Neon artwork stays cached across palette changes to avoid native Qt crashes.
The earlier 1.2.x–1.5.x tags were published before the scheme reset.
They are retained on GitHub for transparency and are treated as legacy builds.
"""

from password_core import parse_version

APP_VERSION = "0.18.0"
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
