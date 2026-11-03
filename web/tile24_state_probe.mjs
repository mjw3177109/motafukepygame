/** Review-only tile-24 branch-local probe. NOT a playable HTML5 event handler.
 * Unlike Python's source-gated tracer, this module does not parse ActionScript.
 * Shared fixtures detect cross-language drift, never Flash parity.
 */
const REQUIRED = [
  'tile_id', 'display_say0', 'mt_changes', 'my_love', 'now_line',
  'get_money', 'now_key_flag', 'last_game_id', 'floor20_7_5',
];
const binary = value => Number.isSafeInteger(value) && (value === 0 || value === 1);

export function traceTile24State(input) {
  if (input === null || typeof input !== 'object' || Array.isArray(input) ||
      (Object.getPrototypeOf(input) !== Object.prototype && Object.getPrototypeOf(input) !== null) ||
      Object.keys(input).length !== REQUIRED.length ||
      REQUIRED.some(key => !Object.hasOwn(input, key))) {
    throw new Error('exact tile-24 review state fields required');
  }
  // Reject accessor fields before reading values or structuredClone: getters can run code.
  if (REQUIRED.some(key => !Object.hasOwn(Object.getOwnPropertyDescriptor(input, key), 'value'))) {
    throw new Error('tile-24 review state requires data properties');
  }
  for (const key of ['display_say0','mt_changes','my_love','now_key_flag','last_game_id']) {
    if (!binary(input[key])) throw new Error('binary state flags required');
  }
  if (!Number.isSafeInteger(input.tile_id) || input.tile_id < 0 ||
      !Number.isSafeInteger(input.now_line) || input.now_line < 0 || input.now_line > 26 ||
      !Number.isSafeInteger(input.floor20_7_5)) {
    throw new Error('invalid tile, floor or map cell');
  }
  if (!Array.isArray(input.get_money) || Object.getPrototypeOf(input.get_money) !== Array.prototype ||
      input.get_money.length !== 3 || Object.keys(input.get_money).length !== 3 ||
      ![0, 1, 2].every(index => Object.hasOwn(input.get_money, index) && binary(input.get_money[index]))) {
    throw new Error('exactly three binary item flags required');
  }
  if (![0, 1, 2].every(index => Object.hasOwn(Object.getOwnPropertyDescriptor(input.get_money, String(index)), 'value'))) {
    throw new Error('tile-24 item flags require data properties');
  }
  const state = structuredClone(input), trace = [];
  if (state.tile_id === 24) {
    if (state.display_say0 === 0) {
      state.display_say0 = 1;
      trace.push({branch:'initial_dialogue',clip_command:'CopyMovie(mt_say_01)'});
    }
    if (state.mt_changes === 1 && state.my_love === 0) {
      state.mt_changes = 0;
      state.last_game_id = 1;
      trace.push({branch:'ending_state_change',dialogue_command:'say_three'});
    }
    if (state.my_love === 1) {
      const dialogue = state.get_money[0] === 1 ? 'say_four' : 'say_two';
      state.floor20_7_5 = 13;
      state.my_love = 0;
      state.mt_changes = 0;
      trace.push({branch:'love_dialogue',dialogue_command:dialogue});
    }
    if (state.now_line === 22) {
      state.now_key_flag = 0;
      state.display_say0 = 1;
      const dialogue = state.get_money.every(v => v === 1) ? 'say_six' : 'say_five';
      trace.push({branch:'floor22_dialogue',clip_command:'CopyMovie(mt_say_01)',dialogue_command:dialogue});
    }
  }
  return {
    state, trace,
    source_branch_order_verified: false, // JS does not independently audit ActionScript
    branch_local_hypothesis_only: true,
    flash_runtime_verified: false,
    dual_client_parity_verified: false,
    gymnasium_ready: false,
  };
}
