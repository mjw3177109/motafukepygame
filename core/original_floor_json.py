"""Strict JSON boundary for source-pinned floor maps.

This is an opt-in data loader, not an assertion of Flash runtime parity.
Reject noncanonical numeric tokens and duplicate keys before they lose their lexical form.
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


def _unique_object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON object key: {key}')
        result[key] = value
    return result


def load_original_floor_json(source: str):
    """Parse source maps with strict numeric and unique-key constraints.

    The caller must still validate floor dimensions and tile semantics.
    """
    return json.loads(source, parse_int=_parse_integer,
                      parse_float=_reject_noninteger,
                      parse_constant=_reject_noninteger,
                      object_pairs_hook=_unique_object_pairs)
