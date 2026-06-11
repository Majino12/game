import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BOSS_INITIAL_HP


class Boss(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image   = pygame.transform.scale(image, (100, 100))
        self.rect    = self.image.get_rect(right=SCREEN_WIDTH - 50, bottom=SCREEN_HEIGHT - 20)
        self.max_hp  = BOSS_INITIAL_HP
        self.hp      = self.max_hp
        self.skills  = pygame.sprite.Group()
        self._timer  = 0

    def update(self):
        self._timer += 1
        if self._timer >= int(FPS * 1.5):
            self._timer = 0
            self.skills.add(BossSkill(self.rect.left, self.rect.centery))
        self.skills.update()

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.skills.draw(screen)
        self._draw_hp_bar(screen)

    def _draw_hp_bar(self, screen):
        bar_w  = 100
        bar_h  = 10
        filled = int(bar_w * max(self.hp, 0) / self.max_hp)
        bx, by = self.rect.x, self.rect.y - 18
        pygame.draw.rect(screen, (255,   0,   0), (bx,          by, filled, bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (bx,          by, bar_w,  bar_h), 2)


class BossSkill(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 60, 60))
        self.rect  = self.image.get_rect(x=x, centery=y)

    def update(self):
        self.rect.x -= 10
        if self.rect.right < 0:
            self.kill()
