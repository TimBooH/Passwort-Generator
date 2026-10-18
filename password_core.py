"""Passwort-Logik ohne GUI-Abhängigkeiten."""

import re
import secrets
import string

SYMBOLS = "!@#$%&*()-_=+[]{}:,.?"
SIMILAR_CHARS = "Il1O0"


def parse_version(value):
    """Compare stable semantic release tags (vMAJOR.MINOR.PATCH)."""
    matched = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(value).strip())
    if matched is None:
        return None
    return tuple(int(part) for part in matched.groups())


def make_password(length, *, use_lower=True, use_upper=True, use_digits=True,
                  use_symbols=True, exclude_similar=False):
    """Generate a password and guarantee every enabled character set is represented."""
    if not isinstance(length, int) or length < 8 or length > 128:
        raise ValueError("Die Passwortlänge muss zwischen 8 und 128 liegen.")

    groups = []
    if use_lower:
        groups.append(string.ascii_lowercase)
    if use_upper:
        groups.append(string.ascii_uppercase)
    if use_digits:
        groups.append(string.digits)
    if use_symbols:
        groups.append(SYMBOLS)
    if exclude_similar:
        groups = ["".join(char for char in group if char not in SIMILAR_CHARS)
                  for group in groups]
    groups = [group for group in groups if group]
    if not groups:
        raise ValueError("Bitte mindestens eine Zeichengruppe auswählen.")
    if length < len(groups):
        raise ValueError("Die Passwortlänge ist zu kurz für die ausgewählten Gruppen.")

    alphabet = "".join(groups)
    result = [secrets.choice(group) for group in groups]
    result.extend(secrets.choice(alphabet) for _ in range(length - len(result)))
    secrets.SystemRandom().shuffle(result)
    return "".join(result)


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


def make_passphrase(word_count=6, separator='-'):
    """Generate a locally random 4–10-word phrase (10 entropy bits/word).

    Compound words are built from two independently uniform 32-word banks.
    Passwords/passphrases are never written to files by this function.
    """
    if not isinstance(word_count, int) or not 4 <= word_count <= 10:
        raise ValueError('Die Passphrase muss zwischen 4 und 10 Wörter enthalten.')
    if separator not in ('-', ' '):
        raise ValueError('Ungültiges Trennzeichen für die Passphrase.')
    return separator.join(
        secrets.choice(PHRASE_FIRST) + secrets.choice(PHRASE_LAST)
        for _ in range(word_count)
    )


def estimate_strength(secret, *, phrase_words=None, pool_size=0):
    """Return a coarse entropy-based label and progress; not a security audit."""
    import math

    if not secret:
        return '--', 0
    if phrase_words is not None:
        bits = max(0, phrase_words) * 10
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
