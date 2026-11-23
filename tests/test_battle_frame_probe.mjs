import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {beginBattle, stepBattleFrame} from '../web/battle_frame_probe.mjs';

const cases = JSON.parse(readFileSync(new URL('./fixtures/battle_frame_probe_cases.json', import.meta.url), 'utf8'));
test('original frame 1 setup', () => {
  assert.deepEqual(beginBattle([10,20,1,1,1,'绿头怪'], {hp:5,attack:11,defense:10}, 0), cases[0].state);
});
for (const c of cases) {
  test(c.name, () => {
    const before = structuredClone(c.state);
    assert.deepEqual(stepBattleFrame(c.state, c.roll), c.expected);
    assert.deepEqual(c.state, before);
  });
}
test('invalid random rolls and incomplete states fail closed', () => {
  assert.throws(() => stepBattleFrame(cases[0].state));
  assert.throws(() => stepBattleFrame(cases[0].state, 200));
  assert.throws(() => stepBattleFrame(cases[1].state, 0));
  assert.throws(() => stepBattleFrame({left_hp:10}));
});
