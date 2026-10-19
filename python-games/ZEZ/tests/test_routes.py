"""Map selection is deterministic, safe to defer, and independent of frames."""

from collections import Counter
import math
import random
import unittest

from runner.routes import MAPS, Route


def visits(seed, count):
    route = Route(seed)
    for _ in range(count - 1):
        route.maybe_advance(route.next_distance, safe=True)
    return route.order


class RouteTests(unittest.TestCase):
    def test_initial_map_and_metadata_are_ready_without_advancing(self):
        route = Route(seed=17)
        self.assertEqual(route.key, "meadow")
        self.assertIs(route.current, MAPS["meadow"])
        self.assertEqual(route.order, ["meadow"])
        self.assertEqual(route.next_distance, 500)
        self.assertEqual(set(MAPS), {"meadow", "dunes", "grove", "ruins"})
        for key, spec in MAPS.items():
            with self.subTest(map=key):
                for field in ("name", "name_en", "hint", "hint_en"):
                    self.assertTrue(spec[field])
                self.assertEqual(spec["gravity"], 1650 if key == "ruins" else 2100)
                self.assertEqual(spec["coin_height_bonus"], 45 if key == "ruins" else 0)
                self.assertTrue(spec["theme"])
                self.assertTrue(spec["tile_theme"])
                self.assertTrue(all(color.startswith('#') and len(color) == 7
                                    for color in spec["palette"].values()))

    def test_same_seed_reproduces_a_long_route_and_other_seeds_vary(self):
        self.assertEqual(visits(77, 80), visits(77, 80))
        self.assertGreater(len({tuple(visits(seed, 12)) for seed in range(12)}), 1)
        self.assertEqual(visits(0, 16), visits(0, 16), "Seed zero must not be treated as missing")

    def test_each_shuffle_bag_visits_all_maps_without_adjacent_repeats(self):
        for seed in range(30):
            with self.subTest(seed=seed):
                order = visits(seed, 80)
                self.assertTrue(all(left != right for left, right in zip(order, order[1:])))
                for start in range(0, len(order), 4):
                    self.assertEqual(set(order[start:start + 4]), set(MAPS))

    def test_route_does_not_consume_global_or_main_run_randomness(self):
        global_before = random.getstate()
        main_rng = random.Random(77)
        expected = random.Random(77)
        route = Route(77)
        self.assertIsInstance(route.rng, random.Random)
        for _ in range(20):
            route.maybe_advance(route.next_distance, safe=True)
            self.assertEqual(main_rng.random(), expected.random())
        self.assertEqual(random.getstate(), global_before)

    def test_threshold_waits_for_safe_ground_and_restarts_from_actual_distance(self):
        route = Route(5)
        self.assertFalse(route.maybe_advance(499.99, safe=True))
        self.assertFalse(route.maybe_advance(500, safe=False))
        self.assertFalse(route.maybe_advance(975, safe=False))
        self.assertEqual(route.order, ["meadow"])
        self.assertEqual(route.next_distance, 500)
        self.assertTrue(route.maybe_advance(975, safe=True))
        self.assertEqual(len(route.order), 2)
        self.assertEqual(route.next_distance, 1475)
        self.assertFalse(route.maybe_advance(975, safe=True))
        self.assertFalse(route.maybe_advance(1474.99, safe=True))
        self.assertTrue(route.maybe_advance(1475, safe=True))

    def test_long_delay_changes_only_one_map_instead_of_catching_up(self):
        route = Route(9)
        self.assertTrue(route.maybe_advance(10000, safe=True))
        self.assertEqual(len(route.order), 2)
        self.assertEqual(route.next_distance, 10500)
        for _ in range(100):
            self.assertFalse(route.maybe_advance(10000, safe=True))
        self.assertEqual(len(route.order), 2)

    def test_unsafe_and_invalid_queries_do_not_change_the_planned_sequence(self):
        route, reference = Route(42), Route(42)
        for invalid in (None, True, False, -1, "500", [], math.nan,
                        math.inf, -math.inf, 10 ** 1000, 1e100):
            self.assertFalse(route.maybe_advance(invalid, safe=True))
        for distance in range(0, 10000, 17):
            self.assertFalse(route.maybe_advance(distance, safe=False))
        self.assertEqual(route.rng.getstate(), reference.rng.getstate())
        self.assertEqual(route.order, reference.order)
        for _ in range(16):
            route.maybe_advance(route.next_distance, safe=True)
            reference.maybe_advance(reference.next_distance, safe=True)
        self.assertEqual(route.order, reference.order)

    def test_same_distance_schedule_has_same_route_at_30_60_and_144_fps(self):
        results = []
        for fps in (30, 60, 144):
            route = Route(19)
            for frame in range(1, 40 * fps + 1):
                # Distance is measured independently of how often we query it.
                route.maybe_advance(frame * 50 / fps, safe=True)
            results.append((route.order, route.key, route.next_distance))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertEqual(len(results[0][0]), 5)
        self.assertEqual(results[0][2], 2500)

    def test_weighted_obstacle_pools_have_distinct_map_profiles(self):
        counts = {key: Counter(spec["obstacle_pool"]) for key, spec in MAPS.items()}
        for spec in MAPS.values():
            self.assertIsInstance(spec["obstacle_pool"], tuple)
            self.assertEqual(set(spec["obstacle_pool"]), {"crate", "spike", "drone"})
        self.assertGreater(counts["meadow"]["crate"], counts["meadow"]["spike"])
        self.assertGreater(counts["dunes"]["spike"], counts["dunes"]["crate"])
        self.assertGreater(counts["grove"]["drone"], counts["grove"]["crate"])
        self.assertEqual(counts["ruins"]["crate"], counts["ruins"]["drone"])
        self.assertGreater(counts["ruins"]["crate"], counts["ruins"]["spike"])

    def test_special_rewards_are_periodic_pure_queries_for_each_map(self):
        expected = {"meadow": "spring", "dunes": "treasure",
                    "grove": "glow", "ruins": "air_coins"}
        route = Route(7)
        seen = set()
        for _ in range(4):
            seen.add(route.key)
            before = (route.rng.getstate(), list(route.order), route.next_distance)
            for index in range(16):
                kind = expected[route.key] if index % 4 == 3 else None
                self.assertEqual(route.special_kind(index), kind)
                spec = route.pattern_spec(index, time=999)
                self.assertEqual(spec["special"], kind)
                self.assertEqual(spec["obstacle_pool"], route.obstacle_pool)
                self.assertEqual(spec["gravity"], route.current["gravity"])
                self.assertEqual(spec, route.pattern_spec(index, time=0))
            for invalid in (None, True, -1, 3.0, "3"):
                self.assertIsNone(route.special_kind(invalid))
            self.assertEqual((route.rng.getstate(), route.order, route.next_distance), before)
            route.maybe_advance(route.next_distance, safe=True)
        self.assertEqual(seen, set(MAPS))


if __name__ == "__main__":
    unittest.main()
