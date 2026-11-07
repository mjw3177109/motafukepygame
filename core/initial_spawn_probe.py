"""Source-pinned initial spawn for SetLineDisplay(0), not runtime parity.

FFDec game.swf export/scripts/frame_4346/DoAction_2.as SHA-256:
0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034
Lines 182-186 select tile 99; 204-214 suppress tile 98 and copy mt_99.
DoAction_3.as invokes SetLineDisplay(0). This does not model event/input state.
"""


def plan_initial_floor_spawn(matrix: list) -> dict:
    """Describe hero placement for the initial draw only (arrow_id == 0)."""
    if not isinstance(matrix, list) or len(matrix) != 11 or any(
        not isinstance(row, list) or len(row) != 11 or
        any(type(tile) is not int or abs(tile) > 9007199254740991 for tile in row)
        for row in matrix
    ):
        raise ValueError('original floor must be an 11x11 safe-integer matrix')
    starts = [(r, c) for r in range(11) for c in range(11) if matrix[r][c] == 99]
    if len(starts) != 1:
        raise ValueError('initial redraw requires exactly one original tile 99')
    row, col = starts[0]
    return {
        'hero': {'row': row, 'col': col, 'x': 207 + col * 32,
                 'y': 47 + row * 32, 'source': 'mt_99',
                 'instance': 'mt_man', 'depth': 1000},
        'suppressed_98': [{'row': r, 'col': c} for r in range(11)
                          for c in range(11) if matrix[r][c] == 98],
    }
