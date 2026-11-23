"""Regression for the Pygame diagnostic's pure replay/commit boundary."""
import unittest

from tools.floor00_pygame_probe import attempt, replay


class Floor00PygameProbeTests(unittest.TestCase):
    def test_zero_step_replay_uses_original_spawn(self):
        trace = replay([])
        self.assertEqual(trace["frames"], [])
        self.assertEqual(trace["initial_state"], trace["final_state"])

    def test_rejected_direction_does_not_commit_or_change_state(self):
        accepted, trace, error = attempt([], 0)
        self.assertEqual(accepted, [])
        self.assertIsNotNone(error)
        self.assertEqual(trace, replay([]))

    def test_repeated_rejection_does_not_mutate_prior_trace(self):
        original = replay([])
        for _ in range(2):
            accepted, trace, error = attempt([], 0)
            self.assertEqual(accepted, [])
            self.assertIsNotNone(error)
            self.assertEqual(trace, original)
        self.assertEqual(replay([]), original)


if __name__ == "__main__":
    unittest.main()
