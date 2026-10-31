"""Passwort-Logik ohne GUI-Abhängigkeiten."""

import re
import secrets
import string
import math

SYMBOLS = "!@#$%&*()-_=+[]{}:,.?"
SIMILAR_CHARS = "0Oo1IlL|"  # Approved eight visually ambiguous characters.


def parse_version(value):
    """Compare stable semantic release tags (vMAJOR.MINOR.PATCH)."""
    matched = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(value).strip())
    if matched is None:
        return None
    return tuple(int(part) for part in matched.groups())


def password_groups(*, use_lower=True, use_upper=True, use_digits=True,
                    use_symbols=True, exclude_similar=False, excluded_chars=''):
    """Return allowed groups, preserving generator constraints and alphabet sizes."""
    if not isinstance(excluded_chars, str) or len(excluded_chars) > 256:
        raise ValueError('Ausgeschlossene Zeichen dürfen höchstens 256 Zeichen enthalten.')
    forbidden = set(excluded_chars)
    if exclude_similar:
        forbidden.update(SIMILAR_CHARS)
    selected = (
        (use_lower, string.ascii_lowercase),
        (use_upper, string.ascii_uppercase),
        (use_digits, string.digits),
        (use_symbols, SYMBOLS),
    )
    groups = [''.join(c for c in alphabet if c not in forbidden)
              for enabled, alphabet in selected if enabled]
    if not groups or any(not group for group in groups):
        raise ValueError('Mindestens eine ausgewählte Zeichengruppe ist leer.')
    return groups


def make_password(length, *, use_lower=True, use_upper=True, use_digits=True,
                  use_symbols=True, exclude_similar=False,
                  excluded_chars='', min_digits=0, min_symbols=0):
    """Generate a secure random password satisfying every selected rule.

    Mandatory characters are sampled with secrets and uniformly shuffled;
    all constraints are guaranteed, rather than relying on repeated retries.
    The conditional distribution is not uniform across all valid passwords.
    """
    if type(length) is not int or not 8 <= length <= 128:
        raise ValueError('Die Passwortlänge muss zwischen 8 und 128 liegen.')
    if any(type(n) is not int or n < 0 or n > 20
           for n in (min_digits, min_symbols)):
        raise ValueError('Mindestanzahl muss zwischen 0 und 20 liegen.')
    if (min_digits and not use_digits) or (min_symbols and not use_symbols):
        raise ValueError('Für Mindestzahlen müssen die zugehörigen Zeichengruppen aktiv sein.')
    groups = password_groups(
        use_lower=use_lower, use_upper=use_upper,
        use_digits=use_digits, use_symbols=use_symbols,
        exclude_similar=exclude_similar, excluded_chars=excluded_chars,
    )
    if length < max(min_digits + min_symbols, len(groups)):
        raise ValueError('Die Passwortlänge ist für die Mindestanforderungen zu kurz.')
    # Construct uniformly at random via position assignment followed by a
    # uniform shuffle. This guarantees each enabled group is represented.
    alphabet = ''.join(groups)
    required = [secrets.choice(group) for group in groups]
    digit_alphabet = ''.join(ch for ch in string.digits if ch in alphabet)
    symbol_alphabet = ''.join(ch for ch in SYMBOLS if ch in alphabet)
    if min_digits > 0 and not digit_alphabet:
        raise ValueError('Keine erlaubten Zahlen verfügbar.')
    if min_symbols > 0 and not symbol_alphabet:
        raise ValueError('Keine erlaubten Sonderzeichen verfügbar.')
    required.extend(secrets.choice(digit_alphabet) for _ in range(
        max(0, min_digits - sum(ch in string.digits for ch in required))
    ))
    required.extend(secrets.choice(symbol_alphabet) for _ in range(
        max(0, min_symbols - sum(ch in SYMBOLS for ch in required))
    ))
    if len(required) > length:
        raise ValueError('Die Passwortlänge ist für die Mindestanforderungen zu kurz.')
    result = required + [secrets.choice(alphabet) for _ in range(length - len(required))]
    secrets.SystemRandom().shuffle(result)
    return ''.join(result)


BATCH_CHOICES = (1, 5, 10, 20)


def make_password_batch(count, length, **rules):
    """Generate 1/5/10/20 unique passwords; fail atomically for bad rules.

    Uses the same secrets-backed generator and constraints as single mode.
    Retrying duplicates has a finite bound even with mocked/broken RNGs.
    """
    if type(count) is not int or count not in BATCH_CHOICES:
        raise ValueError('Es sind nur 1, 5, 10 oder 20 Passwörter möglich.')
    groups = password_groups(
        use_lower=rules.get('use_lower', True),
        use_upper=rules.get('use_upper', True),
        use_digits=rules.get('use_digits', True),
        use_symbols=rules.get('use_symbols', True),
        exclude_similar=rules.get('exclude_similar', False),
        excluded_chars=rules.get('excluded_chars', ''),
    )
    if len(''.join(groups)) ** length < count:
        raise ValueError('Mit diesen Regeln sind nicht genügend verschiedene Passwörter möglich.')
    result, seen = [], set()
    for _ in range(max(100, count * 100)):
        value = make_password(length, **rules)
        if value not in seen:
            seen.add(value)
            result.append(value)
            if len(result) == count:
                return result
    raise ValueError('Nicht genügend unterschiedliche Passwörter erzeugbar. Regeln anpassen.')


