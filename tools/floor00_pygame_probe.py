"""Source-pinned floor-00 Pygame diagnostic viewer (NOT Flash 1:1 parity).

Install pygame separately: python -m pip install pygame
Run from repo root: python -m tools.floor00_pygame_probe
Arrow keys replay the verified movement subset from the original spawn.
Unknown original events are rejected; no fake battle/stairs/ending.
"""
import json

from tools.floor00_trace_cli import run

ARROWS = {"left": 1, "right": 2, "up": 3, "down": 4}
EMPTY_KEYS = {"yellow": 0, "blue": 0, "red": 0}


def replay(arrow_ids):
    """Replay from source-pinned spawn; never accept partial invalid traces."""
    return json.loads(run({"keys": dict(EMPTY_KEYS), "arrow_ids": list(arrow_ids)}))


def attempt(accepted, arrow_id):
    """Return (accepted directions, trace, rejection); failed moves do not commit."""
    candidate = [*accepted, arrow_id]
    try:
        return candidate, replay(candidate), None
    except ValueError as exc:
        return list(accepted), replay(accepted), str(exc)


def main():
    try:
        import pygame
    except ImportError as exc:
        raise SystemExit("pygame is required: python -m pip install pygame") from exc
    pygame.init()
    tile_px = 42
    screen = pygame.display.set_mode((11 * tile_px, 11 * tile_px + 88))
    pygame.display.set_caption("Mota 1.12 - floor 00 diagnostic, NOT Flash parity")
    font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    accepted = []
    trace = replay(accepted)
    status = "Arrows: move | R: reset | Esc: quit"
    bindings = {pygame.K_LEFT: 1, pygame.K_RIGHT: 2,
                pygame.K_UP: 3, pygame.K_DOWN: 4}
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    accepted, trace = [], replay([])
                    status = "Reset to source-pinned spawn"
                elif event.key in bindings:
                    accepted, trace, error = attempt(accepted, bindings[event.key])
                    status = ("REJECTED: " + error) if error else (
                        "Event: " + trace["frames"][-1]["event"])
        if not running:
            break
        state = trace["final_state"]
        screen.fill((22, 24, 30))
        for row, line in enumerate(state["grid"]):
            for col, tile in enumerate(line):
                rect = pygame.Rect(col * tile_px, row * tile_px, tile_px, tile_px)
                shade = (48, 51, 60) if tile == 1 else (87, 91, 104)
                pygame.draw.rect(screen, shade, rect)
                pygame.draw.rect(screen, (30, 33, 40), rect, 1)
                if tile:
                    glyph = font.render(str(tile), True, (235, 235, 235))
                    screen.blit(glyph, glyph.get_rect(center=rect.center))
        hero = pygame.Rect(state["col"] * tile_px + 9,
                           state["row"] * tile_px + 9, tile_px - 18, tile_px - 18)
        pygame.draw.rect(screen, (255, 220, 75), hero)
        for i, line in enumerate((status[:72],
                                  "Keys: " + str(state["keys"]) + " | steps: " + str(len(accepted)),
                                  "DIAGNOSTIC ONLY - unverified events fail closed")):
            screen.blit(font.render(line, True, (240, 240, 240)),
                        (8, 11 * tile_px + 5 + i * 25))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
