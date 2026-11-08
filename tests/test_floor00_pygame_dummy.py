"""Exercise the actual Pygame floor-00 drawing loop with SDL's dummy driver."""
import os
import unittest
from unittest.mock import patch


class Floor00PygameDummyTests(unittest.TestCase):
    def test_draw_first_frame_and_quit(self):
        # CI must install pygame; missing dependency is a failure, not a skip.
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools.floor00_pygame_probe import main

            # Render one frame, then consume QUIT on the next iteration.
            from tools.floor00_pygame_probe import replay
            spawn = replay([])["final_state"]
            hero_pixel = (spawn["col"] * 42 + 21, spawn["row"] * 42 + 21)
            captured = []
            original_flip = pygame.display.flip

            def inspect_frame():
                # Check real framebuffer pixels before pygame.quit().
                surface = pygame.display.get_surface()
                self.assertIsNotNone(surface)
                self.assertEqual(surface.get_size(), (462, 550))
                captured.append(tuple(surface.get_at(hero_pixel)[:3]))
                original_flip()

            with (
                patch.object(pygame.event, "get", side_effect=[[], [pygame.event.Event(pygame.QUIT)]]),
                patch.object(pygame.display, "flip", side_effect=inspect_frame) as flip,
            ):
                try:
                    main()
                    self.assertEqual(flip.call_count, 1)
                    self.assertEqual(captured, [(255, 220, 75)])
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


    def test_immediate_quit_does_not_render_extra_frame(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools.floor00_pygame_probe import main
            with (
                patch.object(pygame.event, "get", return_value=[pygame.event.Event(pygame.QUIT)]),
                patch.object(pygame.display, "flip") as flip,
            ):
                try:
                    main()
                    self.assertEqual(flip.call_count, 0)
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


if __name__ == "__main__":
    unittest.main()
