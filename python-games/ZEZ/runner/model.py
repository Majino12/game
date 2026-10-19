"""Deterministic, display-independent rules for ZEZ Skyline Rush.

All coordinates use pixels.  Entity positions are their top-left corner;
``player_y`` is the player's feet and ``PLAYER_X`` is the left edge.  The
renderer may run at any frame rate: simulation always advances at 120 Hz.
Input-generated sound events are delivered by the following ``update``.
"""

from dataclasses import dataclass
import math
import random
from typing import List, Optional, Tuple


WIDTH = 1280
HEIGHT = 720
GROUND = 580
PLAYER_X = 240
PLAYER_WIDTH = 52
PLAYER_HEIGHT = 72
SLIDE_HEIGHT = 32
GRAVITY = 2100.0
JUMP_VELOCITY = -800.0
DOUBLE_JUMP_VELOCITY = -720.0
FIXED_STEP = 1.0 / 120.0
OBSTACLES = frozenset(("crate", "spike", "drone"))
POWERUPS = frozenset(("magnet", "shield", "battery"))

Rect = Tuple[float, float, float, float]
Event = Tuple[str, float, float]


def _overlap(a: Rect, b: Rect) -> bool:
    return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0]
            and a[1] < b[1] + b[3] and a[1] + a[3] > b[1])


def _inset(rect: Rect, x: float, y: float) -> Rect:
    left, top, width, height = rect
    return (left + x, top + y, max(1.0, width - x * 2),
            max(1.0, height - y * 2))


def _decay(value: float, dt: float) -> float:
    # Avoid extending a 3.0-second timer by one frame because of float residue.
    return 0.0 if value <= dt + 1e-10 else value - dt


@dataclass
class Entity:
    kind: str
    x: float
    y: float
    w: float = 24.0
    h: float = 24.0
    passed: bool = False
    collected: bool = False

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.w, self.h)


@dataclass
class Boss:
    x: float = 1010.0
    y: float = 260.0
    w: float = 160.0
    h: float = 160.0
    hp: int = 160
    max_hp: int = 160
    phase: str = "warning"
    timer: float = 2.0
    telegraph: float = 0.0
    attack: str = "low"
    enraged: bool = False

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.w, self.h)


@dataclass
class Projectile:
    kind: str
    x: float
    y: float
    w: float = 20.0
    h: float = 10.0
    vx: float = 0.0
    vy: float = 0.0

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.w, self.h)


