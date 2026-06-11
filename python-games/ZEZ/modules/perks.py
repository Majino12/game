import random


class Perk:
    """Single perk definition.  apply(player) mutates the Player in-place."""

    def __init__(self, id: str, name: str, description: str, color: tuple, apply_fn):
        self.id          = id
        self.name        = name
        self.description = description   # shown on the card
        self.color       = color         # (R, G, B) accent colour for the card
        self._fn         = apply_fn

    def apply(self, player) -> None:
        self._fn(player)

    def __repr__(self):
        return f"Perk({self.id!r})"


# ── Perk effects (kept as free functions to stay testable without a Player) ───

def _leap(p):
    p.jump_vel_bonus       -= 4          # PLAYER_JUMP_VEL -18 → -22  (+22 % height)

def _bounce(p):
    p.djump_vel_bonus      -= 5          # DOUBLE_JUMP_VEL -15 → -20  (+33 % height)

def _air_master(p):
    p.extra_jump           += 1          # +1 air-jump after double-jump
    p.air_jumps_left        = p.extra_jump

def _power_surge(p):
    p.skill_power_mult     *= 2.0        # ×2 SKILL_DAMAGE (stackable: ×2, ×4, …)

def _iron_shield(p):
    p.shield               += 1          # absorbs 1 fatal hit

def _twin_shield(p):
    p.shield               += 2          # absorbs 2 fatal hits

def _quick_charge(p):
    p.skill_threshold_bonus += 1         # effective threshold = max(1, 5 - bonus)

def _rapid_fire(p):
    p.max_skills_bonus     += 2          # up to 7 concurrent skill projectiles

def _score_hunt(p):
    p.score_bonus          += 1          # each cleared obstacle gives +1 extra point


# ── Full perk pool ────────────────────────────────────────────────────────────

ALL_PERKS: list = [
    Perk(
        "leap",        "도약 강화",
        "점프 높이가 크게 증가합니다",
        (0,   180, 255), _leap,
    ),
    Perk(
        "bounce",      "이중 도약",
        "더블 점프 높이가 향상됩니다",
        (0,   230, 200), _bounce,
    ),
    Perk(
        "air_master",  "에어 마스터",
        "공중에서 1회 추가 점프 가능",
        (100, 255, 120), _air_master,
    ),
    Perk(
        "power_surge", "파워 서지",
        "스킬 데미지가 2배가 됩니다",
        (255, 110,  30), _power_surge,
    ),
    Perk(
        "iron_shield", "철갑 방어막",
        "치명타 1회를 막아줍니다",
        (160, 170, 215), _iron_shield,
    ),
    Perk(
        "twin_shield", "이중 방어막",
        "치명타 2회를 막아줍니다",
        (180,  80, 255), _twin_shield,
    ),
    Perk(
        "quick_charge","빠른 충전",
        "스킬 충전 필요량이 1 감소합니다",
        (230, 200,   0), _quick_charge,
    ),
    Perk(
        "rapid_fire",  "연속 사격",
        "동시 발사 슬롯이 2 증가합니다",
        (255,  60,  60), _rapid_fire,
    ),
    Perk(
        "score_hunt",  "점수 사냥꾼",
        "장애물 처리 시 득점 +1 추가",
        (255, 215,   0), _score_hunt,
    ),
]


def pick3() -> list:
    """Return 3 distinct random Perks from ALL_PERKS."""
    return random.sample(ALL_PERKS, k=3)
