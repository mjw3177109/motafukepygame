import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {frame54Handoff, consumeBattleCompletion} from '../web/battle_settlement_probe.mjs';
const cases = JSON.parse(readFileSync(fileURLToPath(new URL('./fixtures/battle_settlement_cases.json', import.meta.url)), 'utf8'));
for (const c of cases) test(c.name, () => {
  const original = structuredClone(c.world);
  const handoff = frame54Handoff(c.world, c.battle);
  assert.deepStrictEqual(handoff, c.handoff);
  assert.deepStrictEqual(consumeBattleCompletion(handoff.state, c.monster), c.settled);
  assert.deepStrictEqual(c.world, original);
});
test('rejects premature and duplicate rewards', () => {
  const c = cases[0];
  assert.throws(() => consumeBattleCompletion(c.world,c.monster), /display_kill=2/);
  assert.throws(() => consumeBattleCompletion(c.settled.state,c.monster), /display_kill=2/);
});
test('rejects invalid boss footprint', () => {
  const c = cases[1];
  assert.throws(() => consumeBattleCompletion({...c.handoff.state,boss_row:1},c.monster), /footprint/);
});
test('frame54 requires monster death', () => {
  const c = cases[0];
  assert.throws(() => frame54Handoff(c.world,{left_hp:1,right_hp:5}), /completed monster/);
});


test('zero/negative HP reward path is source-scoped, not a Flash death verdict', () => {
  const c = cases[0];
  for (const hp of [0,-15]) {
    const world=structuredClone(c.world);
    const handoff=frame54Handoff(world,{...c.battle,right_hp:hp});
    const reward=consumeBattleCompletion(handoff.state,c.monster);
    assert.equal(reward.state.hp,hp);
    assert.equal(reward.state.money,world.money+c.monster[3]);
    assert.equal(reward.state.mp,world.mp+c.monster[4]);
    assert.equal(reward.state.grid[5][5],0);
    assert.deepEqual(world,c.world);
  }
});
