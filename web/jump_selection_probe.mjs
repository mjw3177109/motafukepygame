/** FFDec-evidenced floor-jump cursor navigation only; no floor transition. */
export function stepJumpSelection(world, cursor, arrowId) {
  if (!world || typeof world !== 'object' || Array.isArray(world) ||
      !cursor || typeof cursor !== 'object' || Array.isArray(cursor))
    throw new Error('world and cursor objects required');
  for (const flag of ['key_flag','display_list','display_jump','display_text','display_buy'])
    if (!Number.isSafeInteger(world[flag])) throw new Error('original keyboard gate flags required');
  if (![3,4].includes(arrowId) || !Number.isSafeInteger(arrowId))
    throw new Error('jump selection requires Up(3) or Down(4)');
  if (world.display_jump !== 1 || world.display_buy === 1)
    throw new Error('jump menu inactive or shop modal takes precedence');
  let index=cursor.now_move_id;
  if (!Number.isSafeInteger(index) || index<1 || index>20)
    throw new Error('original cursor index must be 1..20');
  for (const name of ['moves_x','moves_y','move_x'])
    if (typeof cursor[name] !== 'number' || !Number.isFinite(cursor[name]))
      throw new Error('finite numeric cursor coordinates required');
  const state=structuredClone(world), selection=structuredClone(cursor);
  if (arrowId===3) {
    index--;
    if (index===0) { index=20; selection.moves_y+=150; selection.moves_x+=selection.move_x*2; }
    else if ([7,14].includes(index)) { selection.moves_x-=selection.move_x; selection.moves_y+=180; }
    else selection.moves_y-=30;
  } else {
    index++;
    if (index===21) { index=1; selection.moves_y-=150; selection.moves_x-=selection.move_x*2; }
    else if ([8,15].includes(index)) { selection.moves_x+=selection.move_x; selection.moves_y-=180; }
    else selection.moves_y+=30;
  }
  selection.now_move_id=index;
  return {state,cursor:selection,event:'jump_cursor_moved',effects:['play_sound:music_11']};
}
