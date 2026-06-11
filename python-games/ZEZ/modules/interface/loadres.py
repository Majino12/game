import pygame


def _img(path, fallback_size, fallback_color, alpha=True):
    """Load an image file, returning a coloured fallback Surface on any error.

    Convert is split into a nested try so that a missing display (offscreen
    testing / dummy driver) doesn't hide the real file-not-found errors.
    """
    try:
        surf = pygame.image.load(path)
    except Exception as e:
        print(f"[IMG] fallback for '{path}': {e}")
        surf = pygame.Surface(fallback_size)
        surf.fill(fallback_color)
        return surf

    # convert() requires an initialised display; skip silently if unavailable
    try:
        return surf.convert_alpha() if alpha else surf.convert()
    except Exception:
        return surf   # still a valid Surface, just not GPU-optimised


def _sound(path):
    """Load a Sound object, returning None and logging on any error."""
    try:
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"[SFX] skipped '{path}': {e}")
        return None


def load_resources():
    resources = {}

    # player frames (run_1.png … run_10.png; run_0 has a broken filename, skipped)
    resources['player'] = {
        'run': [
            _img(f'resources/role/run_{i}.png', (60, 80), (80, 120, 200))
            for i in range(1, 11)
        ],
        'jump':   _img('resources/role/jump.png',   (60, 80), (80, 120, 200)),
        'crouch': _img('resources/role/crouch.png', (60, 40), (80, 120, 200)),
    }

    resources['skill'] = _img('resources/role/skill.png',  (20, 10), (255, 255,   0))
    resources['boss']  = _img('resources/role/boss.png',   (100, 100), (220,  50,  50))

    resources['background']     = _img('resources/background/bg.png',      (800, 600), ( 30,  30,  60), alpha=False)
    resources['restart_screen'] = _img('resources/background/restart.png', (800, 600), ( 20,  20,  40), alpha=False)

    # obstacle sprite sheets (4 frames each: ground_0…3, sky_0…3)
    resources['ground_obstacles'] = [
        _img(f'resources/obstacles/ground_{i}.png', (40, 40), (200, 80, 30)) for i in range(4)
    ]
    resources['sky_obstacles'] = [
        _img(f'resources/obstacles/sky_{i}.png', (50, 50), (60, 180, 200)) for i in range(4)
    ]

    # SFX (None when the file is absent — _play() handles None gracefully)
    resources['jump_sound']      = _sound('resources/sound/jump.wav')
    resources['game_over_sound'] = _sound('resources/sound/game_over.wav')
    resources['skill_sound']     = _sound('resources/sound/skill.wav')   # optional

    resources['background_music'] = 'resources/sound/background_music.mp3'

    return resources
