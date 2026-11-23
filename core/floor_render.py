"""Pygame-compatible blit adapter for verified SetLineDisplay(1) placement plans.

Does not extract sprites, resolve Flash registration points, clear backgrounds,
advance animations, complete a floor refresh, or unlock input.
"""
import math


def _finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def prepare_floor_draws(plan, assets):
    """Preflight all sprites before touching a display surface.

    assets maps each source to {'image': pygame.Surface,
    'origin_x': number, 'origin_y': number}. Registration offsets must come
    from verified source-asset metadata, not inferred from tile dimensions.
    """
    if not isinstance(plan, dict) or plan.get('floor_refresh_pending') is not True or plan.get('key_unlock') is not False:
        raise ValueError('requires a pending, input-locked floor placement plan')
    placements = plan.get('placements')
    if not isinstance(placements, list) or not placements:
        raise ValueError('missing placements')
    if not isinstance(assets, dict):
        raise ValueError('assets must be a mapping')
    prepared, instances = [], set()
    for index, item in enumerate(placements):
        if not isinstance(item, dict):
            raise ValueError('invalid placement')
        source, instance = item.get('source'), item.get('instance')
        if not isinstance(source, str) or not source or not isinstance(instance, str) or not instance or instance in instances:
            raise ValueError('invalid or duplicate sprite instance')
        instances.add(instance)
        if type(item.get('depth')) is not int or not all(_finite_number(item.get(k)) for k in ('x', 'y')):
            raise ValueError('invalid placement depth or coordinates')
        asset = assets.get(source)
        if not isinstance(asset, dict) or asset.get('image') is None or not all(_finite_number(asset.get(k)) for k in ('origin_x', 'origin_y')):
            raise ValueError(f'missing verified image/registration for {source}')
        prepared.append({'source': source, 'instance': instance, 'depth': item['depth'],
                         'x': item['x'] - asset['origin_x'], 'y': item['y'] - asset['origin_y'],
                         'image': asset['image'], '_index': index})
    prepared.sort(key=lambda item: (item['depth'], item['_index']))
    return [{k: v for k, v in item.items() if k != '_index'} for item in prepared]


def blit_floor_plan(surface, plan, assets):
    """Execute a prepared depth-ordered plan on a pygame.Surface-like target."""
    draws = prepare_floor_draws(plan, assets)
    if not callable(getattr(surface, 'blit', None)):
        raise ValueError('surface must provide blit(image, position)')
    for item in draws:
        surface.blit(item['image'], (item['x'], item['y']))
    return len(draws)
