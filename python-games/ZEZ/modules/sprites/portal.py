import pygame
import math
from consts import SCREEN_WIDTH, GROUND_Y


class ExitPortal(pygame.sprite.Sprite):
    """Glowing exit portal that scrolls in after a boss is defeated.

    Success is triggered externally when the portal's centre-x passes the
    player's centre-x — no Y-axis dependency, so jumping cannot miss it.
    """
    W = 60
    H = 130

    def __init__(self, speed: int):
        super().__init__()
        self.speed = speed
        self._tick = 0
        self.image = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(x=SCREEN_WIDTH + 120, bottom=GROUND_Y)
        self._render()

    def update(self):
        self.rect.x -= self.speed
        self._tick   += 1
        self._render()
        if self.rect.right < 0:
            self.kill()

    # ── visual ────────────────────────────────────────────────────────────────
    def _render(self):
        p  = 0.5 + 0.5 * math.sin(self._tick * 0.15)
        p2 = 0.5 + 0.5 * math.sin(self._tick * 0.25 + 1.0)
        self.image.fill((0, 0, 0, 0))

        # outer glow
        pygame.draw.rect(
            self.image, (0, 255, 150, int(70 + 60 * p)),
            (0, 0, self.W, self.H), border_radius=10,
        )
        # mid fill
        pygame.draw.rect(
            self.image, (20, 190, 110, int(160 + 80 * p)),
            (5, 7, self.W - 10, self.H - 14), border_radius=8,
        )
        # bright inner core
        pygame.draw.rect(
            self.image, (180, 255, 215, 240),
            (12, 18, self.W - 24, self.H - 36), border_radius=6,
        )
        # three pulsing energy lines
        for i, xo in enumerate((18, 30, 42)):
            la = int(200 + 55 * math.sin(self._tick * 0.2 + i * 1.2))
            pygame.draw.line(
                self.image, (255, 255, 255, la),
                (xo, 22), (xo, self.H - 38), 2,
            )
        # arrow chevrons pointing left (→ player direction)
        cy = self.H // 2
        for dy in (-16, 0, 16):
            pygame.draw.line(
                self.image, (255, 255, 180, int(200 + 55 * p2)),
                (self.W - 8,  cy + dy - 6),
                (self.W - 18, cy + dy),     3,
            )
            pygame.draw.line(
                self.image, (255, 255, 180, int(200 + 55 * p2)),
                (self.W - 8,  cy + dy + 6),
                (self.W - 18, cy + dy),     3,
            )
