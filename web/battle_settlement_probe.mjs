/** Evidence-scoped mt_other_04 frame54 -> sprite855 -> Move_arrow(100). */
const isInt = Number.isSafeInteger;

export function frame54Handoff(world, battle) {
  if (!world || world.display_kill !== 1 || !isInt(world.hp)) throw new Error('frame54 requires an active battle (display_kill=1)');
  if (!battle || !isInt(battle.right_hp) || battle.left_hp !== 0) throw new Error('frame54 requires a completed monster animation');
  return {state: {...structuredClone(world), display_kill: 2, hp: battle.right_hp}, event: 'frame54_handoff'};
}

export function consumeBattleCompletion(world, monster) {
  if (!world || world.display_kill !== 2) throw new Error('battle settlement requires display_kill=2');
  if (!Array.isArray(monster) || monster.length !== 6 || !monster.slice(0, 5).every(isInt) || typeof monster[5] !== 'string') {
    throw new Error('expected original six-field boss_man entry');
  }
  if (!['boss_id', 'boss_row', 'boss_col', 'hp', 'money', 'mp'].every(k => isInt(world[k]))) throw new Error('invalid battle settlement state');
  const {boss_id, boss_row:row, boss_col:col} = world;
  if (boss_id < 0 || boss_id > 32 || row < 0 || row >= 11 || col < 0 || col >= 11) throw new Error('invalid original monster id or coordinates');
  if (!Array.isArray(world.grid) || world.grid.length !== 11 || !world.grid.every(line => Array.isArray(line) && line.length === 11 && line.every(isInt))) {
    throw new Error('expected 11x11 integer grid');
  }
  const cells = [];
  if (boss_id === 31 || boss_id === 32) {
    for (let r = row - 2; r <= row; r++) for (let c = col - 1; c <= col + 1; c++) cells.push([r, c]);
  } else cells.push([row, col]);
  if (cells.some(([r,c]) => r < 0 || r >= 11 || c < 0 || c >= 11)) throw new Error('boss footprint outside original 11x11 floor');
  const state = structuredClone(world);
  state.display_kill = 0;
  state.display_text = 1;
  for (const [r,c] of cells) state.grid[r][c] = 0;
  state.money += monster[3];
  state.mp += monster[4];
  return {state, event:'battle_reward', cleared:cells,
    removed_clips:cells.map(([r,c]) => `mt_m_${r}_${c}`),
    message:`得到金币数 ${monster[3]} 经验值 ${monster[4]} ！`, sound:'music_03'};
}
