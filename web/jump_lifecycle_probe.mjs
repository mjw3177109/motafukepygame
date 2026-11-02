/** FFDec-evidenced jump-menu button actions and sprite855 cleanup; no floor rendering. */
export function stepJumpLifecycle(world, cursor, action) {
  if (!world || typeof world !== 'object' || Array.isArray(world))
    throw new Error('world object required');
  for (const key of ['display_jump', 'key_flag', 'now_line', 'max_line'])
    if (!Number.isSafeInteger(world[key])) throw new Error('original jump flags and floor fields required');
  if (!['confirm', 'cancel', 'cleanup'].includes(action)) throw new Error('unsupported jump action');
  const state = structuredClone(world), mode = state.display_jump;
  if (action === 'confirm') {
    if (mode !== 1) throw new Error('confirmation requires active selection state 1');
    if (!cursor || typeof cursor !== 'object' || Array.isArray(cursor) ||
        !Number.isSafeInteger(cursor.now_move_id) || cursor.now_move_id < 1 || cursor.now_move_id > 20)
      throw new Error('selected floor must be 1..20');
    const accepted = cursor.now_move_id < state.max_line;
    state.display_jump = 2;
    if (accepted) state.now_line = cursor.now_move_id;
    return {state, event: accepted ? 'jump_confirm_accepted' : 'jump_confirm_rejected',
      effects: accepted ? ['del_line_display', 'play_sound:music_07'] : ['play_sound:music_10']};
  }
  if (action === 'cancel') {
    if (![1, 3].includes(mode)) throw new Error('cancel requires jump state 1 or 3');
    state.display_jump = 4;
    if (mode === 1) state.key_flag = 1;
    return {state, event: 'jump_cancel_requested', effects: []};
  }
  if (mode === 2) {
    state.display_jump = 0;
    state.key_flag = 0;
    return {state, event: 'jump_confirm_cleanup',
      effects: ['del_movie:mt_line_jump', 'set_line_display:1']};
  }
  if (mode === 4) {
    state.display_jump = 0;
    state.key_flag = 1;
    return {state, event: 'jump_cancel_cleanup', effects: ['del_movie:mt_line_jump']};
  }
  throw new Error('cleanup requires jump state 2 or 4');
}
