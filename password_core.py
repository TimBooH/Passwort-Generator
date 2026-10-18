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
