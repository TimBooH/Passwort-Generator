"""Exact generator entropy, checked against enumeration and count probabilities."""
from collections import Counter
from fractions import Fraction
from itertools import permutations, product
import math
import string
import time
import unittest
from unittest import mock

from password_core import (
    _generator_entropy_bits, estimate_strength, make_password,
    password_entropy_bits, password_groups,
)


REFERENCE_CASES = (
    (8, {}, 49.94),
    (20, {}, 127.29),
    (8, {'exclude_similar': True}, 49.10),
    (10, {'min_digits': 4, 'min_symbols': 4}, 52.88),
    (12, {'min_digits': 5, 'min_symbols': 5}, 62.99),
    (16, {'min_digits': 7, 'min_symbols': 7}, 83.05),
    (42, {'min_digits': 20, 'min_symbols': 20}, 211.44),
    (8, {'use_upper': False, 'use_symbols': False}, 41.19),
)


def count_vector_distribution(length, sizes, required):
    """Independent full sum using the probability formula for each string."""
    rest = length - sum(required)
    factorials = [math.lgamma(n + 1) / math.log(2) for n in range(length + 1)]

    def visit(index, left, counts):
        if index == len(sizes) - 1:
            if left >= required[index]:
                yield counts + [left]
            return
        for count in range(required[index], left - sum(required[index + 1:]) + 1):
            yield from visit(index + 1, left - count, counts + [count])

    for counts in visit(0, length, []):
        log_probability = (
            sum(factorials[k] - factorials[k - r] - r * math.log2(s)
                for k, r, s in zip(counts, required, sizes))
            - rest * math.log2(sum(sizes)) + factorials[rest] - factorials[length]
        )
        log_count = factorials[length] + sum(
            k * math.log2(s) - factorials[k] for k, s in zip(counts, sizes)
        )
        yield 2 ** (log_count + log_probability), -log_probability


