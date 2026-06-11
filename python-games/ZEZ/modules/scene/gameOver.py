import pygame
from consts import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


def run(screen, clock, resources, game_result, high_score=0):
    title_font = pygame.font.Font(None, 86)
    score_font = pygame.font.Font(None, 56)
    info_font  = pygame.font.Font(None, 38)
    hint_font  = pygame.font.Font(None, 30)

    score         = game_result['score']
    boss_defeated = game_result.get('boss_defeated', 0)
    best          = max(score, high_score)
    new_record    = score > high_score   # strictly beat the previous best

    # Pre-build a semi-transparent dark panel for readability
    PANEL_W, PANEL_H = 480, 400
    panel = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    panel.fill((8, 8, 24, 175))
    panel_x = (SCREEN_WIDTH  - PANEL_W) // 2   # 160
    panel_y = 90

    cx = SCREEN_WIDTH // 2

    # Vertical layout constants (absolute Y positions on screen)
    Y_TITLE   = 110
    Y_SCORE   = 215
    Y_BEST    = 275
    Y_BOSSES  = 335   # shown only when boss_defeated > 0
    Y_NEWBEST = 380   # shown only when new_record
    Y_HINT    = 455

    bg   = resources['background']
    bg_w = bg.get_width()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True     # play again
                if event.key == pygame.K_ESCAPE:
                    return False    # quit

        # ── draw background (static, no scroll needed here) ──────────────────
        screen.blit(bg, (0, 0))
        screen.blit(panel, (panel_x, panel_y))

        # ── GAME OVER title ───────────────────────────────────────────────────
        t = title_font.render("GAME  OVER", True, (220, 55, 55))
        screen.blit(t, (cx - t.get_width() // 2, Y_TITLE))

        # ── Score ─────────────────────────────────────────────────────────────
        s = score_font.render(f"Score:  {score}", True, (255, 255, 255))
        screen.blit(s, (cx - s.get_width() // 2, Y_SCORE))

        # ── Best ──────────────────────────────────────────────────────────────
        b = score_font.render(f"Best:   {best}", True, (255, 215, 0))
        screen.blit(b, (cx - b.get_width() // 2, Y_BEST))

        # ── Boss defeats (only if any) ────────────────────────────────────────
        if boss_defeated > 0:
            bd = info_font.render(f"Bosses defeated: {boss_defeated}", True, (100, 220, 255))
            screen.blit(bd, (cx - bd.get_width() // 2, Y_BOSSES))

        # ── New Best badge ────────────────────────────────────────────────────
        if new_record:
            nr = info_font.render("-- New Best! --", True, (255, 215, 0))
            screen.blit(nr, (cx - nr.get_width() // 2, Y_NEWBEST))

        # ── Controls hint ─────────────────────────────────────────────────────
        h = hint_font.render("Enter: Play Again          Esc: Quit", True, (160, 160, 160))
        screen.blit(h, (cx - h.get_width() // 2, Y_HINT))

        pygame.display.flip()
        clock.tick(FPS)
