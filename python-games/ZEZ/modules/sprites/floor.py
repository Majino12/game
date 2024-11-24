import pygame
from consts import *

class Floor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH, 20))
        self.image.fill((150, 75, 0))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = SCREEN_HEIGHT - 20

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)
