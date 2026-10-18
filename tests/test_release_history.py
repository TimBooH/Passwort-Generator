"""Public GitHub release metadata must be validated before display."""

import unittest

from release_history import normalized_releases

REPO = 'https://github.com/TimBooH/Passwort-Generator'


class ReleaseHistoryTests(unittest.TestCase):
    def test_multiple_versions_and_legacy_releases(self):
        results = normalized_releases([
            {
                'tag_name': 'v0.05.0',
                'published_at': '2026-10-18T10:22:12Z',
                'body': '## Neu\n- Automatische Akzentfarbe',
                'html_url': f'{REPO}/releases/tag/v0.05.0',
            },
            {
                'tag_name': 'v1.5.1',
                'body': 'Älterer Versionszweig.',
                'html_url': f'{REPO}/releases/tag/v1.5.1',
            },
            {'tag_name': 'not-a-version', 'html_url': 'https://evil.invalid'},
            {'tag_name': 'v0.04.0', 'draft': True,
             'html_url': f'{REPO}/releases/tag/v0.04.0'},
        ], REPO)
        self.assertEqual([result['tag'] for result in results], [
            'v0.05.0', 'v1.5.1',
        ])
        self.assertEqual(results[0]['date'], '2026-10-18')
        self.assertIn('Automatische Akzentfarbe', results[0]['body'])
        self.assertEqual(results[1]['date'], '')

    def test_rejects_external_links_and_broken_fields(self):
        results = normalized_releases([
            {'tag_name': 'v0.03.0', 'body': 'safe',
             'html_url': f'{REPO}/releases/tag/v0.03.0'},
            {'tag_name': 'v0.02.0', 'body': 'unsafe',
             'html_url': 'https://evil.invalid/releases/tag/v0.02.0'},
            {'tag_name': 'v0.01.0', 'body': None,
             'html_url': f'{REPO}/releases/tag/v0.01.0'},
            {}, [], None,
        ], REPO)
        self.assertEqual([entry['tag'] for entry in results], ['v0.03.0', 'v0.01.0'])
        self.assertEqual(results[1]['body'], '')
        self.assertEqual(normalized_releases([], REPO), [])
        with self.assertRaises(ValueError):
            normalized_releases({'message': 'rate limit'}, REPO)

    def test_truncates_changelog(self):
        results = normalized_releases([
            {'tag_name': 'v0.05.0', 'body': 'x' * 40_000,
             'html_url': f'{REPO}/releases/tag/v0.05.0'},
        ], REPO)
        self.assertEqual(len(results[0]['body']), 16_000)


if __name__ == '__main__':
    unittest.main()
