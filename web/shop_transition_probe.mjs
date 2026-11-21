/** Static ActionScript shop transitions. Not Flash runtime parity or UI integration. */
const MAX = Number.MAX_SAFE_INTEGER;
const RULES = new Map([
  ['2:1', [25, 'hp', 800]], ['2:2', [25, 'attack', 4]],
  ['2:3', [25, 'defense', 4]], ['4:1', [10, 'yellow_key', 1]],
  ['4:2', [50, 'blue_key', 1]], ['4:3', [100, 'red_key', 1]],
]);
const FIELDS = ['gold','hp','attack','defense','yellow_key','blue_key','red_key'];
const EXITS = {2:'gotoAndPlay',4:'gotoAndStop'};

export function stepShop(state, frame, option) {
  if (!Number.isSafeInteger(frame) || !Number.isSafeInteger(option) ||
      !Object.hasOwn(EXITS, frame) || option < 1 || option > 4)
    throw new Error('unsupported source-backed shop frame/option');
  if (!state || typeof state !== 'object' || Array.isArray(state) ||
      FIELDS.some(k => !Object.hasOwn(state,k) || !Number.isSafeInteger(state[k]) || state[k] < 0))
    throw new Error('shop requires nonnegative safe integer state fields');
  const after = structuredClone(state);
  const provenance = 'static_actionscript_expectation_not_runtime';
  if (option === 4)
    return {state:after, success:true, event:'shop_exit', sound:'music_07', exit_action:EXITS[frame],
      exit_label:'end', provenance};
  const [cost,field,delta] = RULES.get(frame + ':' + option);
  if (after.gold < cost)
    return {state:after, success:false, event:'shop_insufficient_gold', sound:'music_09', provenance};
  if (after[field] > MAX - delta) throw new Error('shop stat overflow');
  after.gold -= cost;
  after[field] += delta;
  return {state:after, success:true, event:'shop_purchase', sound:'music_11', provenance};
}
