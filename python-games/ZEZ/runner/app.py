"""Window, input, audio and presentation for ZEZ: Cloud Dash."""
import math
import random
from pathlib import Path

import pygame

from .assets import Assets, create_music
from .model import Run, WIDTH, HEIGHT, GROUND, PLAYER_X
from .storage import SaveData, load_save, save_data, purchase, costs

INK = '#173c40'
MUTED = '#557675'
CREAM = '#fffdf1'
GREEN = '#126f5b'
GOLD = '#ffd569'


class App:
    def __init__(self, headless=False, seed=None):
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        self.window = pygame.display.set_mode((1152, 648), pygame.RESIZABLE)
        pygame.display.set_caption('ZEZ · 云端冲刺 / Cloud Dash')
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        pygame.display.set_icon(self.assets.sprite('characters/character_beige_front', 64, 64))
        self.data = SaveData() if headless else load_save()
        self.assets.muted = self.data.muted
        self.lang = self.data.language if self.assets.has_cjk else 'en'
        self.headless = headless
        self.seed = seed
        self.run = Run(seed=seed)
        self.scene = 'menu'
        self.running = True
        self.fullscreen = False
        self.buttons = []
        self.particles = []
        self.ui_time = 0.0
        self.toast = ''
        self.toast_time = 0.0
        self.slide_keys = set()
        self.mouse_sliding = False
        self.fire_keys = set()
        self.mouse_firing = False
        self.practice = False
        self.settled = False
        self.previous_best = self.data.best_score
        self.reward = 0
        self.music = None if headless else create_music()
        self.music_channel = self.music.play(-1) if self.music else None
        self._volume()

    def tr(self, zh, en):
        return zh if self.lang == 'zh' else en

    def text(self, text, pos, size=22, color=INK, center=False, latin=False):
        im = self.assets.font(size, latin).render(str(text), True, color)
        rect = im.get_rect(center=pos) if center else im.get_rect(topleft=pos)
        self.canvas.blit(im, rect)
        return rect

    def panel(self, rect, color=CREAM, radius=22, shadow=True):
        rect = pygame.Rect(rect)
        if shadow:
            pygame.draw.rect(self.canvas, '#b9d2bd', rect.move(0, 5), border_radius=radius)
        pygame.draw.rect(self.canvas, color, rect, border_radius=radius)

    def button(self, rect, label, action, primary=False, small=False):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.pointer())
        color = ('#0d8267' if hover else GREEN) if primary else ('#e0f0db' if hover else CREAM)
        self.panel(rect, color, 16, not small)
        self.text(label, rect.center, 20 if small else 25, 'white' if primary else INK, True)
        self.buttons.append((rect, action))

    def pointer(self, raw=None):
        x, y = raw if raw else pygame.mouse.get_pos()
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        return ((x - (w - WIDTH * scale) / 2) / scale,
                (y - (h - HEIGHT * scale) / 2) / scale)

    def _volume(self):
        if self.music_channel:
            self.music_channel.set_volume(0 if self.data.muted or self.scene == 'pause' else 1)

    def notify(self, zh, en):
        self.toast = self.tr(zh, en)
        self.toast_time = 2.4

    def save(self):
        if not self.headless and not save_data(self.data):
            self.notify('存档暂时无法写入，本次记录仍保留在内存', 'Could not save; records remain in this session')

    def start(self, practice=False):
        self.run = Run(seed=self.seed)
        self.practice = practice
        if practice:
            self.run.distance = 350.0
            self.run.energy = 100.0
            self.run.shield = True
        self.scene = 'run'
        self.settled = False
        self.reward = 0
        self.previous_best = self.data.best_score
        self.particles.clear()
        self.slide_keys.clear()
        self.mouse_sliding = False
        self.fire_keys.clear()
        self.mouse_firing = False
        self.assets.play('select')
        self._volume()

    def settle(self):
        if self.settled:
            return
        self.settled = True
        r = self.run
        if self.practice:
            self.reward = 0
            return
        self.reward = sum(25 for ok in (r.distance >= 500, r.coins >= 60, r.dash_count >= 2) if ok)
        self.data.best_score = max(self.data.best_score, r.score)
        self.data.best_distance = max(self.data.best_distance, int(r.distance))
        self.data.total_coins += r.coins + self.reward
        self.data.runs += 1
        self.save()

    def action(self, name):
        if name == 'start':
            self.start(practice=self.practice and self.scene == 'over')
        elif name == 'practice':
            self.start(practice=True)
        elif name == 'jump' and self.scene == 'run':
            self.run.jump()
        elif name == 'slide' and self.scene == 'run':
            self.mouse_sliding = True
            self.sync_slide()
        elif name == 'dash' and self.scene == 'run':
            if not self.run.dash():
                self.notify('收集金币，充满能量后冲刺', 'Collect coins to fill your dash meter')
        elif name == 'fire' and self.scene == 'run':
            self.mouse_firing = True
            self.sync_fire()
        elif name == 'pause' and self.scene == 'run':
            self.slide_keys.clear()
            self.mouse_sliding = False
            self.fire_keys.clear()
            self.mouse_firing = False
            self.run.set_fire(False)
            self.run.set_slide(False)
            self.scene = 'pause'
            self._volume()
        elif name == 'resume' and self.scene == 'pause':
            self.scene = 'run'
            self._volume()
        elif name == 'menu':
            if self.scene in ('pause', 'run'):
                self.settle()
            self.scene = 'menu'
            self._volume()
        elif name == 'mute':
            self.data.muted = not self.data.muted
            self.assets.muted = self.data.muted
            self._volume()
            self.save()
        elif name == 'language':
            if not self.assets.has_cjk:
                self.notify('', 'Install a CJK font to enable Chinese')
            else:
                self.lang = 'en' if self.lang == 'zh' else 'zh'
                self.data.language = self.lang
                self.save()
        elif name.startswith('hero:'):
            color = name.split(':')[1]
            if purchase(self.data, color):
                self.data.selected = color
                self.assets.play('select')
                self.save()
            else:
                self.notify('金币不足，继续跑一局吧', 'Collect more coins to unlock this runner')

    def sync_slide(self):
        self.run.set_slide(bool(self.slide_keys) or self.mouse_sliding)

    def sync_fire(self):
        self.run.set_fire(bool(self.fire_keys) or self.mouse_firing)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.scene in ('run', 'pause'):
                    self.settle()
                self.running = False
            elif event.type == pygame.WINDOWFOCUSLOST and self.scene == 'run':
                self.action('pause')
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    self.window = pygame.display.set_mode((0, 0) if self.fullscreen else (1152, 648), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
                elif k == pygame.K_m:
                    self.action('mute')
                elif k == pygame.K_l:
                    self.action('language')
                elif k in (pygame.K_ESCAPE, pygame.K_p):
                    if self.scene == 'run': self.action('pause')
                    elif self.scene == 'pause': self.action('resume')
                    elif self.scene == 'over': self.action('menu')
                elif k in (pygame.K_RETURN, pygame.K_SPACE) and self.scene in ('menu', 'over'):
                    self.action('start')
                elif k == pygame.K_RETURN and self.scene == 'pause':
                    self.action('resume')
                elif self.scene == 'run':
                    if k in (pygame.K_SPACE, pygame.K_w, pygame.K_UP): self.action('jump')
                    elif k in (pygame.K_s, pygame.K_DOWN, pygame.K_LCTRL, pygame.K_RCTRL):
                        self.slide_keys.add(k)
                        self.sync_slide()
                    elif k in (pygame.K_j, pygame.K_LSHIFT, pygame.K_RSHIFT): self.action('dash')
                    elif k in (pygame.K_k, pygame.K_x):
                        self.fire_keys.add(k)
                        self.sync_fire()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_s, pygame.K_DOWN, pygame.K_LCTRL, pygame.K_RCTRL):
                    self.slide_keys.discard(event.key)
                    self.sync_slide()
                if event.key in (pygame.K_k, pygame.K_x):
                    self.fire_keys.discard(event.key)
                    self.sync_fire()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                point = self.pointer(event.pos)
                for rect, action in reversed(self.buttons):
                    if rect.collidepoint(point):
                        self.action(action)
                        break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_sliding = False
                self.sync_slide()
                self.mouse_firing = False
                self.sync_fire()

    def update(self, dt):
        self.ui_time += dt
        self.toast_time = max(0, self.toast_time - dt)
        if self.scene != 'run':
            return
        self.run.update(dt)
        for event in self.run.events:
            name, x, y = event[:3]
            self.assets.play(name)
            colors = [GOLD, '#fff6bb', '#e9a948'] if name == 'coin' else ['#9de9d9', '#ffffff', '#56baae']
            for _ in range(3 if name == 'shot' else 7 if name == 'coin' else 14):
                self.particles.append([x, y, random.uniform(-130, 130), random.uniform(-190, 0), .5, random.choice(colors)])
            if name == 'bonus': self.notify('金币狂欢！8 秒自动吸金', 'COIN RUSH! 8 seconds of automatic collection')
            if name == 'shield': self.notify('护盾挡住了撞击', 'Shield saved you!')
            if name == 'boss_warning': self.notify('蜂巢守卫来了！按住 K / X 自动瞄准射击', 'HIVE GUARDIAN! Hold K / X to aim and fire')
            if name == 'boss_defeated': self.notify('守卫击破！+50金币 / +500分 / 护盾 / 满能量', 'GUARDIAN DOWN! +50 coins / +500 score / shield / full energy')
        for p in self.particles:
            p[0] += p[2] * dt; p[1] += p[3] * dt; p[3] += 360 * dt; p[4] -= dt
        self.particles = [p for p in self.particles[-250:] if p[4] > 0]
        if not self.run.alive or (self.practice and self.run.boss_defeated > 0 and self.run.boss is None):
            self.settle()
            self.scene = 'over'

    def background(self, distance=0, clock=0):
        biome = int(distance // 500) % 3
        sky = ['#ddf4ec', '#f4e5d1', '#e4e0f5'][biome]
        self.canvas.fill(sky)
        pygame.draw.circle(self.canvas, ['#f7f9d5', '#fff4cd', '#fff5e3'][biome], (1030, 165), 73)
        pygame.draw.circle(self.canvas, '#fffced', (1030, 165), 53)
        for i in range(6):
            x = (i * 265 - distance * 1.5) % 1550 - 160
            y = 160 + (i % 3) * 65
            pygame.draw.ellipse(self.canvas, '#f7fcf4', (x, y, 140, 35))
            pygame.draw.ellipse(self.canvas, '#f7fcf4', (x + 35, y - 23, 65, 55))
        theme = ['hills', 'desert', 'trees'][biome]
        bg = self.assets.landscape(theme, sky)
        offset = int(distance * 4) % 800
        for i in range(-1, 3):
            self.canvas.blit(bg, (i * 800 - offset, GROUND - 460))
        tile_theme = ['grass', 'sand', 'purple'][biome]
        offset = int(distance * 25) % 80
        for x in range(-80, WIDTH + 80, 80):
            self.canvas.blit(self.assets.sprite('tiles/terrain_' + tile_theme + '_block_top', 80, 80, False), (x - offset, GROUND))
        pygame.draw.rect(self.canvas, ['#c98454', '#c9a16e', '#b589ae'][biome], (0, GROUND + 80, WIDTH, HEIGHT - GROUND - 80))
        return biome

    def hero(self, x, feet, height=80, state='walk', color=None, phase=None, alpha=255):
        phase = self.ui_time if phase is None else phase
        frame = ('walk_a' if int(phase * 10) % 2 == 0 else 'walk_b') if state == 'walk' else state
        color = color or self.data.selected
        width = height * (.95 if state == 'duck' else .78)
        image = self.assets.sprite('characters/character_' + color + '_' + frame, int(width), int(height))
        if alpha != 255:
            image = image.copy()
            image.set_alpha(alpha)
        self.canvas.blit(image, (x - (width - 52) / 2, feet - height))

    def top_buttons(self):
        self.button((1020, 26, 96, 42), self.tr('EN / 中', '中 / EN'), 'language', small=True)
        self.button((1128, 26, 120, 42), self.tr('声音 关' if self.data.muted else '声音 开', 'SOUND OFF' if self.data.muted else 'SOUND ON'), 'mute', small=True)

    def menu(self):
        self.background(self.ui_time * 1.8, self.ui_time)
        self.panel((36, 26, 106, 42), INK, 14, False)
        self.text('ZEZ', (89, 48), 36, 'white', True, True)
        self.text('CLOUD DASH', (158, 37), 25, GREEN, latin=True)
        self.top_buttons()
        self.text(self.tr('轻装上阵 · 一路追风', 'ONE MORE RUN. ONE MORE ADVENTURE.'), (78, 135), 24, GREEN)
        self.text(self.tr('云端冲刺', 'CLOUD'), (73, 178), 84, INK)
        self.text(self.tr('把好心情，跑出来。', 'DASH'), (78, 282), 34 if self.lang == 'zh' else 66, INK)
        self.text(self.tr('二段跳、滑铲、吸金币，连击开启金币狂欢。', 'Jump twice. Slide low. Collect a sky full of coins.'), (80, 359), 21, MUTED)
        self.button((80, 414, 290, 64), self.tr('开始冒险   →', 'LET’S RUN   →'), 'start', True)
        self.button((390, 414, 225, 64), self.tr('Boss 练习', 'BOSS PRACTICE'), 'practice')
        self.text(self.tr('或按 Enter / 空格开始', 'or press ENTER / SPACE'), (90, 495), 18, MUTED)
        self.panel((80, 538, 357, 44), '#edf6dd', 14, False)
        self.text(self.tr('最佳', 'BEST'), (96, 550), 18, GREEN)
        self.text(f'{self.data.best_score:,}', (172, 546), 28, INK, latin=True)
        self.text(f'{self.data.total_coins}  ' + self.tr('金币', 'COINS'), (285, 550), 18, GREEN)
        # A character stage doubles as the cosmetic selector.
        self.panel((700, 134, 490, 70), '#f4fae8', 20)
        self.text(self.tr('选择你的追风伙伴', 'CHOOSE YOUR RUNNER'), (945, 159), 23, INK, True)
        self.text(self.tr('不同外观，同样好手感', 'SAME SKILLS. YOUR STYLE.'), (945, 187), 15, MUTED, True)
        for i, color in enumerate(('beige', 'pink', 'purple')):
            x = 720 + i * 162
            selected = self.data.selected == color
            if selected: self.panel((x - 8, 266, 148, 265), '#fff8dc', 28)
            pygame.draw.ellipse(self.canvas, '#90b18b', (x + 13, 451, 100, 18))
            self.hero(x + 35, 452 + math.sin(self.ui_time * 3 + i) * 5, 133, 'walk', color)
            name = [self.tr('奶油', 'CREAM'), self.tr('莓莓', 'BERRY'), self.tr('星云', 'NOVA')][i]
            owned = color in self.data.unlocked
            label = self.tr('已选择', 'SELECTED') if selected else name if owned else str(costs[color]) + self.tr(' 金币', ' COINS')
            self.button((x, 481, 130, 39), label, 'hero:' + color, selected, True)
        for x, y in ((650, 280), (1210, 250), (663, 420)):
            self.canvas.blit(self.assets.sprite('tiles/coin_gold', 30, 36), (x, y + math.sin(self.ui_time * 2 + x) * 9))
        controls = [(50, 'SPACE / W', self.tr('跳跃 · 再按二段跳', 'JUMP · DOUBLE JUMP')),
                    (350, 'S / DOWN', self.tr('按住滑铲 · 空中速降', 'SLIDE · FAST FALL')),
                    (650, 'J / SHIFT', self.tr('满能量冲刺 · 破甲', 'ENERGY DASH · SMASH')),
                    (950, 'K / X', self.tr('Boss 战按住连续射击', 'BOSS · HOLD TO FIRE'))]
        for x, key, label in controls:
            self.panel((x, 620, 280, 67), '#fff7df', 16, False)
            self.text(key, (x + 18, 631), 24, INK, latin=True)
            self.text(label, (x + 18, 660), 16, MUTED)

    def world(self):
        r = self.run
        biome = self.background(r.distance, r.time)
        if r.boss:
            self.draw_boss()
        if r.bonus_timer > 0:
            for i in range(9):
                pygame.draw.line(self.canvas, '#fff8c2', ((i * 180 - int(r.time * 500)) % 1400, 160 + i * 43), ((i * 180 - int(r.time * 500)) % 1400 + 90, 160 + i * 43), 4)
        for e in r.entities:
            if e.kind == 'coin':
                width = max(9, int(28 * abs(math.cos(r.time * 5 + e.x / 150))))
                self.canvas.blit(self.assets.sprite('tiles/coin_gold', width, 30), (e.x + (e.w - width) / 2, e.y))
            elif e.kind in ('magnet', 'shield', 'battery'):
                color, label = {'magnet': ('#b76ce6', 'M'), 'shield': ('#4daed2', 'S'), 'battery': ('#e8b642', '+')}[e.kind]
                pygame.draw.circle(self.canvas, '#fffdf1', (int(e.x + e.w/2), int(e.y + e.h/2)), 29)
                pygame.draw.circle(self.canvas, color, (int(e.x + e.w/2), int(e.y + e.h/2)), 24)
                self.text(label, (e.x + e.w/2, e.y + e.h/2), 30, 'white', True, True)
            else:
                path = {'crate': 'tiles/block_planks', 'spike': 'tiles/spikes', 'drone': 'enemies/bee_' + ('a' if int(r.time * 12) % 2 else 'b')}[e.kind]
                self.canvas.blit(self.assets.sprite(path, int(e.w), int(e.h)), (e.x, e.y))
                if e.kind == 'drone' and e.x > PLAYER_X + 150:
                    self.text(self.tr('↓ 滑铲', '↓ SLIDE'), (e.x + e.w/2, e.y - 25), 16, GREEN, True)
        for projectile in r.projectiles:
            rect = pygame.Rect(projectile.rect)
            if projectile.kind == 'shot':
                pygame.draw.line(self.canvas, '#fffde7', rect.center, (rect.centerx - 22, rect.centery + 4), 5)
                pygame.draw.ellipse(self.canvas, '#6de9df', rect.inflate(6, 6))
                pygame.draw.ellipse(self.canvas, '#fffde7', rect)
            else:
                color = '#f77947' if projectile.kind == 'boss_low' else '#a775e6'
                pygame.draw.ellipse(self.canvas, '#fff2ce', rect.inflate(12, 12))
                pygame.draw.ellipse(self.canvas, color, rect)
                pygame.draw.ellipse(self.canvas, '#ffffff', rect.inflate(-18, -18), 3)
                hint = self.tr('跳跃 ↑', 'JUMP') if projectile.kind == 'boss_low' else self.tr('滑铲 ↓', 'SLIDE')
                self.text(hint, (rect.centerx, rect.top - 20), 18, '#944f32' if projectile.kind == 'boss_low' else '#78509e', True)
        x, y, w, h = r.player_rect
        pygame.draw.ellipse(self.canvas, '#5a9d6a', (PLAYER_X - 7, GROUND - 7, 70, 13))
        if r.dash_timer > 0 or r.bonus_timer > 0:
            pygame.draw.ellipse(self.canvas, '#fdf4b5', (x - 93, y + h/3, 140, h/2))
            for n in range(3):
                pygame.draw.line(self.canvas, '#ffffff', (x - 35 - n * 25, y + 15 + n * 18), (x - 85 - n * 27, y + 15 + n * 18), 4)
        if r.shield:
            pygame.draw.circle(self.canvas, '#b0f3ed', (int(x+w/2), int(y+h/2)), int(h/2 + 17), 4)
        if r.magnet > 0:
            pygame.draw.circle(self.canvas, '#bfa0e2', (int(x+w/2), int(y+h/2)), 68, 2)
        state = 'duck' if r.sliding and r.player_y >= GROUND - 1 else 'jump' if r.player_y < GROUND - 1 else 'walk'
        alpha = 135 if r.invulnerable > 0 and int(r.time * 16) % 2 == 0 else 255
        self.hero(x, r.player_y, 38 if state == 'duck' else 78, state, phase=r.time, alpha=alpha)
        for p in self.particles:
            pygame.draw.circle(self.canvas, p[5], (int(p[0]), int(p[1])), max(1, int(p[4] * 9)))
        self.hud(biome)

    def draw_boss(self):
        r, boss = self.run, self.run.boss
        if boss.telegraph > 0 and boss.phase != 'warning':
            low = boss.attack == 'low'
            lane_y = GROUND - (44 if low else 112)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            color = (240, 110, 60, 40) if low else (152, 96, 220, 40)
            pygame.draw.rect(overlay, color, (PLAYER_X - 30, lane_y, boss.x - PLAYER_X + 30, 50), border_radius=12)
            self.canvas.blit(overlay, (0, 0))
            for x in range(PLAYER_X, int(boss.x), 44):
                pygame.draw.line(self.canvas, '#dc814c' if low else '#a577c4', (x, lane_y + 50), (x + 24, lane_y + 50), 2)
            self.text(self.tr('准备跳跃 ↑' if low else '准备滑铲 ↓', 'GET READY TO JUMP' if low else 'GET READY TO SLIDE'), (640, 265), 25, '#914b32' if low else '#78509e', True)
        bob = math.sin(r.time * 3) * 8
        cx, cy = int(boss.x + boss.w / 2), int(boss.y + boss.h / 2 + bob)
        weak = boss.phase == 'weak'
        color = '#f27b43' if boss.enraged else '#dcad4e'
        if weak: color = '#69d6c0'
        radius = 100 + int(math.sin(r.time * 6) * 3)
        if boss.phase == 'defeated':
            for n in range(10):
                angle = n * math.tau / 10 + r.time
                pygame.draw.circle(self.canvas, GOLD, (int(cx + math.cos(angle) * 105), int(cy + math.sin(angle) * 85)), 7)
        else:
            pygame.draw.circle(self.canvas, '#f8f3d3', (cx, cy), radius)
            pygame.draw.circle(self.canvas, color, (cx, cy), radius, 5)
            for n in range(3):
                angle = r.time * .8 + n * math.tau / 3
                pygame.draw.circle(self.canvas, color, (int(cx + math.cos(angle) * radius), int(cy + math.sin(angle) * radius)), 10)
        sprite = 'enemies/bee_' + ('a' if int(r.time * 12) % 2 else 'b')
        image = self.assets.sprite(sprite, int(boss.w), int(boss.h))
        self.canvas.blit(image, (boss.x, boss.y + bob))
        if weak:
            pygame.draw.circle(self.canvas, '#ffffff', (cx, cy + 19), 23, 3)
            pygame.draw.line(self.canvas, '#ffffff', (cx - 30, cy + 19), (cx + 30, cy + 19), 2)
        label = self.tr('弱点开放 · 开火！', 'WEAK POINT · FIRE!') if weak else self.tr('狂暴装甲' if boss.enraged else '蜂巢装甲', 'ENRAGED ARMOR' if boss.enraged else 'HIVE ARMOR')
        if boss.phase == 'defeated': label = self.tr('击破！', 'GUARDIAN DOWN!')
        self.text(label, (cx, boss.y + boss.h + 43), 19, GREEN if weak else INK, True)

    def boss_hud(self):
        boss = self.run.boss
        self.panel((375, 126, 570, 90), '#fff8df', 19)
        name = self.tr('蜂巢守卫', 'HIVE GUARDIAN')
        if boss.enraged: name += self.tr(' · 狂暴', ' · ENRAGED')
        self.text(name, (395, 138), 22, '#944f32')
        self.text(f'{max(0, int(boss.hp))} / {int(boss.max_hp)}', (811, 141), 23, INK, latin=True)
        pygame.draw.rect(self.canvas, '#e6dac3', (395, 179, 529, 12), border_radius=6)
        fill = int(529 * max(0, boss.hp) / boss.max_hp)
        if fill: pygame.draw.rect(self.canvas, '#40b599' if boss.phase == 'weak' else '#e29548', (395, 179, fill, 12), border_radius=6)
        if boss.phase == 'warning':
            self.text(self.tr('准备迎战 · 按住 K / X 射击', 'GET READY · HOLD K / X TO FIRE'), (640, 248), 24, '#944f32', True)
        elif boss.phase == 'weak':
            self.text(self.tr('弱点开放！射击伤害 ×4', 'WEAK POINT! 4x SHOT DAMAGE'), (640, 248), 24, GREEN, True)

    def hud(self, biome):
        r = self.run
        self.panel((28, 22, 1224, 89), CREAM, 23)
        self.text('ZEZ', (50, 42), 42, GREEN, latin=True)
        self.text(self.tr('得分', 'SCORE'), (167, 37), 16, MUTED)
        self.text(f'{r.score:,}', (165, 57), 40, INK, latin=True)
        self.text(f'{int(r.distance)} m', (400, 49), 35, INK, latin=True)
        self.canvas.blit(self.assets.sprite('tiles/coin_gold', 23, 28), (571, 52))
        self.text(str(r.coins), (607, 50), 34, INK, latin=True)
        self.text(self.tr('最佳', 'BEST') + f'  {self.data.best_score:,}', (748, 48), 19, MUTED)
        self.button((990, 42, 104, 42), self.tr('静音' if not self.data.muted else '有声', 'MUTE' if not self.data.muted else 'SOUND'), 'mute', small=True)
        self.button((1107, 42, 119, 42), self.tr('暂停 II', 'PAUSE II'), 'pause', small=True)
        self.panel((30, 130, 315, 72), '#f4f8e6', 16, False)
        self.text(self.tr('冲刺能量', 'DASH ENERGY'), (47, 140), 17, GREEN)
        self.text(self.tr('就绪！J', 'READY! J') if r.energy >= 100 else f'{int(r.energy)}%', (262, 142), 17, GREEN)
        pygame.draw.rect(self.canvas, '#c9dfce', (48, 175, 277, 10), border_radius=5)
        if r.energy > 0: pygame.draw.rect(self.canvas, '#e8b248' if r.energy >= 100 else '#39a88a', (48, 175, max(10, int(277*r.energy/100)), 10), border_radius=5)
        if r.combo > 1:
            self.text(f'{r.combo} COMBO', (1020, 134), 34, GREEN, latin=True)
            self.text(self.tr('30 连击 → 金币狂欢', '30 COMBO → COIN RUSH'), (1000, 176), 16, MUTED)
        if r.boss:
            self.boss_hud()
        elif r.bonus_timer > 0:
            self.panel((433, 140, 414, 53), GOLD, 18)
            self.text(self.tr('金币狂欢', 'COIN RUSH') + f'   {r.bonus_timer:.1f}s', (640, 167), 27, INK, True)
        elif r.time < 13:
            hint = self.tr('空格跳跃 · 再按一次二段跳', 'SPACE to jump · press twice to double jump') if r.time < 7 else self.tr('按住 ↓ 滑铲，从蜜蜂下面通过', 'Hold ↓ to slide underneath the bees')
            self.text(hint, (640, 232), 25, GREEN, True)
        status = []
        if r.shield: status.append(self.tr('护盾', 'SHIELD'))
        if r.magnet > 0: status.append(self.tr('磁铁 ', 'MAGNET ') + f'{r.magnet:.0f}s')
        if r.dash_timer > 0: status.append(self.tr('冲刺 ', 'DASH ') + f'{r.dash_timer:.1f}s')
        if status: self.text(' / '.join(status), (45, 218), 20, GREEN)
        stage = self.tr('BOSS 练习 · 不计入存档', 'BOSS PRACTICE · NO SAVED REWARDS') if self.practice else ['01 / CLOUD MEADOW', '02 / GOLDEN DUNES', '03 / LILAC GROVE'][biome]
        self.text(stage, (38, 630), 22, '#ffffff')
        goal = self.tr('跳低波，滑高波；弱点开放时全力射击', 'Jump low waves. Slide high waves. Fire at weak points.') if r.boss else self.tr('目标：500米 · 60金币 · 2冲刺 / 每项 +25', 'GOALS: 500m · 60 coins · 2 dashes / +25 each')
        self.text(goal, (38, 671), 17, '#ffffff')
        if not r.boss and not self.practice:
            remaining = max(0, int(r.next_boss_distance - r.distance))
            self.text(self.tr(f'距离守卫 {remaining}m · 已击破 {r.boss_defeated}', f'GUARDIAN IN {remaining}m · CLEARED {r.boss_defeated}'), (390, 633), 17, '#ffffff')
        for x, label, action, primary in [
            (734, self.tr('冲刺 J', 'DASH J'), 'dash', r.energy >= 100),
            (866, self.tr('滑铲 ↓', 'SLIDE ↓'), 'slide', False),
            (998, self.tr('跳跃 ↑', 'JUMP ↑'), 'jump', True),
        ]:
            self.button((x, 625, 122, 64), label, action, primary)
        if r.boss and r.boss.phase not in ('warning', 'defeated'):
            self.button((1130, 625, 122, 64), self.tr('射击 K', 'FIRE K'), 'fire', True)
        else:
            self.panel((1130, 625, 122, 64), '#e9e3cb', 16, False)
            self.text(self.tr('射击 K', 'FIRE K'), (1191, 657), 22, MUTED, True)

    def overlay(self):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((18, 45, 42, 165))
        self.canvas.blit(shade, (0, 0))
        self.buttons.clear()
        if self.scene == 'pause':
            self.panel((380, 170, 520, 382), CREAM, 30, False)
            self.text(self.tr('歇一会儿', 'TAKE A BREATHER'), (640, 233), 39, INK, True)
            self.text(self.tr('准备好，再去追下一阵风。', 'The next adventure can wait a moment.'), (640, 295), 21, MUTED, True)
            self.button((435, 347, 410, 65), self.tr('继续奔跑  →', 'KEEP RUNNING  →'), 'resume', True)
            label = self.tr('结束练习并返回主页', 'LEAVE PRACTICE') if self.practice else self.tr('结算并返回主页', 'BANK COINS & GO HOME')
            self.button((435, 437, 410, 52), label, 'menu')
            self.text('ESC / P / ENTER', (640, 526), 18, MUTED, True, True)
        else:
            r = self.run
            self.panel((327, 98, 626, 538), CREAM, 30, False)
            title = self.tr('新纪录！' if r.score > self.previous_best else '跑得漂亮，再来一次？', 'NEW PERSONAL BEST!' if r.score > self.previous_best else 'READY FOR ONE MORE?')
            if self.practice: title = self.tr('试炼完成！' if r.boss_defeated else '调整节奏，再试一次', 'BOSS CLEAR!' if r.boss_defeated else 'TRY A NEW RHYTHM')
            self.text(title, (640, 150), 32, GREEN, True)
            self.text(f'{r.score:,}', (640, 222), 86, INK, True, True)
            self.text(self.tr('本次得分', 'RUN SCORE'), (640, 279), 19, MUTED, True)
            for x, value, label in [(405, f'{int(r.distance)}m', self.tr('奔跑距离', 'DISTANCE')), (560, str(r.coins), self.tr('收集金币', 'COINS')), (715, str(r.best_combo), self.tr('最高连击', 'COMBO')), (870, str(r.boss_defeated), self.tr('击破守卫', 'BOSSES'))]:
                self.text(value, (x, 343), 40, INK, True, True)
                self.text(label, (x, 380), 18, MUTED, True)
            banked = self.tr('练习模式：不消耗金币，也不计入纪录', 'PRACTICE: NO COST, NO SAVED RECORDS') if self.practice else self.tr(f'已存入 {r.coins + self.reward} 金币（含目标奖励 {self.reward}）', f'BANKED {r.coins + self.reward} COINS · GOAL BONUS +{self.reward}')
            self.text(banked, (640, 432), 20, GREEN, True)
            self.button((389, 480, 502, 64), self.tr('再跑一局   →', 'RUN IT BACK   →'), 'start', True)
            self.button((389, 562, 502, 45), self.tr('返回主页 · 换个伙伴', 'HOME · CHOOSE A RUNNER'), 'menu', small=True)

    def draw(self):
        self.buttons.clear()
        if self.scene == 'menu':
            self.menu()
        else:
            self.world()
            if self.scene in ('pause', 'over'):
                self.overlay()
        if self.toast_time > 0:
            self.panel((260, 558, 760, 42), INK, 12, False)
            self.text(self.toast, (640, 579), 19, 'white', True)
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        size = (max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale)))
        self.window.fill(INK)
        self.window.blit(pygame.transform.smoothscale(self.canvas, size), ((w-size[0])//2, (h-size[1])//2))
        pygame.display.flip()

    def loop(self, frames=0, screenshot=None, scene='menu'):
        if scene != 'menu':
            self.start(practice=scene == 'boss')
            if scene in ('pause', 'over'):
                self.scene = scene
        count = 0
        while self.running and (not frames or count < frames):
            dt = min(self.clock.tick(60) / 1000, .1) if not self.headless else 1/60
            self.events()
            self.update(dt)
            self.draw()
            count += 1
        if screenshot:
            path = Path(screenshot)
            path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.canvas, str(path))
        pygame.quit()
