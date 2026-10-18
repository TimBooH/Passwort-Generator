"""Present GitHub release notes in the language selected for the entire app.

Current releases can contain '## Deutsch' and '## English' sections. Historical
German-only releases have curated English summaries, based on the published
release notes, so choosing English never reverts the Changelog to German.
The underlying GitHub release bodies are never modified.
"""

import re

from release_history import compact_changelog
from localization import translate

# Faithful concise descriptions of the original GitHub release notes, not a
# machine-generated guess at runtime. Old 1.x tags are intentionally included.
LEGACY_EN_NOTES = {
    'v0.01.0': (
        'Introduced the 100-step release plan leading to version 1.0.0.',
        'Previous 1.x releases remain available as history; switching series requires a manual installation.',
        'Secure local password generation, AppImage updates and the previous-version backup remain.',
    ),
    'v0.02.0': (
        'Removed the glass-opacity slider and obsolete settings.',
        'Kept a consistent translucent glass appearance.',
        'Updated UI, resize and design regression tests.',
    ),
    'v0.03.0': (
        'Introduced three tabs for passwords, settings and updates.',
        'Kept the glass cards, wallpaper selection and update functions.',
        'Added GUI tests for navigation and window resizing.',
    ),
    'v0.04.0': (
        'Introduced a dark-blue neon look with glossy glass cards.',
        'Added password/passphrase mode selection and generation controls.',
        'Added random multiword passphrases and a strength indicator.',
        'Added session-only history and additional GUI tests.',
    ),
    'v0.05.0': (
        'Added selectable color themes and automatic accent colors.',
        'Added a release-history list and compact Changelog.',
        'Added a creator credit and help to the Info section.',
        'Retained secure downloads and previous-version backups.',
    ),
    'v0.06.0': (
        'Moved navigation to the left and simplified the glass-card layout.',
        'Displayed newer releases first and shortened the Changelog.',
        'Removed unnecessary release-history action buttons.',
    ),
    'v0.07.0': (
        'Moved password, settings and updates navigation to the top-right.',
        'Improved automatic text contrast and transparency.',
        'Made accent colors adapt to the background and wallpaper.',
        'Added real app screenshots to the README build.',
    ),
    'v0.08.0': (
        'Added an update-available indicator to the navigation.',
        'Enabled update checks at startup and every two hours.',
        'Reduced button sizes and removed unnecessary scrolling.',
        'Added an illustrated guide to the Info section.',
    ),
    'v0.08.1': (
        'Simplified Info by removing the lengthy text guide.',
        'Kept the creator credit, version and short description.',
        'Kept password generation, themes and update checks unchanged.',
    ),
    'v0.09.0': (
        'Restored the three-screen illustrated guide.',
        'Added optional random two-digit numbers to passphrases.',
        'Added configurable passphrase separators.',
        'Moved the Windows installer to Program Files with administrator approval.',
    ),
    'v0.10.0': (
        'Added an update popup at startup.',
        'Introduced a more transparent Glass theme.',
        'Added a first-run guided tour with arrows and replay controls.',
        'Retained the two-hour update check on both platforms.',
    ),
    'v0.11.0': (
        'Fixed arrow positions in the first-run tour.',
        'Moved Info into the main window.',
        'Kept graphical help without page scrollbars.',
        'Improved window layout on Windows and Linux.',
    ),
    'v0.12.0': (
        'Added a newest-first dropdown for published versions.',
        'Placed release changes in a separate glass card.',
        'Added a smaller, left-aligned update-check button.',
        'Saved and restored window size and position.',
    ),
    'v0.13.0': (
        'Renamed the Updates navigation tab to Changelog.',
        'Updated navigation labels, visual help and regression tests.',
        'Retained update checks and release-history features.',
    ),
    'v0.14.0': (
        'Renamed the navigation tab back to Update.',
        'Combined previous versions and change notes into one Changelog card.',
        'Combined appearance settings and wallpaper into one card.',
    ),
    'v0.14.1': (
        'Renamed the navigation tab back to Update.',
        'Combined previous versions and change notes into one Changelog card.',
        'Combined appearance settings and wallpaper into one card.',
        'Preserved the glossy glass styling of both merged cards.',
    ),
    'v0.15.0': (
        'Renamed the button to Check for updates.',
        'Reduced spacing in the Changelog and Appearance cards.',
        'Kept the controls top-aligned and the glass design unchanged.',
    ),
    'v0.16.0': (
        'Shortened and streamlined the GitHub README.',
        'Kept direct downloads, screenshots, features and installation instructions.',
        'Removed old version lists and redundant technical details.',
        'No changes to password generation or the app interface.',
    ),
    'v1.2.0': (
        'Moved the Linux app to the Passwort-Generator GitHub repository.',
        'Added user-level installation with an application-menu shortcut.',
        'Added manual and automatic update checks and checksum-verified AppImage downloads.',
    ),
    'v1.3.0': (
        'Introduced translucent glass cards and an Aurora background.',
        'Added adjustable glass opacity and saved color preferences.',
        'Redesigned buttons and progress indicators.',
    ),
    'v1.3.1': (
        'Refined glossy glass cards with light reflections and smoother edges.',
        'Improved contrast and layout for the dark interface.',
        'Kept secure local generation and verified GitHub updates.',
    ),
    'v1.4.0': (
        'Added custom wallpapers and six image display modes.',
        'Saved background preferences and added local crash diagnostics.',
        'Improved Qt stability, performance and resize tests.',
    ),
    'v1.5.0': (
        'Improved stability while resizing and changing the wallpaper.',
        'Introduced safer AppImage updates with automatic restart.',
        'Kept only the installed and immediately previous AppImage versions.',
        'Expanded GUI and update regression tests.',
    ),
    'v1.5.1': (
        'Streamlined GitHub Actions, release publishing and build caching.',
        'Reduced unnecessary dependency installations and build steps.',
        'Kept existing security and GUI tests in place.',
    ),
}

LANGUAGE_HEADER = re.compile(r'^#{2,4}\s*(Deutsch|German|English|Englisch)\s*$', re.I | re.M)
MISSING_EN = 'English release notes are not available for this older version.'
MISSING_DE = 'Für diese Version sind keine Änderungen dokumentiert.'


def split_language_sections(body):
    """Return separately published German/English Markdown without mixing them."""
    if not isinstance(body, str):
        return {}
    markers = list(LANGUAGE_HEADER.finditer(body))
    if not markers:
        return {}
    results = {}
    for i, marker in enumerate(markers):
        lang = ('en' if marker.group(1).lower() in ('english', 'englisch') else 'de')
        end = markers[i + 1].start() if i + 1 < len(markers) else len(body)
        section = body[marker.end():end].strip()
        if section:
            results[lang] = section
    return results


def release_changelog(body, tag, language='de', max_items=5):
    """Render the chosen release notes, with no German fallback in English mode."""
    sections = split_language_sections(body)
    if language == 'en':
        if sections.get('en'):
            return compact_changelog(sections['en'], max_items=max_items)
        if tag in LEGACY_EN_NOTES:
            return '\n'.join('• ' + line for line in LEGACY_EN_NOTES[tag][:max_items])
        # Unknown older releases cannot be translated accurately offline.
        # An explicit English notice is preferable to silently showing German.
        return MISSING_EN
    if sections.get('de'):
        return compact_changelog(sections['de'], max_items=max_items)
    if sections.get('en'):
        return MISSING_DE
    return compact_changelog(body, max_items=max_items)
