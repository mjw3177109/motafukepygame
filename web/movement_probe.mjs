/** Verified subset of original Move_arrow; no game/UI completeness claim. */
export const DELTAS = Object.freeze({1: [0,-1], 2: [0,1], 3: [-1,0], 4: [1,0]});
const keyPickups = {6:'yellow',7:'blue',8:'red'};
const keyDoors = {2:'yellow',3:'blue',4:'red'};
const statPickups = {9:['defense',3],10:['attack',3],11:['hp',200],12:['hp',500]};

export function stepMoveArrow(snapshot, arrowId) {
  if (!Number.isInteger(arrowId) || !Object.hasOwn(DELTAS, arrowId)) {
    throw new Error('arrow_id must be one of Flash 1,2,3,4');
  }
  const state = structuredClone(snapshot);
  const grid = state.grid;
  if (!Array.isArray(grid) || grid.length !== 11 || grid.some(row => !Array.isArray(row) || row.length !== 11)) {
    throw new Error('expected 11x11 original floor');
  }
  const {row, col} = state;
  if (!Number.isInteger(row) || !Number.isInteger(col) || row < 0 || row > 10 || col < 0 || col > 10) {
    throw new Error('invalid original row/column');
  }
  const [dr,dc] = DELTAS[arrowId];
  const nr = row+dr, nc = col+dc;
  if (nr < 0 || nr > 10 || nc < 0 || nc > 10) return {state,event:'boundary'};
  const tile = grid[nr][nc];
  if (!Number.isInteger(tile)) throw new Error('tile must be an integer');
  if ([0,97,98,99].includes(tile)) {
    // Flash Move_arrow erases the previous cell only if it was 0 or 99.
    if (grid[row][col] === 0 || grid[row][col] === 99) grid[row][col]=0;
    state.row=nr; state.col=nc;
    return {state,event:'move'};
  }
  if (tile === 1) return {state,event:'wall'};
  if (Object.hasOwn(keyPickups,tile)) {
    const key=keyPickups[tile];
    state.keys[key]++; grid[nr][nc]=0;
    return {state,event:'pickup_'+key+'_key'};
  }
  if (Object.hasOwn(keyDoors,tile)) {
    const key=keyDoors[tile];
    if (state.keys[key] <= 0) return {state,event:'locked_'+key+'_door'};
    state.keys[key]--; grid[nr][nc]=0;
    return {state,event:'open_'+key+'_door'};
  }
  if (Object.hasOwn(statPickups,tile)) {
    const [stat,amount]=statPickups[tile];
    state[stat]+=amount; grid[nr][nc]=0;
    return {state,event:'pickup_'+stat+'_'+amount};
  }
  throw new Error('tile '+tile+' needs original event/animation verification');
}
