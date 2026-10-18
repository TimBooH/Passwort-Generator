"""Regression tests for the v0.20.0 password generator extensions."""
import math
import string
import unittest

from password_core import (
    PHRASE_FIRST_EN, PHRASE_LAST_EN, PHRASE_FIRST, PHRASE_LAST,
    SYMBOLS, make_password, make_passphrase, password_entropy_bits,
)

class ExtendedPasswordTests(unittest.TestCase):
    def test_minimum_counts_and_exclusion(self):
        for _ in range(60):
            value = make_password(
                20, use_upper=True, use_lower=True, use_digits=True,
                use_symbols=True, exclude_similar=True,
                excluded_chars='aei!@#$', min_digits=4, min_symbols=3,
            )
            self.assertEqual(len(value), 20)
            self.assertGreaterEqual(sum(x in string.digits for x in value), 4)
            self.assertGreaterEqual(sum(x in SYMBOLS for x in value), 3)
            self.assertFalse(any(x in 'aei!@#$Il1O0' for x in value))
            self.assertTrue(any(x.isupper() for x in value))
            self.assertTrue(any(x.islower() for x in value))

    def test_valid_strong_and_simple_rules(self):
        for _ in range(20):
            simple = make_password(16, use_symbols=False, min_digits=2)
            self.assertTrue(simple.isalnum())
            self.assertGreaterEqual(sum(x.isdigit() for x in simple), 2)
        self.assertGreater(password_entropy_bits(24), 100)

    def test_invalid_requirements_rejected(self):
        for kwargs in [
            {'use_digits': False, 'min_digits': 1},
            {'use_symbols': False, 'min_symbols': 1},
            {'min_digits': -1},
            {'min_digits': True},
            {'min_digits': 20, 'min_symbols': 20},
            {'excluded_chars': string.digits},
            {'excluded_chars': 'a' * 257},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                make_password(12, **kwargs)

    def test_german_and_english_word_banks(self):
        self.assertEqual(len(PHRASE_FIRST_EN), 32)
        self.assertEqual(len(PHRASE_LAST_EN), 32)
        self.assertEqual(len(PHRASE_FIRST), 32)
        self.assertEqual(len(PHRASE_LAST), 32)
        self.assertEqual(len(set(a+b for a in PHRASE_FIRST_EN
                                      for b in PHRASE_LAST_EN)), 1024)
        german_words = {a+b for a in PHRASE_FIRST for b in PHRASE_LAST}
        english_words = {a+b for a in PHRASE_FIRST_EN for b in PHRASE_LAST_EN}
        for lang, bank in [('de', german_words), ('en', english_words)]:
            for _ in range(15):
                p = make_passphrase(6, language=lang)
                self.assertEqual(len(p.split('-')), 6)
                self.assertTrue(set(p.split('-')).issubset(bank))
                suffix = make_passphrase(4, language=lang,
                                         separator='.', add_two_digit_number=True)
                self.assertEqual(len(suffix.split('.')), 5)
                self.assertTrue(suffix.split('.')[-1].isdigit())
        with self.assertRaises(ValueError):
            make_passphrase(6, language='unsupported')

if __name__ == '__main__':
    unittest.main()
