"""Progression screens. Rendering is separate from rules and save mutations."""
import pygame

from .model import PERKS
from .content import HEROES, BOSS_SPECS
from .routes import MAPS
from .storage import contract_status, upgrade_price

INK = '#173c40'
MUTED = '#557675'
CREAM = '#fffdf1'
GREEN = '#126f5b'
GOLD = '#ffd569'

UPGRADES = (
    ('magnet', '磁力线圈', 'MAGNET COIL', '延长拾取磁铁的持续时间', 'Keep each magnet pickup active longer',
     '每级 +2 秒 · 最长 13 秒', '+2 sec per level · up to 13 sec', 'gem_blue'),
    ('recharge', '能量回路', 'ENERGY CIRCUIT', '每枚金币补充更多冲刺能量', 'Charge your dash faster with every coin',
     '每级 +0.5 能量 · 最高 4.5', '+0.5 per level · up to 4.5 energy', 'gem_yellow'),
    ('dash', '冲刺引擎', 'DASH ENGINE', '延长主动冲刺的保护时间', 'Stay in your protected dash for longer',
     '每级 +0.35 秒 · 最长 4.05 秒', '+0.35 sec per level · up to 4.05 sec', 'gem_green'),
)


def fit_text(app, label, center, size, width, color=INK):
    """Keep bilingual labels inside their card without clipping."""
    while size > 13 and app.assets.font(size).size(str(label))[0] > width:
        size -= 1
    app.text(label, center, size, color, True)


def wrapped(app, text, rect, size=21, color=MUTED, spacing=9):
    """Wrap English at words and Chinese at characters using font metrics."""
    x, y, width, _ = rect
    tokens = list(text) if app.lang == 'zh' else text.split(' ')
    joiner = '' if app.lang == 'zh' else ' '
    line = ''
    for token in tokens:
        candidate = line + (joiner if line else '') + token
        if line and app.assets.font(size).size(candidate)[0] > width:
            app.text(line, (x, y), size, color)
            y += size + spacing
            line = token
        else:
            line = candidate
    if line:
        app.text(line, (x, y), size, color)
    return y + size + spacing


def page_header(app, title, subtitle):
    app.background(app.ui_time * 1.8, app.ui_time)
    app.panel((32, 24, 1216, 672), CREAM, 28)
    app.text(title, (72, 56), 39, GREEN)
    app.text(subtitle, (74, 114), 19, MUTED)
    app.button((1070, 53, 136, 45), app.tr('返回 Esc', 'BACK Esc'), 'menu', small=True)
    app.text(f'{app.data.total_coins:,} ' + app.tr('金币', 'COINS'), (892, 71), 22, GREEN, True)


def draw_workshop(app):
    page_header(app, app.tr('追风工坊', 'RUNNER WORKSHOP'),
                app.tr('用跑来的金币升级装备。所有角色共享，普通冒险持续生效。',
                       'Spend earned coins on upgrades shared by all runners in adventure mode.'))
    for i, (key, zh, en, desc, desc_en, effect, effect_en, sprite) in enumerate(UPGRADES):
        x = 72 + i * 384
        level = app.data.upgrades.get(key, 0)
        app.panel((x, 170, 360, 420), ['#e8f5f3', '#fff4cf', '#eaf2de'][i], 24, False)
        app.canvas.blit(app.assets.sprite('tiles/' + sprite, 64, 64), (x + 148, 204))
        fit_text(app, app.tr(zh, en), (x + 180, 304), 30, 328)
        app.text(f'LEVEL {level} / 3', (x + 180, 349), 20, GREEN, True, True)
        for n in range(3):
            pygame.draw.rect(app.canvas, GREEN if n < level else '#c5d9c9',
                             (x + 113 + n * 49, 378, 37, 8), border_radius=4)
        wrapped(app, app.tr(desc, desc_en), (x + 25, 414, 310, 60), 19)
        fit_text(app, app.tr(effect, effect_en), (x + 180, 488), 18, 322, GREEN)
        price = upgrade_price(app.data, key)
        if price is None:
            app.panel((x + 30, 524, 300, 44), '#c9e1cd', 14, False)
            app.text(app.tr('已满级', 'MAX LEVEL'), (x + 180, 546), 21, GREEN, True)
        else:
            label = app.tr(f'升级 · {price} 金币', f'UPGRADE · {price} COINS')
            app.button((x + 30, 524, 300, 44), label, 'upgrade:' + key,
                       app.data.total_coins >= price, True)
    fit_text(app, app.tr('Boss 练习使用基础装备；天赋只保留在当前冒险，工坊升级会永久保存。',
                        'Practice uses base gear. Run perks reset each adventure; workshop upgrades stay.'),
             (640, 642), 20, 1120, MUTED)


