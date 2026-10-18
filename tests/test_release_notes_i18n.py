"""The global UI language must determine how every GitHub release is shown."""
import unittest

from release_notes_i18n import (
    LEGACY_EN_NOTES, MISSING_EN, release_changelog, split_language_sections,
)


class BilingualChangelogTests(unittest.TestCase):
    def test_bilingual_release_selects_only_requested_section(self):
        body = (
            '# PasswortGenerator\n'
            '**Entwicklungsschritt 18 von 100**\n'
            '## Deutsch\n'
            '- Vollständige Sprachumstellung im Programm\n'
            '- Deutsche und englische Änderungsnotizen\n'
            '## English\n'
            '- System-wide language switching in the app\n'
            '- German and English release notes\n'
        )
        sections = split_language_sections(body)
        self.assertIn('Vollständige', sections['de'])
        self.assertIn('System-wide', sections['en'])
        english = release_changelog(body, 'v0.18.0', 'en')
        german = release_changelog(body, 'v0.18.0', 'de')
        self.assertIn('System-wide', english)
        self.assertIn('German and English', english)
        self.assertNotIn('Vollständige', english)
        self.assertIn('Vollständige', german)
        self.assertNotIn('System-wide', german)

    def test_historic_releases_are_readable_in_english(self):
        for tag in LEGACY_EN_NOTES:
            with self.subTest(tag=tag):
                translated = release_changelog(
                    '# Historical\n- Nur deutscher Text', tag, 'en',
                )
                self.assertGreater(len(translated), 15)
                self.assertNotIn('Nur deutscher Text', translated)
                self.assertTrue(translated.startswith('• '))
                self.assertLessEqual(len(translated.splitlines()), 5)

    def test_german_legacy_is_not_changed(self):
        body = '# Older version\n- Nur deutsche Änderungen\n- Schöneres Design'
        self.assertIn('Nur deutsche Änderungen',
                      release_changelog(body, 'v0.15.0', 'de'))

    def test_unknown_english_fallback_and_missing_notes(self):
        self.assertEqual(release_changelog('- Ein deutscher Punkt',
                                           'v0.98.0', 'en'), MISSING_EN)
        self.assertEqual(release_changelog(None, 'v0.99.0', 'en'), MISSING_EN)
        self.assertEqual(release_changelog('', 'v0.99.0', 'de'),
                         'Für diese Version sind keine Änderungen dokumentiert.')

    def test_exact_english_release_body_remains_untouched(self):
        body = (
            '## German\n- Deutsche Beschreibung\n'
            '## Englisch\n- A release note mentioning SHA-256 checksums\n'
        )
        self.assertIn('SHA-256', release_changelog(body, 'v0.18.0', 'en'))
        self.assertNotIn('Deutsche Beschreibung',
                         release_changelog(body, 'v0.18.0', 'en'))


if __name__ == '__main__':
    unittest.main()
