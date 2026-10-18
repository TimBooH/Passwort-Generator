"""Release metadata validation, reverse-chronological sorting and short notes."""

import re
from datetime import datetime, timezone

from password_core import parse_version


def compact_changelog(body, max_items=5):
    """Show at most five concise bullet points, avoiding the full Markdown page."""
    if not isinstance(body, str) or not body.strip():
        return 'Für diese Version sind keine Änderungen dokumentiert.'
    bullets = []
    for raw in body.splitlines():
        line = raw.strip()
        if re.match(r'^#{1,4}\s*(Unverändert|Tests|Weiterhin verfügbar)\b', line, re.I):
            if bullets:
                break
        match = re.match(r'^[-*]\s+(.+)$', line)
        if not match:
            continue
        item = match.group(1).strip()
        item = re.sub(r'!?\[([^\]]+)\]\([^)]+\)', r'\1', item)
        item = re.sub(r'(\*\*|__|`)', '', item)
        item = re.sub(r'\s+', ' ', item).strip()
        if len(item) > 115:
            item = item[:114].rsplit(' ', 1)[0].rstrip(' ,;:.') + '…'
        if item and item not in bullets:
            bullets.append(item)
        if len(bullets) >= max_items:
            break
    if not bullets:
        lines = [line.strip() for line in body.splitlines()
                 if line.strip() and not line.strip().startswith(('#', '**Entwicklungsschritt'))]
        if lines:
            bullets.append(re.sub(r'(\*\*|__|`)', '', lines[0])[:115].strip())
    return '\n'.join('• ' + item for item in bullets) if bullets else (
        'Für diese Version sind keine Änderungen dokumentiert.'
    )


def _timestamp(value):
    if not isinstance(value, str):
        return 0.0
    try:
        instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        return instant.timestamp()
    except (ValueError, OverflowError):
        return 0.0


def normalized_releases(payload, repo_url):
    """Return safe public releases newest-first by date, not by version number."""
    if not isinstance(payload, list):
        raise ValueError('GitHub hat keine gültige Release-Liste geliefert.')
    output = []
    seen = set()
    for release in payload[:100]:
        if not isinstance(release, dict) or release.get('draft'):
            continue
        tag = release.get('tag_name', '')
        if not isinstance(tag, str) or parse_version(tag) is None or len(tag) > 40 or tag in seen:
            continue
        url = release.get('html_url')
        if url != f'{repo_url}/releases/tag/{tag}':
            continue
        body = release.get('body')
        if not isinstance(body, str):
            body = ''
        published = release.get('published_at')
        date = published[:10] if isinstance(published, str) and len(published) >= 10 else ''
        output.append({
            'tag': tag,
            'date': date,
            'body': body[:16_000].strip(),
            'url': url,
            '_order': _timestamp(published),
        })
        seen.add(tag)
    output.sort(key=lambda item: item['_order'], reverse=True)
    for item in output:
        item.pop('_order')
    return output
