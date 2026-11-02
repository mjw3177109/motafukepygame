import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planJumpFloorSpawn} from '../web/floor_spawn_probe.mjs';

const DATA = JSON.parse(readFileSync(new URL('./fixtures/floor_spawn_markers.json', import.meta.url), 'utf8'));
function makeFloor(c) {
  const matrix = Array.from({length: 11}, () => Array(11).fill(0));
  for (const marker of ['97', '98', '99'])
    for (const [row, col] of c[marker]) matrix[row][col] = Number(marker);
  return matrix;
}
test('original 27 floor spawn markers and pixel coordinates', () => {
  assert.equal(Object.keys(DATA.floors).length, 27);
  assert.equal(DATA.source_script_sha256, '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034');
  for (const [floor, c] of Object.entries(DATA.floors)) {
    const matrix = makeFloor(c);
    if (floor === '00') {
      assert.throws(() => planJumpFloorSpawn(matrix), /tile 97/);
      continue;
    }
    const [row, col] = c['97'][0];
    assert.deepEqual(planJumpFloorSpawn(matrix), {
      hero: {row, col, x: 207 + col * 32, y: 47 + row * 32,
        source: 'mt_99', instance: 'mt_man', depth: 1000},
      suppressed_98: c['98'].map(([r, c]) => ({row: r, col: c})),
    }, floor);
  }
});
test('invalid matrices and ambiguous hero marker fail closed', () => {
  for (const bad of [null, [], Array.from({length: 10}, () => Array(11).fill(0)),
    Array.from({length: 11}, () => Array(11).fill(true))])
    assert.throws(() => planJumpFloorSpawn(bad));
  const matrix = makeFloor(DATA.floors['01']);
  matrix[0][0] = 97;
  assert.throws(() => planJumpFloorSpawn(matrix), /tile 97/);
});
