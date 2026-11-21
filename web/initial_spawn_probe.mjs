/** FFDec game.swf frame_4346/DoAction_2.as (SHA-256 0de19a03...):
 * SetLineDisplay(0), arrow_id=0 uses tile 99 and suppresses tile 98.
 * Static placement only; does not claim Flash runtime/event parity.
 */
export function planInitialFloorSpawn(matrix) {
  if (!Array.isArray(matrix) || matrix.length !== 11 ||
      Array.from({length: 11}, (_, r) => r).some(r => {
        if (!Object.hasOwn(matrix, r)) return true;
        const row = matrix[r];
        return !Array.isArray(row) || row.length !== 11 ||
          Array.from({length: 11}, (_, c) => c).some(c =>
            !Object.hasOwn(row, c) || !Number.isSafeInteger(row[c]));
      })) {
    throw new Error('original floor must be an 11x11 safe-integer matrix');
  }
  const starts = [], suppressed = [];
  for (let row = 0; row < 11; row++) {
    for (let col = 0; col < 11; col++) {
      if (matrix[row][col] === 99) starts.push([row, col]);
      if (matrix[row][col] === 98) suppressed.push({row, col});
    }
  }
  if (starts.length !== 1)
    throw new Error('initial redraw requires exactly one original tile 99');
  const [row, col] = starts[0];
  return {hero: {row, col, x: 207 + col * 32, y: 47 + row * 32,
    source: 'mt_99', instance: 'mt_man', depth: 1000}, suppressed_98: suppressed};
}
