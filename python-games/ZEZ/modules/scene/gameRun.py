import pygame
import random
from enum import Enum, auto

from consts import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GROUND_Y,
    OBSTACLE_BASE_SPEED, OBSTACLE_BASE_INTERVAL,
    SPEED_LEVEL_INTERVAL, SPEED_INCREMENT, INTERVAL_DECREMENT,
    MIN_SPAWN_INTERVAL, MAX_OBSTACLE_SPEED,
    SKILL_POINT_THRESHOLD, SKILL_DAMAGE,
)
from modules.sprites.role import Player
from modules.sprites.obstacle import Obstacle
from modules.sprites.boss import Boss
from modules.sprites.floor import Floor
from modules.sprites.portal import ExitPortal
from modules.scene import perkSelect


class BossPhase(Enum):
    NONE  = auto()   # normal gameplay
    ENTRY = auto()   # boss visible but frozen — 1-second warning
    FIGHT = auto()   # active battle
    CLEAR = auto()   # boss dead; exit portal scrolling in


_BOSS_THRESHOLDS = [10, 80, 160, 250, 350]
_ENTRY_FRAMES    = FPS          # 60 frames = 1 second warning


def run(screen, clock, resources, high_score=0):
    # ── All state is local — re-calling is a full reset. ──────────────────────
    player       = Player(resources['player'], resources['skill'])
    floor        = Floor()
    obstacles    = pygame.sprite.Group()
    portal_group = pygame.sprite.GroupSingle()
    boss         = None

    score           = 0
    skill_points    = 0
    boss_defeated   = 0
    next_boss_idx   = 0

    game_ticks       = 0
    obstacle_speed   = float(OBSTACLE_BASE_SPEED)
    spawn_interval   = OBSTACLE_BASE_INTERVAL
    obstacle_timer   = 0
    last_skill_award = 0

    boss_phase       = BossPhase.NONE
    boss_entry_timer = 0

    _perk_pending = False    # set True after portal success; triggers perkSelect

    ground_h = resources['ground_obstacles'][0].get_height()

    bg   = resources['background']
    bg_w = bg.get_width()
    bg_x = 0.0

    font = pygame.font.Font(None, 36)

    # ── main loop ─────────────────────────────────────────────────────────────
    while True:
        clock.tick(FPS)

        # ── events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
                    _play(resources['jump_sound'])

                elif event.key == pygame.K_LCTRL:
                    player.crouch()

                elif event.key == pygame.K_j:
                    in_boss = boss_phase != BossPhase.NONE
                    eff_thr = max(1, SKILL_POINT_THRESHOLD - player.skill_threshold_bonus)
                    can_fire = in_boss or skill_points >= eff_thr
                    if can_fire:
                        if not in_boss:
                            skill_points -= eff_thr
                        player.fire_skill()
                        _play(resources.get('skill_sound'))

                elif event.key == pygame.K_ESCAPE:
                    if boss_phase != BossPhase.NONE:
                        # Flee penalty: immediate game over, no boss credit
                        if boss:
                            boss.skills.empty()
                        if portal_group.sprite:
                            portal_group.sprite.kill()
                        _play(resources['game_over_sound'])
                        return {'score': score, 'boss_defeated': boss_defeated}

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL:
                    player.stand_up()

        # ── update ────────────────────────────────────────────────────────────
        game_ticks += 1
        player.update()
        obstacles.update()
        portal_group.update()

        # Boss moves and fires only during FIGHT (frozen during ENTRY)
        if boss and boss_phase == BossPhase.FIGHT:
            boss.update()

        # ENTRY countdown → transition to FIGHT
        if boss_phase == BossPhase.ENTRY:
            boss_entry_timer -= 1
            if boss_entry_timer <= 0:
                boss_phase = BossPhase.FIGHT

        # ── difficulty progression (normal gameplay only) ─────────────────────
        if boss_phase == BossPhase.NONE and game_ticks % SPEED_LEVEL_INTERVAL == 0:
            obstacle_speed = min(obstacle_speed + SPEED_INCREMENT, MAX_OBSTACLE_SPEED)
            spawn_interval = max(spawn_interval - INTERVAL_DECREMENT, MIN_SPAWN_INTERVAL)

        # ── obstacle spawning (normal gameplay only) ──────────────────────────
        if boss_phase == BossPhase.NONE:
            obstacle_timer += 1
            if obstacle_timer >= spawn_interval:
                obstacle_timer = 0
                spd = int(obstacle_speed)
                if random.random() < 0.5:
                    obs = Obstacle(SCREEN_WIDTH, GROUND_Y - ground_h, "ground",
                                   resources['ground_obstacles'], spd)
                else:
                    obs = Obstacle(SCREEN_WIDTH, GROUND_Y - 130, "sky",
                                   resources['sky_obstacles'], spd)
                obstacles.add(obs)

        # ── collision: player vs obstacles ────────────────────────────────────
        p_hit = player.hit_rect()
        for obs in list(obstacles):
            if p_hit.colliderect(obs.hit_rect()) and not player.is_invincible():
                if player.use_shield():
                    obs.kill()      # shield absorbs both the hit and the obstacle
                else:
                    _play(resources['game_over_sound'])
                    return {'score': score, 'boss_defeated': boss_defeated}
            for skill in list(player.skills):
                if skill.rect.colliderect(obs.rect):
                    obs.kill(); skill.kill(); break

        # ── scoring: obstacle passes the player ───────────────────────────────
        for obs in list(obstacles):
            if obs.rect.right < player.rect.left:
                score += 1 + player.score_bonus
                obs.kill()

        # ── skill point gain: every 5 obstacles cleared, once per milestone ───
        milestone = (score // 5) * 5
        if milestone > last_skill_award and skill_points < SKILL_POINT_THRESHOLD:
            skill_points     += 1
            last_skill_award  = milestone

        # ── boss trigger ──────────────────────────────────────────────────────
        if (boss_phase == BossPhase.NONE
                and next_boss_idx < len(_BOSS_THRESHOLDS)
                and score >= _BOSS_THRESHOLDS[next_boss_idx]):
            next_boss_idx    += 1
            boss              = Boss(resources['boss'])
            boss_phase        = BossPhase.ENTRY
            boss_entry_timer  = _ENTRY_FRAMES
            obstacles.empty()

        # ── boss combat ───────────────────────────────────────────────────────
        if boss:
            # Touching the boss body is fatal in any boss phase (unless shielded)
            if p_hit.colliderect(boss.rect) and not player.is_invincible():
                if player.use_shield():
                    pass    # shield absorbs the body collision
                else:
                    boss.skills.empty()
                    _play(resources['game_over_sound'])
                    return {'score': score, 'boss_defeated': boss_defeated}

            # Skill projectiles damage the boss only during FIGHT
            if boss_phase == BossPhase.FIGHT:
                for skill in list(player.skills):
                    if skill.rect.colliderect(boss.rect):
                        boss.hp -= int(SKILL_DAMAGE * player.skill_power_mult)
                        skill.kill()
                        if boss.hp <= 0:
                            boss.skills.empty()        # prevent orphaned bullets
                            boss       = None
                            boss_phase = BossPhase.CLEAR
                            portal_group.add(ExitPortal(int(obstacle_speed)))
                            # boss_defeated NOT incremented here —
                            # credit is only awarded on successful portal exit
                            break

            # Boss projectiles hit player only during FIGHT
            if boss and boss_phase == BossPhase.FIGHT:
                for bs in list(boss.skills):
                    if p_hit.colliderect(bs.rect) and not player.is_invincible():
                        if player.use_shield():
                            bs.kill()   # shield absorbs the bullet
                        else:
                            boss.skills.empty()
                            _play(resources['game_over_sound'])
                            return {'score': score, 'boss_defeated': boss_defeated}
                    elif bs.rect.right < 0:
                        skill_points = min(skill_points + 1, SKILL_POINT_THRESHOLD)
                        bs.kill()

        # ── exit portal (CLEAR phase) ─────────────────────────────────────────
        if boss_phase == BossPhase.CLEAR:
            portal = portal_group.sprite
            if portal is None:
                # Portal scrolled off screen — player was too slow → game over
                _play(resources['game_over_sound'])
                return {'score': score, 'boss_defeated': boss_defeated}
            if portal.rect.centerx <= player.rect.centerx:
                boss_defeated += 1
                score         += 50
                portal.kill()
                boss_phase    = BossPhase.NONE
                obstacles.empty()
                _perk_pending = True    # show perk selection after this frame

        # ── background scroll ─────────────────────────────────────────────────
        bg_x -= obstacle_speed
        if bg_x <= -bg_w:
            bg_x += bg_w

        # ── draw ──────────────────────────────────────────────────────────────
        bx = int(bg_x)
        screen.blit(bg, (bx,          0))
        screen.blit(bg, (bx + bg_w,   0))
        screen.blit(bg, (bx + bg_w*2, 0))

        floor.draw(screen)
        obstacles.draw(screen)
        portal_group.draw(screen)
        player.draw(screen)
        if boss:
            boss.draw(screen)

        # Red blink overlay during ENTRY (flips every 10 frames → 3 Hz)
        if boss_phase == BossPhase.ENTRY and (boss_entry_timer // 10) % 2 == 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((200, 0, 0, 80))
            screen.blit(flash, (0, 0))

        _draw_hud(screen, font, score, high_score, skill_points, boss_phase, player)

        # Capture frame before flip so perkSelect can use it as a frozen background
        _frozen = screen.copy() if _perk_pending else None
        pygame.display.flip()

        # Launch perk selection (blocking) with the just-rendered victory frame
        if _perk_pending:
            _perk_pending = False
            perkSelect.run(screen, clock, player, _frozen)

    return {'score': score, 'boss_defeated': boss_defeated}


# ── helpers ───────────────────────────────────────────────────────────────────

def _play(sound):
    if sound is None:
        return
    try:
        sound.play()
    except Exception as e:
        print(f"[SFX] playback error: {e}")


def _draw_hud(screen, font, score, high_score, skill_points, boss_phase, player):
    best = max(score, high_score)
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Best:  {best}",  True, (255, 215,   0)), (10, 45))
    screen.blit(font.render("Skill:",           True, (255, 255, 255)), (10, 80))

    # Skill pip bar — dims last N pips that are above the effective threshold
    eff_thr = max(1, SKILL_POINT_THRESHOLD - player.skill_threshold_bonus)
    pip_x   = 78
    for i in range(SKILL_POINT_THRESHOLD):
        if i < skill_points:
            col = (100, 220, 255)          # filled
        elif i >= eff_thr:
            col = (20, 20, 40)             # above effective threshold → greyed out
        else:
            col = (40, 40, 60)             # empty but reachable
        pygame.draw.rect(screen, col,          (pip_x + i * 22, 82, 18, 14))
        pygame.draw.rect(screen, (120, 120, 120),(pip_x + i * 22, 82, 18, 14), 1)

    # Shield indicator (below pip bar)
    if player.shield > 0:
        screen.blit(font.render("Shield:", True, (160, 170, 215)), (10, 105))
        for i in range(player.shield):
            # Flash gold during invincibility window
            flash = player.is_invincible() and (player.invincibility_timer // 8) % 2 == 0
            col = (255, 255, 100) if flash else (160, 170, 215)
            pygame.draw.rect(screen, col,          (78 + i * 22, 107, 16, 16))
            pygame.draw.rect(screen, (200, 210, 255),(78 + i * 22, 107, 16, 16), 1)

    cx = SCREEN_WIDTH // 2

    if boss_phase == BossPhase.ENTRY:
        lbl = font.render("!! BOSS INCOMING !!", True, (255, 60, 60))
        sub = font.render("Prepare yourself ...", True, (220, 180, 180))
        screen.blit(lbl, (cx - lbl.get_width() // 2, 10))
        screen.blit(sub, (cx - sub.get_width() // 2, 42))

    elif boss_phase == BossPhase.FIGHT:
        lbl = font.render("!! BOSS BATTLE !!", True, (255, 80, 80))
        sub = font.render("[J] fire  |  [ESC] flee (no credit)", True, (200, 220, 255))
        screen.blit(lbl, (cx - lbl.get_width() // 2, 10))
        screen.blit(sub, (cx - sub.get_width() // 2, 42))

    elif boss_phase == BossPhase.CLEAR:
        lbl = font.render("BOSS DEFEATED!  RUN TO EXIT >>>", True, (100, 255, 160))
        sub = font.render("[ESC] abandon — no credit awarded", True, (180, 180, 180))
        screen.blit(lbl, (cx - lbl.get_width() // 2, 10))
        screen.blit(sub, (cx - sub.get_width() // 2, 42))
