"""Classify renderer pixel differences by visible sprite edge, interior or outside.

Diagnostics only: an edge correlation does not establish SVG/Flash causality.
"""


def summarize_difference_regions(left: bytes, right: bytes, width: int, height: int):
    """Count raw RGBA/alpha mismatches by four-neighbour visibility geometry.

    A pixel is visible if alpha > 1 in either renderer. A visible pixel is
    edge-adjacent when it is absent in either renderer, or any cardinal
    neighbour is outside the canvas or has alpha <= 1 in either renderer.
    Fully invisible pixels belong to 'outside', even if hidden RGB differs.
    """
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError('invalid raster dimensions')
    size = width * height * 4
    if len(left) != size or len(right) != size:
        raise ValueError('invalid RGBA byte length')

    def visible(data, index):
        return data[index * 4 + 3] > 1

    rgba = {'edge': 0, 'interior': 0, 'outside': 0}
    alpha = {'edge': 0, 'interior': 0, 'outside': 0}
    for i in range(width * height):
        off = i * 4
        differs = left[off:off + 4] != right[off:off + 4]
        alpha_differs = left[off + 3] != right[off + 3]
        if not (differs or alpha_differs):
            continue
        if not (visible(left, i) or visible(right, i)):
            region = 'outside'
        else:
            x, y = i % width, i // width
            neighbours = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if (not visible(left, i) or not visible(right, i) or
                any(nx < 0 or ny < 0 or nx >= width or ny >= height or
                    not visible(left, ny * width + nx) or
                    not visible(right, ny * width + nx)
                    for nx, ny in neighbours)):
                region = 'edge'
            else:
                region = 'interior'
        rgba[region] += int(differs)
        alpha[region] += int(alpha_differs)
    return {'rgba': rgba, 'alpha': alpha,
            'definition': '4-neighbour, union alpha>1; diagnostic only'}
