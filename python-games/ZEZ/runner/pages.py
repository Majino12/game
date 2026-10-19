"""Progression screens. Rendering is separate from rules and save mutations."""
import pygame

from .model import PERKS
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


def draw_changelog(app):
    page_header(app, app.tr('更新日志', 'WHAT’S NEW'), 'v1.1.0  ·  2026-10-19')
    rows = [
        ('01', '每次冒险，不同搭配', 'A NEW BUILD EVERY RUN',
         '击破 Boss 后选择天赋：三段跳、弱点增伤、充能、连射、磁力与连击宽限。',
         'Pick a perk after each boss: a third jump, weak-point damage, charge, rapid fire, magnet range or combo grace.'),
        ('02', '金币有了新用途', 'MAKE YOUR COINS COUNT',
         '工坊提供三项永久升级；远征合约跨局累计里程、金币和击破数，完成一阶自动领奖。',
         'Buy three permanent workshop upgrades. Career contracts reward cumulative distance, coins and guardian defeats.'),
        ('03', '遇见风暴守卫', 'MEET THE STORM GUARDIAN',
         '后续守卫交替登场，攻击节奏不同、血量逐步提高。利用天赋组合应对更远的挑战。',
         'Alternating guardians bring new attack sequences and rising health. Build your perks to face the next challenge.'),
    ]
    for i, (number, title, title_en, body, body_en) in enumerate(rows):
        y = 170 + i * 142
        app.panel((72, y, 1136, 126), ['#e8f5f3', '#fff4cf', '#ece8f7'][i], 20, False)
        app.text(number, (100, y + 31), 44, GREEN, latin=True)
        app.text(app.tr(title, title_en), (190, y + 14), 26, INK)
        wrapped(app, app.tr(body, body_en), (190, y + 56, 975, 68), 20)
    fit_text(app, app.tr('v1.0：跑酷、连击狂欢、角色外观与 Boss 练习 · 完整记录见 CHANGELOG.md',
                        'v1.0: running, coin rush, runners & boss practice. Full history: CHANGELOG.md'),
             (640, 643), 19, 1120, MUTED)
