"""Evidence-scoped Flash 1.12 jump-menu confirm/cancel and sprite855 cleanup.

This does not implement SetLineDisplay, floor map placement, or animation timing.
"""
from copy import deepcopy


def step_jump_lifecycle(world: dict, cursor: dict | None, action: str) -> dict:
    if not isinstance(world, dict):
        raise ValueError('world object required')
    for key in ('display_jump', 'key_flag', 'now_line', 'max_line'):
        if type(world.get(key)) is not int:
            raise ValueError('original jump flags and floor fields required')
    if type(action) is not str or action not in ('confirm', 'cancel', 'cleanup'):
        raise ValueError('unsupported jump action')
    state = deepcopy(world)
    mode = state['display_jump']
    if action == 'confirm':
        if mode != 1:
            raise ValueError('confirmation requires active selection state 1')
        if not isinstance(cursor, dict) or type(cursor.get('now_move_id')) is not int or not 1 <= cursor['now_move_id'] <= 20:
            raise ValueError('selected floor must be 1..20')
        selected = cursor['now_move_id']
        accepted = selected < state['max_line']
        state['display_jump'] = 2
        if accepted:
            state['now_line'] = selected
        return {'state': state, 'event': 'jump_confirm_accepted' if accepted else 'jump_confirm_rejected',
                'effects': ['del_line_display', 'play_sound:music_07'] if accepted else ['play_sound:music_10']}
    if action == 'cancel':
        if mode not in (1, 3):
            raise ValueError('cancel requires jump state 1 or 3')
        state['display_jump'] = 4
        if mode == 1:
            state['key_flag'] = 1  # DefineButton2_718 J
        # DefineButton2_856 J in state 3 leaves key flag unchanged.
        return {'state': state, 'event': 'jump_cancel_requested', 'effects': []}
    if mode == 2:
        state['display_jump'] = 0
        state['key_flag'] = 0
        return {'state': state, 'event': 'jump_confirm_cleanup',
                'effects': ['del_movie:mt_line_jump', 'set_line_display:1']}
    if mode == 4:
        state['display_jump'] = 0
        state['key_flag'] = 1
        return {'state': state, 'event': 'jump_cancel_cleanup',
                'effects': ['del_movie:mt_line_jump']}
    raise ValueError('cleanup requires jump state 2 or 4')
