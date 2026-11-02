/** FFDec-evidenced text frame32 / sprite855 frame1 sub-branch only. */
export function stepTextLifecycle(snapshot, phase) {
  if (!snapshot || typeof snapshot!=='object' || Array.isArray(snapshot) || !['frame32','cleanup'].includes(phase))
    throw new Error('expected snapshot and phase frame32/cleanup');
  if (!Number.isSafeInteger(snapshot.display_text) || !Number.isSafeInteger(snapshot.key_flag))
    throw new Error('display_text and key_flag integers required');
  const state=structuredClone(snapshot);
  if (phase==='frame32') {
    if (state.display_text!==1 || !Number.isSafeInteger(state.boss_kills))
      throw new Error('frame32 requires display_text=1 and boss_kills');
    state.key_flag=state.boss_kills===1 ? 0 : 1;
    state.display_text=2;
    return {state,event:'text_ready_for_cleanup',effects:[]};
  }
  if (state.display_text!==2 || !Number.isSafeInteger(state.floor26_cell_3_5))
    throw new Error('cleanup requires display_text=2 and original floor26 cell');
  state.display_text=0;
  const effects=['remove_text_sprite'];
  if (state.floor26_cell_3_5===0) effects.push('clear_base_display','clear_line_display','goto_game_over');
  return {state,event:effects.length>1?'game_over_requested':'text_removed',effects};
}
