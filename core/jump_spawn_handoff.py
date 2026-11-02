"""Marker-only preflight for SetLineDisplay(1) after a jump-menu replay.

This is NOT a floor renderer or a keyboard-unlock event. Marker-only
fixtures must never be mistaken for the original full 11x11 tile arrays.
"""
from core.floor_spawn_probe import plan_jump_floor_spawn


def plan_jump_spawn_handoff(replay: dict, markers_by_floor: dict) -> dict:
    if not isinstance(replay, dict) or replay.get('floor_refresh_pending') is not True:
        raise ValueError('pending SetLineDisplay(1) required')
    trace, state = replay.get('trace'), replay.get('state')
    if (not isinstance(trace, list) or not trace or
        not isinstance(trace[-1], dict) or
        trace[-1].get('event') != 'jump_confirm_cleanup' or
        'set_line_display:1' not in trace[-1].get('effects', []) or
        not isinstance(state, dict) or
        type(state.get('key_flag')) is not int or state['key_flag'] != 0 or
        type(state.get('display_jump')) is not int or state['display_jump'] != 0):
        raise ValueError('confirmed jump cleanup and locked keyboard required')
    floor = state.get('now_line')
    if type(floor) is not int or not 1 <= floor <= 26:
        raise ValueError('target floor outside evidenced 01..26 jump markers')
    if not isinstance(markers_by_floor, dict):
        raise ValueError('original marker fixture required')
    markers = markers_by_floor.get(f'{floor:02d}')
    if not isinstance(markers, dict) or set(markers) != {'97', '98', '99'}:
        raise ValueError('original 97/98/99 markers required')
    matrix = [[0] * 11 for _ in range(11)]
    occupied = set()
    for tile in ('97', '98', '99'):
        positions = markers[tile]
        if not isinstance(positions, list):
            raise ValueError('marker positions must be lists')
        for position in positions:
            if (not isinstance(position, list) or len(position) != 2 or
                any(type(v) is not int or not 0 <= v < 11 for v in position)):
                raise ValueError('marker coordinates outside original 11x11 grid')
            row, col = position
            if (row, col) in occupied:
                raise ValueError('overlapping original marker coordinates')
            occupied.add((row, col))
            matrix[row][col] = int(tile)
    spawn = plan_jump_floor_spawn(matrix)
    return {'target_floor': floor, 'spawn': spawn,
            'floor_refresh_pending': True, 'render_status': 'blocked_full_map_missing',
            'key_flag': 0}
