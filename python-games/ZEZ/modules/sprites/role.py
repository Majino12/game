import pygame
from enum import Enum, auto
from consts import (
    SCREEN_HEIGHT, GROUND_Y, FPS,
    GRAVITY, PLAYER_JUMP_VEL, DOUBLE_JUMP_VEL,
    ANIM_INTERVAL, HITBOX_INSET_X, HITBOX_INSET_Y,
    SKILL_POINT_THRESHOLD, SCREEN_WIDTH,
)


class State(Enum):
    RUN    = auto()
    JUMP   = auto()
    DJUMP  = auto()   # mid-air after double-jump (or extra jump)
    FALL   = auto()   # descending after single jump apex
    CROUCH = auto()
    HIT    = auto()


class Player(pygame.sprite.Sprite):
    def __init__(self, images, skill_image):
        super().__init__()
        self.run_images   = images['run']
        self.jump_image   = images['jump']
        self.crouch_image = images['crouch']
        self.skill_image  = skill_image

        self.image = self.run_images[0]
        self.rect  = self.image.get_rect(x=100, bottom=GROUND_Y)

        self.velocity  = 0.0
        self.state     = State.RUN
        self.run_frame = 0
        self.anim_tick = 0
        self.skills    = pygame.sprite.Group()

        # ── Perk-modifiable attributes (all at neutral / off values) ──────────
        # Jump
        self.jump_vel_bonus        = 0      # additive to PLAYER_JUMP_VEL (negative = higher)
        self.djump_vel_bonus       = 0      # additive to DOUBLE_JUMP_VEL
        self.extra_jump            = 0      # bonus air-jumps beyond the standard double-jump
        self.air_jumps_left        = 0      # resets to extra_jump each time player lands
        # Skill
        self.skill_power_mult      = 1.0    # multiplier on SKILL_DAMAGE
        self.skill_threshold_bonus = 0      # reduces effective SKILL_POINT_THRESHOLD (min 1)
        self.max_skills_bonus      = 0      # extra concurrent skill projectiles allowed
        # Defence
        self.shield                = 0      # absorbs N fatal hits before death
        self.invincibility_timer   = 0      # post-shield grace frames
        # Scoring
        self.score_bonus           = 0      # extra score per obstacle cleared

    # ── public API ────────────────────────────────────────────────────────────

    def jump(self):
        if self.state in (State.RUN, State.CROUCH):
            self._do_jump(PLAYER_JUMP_VEL + self.jump_vel_bonus)
        elif self.state in (State.JUMP, State.FALL):
            # Standard double-jump
            self.velocity = DOUBLE_JUMP_VEL + self.djump_vel_bonus
            self.state    = State.DJUMP
        elif self.state == State.DJUMP and self.air_jumps_left > 0:
            # Extra jump(s) granted by Air Master perk
            self.air_jumps_left -= 1
            self.velocity        = DOUBLE_JUMP_VEL + self.djump_vel_bonus
            # Keep DJUMP state — same airborne animation

    def crouch(self):
        if self.state == State.RUN:
            self.state = State.CROUCH
            scaled = pygame.transform.scale(
                self.crouch_image, (self.rect.width, self.rect.height // 2)
            )
            self.image = scaled
            self.rect  = self.image.get_rect(midbottom=self.rect.midbottom)

    def stand_up(self):
        if self.state == State.CROUCH:
            self.state = State.RUN
            self.image = self.run_images[0]
            self.rect  = self.image.get_rect(midbottom=self.rect.midbottom)

    def fire_skill(self):
        effective_max = SKILL_POINT_THRESHOLD + self.max_skills_bonus
        if len(self.skills) < effective_max:
            self.skills.add(Skill(self.rect.right, self.rect.centery, self.skill_image))

    def hit_rect(self):
        return self.rect.inflate(-HITBOX_INSET_X * 2, -HITBOX_INSET_Y * 2)

    def is_invincible(self) -> bool:
        return self.invincibility_timer > 0

    def use_shield(self) -> bool:
        """Consume one shield charge and open a 1-second invincibility window.
        Returns True if the hit was absorbed, False if no shield remains."""
        if self.shield > 0:
            self.shield             -= 1
            self.invincibility_timer = FPS   # 60 frames = 1 second
            return True
        return False

    # ── main loop hooks ───────────────────────────────────────────────────────

    def update(self):
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
        self._physics()
        self._animate()
        self.skills.update()

    def draw(self, screen):
        # Blink when invincible: hide every other 4-frame window
        visible = not (self.invincibility_timer > 0
                       and (self.invincibility_timer // 4) % 2 == 0)
        if visible:
            screen.blit(self.image, self.rect)
        self.skills.draw(screen)

    # ── internal ──────────────────────────────────────────────────────────────

    def _do_jump(self, vel):
        if self.state == State.CROUCH:
            self.image = self.run_images[0]
            self.rect  = self.image.get_rect(midbottom=self.rect.midbottom)
        self.velocity = vel
        self.state    = State.JUMP

    def _physics(self):
        if self.state not in (State.JUMP, State.DJUMP, State.FALL):
            return

        self.velocity += GRAVITY
        self.rect.y   += int(self.velocity)

        if self.velocity > 0 and self.state == State.JUMP:
            self.state = State.FALL

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom    = GROUND_Y
            self.velocity       = 0.0
            self.state          = State.RUN
            self.air_jumps_left = self.extra_jump   # restore on landing

    def _animate(self):
        if self.state in (State.JUMP, State.DJUMP, State.FALL):
            self.image = self.jump_image
            return
        if self.state == State.CROUCH:
            return   # image already set in crouch()
        self.anim_tick += 1
        if self.anim_tick >= ANIM_INTERVAL:
            self.anim_tick = 0
            self.run_frame = (self.run_frame + 1) % len(self.run_images)
        self.image = self.run_images[self.run_frame]


class Skill(pygame.sprite.Sprite):
    SPEED = 12

    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect  = self.image.get_rect(x=x, centery=y)

    def update(self):
        self.rect.x += self.SPEED
        if self.rect.left > SCREEN_WIDTH:
            self.kill()
