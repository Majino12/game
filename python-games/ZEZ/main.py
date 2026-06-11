import pygame
from modules.scene import startMenu, gameRun, gameOver
from modules.interface.loadres import load_resources
from consts import SCREEN_WIDTH, SCREEN_HEIGHT

_HIGHSCORE_PATH = 'highscore.txt'


def _load_high_score():
    try:
        with open(_HIGHSCORE_PATH) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _save_high_score(score):
    try:
        with open(_HIGHSCORE_PATH, 'w') as f:
            f.write(str(score))
    except Exception:
        pass


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ZEZ")
    clock = pygame.time.Clock()

    resources  = load_resources()
    high_score = _load_high_score()

    startMenu.run(screen, clock, resources)

    try:
        pygame.mixer.music.load(resources['background_music'])
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"[BGM] skipped background music: {e}")

    playing = True
    while playing:
        game_result = gameRun.run(screen, clock, resources, high_score)
        high_score  = max(high_score, game_result['score'])
        _save_high_score(high_score)

        playing = gameOver.run(screen, clock, resources, game_result, high_score)

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    main()
