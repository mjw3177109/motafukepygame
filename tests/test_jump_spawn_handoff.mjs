import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {replayJumpTurns} from '../web/jump_turn_replay.mjs';
import {planJumpSpawnHandoff} from '../web/jump_spawn_handoff.mjs';

const fixture = (name) => JSON.parse(readFileSync(new URL('./fixtures/' + name, import.meta.url), 'utf8'));
const CASES = fixture('jump_turn_replay_cases.json');
const MARKERS = fixture('floor_spawn_markers.json').floors;
const replay = (c) => replayJumpTurns(c.world, c.cursor, c.actions);

test('accepted and rejected confirmations use original spawn markers without unlocking', () => {
  for (const c of CASES.slice(0, 2)) {
    const state = replay(c), original = structuredClone(state), markers = structuredClone(MARKERS);
    const result = planJumpSpawnHandoff(state, MARKERS);
    assert.equal(result.target_floor, c.expected_floor);
    assert.deepEqual([result.spawn.hero.row, result.spawn.hero.col], MARKERS[String(c.expected_floor).padStart(2, '0')]['97'][0]);
    assert.equal(result.render_status, 'blocked_full_map_missing');
    assert.equal(result.floor_refresh_pending, true);
    assert.equal(result.key_flag, 0);
    assert.deepEqual(state, original);
    assert.deepEqual(MARKERS, markers);
  }
});

test('cancel and fabricated cleanup do not permit spawn planning', () => {
  for (const c of CASES.slice(2))
    assert.throws(() => planJumpSpawnHandoff(replay(c), MARKERS), /pending/);
  const state = replay(CASES[0]);
  state.trace.at(-1).event = 'jump_cancel_cleanup';
  assert.throws(() => planJumpSpawnHandoff(state, MARKERS), /confirmed jump/);
});

test('missing, ambiguous, out-of-bounds and overlapping markers fail closed', () => {
  const state = replay(CASES[0]);
  for (const markers of [{}, {'20': {'97': [], '98': [], '99': []}},
    {'20': {'97': [[0, 0], [1, 1]], '98': [], '99': []}},
    {'20': {'97': [[11, 0]], '98': [], '99': []}},
    {'20': {'97': [[0, 0]], '98': [[0, 0]], '99': []}}])
    assert.throws(() => planJumpSpawnHandoff(state, markers));
  state.state.now_line = 0;
  assert.throws(() => planJumpSpawnHandoff(state, MARKERS), /01..26/);
});
