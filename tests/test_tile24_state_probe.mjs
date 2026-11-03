import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {traceTile24State} from '../web/tile24_state_probe.mjs';

const cases = JSON.parse(readFileSync(new URL('./fixtures/tile24_state_cases.json', import.meta.url), 'utf8'));
for (const c of cases) {
  test('tile24 synthetic shared case: ' + c.name, () => {
    const original = structuredClone(c.input);
    const result = traceTile24State(c.input);
    assert.deepEqual(c.input, original, 'input mutated');
    assert.deepEqual(result.trace.map(x => x.branch), c.branches);
    assert.deepEqual(result.trace.filter(x => x.dialogue_command).map(x => x.dialogue_command), c.dialogues);
    assert.deepEqual(result.trace.filter(x => x.clip_command).map(x => ({branch: x.branch, clip_command: x.clip_command})), c.clip_commands, 'clip command branch/order mismatch');
    assert.deepEqual(result.state, {...c.input, ...c.changed});
    assert.equal(result.flash_runtime_verified, false);
    assert.equal(result.dual_client_parity_verified, false);
    assert.equal(result.gymnasium_ready, false);
    assert.equal(result.source_branch_order_verified, false);
  });
}
test('safe integer boundary matches Python review contract', () => {
  const max = Number.MAX_SAFE_INTEGER;
  assert.equal(traceTile24State({...cases[1].input, tile_id:max}).state.tile_id, max);
  assert.equal(traceTile24State({...cases[1].input, floor20_7_5:-max}).state.floor20_7_5, -max);
});
test('reject unsafe integers without input mutation', () => {
  const unsafe = Number.MAX_SAFE_INTEGER + 1;
  for (const changed of [
    {...cases[1].input, tile_id:unsafe},
    {...cases[1].input, floor20_7_5:unsafe},
    {...cases[1].input, floor20_7_5:-unsafe},
  ]) {
    const before = structuredClone(changed);
    assert.throws(() => traceTile24State(changed));
    assert.deepEqual(changed, before);
  }
});
test('reject malformed and coerced state without mutation', () => {
  const input = cases[1].input;
  for (const bad of [null, [], {...input, my_love:true}, {...input, get_money:[1,1]},
    {...input, now_line:27}, {...input, tile_id:'24'}, {...input, extra:0}]) {
    assert.throws(() => traceTile24State(bad));
  }
});

test('reject sparse three-item list before floor22 dialogue', () => {
  const base = cases.find(c => c.name === 'floor22_all_items').input;
  for (const items of [[1, , 1], Array(3)]) {
    const input = {...base, get_money: items};
    assert.throws(() => traceTile24State(input), /exactly three binary item flags required/);
    assert.equal(Object.hasOwn(items, 1), false, 'validation mutated sparse input');
  }
});
test('reject inherited item slot rather than accepting prototype values', () => {
  const base = cases.find(c => c.name === 'floor22_all_items').input;
  const items = [1, , 1], proto = Object.create(Array.prototype);
  proto[1] = 1;
  Object.setPrototypeOf(items, proto);
  assert.throws(() => traceTile24State({...base, get_money: items}), /exactly three binary item flags required/);
  assert.equal(Object.hasOwn(items, 1), false, 'validation filled inherited slot');
});

test('reject Date and class instances masquerading as review-state records', () => {
  const base = cases[1].input;
  const date = Object.assign(new Date('2020-01-01T00:00:00Z'), base);
  class ReviewRecord { constructor() { Object.assign(this, base); } }
  for (const invalid of [date, new ReviewRecord()]) {
    assert.equal(Object.keys(invalid).length, Object.keys(base).length);
    assert.throws(() => traceTile24State(invalid), /exact tile-24 review state fields required/);
    assert.equal(invalid.tile_id, base.tile_id, 'validation mutated input');
  }
});

test('reject noncanonical item arrays before structured cloning', () => {
  const base = cases.find(c => c.name === 'floor22_all_items').input;
  const subclass = class ItemFlags extends Array {};
  const subclassItems = new subclass(1, 1, 1);
  const extraItems = [1, 1, 1];
  extraItems.note = 'unverified';
  for (const items of [subclassItems, extraItems]) {
    const input = {...base, get_money: items};
    assert.throws(() => traceTile24State(input), /exactly three binary item flags required/);
    assert.equal(input.get_money, items, 'validation replaced input array');
    assert.deepEqual(Array.from(items), [1, 1, 1]);
  }
});

test('reject accessor-backed review fields and item slots without invoking getters', () => {
  const base = cases.find(c => c.name === 'floor22_all_items').input;
  let calls = 0;
  const accessorState = {...base};
  Object.defineProperty(accessorState, 'my_love', {
    enumerable: true, configurable: true, get() { calls++; return 1; },
  });
  assert.throws(() => traceTile24State(accessorState), /data properties/);
  const accessorItems = [1, 1, 1];
  Object.defineProperty(accessorItems, '1', {
    enumerable: true, configurable: true, get() { calls++; return 1; },
  });
  assert.throws(() => traceTile24State({...base, get_money: accessorItems}), /data properties/);
  assert.equal(calls, 0, 'validation invoked an untrusted getter');
});

test('reject hidden and symbol properties before state cloning', () => {
  const base = cases.find(c => c.name === 'floor22_all_items').input;
  const hidden = {...base};
  Object.defineProperty(hidden, 'hidden', {value: 1, enumerable: false});
  const symbolic = {...base, [Symbol('unverified')]: 1};
  const hiddenItems = [1, 1, 1];
  Object.defineProperty(hiddenItems, 'hidden', {value: 1, enumerable: false});
  const symbolicItems = [1, 1, 1];
  symbolicItems[Symbol('unverified')] = 1;
  for (const invalid of [hidden, symbolic, {...base, get_money: hiddenItems}, {...base, get_money: symbolicItems}]) {
    assert.throws(() => traceTile24State(invalid), /exact|three binary/);
  }
});
