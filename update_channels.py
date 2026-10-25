"""Validation and selection for the two independent update channels.

Stable uses the latest Stable release endpoint. Unstable reads a checksum-protected
manifest from a dedicated moving Git tag in the SAME repository, published by
GitHub Actions using only GITHUB_TOKEN. No GitHub release or PAT is needed.
"""

import re

REPOSITORY = 'TimBooH/Passwort-Generator'
UNSTABLE_REF = 'unstable-downloads'  # A Git tag, not a branch.
RELEASE_PREFIX = f'https://raw.githubusercontent.com/{REPOSITORY}/{UNSTABLE_REF}/'
UNSTABLE_API = RELEASE_PREFIX + 'latest.json'
STABLE_API = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
VALID_CHANNELS = ('stable', 'unstable')
_UNSTABLE_SHA = re.compile(r'^[0-9a-f]{12}$')


def channel_api(channel):
    if channel not in VALID_CHANNELS:
        raise ValueError('Ungültiger Update-Kanal.')
    return UNSTABLE_API if channel == 'unstable' else STABLE_API


def unstable_asset_name(platform, build_sha):
    if not isinstance(build_sha, str) or not _UNSTABLE_SHA.fullmatch(build_sha):
        raise ValueError('Ungültige Unstable-Build-ID.')
    if platform == 'nt':
        return f'PasswortGenerator-UNSTABLE-{build_sha}-Setup-x64.exe'
    return f'PasswortGenerator-UNSTABLE-{build_sha}-x86_64.AppImage'


def select_unstable_asset(release, platform):
    """Require the correct manifest, build ID, SHA-256 and download URL."""
    if (not isinstance(release, dict) or release.get('tag_name') != 'unstable'
            or release.get('draft') or release.get('prerelease') is not True):
        raise ValueError('Keine gültige öffentliche Unstable-Testversion vorhanden.')
    name = release.get('name', '')
    if not isinstance(name, str):
        raise ValueError('Unstable-Buildkennung fehlt.')
    match = re.fullmatch(r'PasswortGenerator Unstable ([0-9a-f]{12})', name)
    if not match:
        raise ValueError('Unstable-Buildkennung fehlt.')
    sha = match.group(1)
    filename = unstable_asset_name(platform, sha)
    assets = release.get('assets')
    if not isinstance(assets, list):
        raise ValueError('Unstable-Installationsdateien fehlen.')
    asset = next((x for x in assets if isinstance(x, dict)
                  and x.get('name') == filename), None)
    if asset is None:
        raise ValueError('Unstable-Build ist für dieses System noch nicht verfügbar.')
    url = asset.get('browser_download_url', '')
    digest = asset.get('digest', '')
    size = asset.get('size')
    if (url != f'{RELEASE_PREFIX}{filename}'
            or type(size) is not int or size < 1_000_000
            or not isinstance(digest, str)
            or not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest)):
        raise ValueError('Unstable-Datei ist nicht sicher verifizierbar.')
    return sha, asset


def has_channel_update(selected, running, release_id, installed_version,
                       current_version, current_unstable_sha, is_newer):
    """Compare build SHA on preview, semantic version on stable."""
    if selected == 'unstable':
        return running != 'unstable' or release_id != current_unstable_sha
    if running != 'stable':
        return True  # Explicitly allow returning from preview to stable.
    return is_newer(release_id, installed_version)
