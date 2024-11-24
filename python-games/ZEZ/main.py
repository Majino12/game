import pygame
from modules.scene import startMenu, gameRun, gameOver
from modules.interface.loadres import load_resources
from consts import SCREEN_WIDTH, SCREEN_HEIGHT


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ZEZ")
    clock = pygame.time.Clock()

    resources = load_resources()

    startMenu.run(screen, clock, resources)

    pygame.mixer.music.load(resources['background_music'])
    pygame.mixer.music.play(-1)

    running = True
    while running:
        game_result = gameRun.run(screen, clock, resources)

        running = gameOver.run(screen, clock, resources, game_result)

    pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
