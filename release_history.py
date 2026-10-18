"""Validate public GitHub Releases metadata before showing the version history."""

from password_core import parse_version


def normalized_releases(payload, repo_url):
    """Return safe {tag,date,body,url} items, newest first, maximum 100."""
    if not isinstance(payload, list):
        raise ValueError('GitHub hat keine gültige Release-Liste geliefert.')
    output = []
    for release in payload[:100]:
        if not isinstance(release, dict) or release.get('draft'):
            continue
        tag = release.get('tag_name', '')
        if not isinstance(tag, str) or parse_version(tag) is None or len(tag) > 40:
            continue
        url = release.get('html_url')
        expected = f'{repo_url}/releases/tag/{tag}'
        if url != expected:
            continue
        body = release.get('body')
        if not isinstance(body, str):
            body = ''
        published = release.get('published_at')
        date = (published[:10] if isinstance(published, str) and
                len(published) >= 10 else '')
        output.append({
            'tag': tag,
            'date': date,
            'body': body[:16_000].strip(),
            'url': url,
        })
    return output
