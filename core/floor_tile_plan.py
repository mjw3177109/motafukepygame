"""Static sprite placement plan for original SetLineDisplay(1), not a renderer.

Evidence: game.swf / frame_4346/DoAction_2.as; this intentionally does not
play sounds, mutate game state, complete floor refresh, or unlock input.
"""


def plan_jump_floor_tiles(matrix: list) -> dict:
    if (not isinstance(matrix, list) or len(matrix) != 11 or
        any(not isinstance(row, list) or len(row) != 11 or
            any(type(tile) is not int or tile < 0 for tile in row)
            for row in matrix)):
        raise ValueError('full original floor must be an 11x11 nonnegative integer matrix')
    spawns = [(r, c) for r in range(11) for c in range(11) if matrix[r][c] == 97]
    if len(spawns) != 1:
        raise ValueError('SetLineDisplay(1) requires exactly one original tile 97')
    placements = []
    suppressed = []
    for r, row in enumerate(matrix):
        for c, tile in enumerate(row):
            if tile == 0:
                continue
            if tile == 98:
                suppressed.append({'row': r, 'col': c})
                continue
            if tile == 97:
                source, instance, depth = 'mt_99', 'mt_man', 1000
            else:
                if tile < 10:
                    source = f'mt_0{tile}'
                elif tile == 115:
                    source = 'mt_15'
                elif tile == 120:
                    source = 'mt_20'
                elif tile in (119, 129, 139, 149, 159, 169, 179):
                    source = 'mt_00'
                else:
                    source = f'mt_{tile}'
                instance = 'mt_sister' if source == 'mt_24' else f'mt_m_{r}_{c}'
                depth = 500 + (r + 1) * 11 + c + 1
            placement = {'row': r, 'col': c, 'tile': tile, 'source': source,
                         'instance': instance, 'depth': depth,
                         'x': 207 + 32 * c, 'y': 47 + 32 * r}
            if tile in (1, 2, 3, 4, 5, 15, 115):
                placement['stop_frame'] = 1
            placements.append(placement)
    return {'hero': {'row': spawns[0][0], 'col': spawns[0][1],
                     'x': 207 + 32 * spawns[0][1], 'y': 47 + 32 * spawns[0][0]},
            'placements': placements, 'suppressed_98': suppressed,
            'floor_refresh_pending': True, 'key_unlock': False}
