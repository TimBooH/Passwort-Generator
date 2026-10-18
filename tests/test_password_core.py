import string
import unittest

from password_core import SIMILAR_CHARS, SYMBOLS, make_password, parse_version


class PasswordGeneratorTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(parse_version('v1.2.0'), (1, 2, 0))
        self.assertEqual(parse_version('1.12.3'), (1, 12, 3))
        self.assertGreater(parse_version('1.10.0'), parse_version('1.9.9'))
        self.assertIsNone(parse_version('v1.2.0-beta'))
        self.assertIsNone(parse_version('latest'))

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
