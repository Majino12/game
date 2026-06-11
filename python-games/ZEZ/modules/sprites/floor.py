import pygame
from consts import SCREEN_WIDTH, GROUND_Y


class Floor:
    def __init__(self):
        self.image = pygame.Surface((SCREEN_WIDTH, 20))
        self.image.fill((150, 75, 0))
        self.rect  = self.image.get_rect(x=0, y=GROUND_Y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