def password_entropy_bits(length, *, use_lower=True, use_upper=True,
                          use_digits=True, use_symbols=True,
                          exclude_similar=False, excluded_chars=''):
    """Theoretical upper bound based on the allowed alphabet (not a guarantee)."""
    groups = password_groups(
        use_lower=use_lower, use_upper=use_upper,
        use_digits=use_digits, use_symbols=use_symbols,
        exclude_similar=exclude_similar, excluded_chars=excluded_chars,
    )
    return length * math.log2(len(''.join(groups)))




# Two independent 32-word banks form 1,024 distinct compound words:
# 10 bits per word, selected with cryptographically secure randomness.
# No remote wordlist or network service is required.
PHRASE_FIRST = (
    'Abend', 'Adler', 'Ahorn', 'Anker', 'Apfel', 'Berg', 'Blitz', 'Blumen',
    'Brunnen', 'Drachen', 'Eichen', 'Feder', 'Feuer', 'Flieder', 'Fluss', 'Funkel',
    'Garten', 'Gold', 'Hafen', 'Herbst', 'Himmel', 'Kiesel', 'Kristall', 'Küsten',
    'Licht', 'Morgen', 'Nord', 'Perlen', 'Regen', 'Sonnen', 'Stern', 'Winter',
)
PHRASE_LAST = (
    'Bach', 'Baum', 'Blick', 'Blume', 'Brücke', 'Burg', 'Dach', 'Falter',
    'Feld', 'Fels', 'Fisch', 'Flamme', 'Garten', 'Glanz', 'Hafen', 'Haus',
    'Hof', 'Insel', 'Klang', 'Kreis', 'Land', 'Lauf', 'Licht', 'Meer',
    'Mond', 'Pfad', 'Schein', 'Stern', 'Tal', 'Traum', 'Wald', 'Wind',
)

# Additional 1,024 English compound words from two 32-element banks.
# Both word lists are offline and share the same 10 bits/word.
PHRASE_FIRST_EN = (
    'Amber', 'Apple', 'Autumn', 'Beacon', 'Blue', 'Bright', 'Brook', 'Cedar',
    'Cloud', 'Copper', 'Crystal', 'Dawn', 'Dream', 'Eagle', 'Emerald', 'Forest',
    'Golden', 'Green', 'Harbor', 'Hidden', 'Island', 'Ivory', 'Lemon', 'Lunar',
    'Maple', 'Meadow', 'Midnight', 'Misty', 'Ocean', 'Silver', 'Summer', 'Winter',
)
PHRASE_LAST_EN = (
    'Anchor', 'Arrow', 'Beacon', 'Bird', 'Bloom', 'Bridge', 'Brook', 'Castle',
    'Clover', 'Comet', 'Dancer', 'Field', 'Flame', 'Flower', 'Garden', 'Grove',
    'Harbor', 'Hill', 'Horizon', 'Island', 'Lantern', 'Leaf', 'Light', 'Meadow',
    'Mirror', 'Moon', 'Mountain', 'River', 'Shadow', 'Star', 'Stone', 'Valley',
)
PHRASE_LANGUAGES = ('de', 'en')


# Explicit separator choices are shared by the GUI and password logic.
# Use fixed allowed values instead of arbitrary user input.
PHRASE_SEPARATORS = (
    ('Bindestrich (-)', '-'),
    ('Leerzeichen', ' '),
    ('Unterstrich (_)', '_'),
    ('Punkt (.)', '.'),
)


def make_passphrase(word_count=6, separator='-', add_two_digit_number=False, language='de'):
    """Create 4–10 secure words, optionally followed by a random 10–99 suffix.

    Each compound word has 1,024 combinations (10 bits). The extra number
    adds log2(90) ≈ 6.49 bits; it uses the same selected separator.
    No network calls or persistent storage.
    """
    if not isinstance(word_count, int) or isinstance(word_count, bool) or not 4 <= word_count <= 10:
        raise ValueError('Die Passphrase muss zwischen 4 und 10 Wörter enthalten.')
    if separator not in tuple(value for _label, value in PHRASE_SEPARATORS):
        raise ValueError('Ungültiges Trennzeichen für die Passphrase.')
    if not isinstance(add_two_digit_number, bool):
        raise ValueError('Zweistellige Zahl muss ein- oder ausgeschaltet sein.')
    if language not in PHRASE_LANGUAGES:
        raise ValueError('Ungültige Passphrasen-Sprache.')
    first, last = ((PHRASE_FIRST_EN, PHRASE_LAST_EN) if language == 'en'
                   else (PHRASE_FIRST, PHRASE_LAST))
    parts = [secrets.choice(first) + secrets.choice(last)
             for _ in range(word_count)]
    if add_two_digit_number:
        parts.append(str(10 + secrets.randbelow(90)))
    return separator.join(parts)


def estimate_strength(secret, *, phrase_words=None, pool_size=0,
                      extra_entropy_bits=0):
    """Return a coarse entropy-based label and progress; not a security audit."""
    import math

    if not secret:
        return '--', 0
    if phrase_words is not None:
        bits = max(0, phrase_words) * 10 + max(0, extra_entropy_bits)
    else:
        bits = len(secret) * math.log2(max(2, pool_size))
    if bits < 35:
        label = 'Schwach'
    elif bits < 55:
        label = 'Mittel'
    elif bits < 80:
        label = 'Stark'
    else:
        label = 'Sehr stark'
    return label, min(100, max(8, round(bits / 1.05)))
