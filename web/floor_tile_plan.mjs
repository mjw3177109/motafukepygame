// Static FFDec SetLineDisplay(1) placement plan, NOT actual Canvas redraw.
export function planJumpFloorTiles(matrix) {
  if (!Array.isArray(matrix) || matrix.length !== 11 ||
      matrix.some(row => !Array.isArray(row) || row.length !== 11 ||
        row.some(tile => !Number.isSafeInteger(tile) || tile < 0))) {
    throw new Error('full original floor must be an 11x11 nonnegative integer matrix');
  }
  const spawns = [];
  for (let r = 0; r < 11; r++) for (let c = 0; c < 11; c++) {
    if (matrix[r][c] === 97) spawns.push([r, c]);
  }
  if (spawns.length !== 1) throw new Error('SetLineDisplay(1) requires exactly one original tile 97');
  const placements = [], suppressed_98 = [];
  for (let r = 0; r < 11; r++) for (let c = 0; c < 11; c++) {
    const tile = matrix[r][c];
    if (tile === 0) continue;
    if (tile === 98) { suppressed_98.push({row:r,col:c}); continue; }
    let source, instance, depth;
    if (tile === 97) {
      source = 'mt_99'; instance = 'mt_man'; depth = 1000;
    } else {
      source = tile < 10 ? `mt_0${tile}` : tile === 115 ? 'mt_15' :
        tile === 120 ? 'mt_20' : [119,129,139,149,159,169,179].includes(tile) ?
        'mt_00' : `mt_${tile}`;
      instance = source === 'mt_24' ? 'mt_sister' : `mt_m_${r}_${c}`;
      depth = 500 + (r + 1) * 11 + c + 1;
    }
    const p = {row:r,col:c,tile,source,instance,depth,x:207+32*c,y:47+32*r};
    if ([1,2,3,4,5,15,115].includes(tile)) p.stop_frame = 1;
    placements.push(p);
  }
  const [r,c] = spawns[0];
  return {hero:{row:r,col:c,x:207+32*c,y:47+32*r},placements,suppressed_98,
          floor_refresh_pending:true,key_unlock:false};
}
