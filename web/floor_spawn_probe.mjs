/** FFDec-evidenced SetLineDisplay(1) hero placement; NOT a floor renderer. */
export function planJumpFloorSpawn(matrix) {
  if (!Array.isArray(matrix) || matrix.length !== 11 ||
      matrix.some(row => !Array.isArray(row) || row.length !== 11 ||
        row.some(tile => !Number.isSafeInteger(tile))))
    throw new Error('original floor must be an 11x11 integer matrix');
  const starts = [], suppressed = [];
  for (let row = 0; row < 11; row++) {
    for (let col = 0; col < 11; col++) {
      if (matrix[row][col] === 97) starts.push([row, col]);
      if (matrix[row][col] === 98) suppressed.push({row, col});
    }
  }
  if (starts.length !== 1)
    throw new Error('jump redraw requires exactly one original tile 97');
  const [row, col] = starts[0];
  return {hero: {row, col, x: 207 + col * 32, y: 47 + row * 32,
    source: 'mt_99', instance: 'mt_man', depth: 1000}, suppressed_98: suppressed};
}
