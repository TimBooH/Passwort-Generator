"""Profiles store only validated generation settings, never passwords."""
import json
import unittest

from password_presets import PRESETS, encode_profile, decode_profile, validate_profile


class ProfileTests(unittest.TestCase):
    def test_builtin_presets_are_valid_and_distinct(self):
        self.assertEqual(set(PRESETS), {'standard', 'strong', 'simple'})
        for key, data in PRESETS.items():
            with self.subTest(key=key):
                self.assertEqual(validate_profile(data), data)
        self.assertEqual(PRESETS['standard']['length'], 20)
        self.assertEqual(PRESETS['strong']['length'], 32)
        self.assertEqual(PRESETS['simple']['length'], 16)
        self.assertFalse(PRESETS['simple']['symbols'])

    def test_custom_profile_round_trip_contains_no_secret(self):
        profile = dict(PRESETS['strong'])
        encoded = encode_profile(profile)
        self.assertEqual(decode_profile(encoded), profile)
        self.assertNotIn('password', encoded.lower())
        self.assertEqual(set(json.loads(encoded)), set(profile))
        self.assertNotIn('secret', encoded.lower())

    def test_rejects_bad_or_incomplete_profiles(self):
        invalid = [None, {}, {'length': '20'}, {'length': True},
                   {'length': 2}, {'length': 1000}, {'length': 8, 'upper': True},
                   dict(PRESETS['standard'], upper='true'),
                   dict(PRESETS['standard'], lower=False, upper=False,
                        digits=False, symbols=False)]
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(validate_profile(value))
        self.assertIsNone(decode_profile('not json'))
        self.assertIsNone(decode_profile('{"password": "secret"}'))
        with self.assertRaises(ValueError):
            encode_profile({'password': 'secret'})


if __name__ == '__main__':
    unittest.main()
