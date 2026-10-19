"""Display-independent map progression, isolated from the run's random stream.

The run supplies the actual distance and decides when changing maps is safe.
This module selects metadata and pattern candidates; it creates no entities,
changes no physics state, and applies no pickup rewards.
"""

import math
import random
from typing import Optional, Tuple


MAP_INTERVAL = 500.0
MAPS = {
    "meadow": {
        "name": "云野", "name_en": "Cloud Meadow",
        "hint": "可选弹簧带你跃向奖励金币", "hint_en": "Optional spring pads lift you toward bonus coins.",
        "gravity": 2100.0, "coin_height_bonus": 0.0,
        "theme": "hills", "tile_theme": "grass",
        "palette": {"sky": "#ddf4ec", "sun": "#f7f9d5", "soil": "#c98454", "accent": "#126f5b"},
        "obstacle_pool": ("crate", "crate", "drone", "spike"),
        "special": "spring",
    },
    "dunes": {
        "name": "流金沙丘", "name_en": "Golden Dunes",
        "hint": "拾取宝箱，补充金币与冲刺能量", "hint_en": "Open chests for coins and dash energy.",
        "gravity": 2100.0, "coin_height_bonus": 0.0,
        "theme": "desert", "tile_theme": "sand",
        "palette": {"sky": "#f4e5d1", "sun": "#fff4cd", "soil": "#c9a16e", "accent": "#ae703b"},
        "obstacle_pool": ("crate", "spike", "spike", "drone"),
        "special": "treasure",
    },
    "grove": {
        "name": "荧光林地", "name_en": "Glow Grove",
        "hint": "荧光球补充能量，并短暂吸引金币", "hint_en": "Catch glow orbs for energy and a brief magnet.",
        "gravity": 2100.0, "coin_height_bonus": 0.0,
        "theme": "trees", "tile_theme": "purple",
        "palette": {"sky": "#e3edf5", "sun": "#f1f8dc", "soil": "#8f9aaf", "accent": "#497d87"},
        "obstacle_pool": ("drone", "drone", "crate", "spike"),
        "special": "glow",
    },
    "ruins": {
        "name": "浮空遗迹", "name_en": "Floating Ruins",
        "hint": "重力更轻，跃向更高的金币路线", "hint_en": "Lower gravity carries you toward high coin trails.",
        "gravity": 1650.0, "coin_height_bonus": 45.0,
        "theme": "hills", "tile_theme": "purple",
        "palette": {"sky": "#e4e0f5", "sun": "#fff5e3", "soil": "#b589ae", "accent": "#765a99"},
        "obstacle_pool": ("crate", "crate", "drone", "drone", "spike"),
        "special": "air_coins",
    },
}


class Route:
    """A seeded shuffle bag of maps, with an explicit safe transition gate.

    The first group starts with meadow and visits each other map once. Every
    subsequent group visits all four maps in shuffled order. Adjacent groups
    are adjusted to avoid repeating the map at the boundary.
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.key = "meadow"
        self.order = [self.key]
        self.next_distance = MAP_INTERVAL
        self._bag = [key for key in MAPS if key != self.key]
        self.rng.shuffle(self._bag)

    @property
    def current(self) -> dict:
        """Metadata for the active map; gravity is an absolute px/s² value."""
        return MAPS[self.key]

    @property
    def obstacle_pool(self) -> Tuple[str, ...]:
        """Weighted candidates; the model chooses using its own run RNG."""
        return self.current["obstacle_pool"]

    def special_kind(self, index: int) -> Optional[str]:
        """Return a reward on zero-based segment 3, 7, 11, ... without RNG."""
        if type(index) is not int or index < 0 or index % 4 != 3:
            return None
        return self.current["special"]

    def pattern_spec(self, index: int, time: float = 0.0) -> dict:
        """Pure metadata query; time is reserved for the caller's tutorial.

        The route deliberately does not select an obstacle or consume random
        numbers here. Introductory patterns and entities belong to the model.
        """
        return {"key": self.key, "obstacle_pool": self.obstacle_pool,
                "special": self.special_kind(index),
                "gravity": self.current["gravity"],
                "coin_height_bonus": self.current["coin_height_bonus"]}

    def maybe_advance(self, distance: float, safe: bool) -> bool:
        """Change at most one map, measuring the next interval from this point.

        A deferred transition never catches up through multiple maps. The run
        should pass safe=True only on ordinary ground outside a dash, bonus,
        boss encounter, or other state that must finish before a transition.
        """
        if safe is not True or type(distance) not in (int, float) or distance < 0:
            return False
        try:
            actual_distance = float(distance)
        except (OverflowError, ValueError):
            return False
        if not math.isfinite(actual_distance) or actual_distance < self.next_distance:
            return False
        next_distance = actual_distance + MAP_INTERVAL
        if not math.isfinite(next_distance) or next_distance <= actual_distance:
            return False
        if not self._bag:
            self._bag = list(MAPS)
            self.rng.shuffle(self._bag)
            if self._bag[0] == self.key:
                other = self.rng.randrange(1, len(self._bag))
                self._bag[0], self._bag[other] = self._bag[other], self._bag[0]
        self.key = self._bag.pop(0)
        self.order.append(self.key)
        self.next_distance = next_distance
        return True
