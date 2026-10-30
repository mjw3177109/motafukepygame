/** Pure frame-1/frame-24 probe for original mt_other_04 battle sprite. */
const fields = ['left_hp','left_gong','left_fang','right_hp','right_gong','right_fang','life','kill_left','kill_right','kill_number'];

export function beginBattle(monster, hero, life) {
  if (!Array.isArray(monster) || monster.length !== 6 || !monster.slice(0,5).every(Number.isSafeInteger) || typeof monster[5] !== 'string') {
    throw new Error('expected raw six-field boss_man entry');
  }
  if (!hero || !['hp','attack','defense'].every(k => Number.isSafeInteger(hero[k]))) {
    throw new Error('hero requires integer hp, attack and defense');
  }
  if (!Number.isSafeInteger(life) || life < 0) throw new Error('life must be a nonnegative integer');
  const [left_hp,left_gong,left_fang] = monster;
  const {hp:right_hp,attack:right_gong,defense:right_fang} = hero;
  return {left_hp,left_gong,left_fang,right_hp,right_gong,right_fang,life,
    kill_left:Math.max(0,left_gong-right_fang),kill_right:Math.max(0,right_gong-left_fang),kill_number:0};
}

export function stepBattleFrame(snapshot, criticalRoll = null) {
  if (!snapshot || !fields.every(k => Number.isSafeInteger(snapshot[k]))) {
    throw new Error('battle snapshot requires integer original fields');
  }
  if (['kill_number','life','kill_left','kill_right'].some(k => snapshot[k] < 0)) {
    throw new Error('invalid battle counters or damage');
  }
  const state = {...snapshot};
  if (!(state.left_hp > 0 || state.right_hp > 0)) {
    if (criticalRoll !== null) throw new Error('idle frame does not consume a random roll');
    return {state,event:'idle',damage:0,critical:null,jump_to_35:false};
  }
  let damage, critical, event, jump;
  if (state.kill_number % 2 === 0) {
    if (!Number.isSafeInteger(criticalRoll) || criticalRoll < 0 || criticalRoll >= 200) {
      throw new Error('hero attack requires Flash random(200) result in 0..199');
    }
    critical = criticalRoll <= state.life;
    damage = state.kill_right * (critical ? 2 : 1);
    state.left_hp = Math.max(0,state.left_hp-damage);
    event = 'hero_attack'; jump = false;
  } else {
    if (criticalRoll !== null) throw new Error('monster counterattack must not consume a random roll');
    damage = state.kill_left; critical = null;
    state.right_hp -= damage; // Deliberately NOT clamped in original.
    event = 'monster_counterattack'; jump = state.left_hp === 0;
  }
  state.kill_number += 1;
  return {state,event,damage,critical,jump_to_35:jump};
}
