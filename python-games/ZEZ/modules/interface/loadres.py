import pygame


def load_resources():
    resources = {}

    resources['player'] = {
        'run': [pygame.image.load(f'resources/role/run_{i}.png').convert_alpha() for i in range(1, 11)],
        'jump': pygame.image.load('resources/role/jump.png').convert_alpha(),
        'crouch': pygame.image.load('resources/role/crouch.png').convert_alpha()
    }

    resources['skill'] = pygame.image.load('resources/role/skill.png').convert_alpha()

    resources['boss'] = pygame.image.load('resources/role/boss.png').convert_alpha()

    resources['background'] = pygame.image.load('resources/background/bg.png').convert()
    resources['restart_screen'] = pygame.image.load('resources/background/restart.png').convert()

    resources['jump_sound'] = pygame.mixer.Sound('resources/sound/jump.wav')
    resources['game_over_sound'] = pygame.mixer.Sound('resources/sound/game_over.wav')
    resources['background_music'] = 'resources/sound/background_music.mp3'

    return resources
