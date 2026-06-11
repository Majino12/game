import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


def run(screen, clock, resources):
    big_font = pygame.font.Font(None, 64)
    sub_font = pygame.font.Font(None, 34)
    title    = big_font.render("ZEZ Runner",            True, (255, 255, 255))
    hint     = sub_font.render("Press  Enter  to  Start", True, (180, 180, 180))
    ctrl     = sub_font.render("Space: Jump   Ctrl: Crouch   J: Skill", True, (120, 120, 120))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

        screen.blit(resources['background'], (0, 0))
        screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 3 - 20))
        screen.blit(hint,  ((SCREEN_WIDTH - hint.get_width())  // 2, SCREEN_HEIGHT // 2))
        screen.blit(ctrl,  ((SCREEN_WIDTH - ctrl.get_width())  // 2, SCREEN_HEIGHT // 2 + 50))
        pygame.display.flip()
        clock.tick(FPS)
