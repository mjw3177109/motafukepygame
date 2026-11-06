"""Strict JSON boundary for source-pinned floor maps.

This is an opt-in data loader, not an assertion of Flash runtime parity.
Reject noncanonical numeric tokens before they lose their lexical form.
"""
import json

MAX_SAFE_INTEGER = 2**53 - 1


def _reject_noninteger(token):
    raise ValueError(f'non-integer JSON numeric token: {token}')


def _parse_integer(token):
    value = int(token)
    if abs(value) > MAX_SAFE_INTEGER:
        raise ValueError(f'unsafe JSON integer: {token}')
    return value


def load_original_floor_json(source: str):
    """Parse JSON while preserving integer-only map input constraints.

    The caller must still validate floor dimensions and tile semantics.
    """
    return json.loads(source, parse_int=_parse_integer,
                      parse_float=_reject_noninteger,
                      parse_constant=_reject_noninteger)
