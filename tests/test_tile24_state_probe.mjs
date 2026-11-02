import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {traceTile24State} from '../web/tile24_state_probe.mjs';

const cases = JSON.parse(readFileSync(new URL('./fixtures/tile24_state_cases.json', import.meta.url), 'utf8'));
for (const c of cases) {
  test('tile24 synthetic shared case: ' + c.name, () => {
    const original = structuredClone(c.input);
    const result = traceTile24State(c.input);
    assert.deepEqual(c.input, original, 'input mutated');
    assert.deepEqual(result.trace.map(x => x.branch), c.branches);
    assert.deepEqual(result.trace.filter(x => x.dialogue_command).map(x => x.dialogue_command), c.dialogues);
    assert.deepEqual(result.trace.filter(x => x.clip_command).map(x => ({branch: x.branch, clip_command: x.clip_command})), c.clip_commands, 'clip command branch/order mismatch');
    assert.deepEqual(result.state, {...c.input, ...c.changed});
    assert.equal(result.flash_runtime_verified, false);
    assert.equal(result.dual_client_parity_verified, false);
    assert.equal(result.gymnasium_ready, false);
    assert.equal(result.source_branch_order_verified, false);
  });
}
test('safe integer boundary matches Python review contract', () => {
  const max = Number.MAX_SAFE_INTEGER;
  assert.equal(traceTile24State({...cases[1].input, tile_id:max}).state.tile_id, max);
  assert.equal(traceTile24State({...cases[1].input, floor20_7_5:-max}).state.floor20_7_5, -max);
});
test('reject unsafe integers without input mutation', () => {
  const unsafe = Number.MAX_SAFE_INTEGER + 1;
  for (const changed of [
    {...cases[1].input, tile_id:unsafe},
    {...cases[1].input, floor20_7_5:unsafe},
    {...cases[1].input, floor20_7_5:-unsafe},
  ]) {
    const before = structuredClone(changed);
    assert.throws(() => traceTile24State(changed));
    assert.deepEqual(changed, before);
  }
});
test('reject malformed and coerced state without mutation', () => {
  const input = cases[1].input;
  for (const bad of [null, [], {...input, my_love:true}, {...input, get_money:[1,1]},
    {...input, now_line:27}, {...input, tile_id:'24'}, {...input, extra:0}]) {
    assert.throws(() => traceTile24State(bad));
  }
});
