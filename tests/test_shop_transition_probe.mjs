import test from 'node:test';
import assert from 'node:assert/strict';
import {stepShop} from '../web/shop_transition_probe.mjs';

const initial = () => ({gold:100,hp:10,attack:3,defense:2,yellow_key:0,blue_key:0,red_key:0});
const purchases = [
  [2,1,25,'hp',800],[2,2,25,'attack',4],[2,3,25,'defense',4],
  [4,1,10,'yellow_key',1],[4,2,50,'blue_key',1],[4,3,100,'red_key',1],
];
test('all six source-scoped shop purchases are immutable', () => {
  for (const [frame,option,cost,field,delta] of purchases) {
    const before = initial(), snapshot = structuredClone(before);
    const result = stepShop(before,frame,option);
    assert.deepEqual(before,snapshot);
    assert.equal(result.success,true);
    assert.equal(result.event,'shop_purchase');
    assert.equal(result.state.gold,100-cost);
    assert.equal(result.state[field],before[field]+delta);
    assert.equal(result.provenance,'static_actionscript_expectation_not_runtime');
  }
});
test('insufficient gold does not mutate state', () => {
  for (const [frame,option,cost] of purchases) {
    const before={...initial(),gold:cost-1};
    const result=stepShop(before,frame,option);
    assert.equal(result.success,false);
    assert.equal(result.event,'shop_insufficient_gold');
    assert.deepEqual(result.state,before);
  }
});
test('exit actions retain distinct frame semantics', () => {
  for (const [frame,action] of [[2,'gotoAndPlay'],[4,'gotoAndStop']]) {
    const result=stepShop(initial(),frame,4);
    assert.equal(result.exit_action,action);
    assert.equal(result.exit_label,'end');
    assert.deepEqual(result.state,initial());
  }
});
test('invalid values and overflow are rejected', () => {
  for (const [frame,option] of [[3,1],[2,0],[2,5],[true,1],[2,false]]) {
    assert.throws(()=>stepShop(initial(),frame,option));
  }
  for (const value of [-1,true,null,Number.MAX_SAFE_INTEGER+1]) {
    assert.throws(()=>stepShop({...initial(),gold:value},2,1));
  }
  const before={...initial(),hp:Number.MAX_SAFE_INTEGER};
  assert.throws(()=>stepShop(before,2,1),/overflow/);
  assert.equal(before.hp,Number.MAX_SAFE_INTEGER);
});
