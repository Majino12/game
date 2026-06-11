import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from modules.perks import pick3

# ── Card geometry ─────────────────────────────────────────────────────────────
_W    = 190        # card width
_H    = 265        # card height
_CY   = 118        # card top-y on screen
_LIFT = 10         # pixels focused card rises above baseline
_GAP  = (SCREEN_WIDTH - 3 * _W) // 4   # equal spacing ≈ 57 px

# Pre-compute card left-x positions: [57, 304, 551]
_XS   = [_GAP + i * (_W + _GAP) for i in range(3)]


def run(screen, clock, player, frozen_bg) -> None:
    """Blocking perk-selection scene.

    Called from within gameRun after portal exit. Draws on top of the paused
    game frame (frozen_bg), applies the chosen Perk to `player`, then returns.
    """
    perks   = pick3()
    focused = 0

    fnt_title = pygame.font.Font(None, 58)
    fnt_sub   = pygame.font.Font(None, 28)
    fnt_name  = pygame.font.Font(None, 34)
    fnt_desc  = pygame.font.Font(None, 25)
    fnt_num   = pygame.font.Font(None, 44)
    fnt_hint  = pygame.font.Font(None, 27)

    dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 168))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    focused = (focused - 1) % 3
                elif event.key == pygame.K_RIGHT:
                    focused = (focused + 1) % 3
                elif event.key == pygame.K_RETURN:
                    perks[focused].apply(player)
                    return
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    perks[0].apply(player); return
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    perks[1].apply(player); return
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    perks[2].apply(player); return

        # ── draw ──────────────────────────────────────────────────────────────
        screen.blit(frozen_bg, (0, 0))
        screen.blit(dark,      (0, 0))

        # title
        t = fnt_title.render("PERK  SELECTION", True, (255, 228, 100))
        screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 26))

        sub = fnt_sub.render("보스를 처치했습니다!  능력을 하나 선택하세요.", True, (190, 195, 210))
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 78))

        for i, perk in enumerate(perks):
            _draw_card(screen, fnt_name, fnt_desc, fnt_num, perk,
                       _XS[i], _CY, focused == i, i + 1)

        hint = fnt_hint.render(
            "[ 1 / 2 / 3 ]  즉시 선택     [ ◄ ► ]  카드 이동     [ Enter ]  확인",
            True, (130, 138, 155),
        )
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, _CY + _H + 24))

        pygame.display.flip()
        clock.tick(FPS)


# ── Card renderer ─────────────────────────────────────────────────────────────

def _draw_card(screen, fnt_name, fnt_desc, fnt_num, perk, x, y, focused, number):
    oy = -_LIFT if focused else 0   # lift focused card up

    # glow shadow behind focused card
    if focused:
        glow = pygame.Surface((_W + 18, _H + 18), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*perk.color, 52),
                         (0, 0, _W + 18, _H + 18), border_radius=16)
        screen.blit(glow, (x - 9, y + oy - 9))

    # card body
    body_col = (30, 35, 52) if focused else (18, 21, 34)
    pygame.draw.rect(screen, body_col,
                     (x, y + oy, _W, _H), border_radius=12)

    # coloured header strip (rounded top only)
    pygame.draw.rect(
        screen, perk.color, (x, y + oy, _W, 54),
        border_top_left_radius=12, border_top_right_radius=12,
        border_bottom_left_radius=0, border_bottom_right_radius=0,
    )

    # card border
    bdr = perk.color if focused else tuple(max(0, c - 90) for c in perk.color)
    pygame.draw.rect(screen, bdr,
                     (x, y + oy, _W, _H), 3 if focused else 1, border_radius=12)

    # key number in header
    num = fnt_num.render(f"[ {number} ]", True, (255, 255, 255))
    screen.blit(num, (x + _W // 2 - num.get_width() // 2, y + oy + 10))

    # perk name
    nm = fnt_name.render(perk.name, True, (255, 255, 255))
    screen.blit(nm, (x + _W // 2 - nm.get_width() // 2, y + oy + 64))

    # thin divider
    dc = tuple(min(255, c + 50) for c in perk.color)
    pygame.draw.line(screen, dc,
                     (x + 18, y + oy + 94), (x + _W - 18, y + oy + 94), 1)

    # description (auto-wrapped)
    for j, line in enumerate(_wrap(perk.description, fnt_desc, _W - 22)):
        s = fnt_desc.render(line, True, (195, 210, 225))
        screen.blit(s, (x + _W // 2 - s.get_width() // 2, y + oy + 106 + j * 25))

    # focused: "▶ 선택 중 ◀" indicator
    if focused:
        sel = fnt_desc.render("▶  선택 중  ◀", True, perk.color)
        screen.blit(sel, (x + _W // 2 - sel.get_width() // 2, y + oy + _H - 38))

    # bottom accent bar
    pygame.draw.rect(screen, perk.color,
                     (x + 18, y + oy + _H - 20, _W - 36, 6), border_radius=3)


def _wrap(text: str, font: pygame.font.Font, max_w: int) -> list:
    """Greedy word-wrap; returns list of lines that each fit within max_w px."""
    words, lines, cur = text.split(), [], ''
    for w in words:
        candidate = (cur + ' ' + w).strip()
        if font.size(candidate)[0] <= max_w:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]
