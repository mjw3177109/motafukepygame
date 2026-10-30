"""Cross-language vectors use raw entries extracted from original_tables.json."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.encounter_pipeline_probe import resolve_encounter

CASES=json.loads((Path(__file__).parent/"fixtures"/"encounter_pipeline_cases.json").read_text(encoding="utf-8"))

def make_world(case):
    grid=[[0]*11 for _ in range(11)]
    grid[5][6]=case["tile"]
    return {"grid":grid,"row":5,"col":5,**case["hero"],"display_kill":0,
            "key_flag":1,"money":0,"mp":0}

class PipelineTests(unittest.TestCase):
    def test_original_monster_vectors(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                world=make_world(case)
                before=deepcopy(world)
                result=resolve_encounter(world,2,{str(case["tile"]-40):case["monster"]},case["rolls"])
                expected=case["expected"]
                self.assertEqual(result["events"][-1]["event"],expected["event"])
                for key in ("hp","money","mp","display_kill"):
                    self.assertEqual(result["state"][key],expected[key])
                self.assertEqual(len(result["steps"]),expected["actions"])
                self.assertEqual(sum(s["event"]=="monster_counterattack" for s in result["steps"]),expected["counterattacks"])
                self.assertEqual(result["cleared"],expected["cleared"])
                self.assertEqual(result["state"]["grid"][5][6],0 if expected["cleared"] else case["tile"])
                self.assertEqual(world,before)

    def test_fails_closed_on_missing_rolls_and_busy_state(self):
        case=CASES[0]
        world=make_world(case)
        with self.assertRaisesRegex(ValueError,"missing"):
            resolve_encounter(world,2,{"0":case["monster"]},[])
        with self.assertRaisesRegex(ValueError,"idle"):
            resolve_encounter({**world,"display_kill":1},2,{"0":case["monster"]},[199])
        blocked=CASES[2]
        with self.assertRaisesRegex(ValueError,"blocked"):
            resolve_encounter(make_world(blocked),2,{"0":blocked["monster"]},[199])

if __name__=="__main__":
    unittest.main()
