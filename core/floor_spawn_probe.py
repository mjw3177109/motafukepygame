"""FFDec-evidenced SetLineDisplay(1) hero placement; NOT a floor renderer."""


def plan_jump_floor_spawn(matrix: list) -> dict:
    if not isinstance(matrix, list) or len(matrix) != 11 or any(
        not isinstance(row, list) or len(row) != 11 or
        any(type(tile) is not int for tile in row) for row in matrix
    ):
        raise ValueError('original floor must be an 11x11 integer matrix')
    starts = [(row, col) for row in range(11) for col in range(11)
              if matrix[row][col] == 97]
    if len(starts) != 1:
        raise ValueError('jump redraw requires exactly one original tile 97')
    row, col = starts[0]
    return {
        'hero': {'row': row, 'col': col, 'x': 207 + col * 32,
                 'y': 47 + row * 32, 'source': 'mt_99',
                 'instance': 'mt_man', 'depth': 1000},
        'suppressed_98': [{'row': r, 'col': c} for r in range(11)
                          for c in range(11) if matrix[r][c] == 98],
    }
