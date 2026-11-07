/** Evidence-scoped Move_arrow monster encounter -> battle frame-1 handoff. */
import {previewEncounter} from './combat_probe.mjs';
import {beginBattle} from './battle_frame_probe.mjs';

const directions = {1:[0,-1],2:[0,1],3:[-1,0],4:[1,0]};
const sounds = {20:'music_20',12:'music_24',10:'music_22',17:'music_23'};

export function startEncounter(world, arrowId, monsters) {
  if (!Number.isSafeInteger(arrowId) || !Object.hasOwn(directions,arrowId)) throw new Error('expected original Flash arrow id 1..4');
  if (!world || !['row','col','hp','attack','defense','life','line'].every(k => Number.isSafeInteger(world[k]))) throw new Error('invalid original encounter state');
  const {row,col,grid} = world;
  if (row<0 || row>=11 || col<0 || col>=11) throw new Error('invalid original coordinates');
  if (!Array.isArray(grid) || grid.length!==11 || grid.some(r => !Array.isArray(r) || r.length!==11 || !r.every(Number.isSafeInteger))) throw new Error('expected original 11x11 integer grid');
  const [dr,dc] = directions[arrowId];
  const nr=row+dr, nc=col+dc;
  if (nr<0 || nr>=11 || nc<0 || nc>=11) throw new Error('encounter target outside floor');
  const tile=grid[nr][nc];
  if (!((tile>=40 && tile<=70) || tile===188 || tile===198)) throw new Error('target is not an original monster tile');
  const enemyId=tile===188?31:tile===198?32:tile-40;
  if (!monsters || !Object.hasOwn(monsters,String(enemyId))) throw new Error('missing verified monster entry');
  const monster=monsters[String(enemyId)];
  const preview=previewEncounter(tile,monster,world);
  const state=structuredClone(world);
  if (enemyId===19 && state.line<22) state.boss_kills=1;
  if (!preview.can_start) return {state,event:'encounter_blocked',sound:'music_10',preview,battle:null};
  state.hp-=preview.special_loss;
  state.boss_id=enemyId;
  state.boss_row=nr;state.boss_col=nc;
  state.key_flag=0;state.display_kill=1;
  const battle=beginBattle(monster,state,state.life);
  return {state,event:'encounter_started',sound:sounds[enemyId]??null,preview,battle};
}
