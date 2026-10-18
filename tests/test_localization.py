"""Pure-Python regression tests for the built-in German/English catalog."""
import unittest

from localization import LANGUAGES, translate


class LocalizationTests(unittest.TestCase):
    def test_languages_and_de_fallback(self):
        self.assertEqual([code for _, code in LANGUAGES], ['de', 'en'])
        self.assertEqual(translate('Passwort', 'de'), 'Passwort')
        self.assertEqual(translate('Passwort', 'en'), 'Password')
        self.assertEqual(translate('Info', 'en'), 'Info')

    def test_navigation_and_update_messages(self):
        self.assertEqual(translate('⌑ Passwort', 'en'), '⌑ Password')
        self.assertEqual(translate('↻ Update • NEU', 'en'), '↻ Update • NEW')
        self.assertEqual(translate('↻ Auf Update prüfen', 'en'), '↻ Check for updates')
        self.assertEqual(
            translate('Installiert: v0.17.0 · Noch nicht geprüft', 'en'),
            'Installed: v0.17.0 · Not checked yet',
        )
        self.assertEqual(
            translate('Neue Version v0.18.0 verfügbar! Installiert: v0.17.0', 'en'),
            'New version v0.18.0 available! Installed: v0.17.0',
        )

    def test_strength_and_settings(self):
        self.assertEqual(translate('🛡  Stärke: Sehr stark', 'en'), '🛡  Strength: Very strong')
        self.assertEqual(translate('Sprache:', 'en'), 'Language:')
        self.assertEqual(translate('ERSCHEINUNGSBILD', 'en'), 'APPEARANCE')
        self.assertEqual(
            translate('Passwort-Generator v0.17.0 · Entwicklung 17/100', 'en'),
            'Passwort-Generator v0.17.0 · Development 17/100',
        )
        self.assertEqual(
            translate('●  Automatisch (Bild): #123ABC', 'en'),
            '●  Automatic (Image): #123ABC',
        )

    def test_does_not_change_password_or_unrecognized_release_notes(self):
        secret = 'Xb#vA7_Se!reT97'
        self.assertEqual(translate(secret, 'en'), secret)
        self.assertEqual(translate('Some release notes from GitHub', 'en'),
                         'Some release notes from GitHub')


if __name__ == '__main__':
    unittest.main()