class Run:
    """One run. Create a new instance to restart without carrying timers over."""

    def __init__(self, seed: Optional[int] = None, bosses: bool = True):
        self.rng = random.Random(seed)
        self.time = 0.0
        self.distance = 0.0
        self.speed = 350.0
        self.score = 0
        self.coins = 0
        self.combo = 0
        self.best_combo = 0
        self.energy = 30.0
        self.shield = False
        self.magnet = 0.0
        self.dash_timer = 0.0
        self.bonus_timer = 0.0
        self.invulnerable = 0.0
        self.alive = True
        self.player_y = float(GROUND)
        self.player_vy = 0.0
        self.jumps = 0
        self.sliding = False
        self.entities: List[Entity] = []
        self.events: List[Event] = []
        self.dash_count = 0
        self.dodged = 0
        self.bosses_enabled = bool(bosses)
        self.boss: Optional[Boss] = None
        self.boss_defeated = 0
        self.next_boss_distance = 350.0
        self.projectiles: List[Projectile] = []

        self._pending_events: List[Event] = []
        self._accumulator = 0.0
        self._slide_held = False
        self._jump_buffer = 0.0
        self._since_coin = 0.0
        self._bonus_cooldown = 0.0
        self._next_bonus_combo = 30
        self._score_points = 0
        self._spawn_timer = 2.65
        self._pattern_count = 0
        self._last_obstacle_world_x = -10000.0
        self._fire_held = False
        self._fire_cooldown = 0.0
        self._boss_dash_hit = -1
        self._spawn_pattern()

    @property
    def player_rect(self) -> Rect:
        height = SLIDE_HEIGHT if self.sliding else PLAYER_HEIGHT
        return (float(PLAYER_X), self.player_y - height,
                float(PLAYER_WIDTH), float(height))

    @property
    def is_bonus(self) -> bool:
        return self.bonus_timer > 0.0

    @property
    def is_dashing(self) -> bool:
        return self.dash_timer > 0.0 or self.is_bonus

    @property
    def multiplier(self) -> int:
        return min(5, 1 + self.combo // 10)

    def _emit(self, name: str, x: Optional[float] = None,
              y: Optional[float] = None, pending: bool = False) -> None:
        event = (name, float(PLAYER_X + PLAYER_WIDTH / 2 if x is None else x),
                 float(self.player_y - 36 if y is None else y))
        (self._pending_events if pending else self.events).append(event)

    def jump(self) -> bool:
        """Jump or double jump. A late third press is buffered for landing."""
        if not self.alive:
            return False
        if self.jumps >= 2:
            self._jump_buffer = 0.10
            return False
        self.player_vy = JUMP_VELOCITY if self.jumps == 0 else DOUBLE_JUMP_VELOCITY
        self.jumps += 1
        self.sliding = False
        self._jump_buffer = 0.0
        self._emit("jump", pending=True)
        return True

    def set_slide(self, held: bool) -> None:
        """Hold to slide; pressing in the air accelerates the descent."""
        newly_pressed = bool(held) and not self._slide_held
        self._slide_held = bool(held)
        if not self.alive:
            return
        if self.jumps == 0 and self.player_y >= GROUND:
            self.sliding = self._slide_held
        elif newly_pressed:
            self.player_vy = max(self.player_vy, 900.0)

    def dash(self) -> bool:
        """Spend a full energy bar for three seconds of protected running."""
        if not self.alive or self.energy < 100.0 or self.is_dashing:
            return False
        self.energy = 0.0
        self.dash_timer = 3.0
        self.dash_count += 1
        self._clear_obstacles()
        self._emit("dash", pending=True)
        self._dash_boss(pending=True)
        return True

    def set_fire(self, held: bool) -> None:
        """Hold to fire automatically when a boss is ready to fight."""
        self._fire_held = bool(held)

    def fire(self) -> bool:
        """Fire once if the boss is active and the shared cooldown is ready."""
        return self._fire(pending=True)

    def _fire(self, pending: bool = False) -> bool:
        boss = self.boss
        if (not self.alive or boss is None or boss.phase not in ("fight", "weak")
                or self._fire_cooldown > 0.0):
            return False
        x = float(PLAYER_X + PLAYER_WIDTH + 4)
        y = self.player_y - (16.0 if self.sliding else 36.0)
        dx, dy = boss.x + boss.w / 2 - x, boss.y + boss.h / 2 - y
        length = max(1.0, math.hypot(dx, dy))
        self.projectiles.append(Projectile("shot", x, y - 5.0, 20.0, 10.0,
                                           dx / length * 1000.0, dy / length * 1000.0))
        self._fire_cooldown = 0.25
        self._emit("shot", x, y, pending=pending)
        return True

    def update(self, dt: float) -> None:
        """Advance at most 0.1 s, replacing events with this update's events."""
        self.events.clear()
        self.events.extend(self._pending_events)
        self._pending_events.clear()
        if not self.alive or not math.isfinite(dt) or dt <= 0.0:
            return
        self._accumulator += min(float(dt), 0.1)
        while self._accumulator + 1e-12 >= FIXED_STEP and self.alive:
            self._accumulator -= FIXED_STEP
            self._step(FIXED_STEP)
        if not self.alive:
            self._accumulator = 0.0

    def _step(self, dt: float) -> None:
        self.time += dt
        self.speed = min(620.0, 350.0 + self.time * 1.65)
        # A dash really accelerates the world; ordinary difficulty still caps
        # at 620 px/s. Hazards are cleared while this temporary boost is active.
        boost = 1.55 if self.dash_timer > 0.0 else 1.25 if self.is_bonus else 1.0
        travel = self.speed * boost * dt
        self.distance += travel / 25.0

        old_dash, old_bonus = self.dash_timer, self.bonus_timer
        self.dash_timer = _decay(self.dash_timer, dt)
        self.bonus_timer = _decay(self.bonus_timer, dt)
        self.magnet = _decay(self.magnet, dt)
        self.invulnerable = _decay(self.invulnerable, dt)
        self._bonus_cooldown = _decay(self._bonus_cooldown, dt)
        if ((old_dash > 0.0 and self.dash_timer <= 0.0)
                or (old_bonus > 0.0 and self.bonus_timer <= 0.0)):
            self.invulnerable = max(self.invulnerable, 0.8)
            # A clear runway makes the transition from autopilot readable.
            self._clear_obstacles(PLAYER_X + self.speed * 1.2)
            self._spawn_timer = max(self._spawn_timer, 1.2)

        self._since_coin += dt
        if self._since_coin > 3.0 and self.combo:
            self.combo = 0
            self._next_bonus_combo = 30

        if self.jumps > 0 or self.player_y < GROUND:
            self.player_vy += GRAVITY * dt
            self.player_y += self.player_vy * dt
            if self.player_y >= GROUND:
                self.player_y = float(GROUND)
                self.player_vy = 0.0
                self.jumps = 0
                self.sliding = self._slide_held
                if self._jump_buffer > 0.0:
                    self.player_vy = JUMP_VELOCITY
                    self.jumps = 1
                    self.sliding = False
                    self._jump_buffer = 0.0
                    self._emit("jump")
        else:
            self.sliding = self._slide_held
        self._jump_buffer = max(0.0, self._jump_buffer - dt)

        entered_boss = self._maybe_start_boss()
        if self.boss is not None:
            if not entered_boss:
                self._update_boss(dt)
        else:
            self._spawn_timer -= dt
            if self._spawn_timer <= 0.0:
                self._spawn_pattern()
                self._spawn_timer += self.rng.uniform(2.45, 2.95)

        self._fire_cooldown = _decay(self._fire_cooldown, dt)
        self._dash_boss()
        if self._fire_held:
            self._fire()

        player_hit = _inset(self.player_rect, 9.0, 5.0)
        for entity in self.entities:
            if entity.collected:
                continue
            entity.x -= travel
            if entity.kind == "coin":
                self._attract_coin(entity, dt)
                if _overlap(self.player_rect, entity.rect):
                    self._collect_coin(entity)
            elif entity.kind in POWERUPS:
                if _overlap(self.player_rect, entity.rect):
                    self._collect_powerup(entity)

        # Pickups are resolved first, allowing a shield obtained on the same
        # fixed step as a hazard to protect the player.
        for entity in self.entities:
            if entity.collected or entity.kind not in OBSTACLES:
                continue
            if self.is_dashing:
                entity.collected = True
                continue
            hazard_hit = _inset(entity.rect, 7.0, 5.0)
            if _overlap(player_hit, hazard_hit) and self.invulnerable <= 0.0:
                if self.shield:
                    self.shield = False
                    self.invulnerable = 0.9
                    entity.collected = True
                    self._emit("shield", entity.x + entity.w / 2,
                               entity.y + entity.h / 2)
                else:
                    self.alive = False
                    self._emit("hit")
                    break
            if entity.x + entity.w < PLAYER_X and not entity.passed:
                entity.passed = True
                self.dodged += 1
                self._score_points += 25
                self.energy = min(100.0, self.energy + 4.0)

        self.entities[:] = [e for e in self.entities
                            if not e.collected and e.x + e.w > -100.0]
        if self.alive:
            self._update_projectiles(dt)
        self.score = int(self.distance * 5.0) + self._score_points

    def _maybe_start_boss(self) -> bool:
        if (not self.bosses_enabled or self.boss is not None or not self.alive
                or self.distance < self.next_boss_distance or self.is_dashing):
            return False
        self.boss = Boss()
        self._clear_obstacles()
        self.projectiles.clear()
        self._fire_cooldown = 0.0
        self.invulnerable = max(self.invulnerable, 2.0)
        self._emit("boss_warning", self.boss.x + self.boss.w / 2,
                   self.boss.y + self.boss.h / 2)
        return True

    def _update_boss(self, dt: float) -> None:
        boss = self.boss
        if boss is None:
            return
        boss.timer = _decay(boss.timer, dt)
        if boss.phase == "warning":
            if boss.timer == 0.0:
                boss.phase = "fight"
                boss.timer = 1.35
                boss.telegraph = boss.timer
        elif boss.phase == "fight":
            boss.telegraph = boss.timer
            if boss.timer == 0.0:
                self._boss_attack()
                boss.phase = "weak"
                boss.timer = 2.5
                boss.telegraph = 0.0
        elif boss.phase == "weak":
            if boss.timer == 0.0:
                boss.attack = "high" if boss.attack == "low" else "low"
                boss.phase = "fight"
                boss.timer = 1.0 if boss.enraged else 1.35
                boss.telegraph = boss.timer
        elif boss.phase == "defeated" and boss.timer == 0.0:
            self.boss = None
            self.projectiles.clear()
            self._spawn_timer = 2.0
            self._last_obstacle_world_x = self.distance * 25.0 - 1000.0
            self.invulnerable = max(self.invulnerable, 1.0)

    def _boss_attack(self) -> None:
        boss = self.boss
        if boss is None:
            return
        speed = 560.0 if boss.enraged else 500.0
        if boss.attack == "low":
            wave = Projectile("boss_low", boss.x, GROUND - 44.0,
                              82.0, 44.0, -speed, 0.0)
        else:
            # The top wave hits a standing body but leaves a clear slide lane.
            wave = Projectile("boss_high", boss.x, GROUND - 112.0,
                              92.0, 62.0, -speed, 0.0)
        self.projectiles.append(wave)
        self._emit("boss_attack", wave.x + wave.w / 2, wave.y + wave.h / 2)

    def _dash_boss(self, pending: bool = False) -> None:
        if (self.boss is not None and self.boss.phase in ("fight", "weak")
                and self.dash_timer > 0.0 and self._boss_dash_hit != self.dash_count):
            # A dash begun during the entrance can still strike when the armor
            # becomes targetable, but its counter can never damage twice.
            self._boss_dash_hit = self.dash_count
            self._damage_boss(25, pending=pending)

    def _damage_boss(self, amount: int, pending: bool = False) -> None:
        boss = self.boss
        if boss is None or boss.phase not in ("fight", "weak") or amount <= 0:
            return
        boss.hp = max(0, boss.hp - amount)
        boss.enraged = boss.hp < boss.max_hp * 0.5
        self._emit("boss_hit", boss.x + boss.w / 2, boss.y + boss.h / 2,
                   pending=pending)
        if boss.hp == 0:
            self._defeat_boss(pending=pending)

    def _defeat_boss(self, pending: bool = False) -> None:
        boss = self.boss
        if boss is None or boss.phase == "defeated":
            return
        boss.hp = 0
        boss.phase = "defeated"
        boss.timer = 2.5
        boss.telegraph = 0.0
        self.projectiles.clear()
        self._clear_obstacles()
        self.boss_defeated += 1
        self.coins += 50
        self._score_points += 500
        self.shield = True
        self.energy = 100.0
        self.invulnerable = max(self.invulnerable, 2.5)
        self.next_boss_distance = self.distance + 600.0
        self.score = int(self.distance * 5.0) + self._score_points
        self._emit("boss_defeated", boss.x + boss.w / 2, boss.y + boss.h / 2,
                   pending=pending)

    def _update_projectiles(self, dt: float) -> None:
        # Resolve outgoing shots first: a winning hit removes an incoming wave
        # on the same physics step, so victory cannot become a surprise death.
        ordered = ([p for p in self.projectiles if p.kind == "shot"]
                   + [p for p in self.projectiles if p.kind != "shot"])
        survivors = []
        player_hit = _inset(self.player_rect, 9.0, 5.0)
        for projectile in ordered:
            projectile.x += projectile.vx * dt
            projectile.y += projectile.vy * dt
            if (projectile.x + projectile.w < -100.0 or projectile.x > WIDTH + 100.0
                    or projectile.y + projectile.h < -100.0 or projectile.y > HEIGHT + 100.0):
                continue
            boss = self.boss
            if projectile.kind == "shot":
                if boss is None or boss.phase not in ("fight", "weak"):
                    continue
                if _overlap(projectile.rect, boss.rect):
                    self._damage_boss(8 if boss.phase == "weak" else 2)
                    continue
            else:
                if boss is not None and boss.phase == "defeated":
                    continue
                if _overlap(player_hit, _inset(projectile.rect, 5.0, 4.0)):
                    if not self.is_dashing and self.invulnerable <= 0.0:
                        if self.shield:
                            self.shield = False
                            self.invulnerable = 0.9
                            self._emit("shield", projectile.x, projectile.y)
                        else:
                            self.alive = False
                            self._emit("hit")
                            break
                    continue
            survivors.append(projectile)
        if self.boss is not None and self.boss.phase == "defeated":
            survivors.clear()
        self.projectiles[:] = survivors

    def _attract_coin(self, coin: Entity, dt: float) -> None:
        cx, cy = coin.x + coin.w / 2, coin.y + coin.h / 2
        px = PLAYER_X + PLAYER_WIDTH / 2
        py = self.player_y - (16.0 if self.sliding else 36.0)
        dx, dy = px - cx, py - cy
        distance = math.hypot(dx, dy)
        bonus_reach = self.is_bonus and coin.x < WIDTH + 100
        if not bonus_reach and not ((self.magnet > 0.0 or self.dash_timer > 0.0) and distance < 310.0):
            return
        rate = 1500.0 if bonus_reach else 850.0
        if distance > 0.0:
            factor = min(1.0, rate * dt / distance)
            coin.x += dx * factor
            coin.y += dy * factor

    def _collect_coin(self, coin: Entity) -> None:
        coin.collected = True
        self.coins += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self._since_coin = 0.0
        self.energy = min(100.0, self.energy + 3.0)
        self._score_points += 10 * self.multiplier
        self._emit("coin", coin.x + coin.w / 2, coin.y + coin.h / 2)
        if (self.combo >= self._next_bonus_combo and not self.is_dashing
                and self.boss is None
                and self._bonus_cooldown <= 0.0):
            self.bonus_timer = 8.0
            self._bonus_cooldown = 20.0
            self._next_bonus_combo = self.combo + 30
            self._clear_obstacles()
            self._spawn_timer = min(self._spawn_timer, 0.4)
            self._emit("bonus")

    def _collect_powerup(self, entity: Entity) -> None:
        entity.collected = True
        if entity.kind == "magnet":
            self.magnet = 7.0
        elif entity.kind == "shield":
            self.shield = True
        elif entity.kind == "battery":
            self.energy = min(100.0, self.energy + 35.0)
        self._emit("power", entity.x + entity.w / 2, entity.y + entity.h / 2)

    def _clear_obstacles(self, before_x: Optional[float] = None) -> None:
        # Mark rather than deleting: this is safe during a coin collection loop.
        for entity in self.entities:
            if entity.kind in OBSTACLES and (before_x is None or entity.x < before_x):
                entity.collected = True

    def _coin(self, center_x: float, center_y: float) -> None:
        self.entities.append(Entity("coin", center_x - 12.0, center_y - 12.0))

    def _spawn_pattern(self) -> None:
        """One readable action per segment; never mix a low roof with a jump."""
        if self.boss is not None:
            return
        base = float(WIDTH + 120)
        if self.is_bonus:
            for column in range(7):
                for row in range(3):
                    self._coin(base + column * 54.0, GROUND - 60.0 - row * 55.0)
            return

        index = self._pattern_count
        self._pattern_count += 1
        # The first fifteen seconds introduce one obstacle type at a time.
        if self.time < 15.0:
            kind = ("crate", "drone", "crate", "spike", "drone", "crate")[index % 6]
        else:
            kind = self.rng.choice(("crate", "crate", "spike", "drone", "drone"))

        # Even after a bonus interrupted spawning, no hazard can appear too
        # close to its predecessor. Extra speed margin covers acceleration
        # during the approach from the right edge.
        world_px = self.distance * 25.0
        minimum_gap = (self.speed + 15.0) * 2.15 + 90.0
        base = max(base, self._last_obstacle_world_x + minimum_gap - world_px)
        self._last_obstacle_world_x = world_px + base
        if kind == "drone":
            self.entities.append(Entity(kind, base, GROUND - 104.0, 88.0, 52.0))
            for offset in range(-3, 5):
                self._coin(base + 44.0 + offset * 42.0, GROUND - 26.0)
        else:
            width, height = (62.0, 64.0) if kind == "crate" else (74.0, 40.0)
            self.entities.append(Entity(kind, base, GROUND - height, width, height))
            # Coins trace a jump, rewarding the player for following the arc.
            half_span = max(155.0, self.speed * 0.39)
            for i in range(9):
                fraction = i / 8.0
                self._coin(base + width / 2.0 + (fraction * 2.0 - 1.0) * half_span,
                           GROUND - 65.0 - math.sin(fraction * math.pi) * 135.0)

        # Predictable early help, then a rotating reward every third segment.
        if index % 3 == 1:
            power = ("magnet", "shield", "battery")[(index // 3) % 3]
            self.entities.append(Entity(power, base + 260.0, GROUND - 56.0, 36.0, 36.0))
        # A short low trail connects segments, keeping the combo achievable.
        for offset in (260.0, 310.0, 360.0):
            self._coin(base + offset, GROUND - 29.0)
