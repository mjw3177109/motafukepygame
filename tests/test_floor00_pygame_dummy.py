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


    def test_escape_key_quits_without_rendering(self):
        # ESC must behave like window-close: no stale frame after exit.
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools.floor00_pygame_probe import main
            escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
            with (
                patch.object(pygame.event, "get", return_value=[escape]),
                patch.object(pygame.display, "flip") as flip,
            ):
                try:
                    main()
                    flip.assert_not_called()
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


    def test_quit_ignores_later_queued_reset_and_move(self):
        # A batch of events may contain input after QUIT; none may mutate state.
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools import floor00_pygame_probe as probe

            queued = [
                pygame.event.Event(pygame.QUIT),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT),
            ]
            with (
                patch.object(pygame.event, "get", return_value=queued),
                patch.object(pygame.display, "flip") as flip,
                patch.object(probe, "attempt", side_effect=AssertionError("input after quit")) as attempt,
                patch.object(probe, "replay", wraps=probe.replay) as replay,
            ):
                try:
                    probe.main()
                    flip.assert_not_called()
                    attempt.assert_not_called()
                    self.assertEqual(replay.call_count, 1)  # initial spawn only
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


    def test_reset_key_renders_source_spawn(self):
        # Reset must discard an earlier accepted move and render the original spawn.
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools.floor00_pygame_probe import main, replay

            spawn = replay([])["final_state"]
            hero_pixel = (spawn["col"] * 42 + 21, spawn["row"] * 42 + 21)
            pixels = []
            original_flip = pygame.display.flip

            def inspect_frame():
                surface = pygame.display.get_surface()
                pixels.append(tuple(surface.get_at(hero_pixel)[:3]))
                original_flip()

            reset = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
            quit_event = pygame.event.Event(pygame.QUIT)
            with (
                patch.object(pygame.event, "get", side_effect=[[reset], [quit_event]]),
                patch.object(pygame.display, "flip", side_effect=inspect_frame) as flip,
            ):
                try:
                    main()
                    self.assertEqual(flip.call_count, 1)
                    self.assertEqual(pixels, [(255, 220, 75)])
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


    def test_reset_after_real_move_restores_spawn_frame(self):
        # Unlike reset-at-spawn, this verifies that a committed movement is undone.
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            import pygame
            from tools.floor00_pygame_probe import main, replay, attempt

            spawn = replay([])["final_state"]
            valid = []
            for direction in (1, 2, 3, 4):
                accepted, moved, error = attempt([], direction)
                if error is None and (moved["final_state"]["row"], moved["final_state"]["col"]) != (spawn["row"], spawn["col"]):
                    valid.append((direction, moved["final_state"]))
            self.assertTrue(valid, "No source-verified adjacent move from floor-00 spawn")
            direction, moved_state = valid[0]
            keys = {1: pygame.K_LEFT, 2: pygame.K_RIGHT, 3: pygame.K_UP, 4: pygame.K_DOWN}
            spawn_pixel = (spawn["col"] * 42 + 21, spawn["row"] * 42 + 21)
            moved_pixel = (moved_state["col"] * 42 + 21, moved_state["row"] * 42 + 21)
            captured = []
            original_flip = pygame.display.flip

            def inspect_frame():
                surface = pygame.display.get_surface()
                captured.append((
                    tuple(surface.get_at(spawn_pixel)[:3]),
                    tuple(surface.get_at(moved_pixel)[:3]),
                ))
                original_flip()

            move = pygame.event.Event(pygame.KEYDOWN, key=keys[direction])
            reset = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
            quit_event = pygame.event.Event(pygame.QUIT)
            with (
                patch.object(pygame.event, "get", side_effect=[[move], [reset], [quit_event]]),
                patch.object(pygame.display, "flip", side_effect=inspect_frame) as flip,
            ):
                try:
                    main()
                    self.assertEqual(flip.call_count, 2)
                    self.assertEqual(captured[0][1], (255, 220, 75))
                    self.assertNotEqual(captured[0][0], (255, 220, 75))
                    self.assertEqual(captured[1][0], (255, 220, 75))
                    self.assertNotEqual(captured[1][1], (255, 220, 75))
                finally:
                    pygame.quit()
            self.assertFalse(pygame.get_init())


if __name__ == "__main__":
    unittest.main()
