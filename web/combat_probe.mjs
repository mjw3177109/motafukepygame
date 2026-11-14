/** Read-only original Move_arrow monster entry gate; NOT the fight animation. */
export function previewEncounter(tile, monster, hero) {
  if (!Number.isSafeInteger(tile) || !((tile >= 40 && tile <= 70) || tile === 188 || tile === 198)) {
    throw new Error('unsupported original monster tile');
  }
  const enemyId = tile === 188 ? 31 : tile === 198 ? 32 : tile - 40;
  if (!Array.isArray(monster) || monster.length !== 6 || !monster.slice(0,5).every(Number.isSafeInteger) || typeof monster[5] !== 'string') {
    throw new Error('expected raw six-field original boss_man array');
  }
  if (!hero || !['hp','attack','defense'].every(k => Number.isSafeInteger(hero[k]))) {
    throw new Error('hero must contain integer hp, attack and defense');
  }
  const [enemyHp,enemyAttack,enemyDefense] = monster;
  if (hero.attack <= enemyDefense) {
    return {enemy_id:enemyId,can_start:false,reason:'insufficient_attack',base_loss:null,special_loss:null,estimated_loss:null};
  }
  // Flash int() truncates toward zero. Never round up or clamp negative loss.
  const baseLoss = Math.trunc(enemyHp / (hero.attack - enemyDefense)) * (enemyAttack - hero.defense);
  const specialLoss = enemyId === 20 ? 100 : enemyId === 12 ? 300 : enemyId === 10 ? Math.trunc(hero.hp / 4) : enemyId === 17 ? Math.trunc(hero.hp / 3) : 0;
  const loss = baseLoss + specialLoss;
  const canStart = loss <= hero.hp;
  return {enemy_id:enemyId,can_start:canStart,reason:canStart?'ok':'insufficient_hp',base_loss:baseLoss,special_loss:specialLoss,estimated_loss:loss};
}
