import pygame
from consts import *
from modules.sprites.role import Player
from modules.sprites.obstacle import Obstacle
from modules.sprites.boss import Boss
from modules.sprites.floor import Floor
import random

def run(screen, clock, resources):
    player = Player(resources['player'], resources['skill'])
    floor = Floor()
    obstacles = pygame.sprite.Group()
    boss = None
    score = 0
    skill_points = 0
    boss_defeated = 0
    boss_thresholds = [6, 120, 190, 260, 330]

    obstacle_timer = 0
    in_boss_battle = False

    ground_obstacle_images = [pygame.image.load(f'resources/obstacles/ground_{i}.png').convert_alpha() for i in range(1, 4)]
    sky_obstacle_images = [pygame.image.load(f'resources/obstacles/sky_{i}.png').convert_alpha() for i in range(1, 4)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
                    resources['jump_sound'].play()
                elif event.key == pygame.K_LCTRL:
                    player.crouch()
                elif event.key == pygame.K_j and (skill_points >= SKILL_POINT_THRESHOLD or in_boss_battle):
                    if not in_boss_battle:
                        skill_points -= SKILL_POINT_THRESHOLD
                    player.fire_skill()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL:
                    player.stand_up()

        player.update()
        floor.update()
        obstacles.update()
        if boss:
            boss.update()

        for obstacle in obstacles:
            if player.rect.colliderect(obstacle.rect):
                resources['game_over_sound'].play()
                return {'score': score, 'boss_defeated': boss_defeated, 'game_over': True}
            for skill in player.skills:
                if skill.rect.colliderect(obstacle.rect):
                    obstacle.kill()
                    skill.kill()
                    break

        if boss and player.rect.colliderect(boss.rect):
            resources['game_over_sound'].play()
            return {'score': score, 'boss_defeated': boss_defeated, 'game_over': True}

        if boss:
            for skill in player.skills:
                if skill.rect.colliderect(boss.rect):
                    boss.hp -= SKILL_DAMAGE
                    skill.kill()
                    if boss.hp <= 0:
                        boss_defeated += 1
                        score += 50
                        boss = None
                        in_boss_battle = False
                        obstacles.empty()
                        break

            if boss is not None:
                for boss_skill in list(boss.skills):
                    if player.rect.colliderect(boss_skill.rect):
                        resources['game_over_sound'].play()
                        return {'score': score, 'boss_defeated': boss_defeated, 'game_over': True}
                    elif boss_skill.rect.right < 0:
                        skill_points += 1
                        if skill_points > 5:
                            skill_points = 5
                        boss_skill.kill()

        if not boss:
            obstacle_timer += 1
            if obstacle_timer >= 120:
                obstacle_timer = 0
                if random.random() < 0.5:
                    obstacle_type = "ground"
                    new_obstacle = Obstacle(SCREEN_WIDTH, SCREEN_HEIGHT - 70, 40, 40, obstacle_type, ground_obstacle_images)
                else:
                    obstacle_type = "sky"
                    new_obstacle = Obstacle(SCREEN_WIDTH, SCREEN_HEIGHT - 150, 50, 50, obstacle_type, sky_obstacle_images)
                obstacles.add(new_obstacle)

        for obstacle in obstacles:
            if obstacle.rect.right < player.rect.left:
                score += 1
                obstacle.kill()

        if score in boss_thresholds and not boss:
            boss = Boss(resources['boss'])
            in_boss_battle = True
            obstacles.empty()

        if score % 5 == 0 and skill_points < 5:
            skill_points += 1

        screen.fill((0, 0, 0))
        screen.blit(resources['background'], (0, 0))
        floor.draw(screen)
        player.draw(screen)
        obstacles.draw(screen)
        if boss:
            boss.draw(screen)

        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        skill_text = font.render(f"Skill Points: {skill_points}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        screen.blit(skill_text, (10, 50))

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    return True

def show_restart_screen(screen, resources):
    screen.blit(resources['restart_screen'], (0, 0))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ZEZ")
    clock = pygame.time.Clock()


    running = True
    while running:
        game_result = run(screen, clock)
        if game_result['game_over']:
            show_restart_screen(screen)
            continue

    pygame.quit()

if __name__ == "__main__":
    main()
