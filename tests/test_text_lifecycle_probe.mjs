import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stepTextLifecycle} from '../web/text_lifecycle_probe.mjs';
const cases=JSON.parse(readFileSync(new URL('./fixtures/text_lifecycle_cases.json',import.meta.url),'utf8'));
for (const c of cases) test('text lifecycle '+c.name,()=>{
  const before=structuredClone(c.state);
  if (c.error) assert.throws(()=>stepTextLifecycle(c.state,c.phase),new RegExp(c.error));
  else {
    const result=stepTextLifecycle(c.state,c.phase);
    assert.equal(result.event,c.event);
    assert.deepEqual(result.effects,c.effects);
    for (const [key,value] of Object.entries(c.expected)) assert.deepEqual(result.state[key],value);
  }
  assert.deepEqual(c.state,before);
});
test('two-phase cleanup does not release boss lock',()=>{
  for (const boss of [0,1]) {
    const state={display_text:1,key_flag:0,boss_kills:boss,floor26_cell_3_5:188};
    const first=stepTextLifecycle(state,'frame32');
    const second=stepTextLifecycle(first.state,'cleanup');
    assert.equal(second.state.key_flag,boss===1?0:1);
    assert.equal(second.state.display_text,0);
    assert.equal(state.display_text,1);
  }
});
