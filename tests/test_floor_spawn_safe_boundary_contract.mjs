import test from 'node:test';
import assert from 'node:assert/strict';
import {planJumpFloorSpawn} from '../web/floor_spawn_probe.mjs';

function blankFloor() {
  return Array.from({length: 11}, () => Array(11).fill(0));
}

test('maximum safe integer preserves independent spawn and suppression contract', () => {
  const floor = blankFloor();
  floor[0][0] = Number.MAX_SAFE_INTEGER;
  floor[4][7] = 97;
  floor[2][3] = 98;
  floor[9][1] = 98;
  assert.deepEqual(planJumpFloorSpawn(floor), {
    hero: {row: 4, col: 7, x: 431, y: 175,
      source: 'mt_99', instance: 'mt_man', depth: 1000},
    suppressed_98: [{row: 2, col: 3}, {row: 9, col: 1}],
  });
});

test('negative maximum safe integer preserves independent spawn contract', () => {
  const floor = blankFloor();
  floor[0][0] = Number.MIN_SAFE_INTEGER;
  floor[10][10] = 97;
  assert.deepEqual(planJumpFloorSpawn(floor).hero, {
    row: 10, col: 10, x: 527, y: 367,
    source: 'mt_99', instance: 'mt_man', depth: 1000,
  });
});
