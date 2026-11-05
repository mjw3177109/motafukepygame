import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planInitialFloorSpawn} from '../web/initial_spawn_probe.mjs';

const payload = JSON.parse(readFileSync(new URL('../data/original_floors.json', import.meta.url), 'utf8'));
const floor = payload.floors['00'];

test('FFDec-pinned committed floor 00 initial spawn matches Python planner', () => {
  assert.equal(payload.source.renderer_actionscript_sha256,
    '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034');
  assert.deepEqual(planInitialFloorSpawn(floor), {
    hero: {row: 9, col: 5, x: 367, y: 335, source: 'mt_99', instance: 'mt_man', depth: 1000},
    suppressed_98: [{row: 1, col: 5}],
  });
  assert.equal(floor.flat().includes(97), false);
});

test('missing, duplicate, unsafe and sparse markers fail closed', () => {
  const altered = () => floor.map(row => [...row]);
  for (const replacement of [0, 97]) {
    const m = altered(); m[9][5] = replacement;
    assert.throws(() => planInitialFloorSpawn(m), /tile 99/);
  }
  const duplicate = altered(); duplicate[0][0] = 99;
  assert.throws(() => planInitialFloorSpawn(duplicate), /tile 99/);
  for (const value of [true, 2 ** 53, -(2 ** 53)]) {
    const m = altered(); m[0][0] = value;
    assert.throws(() => planInitialFloorSpawn(m), /safe-integer matrix/);
  }
  const sparse = altered(); delete sparse[0][0];
  assert.throws(() => planInitialFloorSpawn(sparse), /safe-integer matrix/);
  assert.deepEqual(planInitialFloorSpawn(floor), planInitialFloorSpawn(altered()));
});
