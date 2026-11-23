"""Source-anchored floor selector and coordinate lookup within Move_arrow.

Static ActionScript evidence only; not a runtime event or Flash parity proof.
"""
import re


def verify_move_arrow_binding(source: str) -> dict:
    declarations = list(re.finditer(r'(?m)^function[ \t]+Move_arrow\(arrow_id\)[ \t]*\r?\n\{', source))
    if len(declarations) != 1:
        raise ValueError(f'expected exactly one Move_arrow(arrow_id), found {len(declarations)}')
    start = declarations[0]
    tail = source[start.end():]
    end = re.search(r'(?m)^}[ \t\r]*$', tail)
    if end is None:
        raise ValueError('missing Move_arrow top-level closing brace')
    body = tail[:end.start()]

    def exactly_one(pattern: str, label: str) -> None:
        count = len(list(re.finditer(pattern, body, re.MULTILINE | re.DOTALL)))
        if count != 1:
            raise ValueError(f'Move_arrow {label} anchor count: {count} (expected 1)')

    exactly_one(
        r'if\s*\(\s*_root\.Now_line\s*<\s*10\s*\)\s*\{\s*'
        r'temp_lines\s*=\s*"_root\.mt_line_0"\s+add\s+_root\.Now_line\s*;\s*\}'
        r'\s*else\s*\{\s*temp_lines\s*=\s*"_root\.mt_line_"\s+add\s+_root\.Now_line\s*;\s*\}',
        'zero-padded floor selector',
    )
    assignments = re.findall(r'(?m)^[ \t]*temp_lines[ \t]*=', body)
    if len(assignments) != 2:
        raise ValueError('Move_arrow has unexpected temp_lines reassignment')
    exactly_one(r'temp_x\s*=\s*_root\.Now_xid\s*;\s*temp_y\s*=\s*_root\.Now_yid\s*;',
                'player index initialization')
    exactly_one(r'_root\.mt_man\._x\s*=\s*207\s*\+\s*temp_y\s*\*\s*32\s*;',
                'screen x mapping')
    exactly_one(r'_root\.mt_man\._y\s*=\s*47\s*\+\s*temp_x\s*\*\s*32\s*;',
                'screen y mapping')
    for tile, expected in ((129, 1), (24, 4)):
        pattern = (r'if\s*\(\s*Number\(eval\(temp_lines\)\[temp_x\]\[temp_y\]\)\s*==\s*'
                   + str(tile) + r'\s*&&')
        count = len(list(re.finditer(pattern, body)))
        if count != expected:
            raise ValueError(f'Move_arrow event tile {tile} lookup count: {count} (expected {expected})')
    return {
        'floor_selector': 'Now_line < 10: mt_line_0 + Now_line; otherwise mt_line_ + Now_line',
        'lookup_indices': 'eval(temp_lines)[temp_x][temp_y]',
        'initial_indices': {'temp_x': 'Now_xid', 'temp_y': 'Now_yid'},
        'screen_x_source_formula': '207 + temp_y * 32',
        'screen_y_source_formula': '47 + temp_x * 32',
        'tile_event_lookup_counts_within_move_arrow': {'24': 4, '129': 1},
        'static_source_binding_verified': True,
        'runtime_floor_selection_verified': False,
        'runtime_event_reachability_verified': False,
    }