def draw_contracts(app):
    page_header(app, app.tr('远征合约', 'EXPEDITION CONTRACTS'),
                app.tr('每一局都算数。累积目标，结算时自动领奖，随后开启下一阶。',
                       'Every adventure counts. Bank progress, earn rewards and advance to the next tier.'))
    for i, item in enumerate(contract_status(app.data)):
        y = 171 + i * 145
        app.panel((72, y, 1136, 126), ['#e8f5f3', '#fff4cf', '#ece8f7'][i], 20, False)
        app.text(f'{i + 1:02}', (100, y + 33), 44, GREEN, latin=True)
        app.text(app.tr(item['title'], item['title_en']), (186, y + 19), 26, INK)
        app.text(app.tr(f'第 {item["level"] + 1} 阶', f'TIER {item["level"] + 1}'),
                 (186, y + 58), 18, MUTED)
        target, progress = item['target'], item['progress']
        previous = target * item['level'] / (item['level'] + 1)
        fraction = min(1, max(0, (progress - previous) / (target - previous)))
        pygame.draw.rect(app.canvas, '#cbded1', (500, y + 76, 450, 12), border_radius=6)
        if fraction > 0:
            pygame.draw.rect(app.canvas, GREEN, (500, y + 76, max(2, int(450 * fraction)), 12), border_radius=6)
        unit = ' m' if item['key'] == 'distance' else ''
        fit_text(app, f'{int(progress):,} / {target:,}{unit}', (725, y + 42), 25, 450)
        app.text(f'+{item["reward"]}', (1072, y + 44), 37, GREEN, True, True)
        app.text(app.tr('金币 / 阶', 'COINS / TIER'), (1072, y + 81), 16, MUTED, True)
    fit_text(app, app.tr('合约只记录新版普通冒险；练习不计入。旧钱包、外观和纪录都会保留。',
                        'Contracts track new adventures, excluding practice. Your previous wallet and records stay.'),
             (640, 642), 20, 1120, MUTED)


def draw_perks(app):
    shade = pygame.Surface((1280, 720), pygame.SRCALPHA)
    shade.fill((18, 45, 42, 195))
    app.canvas.blit(shade, (0, 0))
    app.buttons.clear()
    app.text(app.tr('击破之后，选择你的新力量', 'GUARDIAN DOWN. CHOOSE YOUR POWER.'),
             (640, 108), 38, CREAM, True)
    app.text(app.tr('时间已暂停 · 天赋可叠加，本局结束后重置',
                    'Time is paused. Stack perks for this adventure only.'), (640, 160), 21, '#d9ead8', True)
    count = len(app.run.perk_choices)
    start = (1280 - (count * 350 + max(0, count - 1) * 26)) / 2
    for i, key in enumerate(app.run.perk_choices):
        spec = PERKS[key]
        x = int(start + i * 376)
        app.panel((x, 214, 350, 350), CREAM, 25, False)
        app.panel((x + 139, 238, 72, 55), GOLD, 16, False)
        app.text(str(i + 1), (x + 175, 266), 38, GREEN, True, True)
        fit_text(app, app.tr(spec['name'], spec['name_en']), (x + 175, 333), 30, 308)
        level = app.run.perks.get(key, 0)
        label = app.tr('补给奖励', 'SUPPLY REWARD') if key == 'supply' else f'LEVEL {level} → {level + 1} / {spec["max_level"]}'
        app.text(label, (x + 175, 378), 19, GREEN, True)
        wrapped(app, app.tr(spec['desc'], spec['desc_en']), (x + 27, 413, 296, 85), 20)
        app.button((x + 25, 500, 300, 44), app.tr(f'选择 {i + 1}', f'CHOOSE {i + 1}'),
                   'perk:' + key, True, True)
    app.button((457, 615, 366, 44), app.tr('结算并返回主页 · Esc', 'BANK & GO HOME · Esc'), 'menu', small=True)


