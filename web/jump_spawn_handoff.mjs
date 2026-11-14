/** Marker-only preflight; never redraws floors or unlocks the keyboard. */
import {planJumpFloorSpawn} from './floor_spawn_probe.mjs';

export function planJumpSpawnHandoff(replay, markersByFloor) {
  if (!replay || replay.floor_refresh_pending !== true)
    throw new Error('pending SetLineDisplay(1) required');
  const {trace, state} = replay;
  if (!Array.isArray(trace) || !trace.length ||
      trace.at(-1)?.event !== 'jump_confirm_cleanup' ||
      !Array.isArray(trace.at(-1)?.effects) ||
      !trace.at(-1).effects.includes('set_line_display:1') ||
      !state || state.key_flag !== 0 || state.display_jump !== 0)
    throw new Error('confirmed jump cleanup and locked keyboard required');
  const floor = state.now_line;
  if (!Number.isSafeInteger(floor) || floor < 1 || floor > 26)
    throw new Error('target floor outside evidenced 01..26 jump markers');
  if (!markersByFloor || typeof markersByFloor !== 'object' || Array.isArray(markersByFloor))
    throw new Error('original marker fixture required');
  const markers = markersByFloor[String(floor).padStart(2, '0')];
  if (!markers || typeof markers !== 'object' || Array.isArray(markers) ||
      Object.keys(markers).sort().join(',') !== '97,98,99')
    throw new Error('original 97/98/99 markers required');
  const matrix = Array.from({length: 11}, () => Array(11).fill(0));
  const occupied = new Set();
  for (const tile of ['97', '98', '99']) {
    if (!Array.isArray(markers[tile])) throw new Error('marker positions must be lists');
    for (const pos of markers[tile]) {
      if (!Array.isArray(pos) || pos.length !== 2 ||
          pos.some(v => !Number.isSafeInteger(v) || v < 0 || v >= 11))
        throw new Error('marker coordinates outside original 11x11 grid');
      const [row, col] = pos, key = row + ':' + col;
      if (occupied.has(key)) throw new Error('overlapping original marker coordinates');
      occupied.add(key);
      matrix[row][col] = Number(tile);
    }
  }
  return {target_floor: floor, spawn: planJumpFloorSpawn(matrix),
    floor_refresh_pending: true, render_status: 'blocked_full_map_missing', key_flag: 0};
}
