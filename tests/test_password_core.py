import string
import unittest
from unittest import mock

from password_core import (
    PHRASE_FIRST, PHRASE_LAST, PHRASE_SEPARATORS, SIMILAR_CHARS, SYMBOLS,
    make_password, make_passphrase, estimate_strength, parse_version,
)
from version import APP_VERSION, TOTAL_RELEASE_STEPS, is_newer_release, release_step, version_status


class PasswordGeneratorTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(parse_version('v1.2.0'), (1, 2, 0))
        self.assertEqual(parse_version('1.12.3'), (1, 12, 3))
        self.assertGreater(parse_version('1.10.0'), parse_version('1.9.9'))
        self.assertIsNone(parse_version('v1.2.0-beta'))
        self.assertIsNone(parse_version('latest'))

    def test_100_step_release_plan(self):
        self.assertIsNotNone(parse_version(APP_VERSION))
        self.assertIn(release_step(APP_VERSION), range(1, TOTAL_RELEASE_STEPS + 1))
        self.assertEqual(release_step(APP_VERSION), release_step())
        self.assertEqual(TOTAL_RELEASE_STEPS, 100)
        for step in range(1, 100):
            self.assertEqual(release_step(f'v0.{step:02d}.0'), step)
        self.assertEqual(release_step('v1.0.0'), 100)
        self.assertEqual(release_step('v1.0.2'), 100)
        self.assertIsNone(release_step('v0.00.0'))
        self.assertEqual(version_status('v0.01.0'), 'Entwicklung 01/100')
        self.assertEqual(version_status('v0.99.0'), 'Entwicklung 99/100')
        self.assertEqual(version_status('v1.0.0'), 'Vollversion')

    def test_new_version_order_and_legacy_tags(self):
        self.assertTrue(is_newer_release('v0.02.0', '0.01.0'))
        self.assertTrue(is_newer_release('v0.99.0', 'v0.98.3'))
        self.assertTrue(is_newer_release('v1.0.0', 'v0.99.0'))
        self.assertFalse(is_newer_release('v0.01.0', '0.01.0'))
        self.assertFalse(is_newer_release('v0.01.0', '0.02.0'))
        # The old 1.5.x tags must never be mistaken for the next update.
        self.assertFalse(is_newer_release('v1.5.1', 'v0.01.0'))
        self.assertFalse(is_newer_release('v1.2.0', 'v1.0.0'))
        # New code can compare migration order, but old binaries cannot.
        self.assertTrue(is_newer_release('v0.01.0', 'v1.5.1'))
        self.assertFalse(is_newer_release('latest', 'v0.01.0'))

    def test_passphrase_wordlists_and_generation(self):
        self.assertEqual(len(PHRASE_FIRST), 32)
        self.assertEqual(len(PHRASE_LAST), 32)
        vocabulary = {a + b for a in PHRASE_FIRST for b in PHRASE_LAST}
        self.assertEqual(len(vocabulary), 1024)
        seen = set()
        for _ in range(30):
            phrase = make_passphrase(6)
            words = phrase.split('-')
            self.assertEqual(len(words), 6)
            self.assertTrue(all(word in vocabulary for word in words))
            seen.add(phrase)
        self.assertGreater(len(seen), 25)
        with self.assertRaises(ValueError):
            make_passphrase(3)
        with self.assertRaises(ValueError):
            make_passphrase(11)
        with self.assertRaises(ValueError):
            make_passphrase(6, separator='unsafe')
        self.assertEqual(estimate_strength(''), ('--', 0))
        self.assertEqual(estimate_strength('valid', phrase_words=6)[0], 'Stark')
        self.assertEqual(estimate_strength('valid', phrase_words=10)[0], 'Sehr stark')

    def test_separator_choices(self):
        self.assertEqual([value for _, value in PHRASE_SEPARATORS], ['-', ' ', '_', '.'])
        for _, separator in PHRASE_SEPARATORS:
            value = make_passphrase(5, separator=separator)
            self.assertEqual(len(value.split(separator)), 5)

    def test_two_digit_number_is_secure_and_optional(self):
        for separator in ('-', ' ', '_', '.'):
            for rand, expected in ((0, '10'), (89, '99')):
                with mock.patch('password_core.secrets.randbelow', return_value=rand) as random_number:
                    value = make_passphrase(6, separator=separator, add_two_digit_number=True)
                random_number.assert_called_once_with(90)
                parts = value.split(separator)
                self.assertEqual(len(parts), 7)
                self.assertEqual(parts[-1], expected)
                self.assertTrue(parts[-1].isdigit())
        self.assertEqual(len(make_passphrase(6).split('-')), 6)
        with self.assertRaises(ValueError):
            make_passphrase(6, add_two_digit_number='true')
        with self.assertRaises(ValueError):
            make_passphrase(True)

    def test_optional_digit_suffix_adds_entropy(self):
        phrase = make_passphrase(5)
        plain = estimate_strength(phrase, phrase_words=5)[1]
        with_digits = estimate_strength(phrase, phrase_words=5, extra_entropy_bits=6.49)[1]
        self.assertGreater(with_digits, plain)

    def test_all_selected_groups_and_length(self):
        for length in (8, 20, 64, 128):
            for _ in range(10):
                result = make_password(length)
                self.assertEqual(len(result), length)
                self.assertTrue(any(char.islower() for char in result))
                self.assertTrue(any(char.isupper() for char in result))
                self.assertTrue(any(char.isdigit() for char in result))
                self.assertTrue(any(char in SYMBOLS for char in result))

    def test_excluded_similar(self):
        for _ in range(20):
            self.assertTrue(set(make_password(128, exclude_similar=True)).isdisjoint(SIMILAR_CHARS))

    def test_approved_ambiguous_characters(self):
        self.assertEqual(set(SIMILAR_CHARS), set('0Oo1IlL|'))
        for _ in range(15):
            secret = make_password(128, exclude_similar=True)
            self.assertFalse(set(secret) & set(SIMILAR_CHARS))

    def test_unique_password_batch_and_failed_atomic_generation(self):
        from password_core import make_password_batch
        for count in (1, 5, 10, 20):
            group = make_password_batch(count, 16, exclude_similar=True)
            self.assertEqual(len(group), count)
            self.assertEqual(len(set(group)), count)
            self.assertTrue(all(len(p) == 16 for p in group))
            self.assertTrue(all(not (set(p) & set(SIMILAR_CHARS)) for p in group))
        for count in (0, 2, 50, True):
            with self.assertRaises(ValueError):
                make_password_batch(count, 16)
        with mock.patch('password_core.make_password', return_value='A'*20):
            with self.assertRaises(ValueError):
                make_password_batch(5, 20)

    def test_numeric_password(self):
        result = make_password(15, use_lower=False, use_upper=False, use_symbols=False)
        self.assertEqual(len(result), 15)
        self.assertTrue(set(result) <= set(string.digits))

    def test_missing_groups_rejected(self):
        with self.assertRaises(ValueError):
            make_password(20, use_lower=False, use_upper=False,
                          use_digits=False, use_symbols=False)

    def test_bounds(self):
        for length in (0, 7, 129):
            with self.assertRaises(ValueError):
                make_password(length)


if __name__ == '__main__':
    unittest.main()
