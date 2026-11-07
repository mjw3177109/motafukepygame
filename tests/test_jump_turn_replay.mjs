import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {replayJumpTurns} from '../web/jump_turn_replay.mjs';

const CASES = JSON.parse(readFileSync(new URL('./fixtures/jump_turn_replay_cases.json', import.meta.url), 'utf8'));

test('shared jump sequences and input immutability', () => {
  for (const c of CASES) {
    const world = structuredClone(c.world), cursor = structuredClone(c.cursor), actions = structuredClone(c.actions);
    const result = replayJumpTurns(world, cursor, actions);
    assert.deepEqual(result.trace.map(t => t.event), c.events, c.name);
    assert.equal(result.state.now_line, c.expected_floor, c.name);
    assert.equal(result.state.display_jump, c.expected_mode, c.name);
    assert.equal(result.state.key_flag, c.expected_key, c.name);
    assert.equal(result.cursor.now_move_id, c.expected_index, c.name);
    assert.deepEqual([result.cursor.moves_x, result.cursor.moves_y], [c.expected_x, c.expected_y], c.name);
    assert.equal(result.floor_refresh_pending, c.floor_refresh_pending, c.name);
    assert.deepEqual(world, c.world);
    assert.deepEqual(cursor, c.cursor);
    assert.deepEqual(actions, c.actions);
    assert.deepEqual(result.trace.at(-1).state, result.state);
  }
});

test('no unverified floor redraw or premature cleanup', () => {
  const c = CASES[0];
  assert.throws(() => replayJumpTurns(c.world, c.cursor, [...c.actions, {type: 'down'}]), /floor redraw not implemented/);
  assert.throws(() => replayJumpTurns(c.world, c.cursor, [{type: 'cleanup'}]), /cleanup requires/);
});

test('invalid actions and shop precedence fail closed', () => {
  const c = CASES[0];
  for (const actions of [[{type: 'render_floor'}], [{type: 'up', roll: 0}], [null]])
    assert.throws(() => replayJumpTurns(c.world, c.cursor, actions));
  assert.throws(() => replayJumpTurns({...c.world, display_buy: 1}, c.cursor, [{type: 'up'}]), /shop modal/);
});

test('empty actions do not mutate state', () => {
  const c = CASES[0], result = replayJumpTurns(c.world, c.cursor, []);
  assert.deepEqual(result.trace, []);
  assert.deepEqual(result.state, c.world);
  assert.equal(result.floor_refresh_pending, false);
});
