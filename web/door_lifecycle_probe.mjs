/** Narrow FFDec-evidenced door completion / sprite855 cleanup; no animation clock. */
export const DOOR_SPRITE_FRAMES=Object.freeze({mt_15:5,mt_05:10,mt_03:10,mt_04:10,mt_02:10});

export function stepDoorLifecycle(snapshot, phase, {sprite=null,frame=null}={}) {
  if (!snapshot || typeof snapshot!=='object' || Array.isArray(snapshot) ||
      !['frame_complete','cleanup'].includes(phase))
    throw new Error('expected snapshot and phase frame_complete/cleanup');
  if (!Number.isSafeInteger(snapshot.open_room) || !Number.isSafeInteger(snapshot.key_flag))
    throw new Error('open_room and key_flag integers required');
  const state=structuredClone(snapshot);
  if (phase==='frame_complete') {
    if (!Object.hasOwn(DOOR_SPRITE_FRAMES,sprite) || !Number.isSafeInteger(frame) ||
        DOOR_SPRITE_FRAMES[sprite]!==frame)
      throw new Error('unverified door sprite/frame');
    if (state.open_room!==1) throw new Error('door frame requires open_room=1');
    state.open_room=2;
    return {state,event:'door_ready_for_cleanup',effects:[]};
  }
  if (sprite!==null || frame!==null) throw new Error('cleanup does not accept sprite/frame');
  if (state.open_room!==2) throw new Error('door cleanup requires open_room=2');
  const x=state.last_x,y=state.last_y;
  if (![x,y].every(Number.isSafeInteger) || x<0 || x>=11 || y<0 || y>=11)
    throw new Error('door cleanup requires original Last_x/Last_y');
  state.open_room=0;
  state.key_flag=1;
  return {state,event:'door_removed',effects:['remove_map_sprite:mt_m_'+x+'_'+y]};
}
