"""Cached art, portable fonts and optional audio. All paths are module-relative."""
from array import array
from functools import lru_cache
import math
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'


class Assets:
    def __init__(self):
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        self.font_path = next((p for p in candidates if Path(p).is_file()), None)
        if not self.font_path:
            self.font_path = pygame.font.match_font('notosanscjksc,wenquanyizenhei,microsoftyahei')
        self.has_cjk = self.font_path is not None
        self.sounds = {}
        self.muted = False
        if pygame.mixer.get_init():
            for name, filename in {
                'coin': 'coin', 'jump': 'jump', 'double_jump': 'jump-high',
                'hit': 'hurt', 'power': 'gem', 'shield': 'bump',
                'dash': 'magic', 'bonus': 'magic', 'select': 'select',
                'shot': 'throw', 'boss_hit': 'bump', 'boss_warning': 'magic',
                'boss_attack': 'throw', 'boss_defeated': 'gem',
            }.items():
                try:
                    sound = pygame.mixer.Sound(str(ASSETS / 'sounds' / ('sfx_' + filename + '.ogg')))
                    sound.set_volume(.10 if name in ('shot', 'boss_hit') else .18 if name == 'coin' else .3)
                    self.sounds[name] = sound
                except pygame.error:
                    pass

    @lru_cache(maxsize=256)
    def sprite(self, path, width, height, trim=True):
        source = pygame.image.load(str(ASSETS / (path + '.png'))).convert_alpha()
        if trim:
            source = source.subsurface(source.get_bounding_rect()).copy()
        return pygame.transform.smoothscale(source, (int(width), int(height)))

    @lru_cache(maxsize=32)
    def font(self, size, latin=False):
        return pygame.font.Font(None if latin else self.font_path, size)

    @lru_cache(maxsize=3)
    def landscape(self, theme, sky):
        image = self.sprite('backgrounds/background_color_' + theme, 800, 460, False).copy()
        image.fill(sky, special_flags=pygame.BLEND_RGB_MULT)
        image.set_alpha(150)
        return image

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()


def create_music():
    """An original, quiet eight-bar synth loop; no third-party recording."""
    if not pygame.mixer.get_init():
        return None
    rate, _, channels = pygame.mixer.get_init()
    duration = 8.0
    samples = array('h')
    melody = [64, 67, 71, 67, 69, 72, 76, 72, 67, 71, 74, 71, 62, 66, 69, 66]
    bass = [40, 45, 43, 38]
    for i in range(int(rate * duration)):
        t = i / rate
        phase = t % .5
        note = melody[int(t * 2) % len(melody)]
        f = 440 * 2 ** ((note - 69) / 12)
        env = min(1, phase / .025) * math.exp(-phase * 8)
        b = 440 * 2 ** ((bass[int(t / 2) % 4] - 69) / 12)
        # The loop fades at both ends to avoid a discontinuity.
        fade = min(1, t / .03, (duration - t) / .03)
        value = int(1400 * fade * (math.sin(t * math.tau * f) * env + .35 * math.sin(t * math.tau * b)))
        for _ in range(channels):
            samples.append(value)
    sound = pygame.mixer.Sound(buffer=samples.tobytes())
    sound.set_volume(.32)
    return sound
