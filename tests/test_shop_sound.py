"""Static ActionScript sound cue regression; not runtime audio verification."""
import unittest
from core.shop_transition_probe import step_shop


class ShopSoundTests(unittest.TestCase):
    def test_source_scoped_sound_cues(self):
        base = dict(gold=100, hp=10, attack=3, defense=2,
                    yellow_key=0, blue_key=0, red_key=0)
        for frame in (2, 4):
            for option in (1, 2, 3):
                with self.subTest(frame=frame, option=option):
                    self.assertEqual(step_shop(base, frame, option)["sound"], "music_11")
                    self.assertEqual(step_shop({**base, "gold": 0}, frame, option)["sound"], "music_09")
            self.assertEqual(step_shop({**base, "gold": 0}, frame, 4)["sound"], "music_07")


if __name__ == "__main__":
    unittest.main()
