import pygame
from consts import OBSTACLE_BASE_SPEED, ANIM_INTERVAL, HITBOX_INSET_X, HITBOX_INSET_Y


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, obstacle_type, images, speed=OBSTACLE_BASE_SPEED):
        super().__init__()
        self.images     = images
        self.anim_frame = 0
        self.anim_tick  = 0
        self.image      = self.images[0]
        self.rect       = self.image.get_rect(x=x, y=y)
        self.speed      = speed

    def hit_rect(self):
        """Shrunk rect for more forgiving collision."""
        return self.rect.inflate(-HITBOX_INSET_X * 2, -HITBOX_INSET_Y * 2)

    def update(self):
        self.rect.x -= self.speed

        # safety net: destroy if fully scrolled off the left
        if self.rect.right < 0:
            self.kill()
            return

        # advance animation frame
        self.anim_tick += 1
        if self.anim_tick >= ANIM_INTERVAL:
            self.anim_tick  = 0
            self.anim_frame = (self.anim_frame + 1) % len(self.images)
            self.image      = self.images[self.anim_frame]
