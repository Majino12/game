import pygame
from consts import *


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, obstacle_type, images):
        super().__init__()
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.obstacle_type = obstacle_type

        if obstacle_type == "ground":
            self.rect.y = SCREEN_HEIGHT - height - 20
        elif obstacle_type == "sky":
            self.rect.y = y

        self.animation_index = 0
        self.animation_speed = 0.1

    def update(self):
        self.rect.x -= 5
        if self.rect.x < 0:
            self.kill()

        # Update animation
        self.animation_index += self.animation_speed
        if self.animation_index >= len(self.images):
            self.animation_index = 0
        self.image = self.images[int(self.animation_index)]

    def draw(self, screen):
        screen.blit(self.image, self.rect)
