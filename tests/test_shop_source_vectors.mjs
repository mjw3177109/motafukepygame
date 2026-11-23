import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stepShop} from '../web/shop_transition_probe.mjs';

const fixture = JSON.parse(readFileSync(new URL('../data/original_shop_transactions_static.json', import.meta.url), 'utf8'));
const initial = () => ({gold:100,hp:10,attack:3,defense:2,yellow_key:0,blue_key:0,red_key:0});

test('all 20 shop boundary vectors derive from source-scoped fixture', () => {
  assert.equal(fixture.verification, 'static_actionscript_only_not_runtime_parity');
  assert.equal(fixture.transactions.length, 6);
  assert.equal(fixture.exit.length, 2);
  let checked = 0;
  for (const tx of fixture.transactions) {
    const changes = Object.entries(tx.delta);
    assert.equal(changes.length, 1);
    const [field, increment] = changes[0];
    for (const gold of [tx.cost - 1, tx.cost, tx.cost + 1]) {
      const before = {...initial(), gold};
      const snapshot = structuredClone(before);
      const result = stepShop(before, tx.frame, tx.option);
      const affordable = gold >= tx.cost;
      const expected = {...before};
      if (affordable) {expected.gold -= tx.cost; expected[field] += increment;}
      assert.deepEqual(result.state, expected, `frame=${tx.frame} option=${tx.option} gold=${gold}`);
      assert.equal(result.success, affordable);
      assert.equal(result.event, affordable ? 'shop_purchase' : 'shop_insufficient_gold');
      assert.equal(result.provenance, 'static_actionscript_expectation_not_runtime');
      assert.deepEqual(before, snapshot);
      checked++;
    }
  }
  for (const exit of fixture.exit) {
    const before = {...initial(),gold:0};
    const result = stepShop(before, exit.frame, exit.option);
    assert.equal(result.event, 'shop_exit');
    assert.equal(result.exit_action, exit.action);
    assert.equal(result.exit_label, exit.label);
    assert.deepEqual(result.state, before);
    checked++;
  }
  assert.equal(checked, 20);
});
