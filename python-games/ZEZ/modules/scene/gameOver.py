import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT

def run(screen, clock, resources, game_result):
    game_over_font = pygame.font.Font(None, 74)
    score_text = game_over_font.render(f"Score: {game_result['score']}", True, (100, 155, 155))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True

        screen.fill((0, 0, 0))
        screen.blit(resources['restart_screen'], (0, 0))
        screen.blit(score_text, ((SCREEN_WIDTH - score_text.get_width()) // 2, (SCREEN_HEIGHT - score_text.get_height()) // 2))
        pygame.display.flip()
        clock.tick(15)

    return False

