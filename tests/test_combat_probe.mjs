import {createHash} from 'node:crypto';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {previewEncounter} from '../web/combat_probe.mjs';
const cases = JSON.parse(readFileSync(new URL('./fixtures/combat_probe_cases.json', import.meta.url),'utf8'));
for (const vector of cases) {
  test(vector.name, () => {
    const before = JSON.stringify(vector);
    assert.deepEqual(previewEncounter(vector.tile,vector.monster,vector.hero),vector.expected);
    assert.equal(JSON.stringify(vector),before);
  });
}
test('invalid tile rejected',()=>assert.throws(()=>previewEncounter(71,cases[0].monster,cases[0].hero)));
test('invalid monster rejected',()=>assert.throws(()=>previewEncounter(40,[50,20],cases[0].hero)));

// Source-roster regression: 132 synthetic entry estimates, NOT Flash replay.
const roster = JSON.parse(readFileSync(new URL('../data/original_combat_tables.json', import.meta.url), 'utf8'));
function expectedRosterEntry(enemyId, monster, hero) {
  const [hp, attack, defense] = monster;
  if (hero.attack <= defense) return {enemy_id: enemyId, can_start: false,
    reason: 'insufficient_attack', base_loss: null, special_loss: null, estimated_loss: null};
  const base = Math.floor(hp / (hero.attack - defense)) * (attack - hero.defense);
  const special = enemyId === 20 ? 100 : enemyId === 12 ? 300 :
    enemyId === 10 ? Math.floor(hero.hp / 4) :
    enemyId === 17 ? Math.floor(hero.hp / 3) : 0;
  const loss = base + special, allowed = loss <= hero.hp;
  return {enemy_id: enemyId, can_start: allowed,
    reason: allowed ? 'ok' : 'insufficient_hp',
    base_loss: base, special_loss: special, estimated_loss: loss};
}
test('all 33 original monster rows, SWF anchor and RL gate remain pinned', () => {
  const swfHash = createHash('sha256').update(readFileSync(new URL('../game.swf',import.meta.url))).digest('hex');
  assert.equal(roster.source.swf_sha256, swfHash);
  assert.deepEqual(Object.keys(roster.monsters).sort((a,b)=>Number(a)-Number(b)),
    Array.from({length:33},(_,i)=>String(i)));
  assert.equal(roster.gameplay_parity_verified, false);
  assert.equal(roster.gymnasium_ready, false);
  for (const monster of Object.values(roster.monsters)) {
    assert.equal(monster.length, 6);
    assert.ok(monster.slice(0,5).every(Number.isSafeInteger));
    assert.ok(monster[0] > 0);
  }
});
test('all 33 original monster tiles across four synthetic hero profiles (132 cases)', () => {
  for (let enemyId=0;enemyId<33;enemyId++) {
    const monster = roster.monsters[String(enemyId)];
    const tile = enemyId < 31 ? enemyId+40 : enemyId === 31 ? 188 : 198;
    const profiles = [
      {hp:1000,attack:1,defense:10},
      {hp:1000,attack:200,defense:50},
      {hp:100000,attack:6000,defense:1000},
      {hp:100000,attack:monster[2]+1,defense:monster[1]},
    ];
    for (const hero of profiles) {
      const beforeMonster = structuredClone(monster), beforeHero = structuredClone(hero);
      assert.deepEqual(previewEncounter(tile,monster,hero),expectedRosterEntry(enemyId,monster,hero),
        'monster '+enemyId+', hero '+JSON.stringify(hero));
      assert.deepEqual(monster,beforeMonster);
      assert.deepEqual(hero,beforeHero);
    }
  }
});