class PasswordEntropyTests(unittest.TestCase):
    def test_reference_values(self):
        for length, rules, expected in REFERENCE_CASES:
            with self.subTest(length=length, rules=rules):
                self.assertAlmostEqual(password_entropy_bits(length, **rules), expected, delta=0.01)

    def test_brute_force_mandatory_rest_and_shuffle(self):
        # Exactly mirror make_password's sampling: one choice per group,
        # remaining choices from their union, then every index permutation.
        # The internal evaluator also accepts this L=3 mathematical toy case;
        # the public generator/entropy API retains the L>=8 validation.
        groups = ('ab', '01')
        outcomes = Counter()
        for mandatory in product(*groups):
            for rest in product(''.join(groups), repeat=1):
                for order in permutations(range(3)):
                    before_shuffle = mandatory + rest
                    outcomes[''.join(before_shuffle[i] for i in order)] += 1
        probabilities = [Fraction(count, sum(outcomes.values())) for count in outcomes.values()]
        self.assertEqual(sum(probabilities), 1)
        entropy = -math.fsum(float(p) * math.log2(p) for p in probabilities)
        self.assertAlmostEqual(entropy, 5.584962500721156, places=12)
        self.assertAlmostEqual(_generator_entropy_bits(3, (2, 2), (1, 1)), entropy, places=12)

    def test_count_vector_probability_mass_and_entropy(self):
        for length, sizes, required in (
            (3, (2, 2), (1, 1)),
            (8, (26, 26, 10, 21), (1, 1, 1, 1)),
            (20, (26, 26, 10, 21), (1, 1, 1, 1)),
            (8, (24, 23, 8, 21), (1, 1, 1, 1)),
            (10, (26, 26, 10, 21), (1, 1, 4, 4)),
            (42, (26, 26, 10, 21), (1, 1, 20, 20)),
        ):
            with self.subTest(length=length, sizes=sizes, required=required):
                terms = list(count_vector_distribution(length, sizes, required))
                self.assertAlmostEqual(math.fsum(p for p, _ in terms), 1, places=11)
                self.assertAlmostEqual(
                    math.fsum(p * bits for p, bits in terms),
                    _generator_entropy_bits(length, sizes, required), places=10,
                )

    def test_brute_force_against_actual_generator(self):
        # Exercise the actual generator at its minimum supported length.
        # Singleton groups keep exhaustive sampling + 8! shuffles tractable.
        rules = dict(use_upper=False, use_symbols=False,
                     excluded_chars=''.join(c for c in string.ascii_lowercase + string.digits
                                            if c not in 'a0'))
        outcomes = Counter()
        orders = list(permutations(range(8)))

        def enumerate_shuffle(chars):
            for order in orders:
                outcomes[''.join(chars[i] for i in order)] += 1

        with mock.patch('password_core.secrets.SystemRandom') as rng:
            rng.return_value.shuffle.side_effect = enumerate_shuffle
            for rest in product('a0', repeat=6):
                choices = iter(('a', '0') + rest)

                def choose(alphabet):
                    chosen = next(choices)
                    self.assertIn(chosen, alphabet)
                    return chosen

                with mock.patch('password_core.secrets.choice', side_effect=choose):
                    make_password(8, **rules)
        self.assertEqual(sum(outcomes.values()), 2 ** 6 * math.factorial(8))
        total = sum(outcomes.values())
        entropy = -math.fsum((count / total) * math.log2(count / total)
                             for count in outcomes.values())
        self.assertAlmostEqual(password_entropy_bits(8, **rules), entropy, places=12)

    def test_direct_strength_bits_preserve_thresholds_and_score(self):
        bits = password_entropy_bits(10, min_digits=4, min_symbols=4)
        self.assertEqual(estimate_strength('aA0123!@#$', entropy_bits=bits), ('Mittel', 50))
        for bits, label in ((0, 'Schwach'), (35, 'Mittel'), (55, 'Stark'), (80, 'Sehr stark')):
            self.assertEqual(estimate_strength('secret', entropy_bits=bits),
                             (label, min(100, max(8, round(bits / 1.05)))))

    def test_upper_bound_and_filtered_alphabets(self):
        for flags in product((False, True), repeat=4):
            if not any(flags):
                continue
            rules = dict(zip(('use_lower', 'use_upper', 'use_digits', 'use_symbols'), flags))
            for length in (8, 20, 128):
                for filters in ({}, {'exclude_similar': True, 'excluded_chars': 'abc239!@'}):
                    with self.subTest(length=length, rules=rules, filters=filters):
                        groups = password_groups(**rules, **filters)
                        bits = password_entropy_bits(length, **rules, **filters)
                        self.assertGreaterEqual(bits, -1e-10)
                        self.assertLessEqual(bits, length * math.log2(sum(map(len, groups))) + 1e-10)
        # Filtered mandatory digit/symbol alphabets, with no random rest.
        rules = dict(exclude_similar=True, excluded_chars='abc239!@', min_digits=4, min_symbols=4)
        sizes = list(map(len, password_groups(exclude_similar=True, excluded_chars='abc239!@')))
        self.assertAlmostEqual(password_entropy_bits(10, **rules),
                               _generator_entropy_bits(10, sizes, (1, 1, 4, 4)), places=12)

    def test_validation_matches_generator(self):
        cases = [(length, {}) for length in (True, 7, 129, 8.0)] + [
            (10, {'min_digits': value}) for value in (-1, 21, True, 2.5)
        ] + [
            (10, {'min_digits': 1, 'use_digits': False}),
            (10, {'min_symbols': 1, 'use_symbols': False}),
            (8, {'min_digits': 4, 'min_symbols': 4}),
            (10, {'excluded_chars': '0123456789'}),
            (10, {'excluded_chars': None}),
            (10, {'excluded_chars': 'x' * 257}),
            (10, dict(use_lower=False, use_upper=False, use_digits=False, use_symbols=False)),
        ]
        for length, rules in cases:
            with self.subTest(length=length, rules=rules):
                with self.assertRaises(ValueError) as generator_error:
                    make_password(length, **rules)
                with self.assertRaises(ValueError) as entropy_error:
                    password_entropy_bits(length, **rules)
                self.assertEqual(str(entropy_error.exception), str(generator_error.exception))

    def test_length_128_runtime(self):
        start = time.perf_counter()
        bits = password_entropy_bits(128, min_digits=20, min_symbols=20)
        elapsed = time.perf_counter() - start
        self.assertGreater(bits, 0)
        self.assertLess(elapsed, 0.05)


if __name__ == '__main__':
    unittest.main()
