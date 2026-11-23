/** Defensive numeric-domain checks for the source-scoped HTML5 shop probe.
 * These are not original Flash runtime parity or UI integration tests.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {stepShop} from '../web/shop_transition_probe.mjs';

const MAX = Number.MAX_SAFE_INTEGER;
const base = () => ({gold: 100, hp: 10, attack: 3, defense: 2,
  yellow_key: 0, blue_key: 0, red_key: 0});

test('reject unsafe numeric input without mutating source state', () => {
  const badValues = [-1, 1.5, NaN, Infinity, MAX + 1, '100', null, true];
  for (const field of Object.keys(base())) {
    for (const value of badValues) {
      const before = {...base(), [field]: value};
      const snapshot = {...before};
      assert.throws(() => stepShop(before, 2, 1), /nonnegative safe integer/,
        `${field}=${String(value)}`);
      assert.deepEqual(before, snapshot);
    }
  }
  for (const [frame, option] of [[2.5,1],[2,0],[2,5],[3,1],[2,'1'],[true,1]]) {
    const before = base();
    assert.throws(() => stepShop(before, frame, option), /unsupported source-backed/);
    assert.deepEqual(before, base());
  }
});

test('successful purchase at safe-integer limit and overflow rejection', () => {
  for (const [frame, option, field, delta, cost] of [
    [2,1,'hp',800,25], [2,2,'attack',4,25], [2,3,'defense',4,25],
    [4,1,'yellow_key',1,10], [4,2,'blue_key',1,50], [4,3,'red_key',1,100],
  ]) {
    const allowed = {...base(), gold: cost, [field]: MAX - delta};
    const success = stepShop(allowed, frame, option);
    assert.equal(success.state[field], MAX);
    assert.equal(success.state.gold, 0);
    assert.equal(allowed[field], MAX - delta);
    const overflow = {...base(), gold: cost, [field]: MAX - delta + 1};
    const snapshot = {...overflow};
    assert.throws(() => stepShop(overflow, frame, option), /shop stat overflow/);
    assert.deepEqual(overflow, snapshot);
    const insufficient = {...overflow, gold: cost - 1};
    const result = stepShop(insufficient, frame, option);
    assert.equal(result.success, false);
    assert.deepEqual(result.state, insufficient);
  }
});
