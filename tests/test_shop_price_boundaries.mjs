/** Source-scoped price boundaries for HTML5; not Flash runtime or UI parity. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {stepShop} from '../web/shop_transition_probe.mjs';

const rules = [
  [2, 1, 25, 'hp', 800], [2, 2, 25, 'attack', 4],
  [2, 3, 25, 'defense', 4], [4, 1, 10, 'yellow_key', 1],
  [4, 2, 50, 'blue_key', 1], [4, 3, 100, 'red_key', 1],
];
const base = () => ({gold: 0, hp: 10, attack: 3, defense: 2,
  yellow_key: 0, blue_key: 0, red_key: 0});

test('six source-backed purchases at price minus one, exact price and plus one', () => {
  for (const [frame, option, cost, field, delta] of rules) {
    for (const gold of [cost - 1, cost, cost + 1]) {
      const before = {...base(), gold};
      const snapshot = structuredClone(before);
      const result = stepShop(before, frame, option);
      const expected = structuredClone(snapshot);
      const success = gold >= cost;
      if (success) {
        expected.gold -= cost;
        expected[field] += delta;
      }
      const label = `frame=${frame} option=${option} gold=${gold}`;
      assert.deepEqual(before, snapshot, `${label}: input mutated`);
      assert.deepEqual(result.state, expected, `${label}: state mismatch`);
      assert.equal(result.success, success, label);
      assert.equal(result.event, success ? 'shop_purchase' : 'shop_insufficient_gold', label);
      assert.equal(result.sound, success ? 'music_11' : 'music_09', label);
      assert.equal(result.provenance, 'static_actionscript_expectation_not_runtime', label);
    }
  }
});

test('zero-gold exit preserves state and distinct ActionScript jump', () => {
  for (const [frame, action] of [[2, 'gotoAndPlay'], [4, 'gotoAndStop']]) {
    const before = base();
    const result = stepShop(before, frame, 4);
    assert.deepEqual(before, base());
    assert.deepEqual(result.state, base());
    assert.equal(result.success, true);
    assert.equal(result.event, 'shop_exit');
    assert.equal(result.sound, 'music_07');
    assert.equal(result.exit_action, action);
    assert.equal(result.exit_label, 'end');
    assert.equal(result.provenance, 'static_actionscript_expectation_not_runtime');
  }
});
