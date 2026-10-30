import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {previewEncounter} from '../web/combat_probe.mjs';
const cases = JSON.parse(readFileSync(new URL('./fixtures/combat_probe_cases.json', import.meta.url),'utf8'));
for (const vector of cases) {
  test(vector.name, () => {
    const before = JSON.stringify(vector);
    assert.deepEqual(previewEncounter(vector.tile,vector.monster,vector.hero),vector.expected);
    assert.equal(JSON.stringify(vector),before);
  });
}
test('invalid tile rejected',()=>assert.throws(()=>previewEncounter(71,cases[0].monster,cases[0].hero)));
test('invalid monster rejected',()=>assert.throws(()=>previewEncounter(40,[50,20],cases[0].hero)));
