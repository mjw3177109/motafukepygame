import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planJumpFloorTiles} from '../web/floor_tile_plan.mjs';
const data = JSON.parse(readFileSync(new URL('../data/original_floors.json', import.meta.url),'utf8'));
const markers = JSON.parse(readFileSync(new URL('./fixtures/floor_spawn_markers.json', import.meta.url),'utf8'));
test('27 original maps match independent marker extraction', () => {
  assert.equal(Object.keys(data.floors).length,27);
  assert.equal(data.source.actionscript_sha256,markers.map_script_sha256);
  for (const [floor,matrix] of Object.entries(data.floors)) {
    assert.equal(matrix.length,11);
    for (const row of matrix) assert.equal(row.length,11);
    for (const tile of ['97','98','99']) {
      const actual = [];
      for (let r=0;r<11;r++) for(let c=0;c<11;c++) if(matrix[r][c]===Number(tile)) actual.push([r,c]);
      assert.deepEqual(actual,markers.floors[floor][tile]);
    }
    if (floor !== '00') {
      const plan = planJumpFloorTiles(matrix);
      assert.equal(plan.hero.row,markers.floors[floor]['97'][0][0]);
      assert.equal(plan.key_unlock,false);
    }
  }
});
test('special sprite mapping and depth',()=>{
  const m = Array.from({length:11},()=>Array(11).fill(0));
  m[0]=[97,98,1,15,115,120,119,129,24,179,99];
  const p=planJumpFloorTiles(m);
  assert.deepEqual(p.placements.map(x=>x.source),['mt_99','mt_01','mt_15','mt_15','mt_20','mt_00','mt_00','mt_24','mt_00','mt_99']);
  assert.equal(p.placements[0].depth,1000);
  assert.equal(p.placements[1].depth,514);
  assert.equal(p.placements[7].instance,'mt_sister');
  assert.equal(p.placements[2].stop_frame,1);
  assert.deepEqual(p.suppressed_98,[{row:0,col:1}]);
});
test('incomplete and ambiguous maps rejected',()=>{
  assert.throws(()=>planJumpFloorTiles([]));
  assert.throws(()=>planJumpFloorTiles(Array.from({length:11},()=>Array(11).fill(0))));
  assert.throws(()=>planJumpFloorTiles(Array.from({length:11},()=>Array(11).fill(97))));
});