def draw_maps(app):
    page_header(app, app.tr('云端地图图鉴', 'ATLAS OF THE CLOUDS'),
                app.tr('云野出发，之后随机轮换。每约 500 米在安全时切换，连续地图不重复。',
                       'Start in the meadow. Maps shuffle about every 500m, once safe, without immediate repeats.'))
    for i, (key, spec) in enumerate(MAPS.items()):
        x, y = 72 + (i % 2) * 580, 169 + (i // 2) * 216
        app.panel((x, y, 556, 198), spec['palette']['sky'], 22, False)
        sprite = {'meadow': 'spring_out', 'dunes': 'gem_yellow',
                  'grove': 'gem_green', 'ruins': 'gem_blue'}[key]
        app.canvas.blit(app.assets.sprite('tiles/' + sprite, 63, 67), (x + 30, y + 34))
        app.text(app.tr(spec['name'], spec['name_en']), (x + 118, y + 28), 27, INK)
        wrapped(app, app.tr(spec['hint'], spec['hint_en']), (x + 118, y + 74, 403, 75), 19)
        detail = {
            'meadow': ('弹簧可跳过 · 箱子更多', 'Optional springs · More crates'),
            'dunes': ('宝箱 +15金币 / +15能量 / +150分', 'Chest: +15 coins / +15 energy / +150 score'),
            'grove': ('荧光球 +20能量 / 3秒磁铁', 'Glow: +20 energy / 3s magnet'),
            'ruins': ('轻重力 · 高空金币路线', 'Lower gravity · Higher coin trails'),
        }[key]
        fit_text(app, app.tr(*detail), (x + 278, y + 166), 18, 514, spec['palette']['accent'])
    fit_text(app, app.tr('Boss、冲刺和腾空期间延后切图；到达新地图后重新计算 500 米。',
                        'Boss fights, dashes and airborne moves delay transitions. The next interval starts after arrival.'),
             (640, 644), 19, 1136, MUTED)


def draw_practice(app):
    page_header(app, app.tr('守卫试炼场', 'GUARDIAN TRAINING'),
                app.tr('选择对手，练习读招。使用当前角色技能和基础装备，不消耗金币、不记录成绩。',
                       'Choose a guardian. Use your runner skill and base gear, with no cost or saved rewards.'))
    for i, (kind, spec) in enumerate(BOSS_SPECS.items()):
        x = 72 + i * 384
        app.panel((x, 170, 360, 420), ['#fff4cf', '#eee7f6', '#e3f3f1'][i], 24, False)
        sprite = {'bee': 'enemies/bee_a', 'storm': 'enemies/fly_a', 'crystal': 'tiles/gem_blue'}[kind]
        pygame.draw.circle(app.canvas, '#fffdf1', (x + 180, 255), 65)
        app.canvas.blit(app.assets.sprite(sprite, 96, 94), (x + 132, 207))
        fit_text(app, app.tr(spec['name'], spec['name_en']), (x + 180, 348), 29, 324)
        wrapped(app, app.tr(spec['desc'], spec['desc_en']), (x + 25, 393, 310, 105), 20)
        app.button((x + 30, 524, 300, 44), app.tr('开始试炼 →', 'START TRAINING →'), 'practice:' + kind, True, True)
    hero = HEROES[app.data.selected]
    fit_text(app, app.tr('当前伙伴：', 'RUNNER: ') + app.tr(hero['name'], hero['name_en']) + ' · E / ' + app.tr(hero['skill'], hero['skill_en']),
             (640, 644), 22, 1136, GREEN)


def draw_changelog(app):
    page_header(app, app.tr('更新日志', 'WHAT’S NEW'), 'v1.2.0  ·  2026-10-19')
    rows = [
        ('01', '不同伙伴，不同绝招', 'THREE RUNNERS. THREE POWERS.',
         '按 E 释放专属技能：奶油守护脉冲、莓莓流星跃、星云星环爆发。技能开局就绪，冷却暂停时冻结。',
         'Press E for Guardian Pulse, Meteor Leap or Nova Ring. Ready at the start, with cooldowns frozen during pauses.'),
        ('02', '四张地图，随机旅程', 'FOUR MAPS. A SHUFFLED JOURNEY.',
         '云野弹簧、沙丘宝箱、林地荧光球与遗迹轻重力。安全时随机切换地图，每局路线更有变化。',
         'Spring pads, desert chests, forest glow orbs and low-gravity ruins. Maps shuffle when the route is safe to change.'),
        ('03', '新的守卫，新的节奏', 'NEW GUARDIANS. NEW RHYTHMS.',
         '风暴守卫发射连续双波，晶岩巨像锁定高度攻击。三个 Boss 轮换登场，也可在试炼场单独练习。',
         'Dodge the Storm Guardian’s double waves and Crystal Colossus’s locked-height orbs. Train against each guardian separately.'),
    ]
    for i, (number, title, title_en, body, body_en) in enumerate(rows):
        y = 170 + i * 142
        app.panel((72, y, 1136, 126), ['#e8f5f3', '#fff4cf', '#ece8f7'][i], 20, False)
        app.text(number, (100, y + 31), 44, GREEN, latin=True)
        app.text(app.tr(title, title_en), (190, y + 14), 26, INK)
        wrapped(app, app.tr(body, body_en), (190, y + 56, 975, 68), 20)
    fit_text(app, app.tr('保留 v1.1 工坊、合约与天赋系统 · 完整版本记录见 CHANGELOG.md',
                        'Includes the v1.1 workshop, contracts and perks. Full version history: CHANGELOG.md'),
             (640, 643), 19, 1120, MUTED)
