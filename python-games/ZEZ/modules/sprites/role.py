import pygame
from consts import *

class Player(pygame.sprite.Sprite):
    def __init__(self, images, skill_image):
        super().__init__()
        self.run_images = images['run']
        self.jump_image = images['jump']
        self.crouch_image = images['crouch']
        self.skill_image = skill_image
        self.image = self.run_images[0]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - self.rect.height - 20
        self.velocity = 0
        self.skills = pygame.sprite.Group()
        self.crouching = False
        self.jumping = False
        self.run_index = 0

    def jump(self):
        if not self.jumping and not self.crouching:
            self.velocity = -PLAYER_JUMP_HEIGHT
            self.jumping = True

    def crouch(self):
        if not self.crouching and not self.jumping:
            self.image = pygame.transform.scale(self.crouch_image, (self.rect.width, self.rect.height // 2))
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.crouching = True

    def stand_up(self):
        if self.crouching:
            self.image = self.run_images[0]
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.crouching = False

    def fire_skill(self):
        if len(self.skills) < SKILL_POINT_THRESHOLD:
            skill = Skill(self.rect.right, self.rect.centery, self.skill_image)
            self.skills.add(skill)

    def update(self):
        if self.jumping:
            self.image = self.jump_image
        elif self.crouching:
            self.image = self.crouch_image
        else:
            self.run_index = (self.run_index + 1) % len(self.run_images)
            self.image = self.run_images[self.run_index]

        self.velocity += 1
        self.rect.y += self.velocity
        if self.rect.y >= SCREEN_HEIGHT - self.rect.height - 20:
            self.rect.y = SCREEN_HEIGHT - self.rect.height - 20
            self.velocity = 0
            self.jumping = False

        self.skills.update()

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.skills.draw(screen)

    def collides_with(self, sprite):
        return self.rect.colliderect(sprite.rect)

class Skill(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x += 10
        if self.rect.x > SCREEN_WIDTH:
            self.kill()
