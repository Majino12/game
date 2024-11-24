import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT

def run(screen, clock, resources):
    start_font = pygame.font.Font(None, 74)
    start_text = start_font.render("Press Enter to Start", True, (255, 255, 255))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    running = False

        screen.fill((0, 0, 0))
        screen.blit(resources['background'], (0, 0))
        screen.blit(start_text, ((SCREEN_WIDTH - start_text.get_width()) // 2, (SCREEN_HEIGHT - start_text.get_height()) // 2))
        pygame.display.flip()
        clock.tick(15)
