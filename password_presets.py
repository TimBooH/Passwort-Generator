"""Non-secret reusable password settings. Generated passwords are never saved."""

import json

FIELDS = ('upper', 'lower', 'digits', 'symbols', 'exclude')

# Profile IDs and data stay stable across German and English UI languages.
PRESETS = {
    'standard': {'length': 20, 'upper': True, 'lower': True,
                 'digits': True, 'symbols': True, 'exclude': False},
    'strong': {'length': 32, 'upper': True, 'lower': True,
               'digits': True, 'symbols': True, 'exclude': True},
    'simple': {'length': 16, 'upper': True, 'lower': True,
               'digits': True, 'symbols': False, 'exclude': True},
}


def validate_profile(data):
    """Return safe settings or None; require at least one character group."""
    if not isinstance(data, dict) or type(data.get('length')) is not int:
        return None
    length = data['length']
    if not 8 <= length <= 128:
        return None
    if any(type(data.get(key)) is not bool for key in FIELDS):
        return None
    if not any(data[key] for key in FIELDS[:4]):
        return None
    if length < sum(bool(data[key]) for key in FIELDS[:4]):
        return None
    return {'length': length, **{key: data[key] for key in FIELDS}}


def decode_profile(value):
    """Reject malformed QSettings data instead of applying incomplete states."""
    try:
        parsed = json.loads(value) if isinstance(value, str) else None
    except (TypeError, ValueError):
        return None
    return validate_profile(parsed)


def encode_profile(profile):
    validated = validate_profile(profile)
    if validated is None:
        raise ValueError('Invalid password profile.')
    return json.dumps(validated, sort_keys=True)
