import pygame
from consts import *


class Boss(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = pygame.transform.scale(image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH - 150
        self.rect.y = SCREEN_HEIGHT - 200
        self.max_hp = BOSS_INITIAL_HP
        self.hp = self.max_hp
        self.skills = pygame.sprite.Group()
        self.skill_timer = 0

    def update(self):
        self.skill_timer += 1
        if self.skill_timer > FPS * 1.5:
            self.skill_timer = 0
            skill = BossSkill(self.rect.left, self.rect.centery)
            self.skills.add(skill)

        self.skills.update()

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.skills.draw(screen)

        health_bar_width = 100
        health_bar_height = 10
        health_ratio = self.hp / self.max_hp
        current_health_bar_width = health_bar_width * health_ratio
        health_bar_rect = pygame.Rect(self.rect.x, self.rect.y - 20, current_health_bar_width, health_bar_height)
        health_bar_border_rect = pygame.Rect(self.rect.x, self.rect.y - 20, health_bar_width, health_bar_height)

        pygame.draw.rect(screen, (255, 0, 0), health_bar_rect)
        pygame.draw.rect(screen, (255, 255, 255), health_bar_border_rect, 2)

    def collides_with(self, sprite):
        return self.rect.colliderect(sprite.rect)


class BossSkill(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= 10
        if self.rect.x < 0:
            self.kill()
