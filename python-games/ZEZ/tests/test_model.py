"""Headless tests of player-visible rules and procedural course playability."""

import math
import unittest

from runner.model import (
    Entity, FIXED_STEP, GROUND, OBSTACLES, PLAYER_WIDTH, PLAYER_X, Run,
)


def empty_run(seed=1):
    """Isolate an interaction without random arrivals during the assertion."""
    run = Run(seed=seed, bosses=False)
    run.entities.clear()
    run._spawn_timer = 100000.0
    return run


def advance(run, seconds, fps=120):
    events = []
    for _ in range(round(seconds * fps)):
        run.update(1.0 / fps)
        events.extend(event[0] for event in run.events)
    return events


def pickup(run, kind):
    item = Entity(kind, PLAYER_X + 12, GROUND - 45)
    run.entities.append(item)
    run.update(FIXED_STEP)
    return item


def overlapping_crate():
    return Entity("crate", PLAYER_X + 14, GROUND - 64, 62, 64)


class MovementTests(unittest.TestCase):
    def test_double_jump_then_landing_restores_jump(self):
        run = empty_run()
        self.assertTrue(run.jump())
        advance(run, 0.2)
        self.assertLess(run.player_y, GROUND)
        self.assertTrue(run.jump())
        second_jump_height = run.player_y
        advance(run, 0.15)
        self.assertLess(run.player_y, second_jump_height)
        self.assertEqual(run.jumps, 2)
        self.assertFalse(run.jump(), "A third jump must not grant another impulse")
        advance(run, 1.1)
        self.assertEqual(run.player_y, GROUND)
        self.assertEqual(run.jumps, 0)
        self.assertTrue(run.jump())

    def test_slide_clears_drone_that_hits_a_standing_player(self):
        standing, sliding = empty_run(), empty_run()
        for run in (standing, sliding):
            run.entities.append(Entity("drone", PLAYER_X + 12, GROUND - 104, 88, 52))
        original_height = sliding.player_rect[3]
        sliding.set_slide(True)
        self.assertLess(sliding.player_rect[3], original_height)
        advance(standing, 0.5)
        advance(sliding, 0.5)
        self.assertFalse(standing.alive)
        self.assertTrue(sliding.alive)
        self.assertEqual(sliding.dodged, 1)
        sliding.set_slide(False)
        self.assertEqual(sliding.player_rect[3], original_height)

    def test_air_slide_lands_earlier_and_held_slide_survives_landing(self):
        normal, fast = empty_run(), empty_run()
        for run in (normal, fast):
            run.jump()
            advance(run, 0.15)
        fast.set_slide(True)
        advance(fast, 0.2)
        advance(normal, 0.2)
        self.assertEqual(fast.player_y, GROUND)
        self.assertTrue(fast.sliding)
        self.assertLess(normal.player_y, GROUND)
        fast.jump()
        self.assertFalse(fast.sliding)

    def test_late_jump_press_is_buffered_but_early_third_press_is_not(self):
        run = empty_run()
        run.jump()
        advance(run, 0.2)
        run.jump()
        # Wait until the final few pixels of the second descent.
        for _ in range(240):
            if run.player_vy > 0 and run.player_y > GROUND - 25:
                break
            run.update(FIXED_STEP)
        self.assertEqual(run.jumps, 2)
        self.assertFalse(run.jump())
        events = advance(run, 0.1)
        self.assertEqual(run.jumps, 1)
        self.assertLess(run.player_y, GROUND)
        self.assertIn("jump", events)

    def test_death_freezes_run_and_rejects_actions(self):
        run = empty_run()
        run.energy = 100
        run.entities.append(overlapping_crate())
        run.update(FIXED_STEP)
        self.assertFalse(run.alive)
        self.assertIn("hit", [event[0] for event in run.events])
        state = (run.time, run.distance, run.score, run.player_y)
        self.assertFalse(run.jump())
        self.assertFalse(run.dash())
        advance(run, 1)
        self.assertEqual((run.time, run.distance, run.score, run.player_y), state)


class PickupAndRewardTests(unittest.TestCase):
    def test_coin_is_counted_once_and_combo_increases_score(self):
        run, baseline = empty_run(), empty_run()
        coin = pickup(run, "coin")
        baseline.update(FIXED_STEP)
        self.assertTrue(coin.collected)
        self.assertEqual(run.coins, 1)
        self.assertEqual(run.energy, 33)
        self.assertNotIn(coin, run.entities)
        for _ in range(9):
            pickup(run, "coin")
            baseline.update(FIXED_STEP)
        self.assertEqual(run.coins, 10)
        self.assertEqual(run.combo, 10)
        self.assertEqual(run.multiplier, 2)
        self.assertEqual(run.score - baseline.score, 110)
        advance(run, 3.1)
        self.assertEqual(run.coins, 10)
        self.assertEqual(run.combo, 0)
        self.assertEqual(run.best_combo, 10)

    def test_magnet_collects_an_unreachable_coin_and_expires(self):
        normal, magnetic = empty_run(), empty_run()
        pickup(magnetic, "magnet")
        for run in (normal, magnetic):
            run.entities.append(Entity("coin", PLAYER_X + 150, GROUND - 180))
        advance(normal, 0.6)
        advance(magnetic, 0.6)
        self.assertEqual(normal.coins, 0)
        self.assertEqual(magnetic.coins, 1)
        self.assertGreater(magnetic.magnet, 0)
        advance(magnetic, 6.5)
        self.assertEqual(magnetic.magnet, 0)
        magnetic.entities.append(Entity("coin", PLAYER_X + 150, GROUND - 180))
        advance(magnetic, 0.6)
        self.assertEqual(magnetic.coins, 1)

    def test_shield_collected_on_impact_protects_once_and_then_expires(self):
        run = empty_run()
        run.entities.extend([overlapping_crate(), overlapping_crate(),
                             Entity("shield", PLAYER_X + 12, GROUND - 45)])
        run.update(FIXED_STEP)
        self.assertTrue(run.alive, "Same-frame pickups must protect before hazard resolution")
        self.assertFalse(run.shield)
        self.assertGreater(run.invulnerable, 0)
        self.assertEqual([event[0] for event in run.events].count("shield"), 1)
        advance(run, 1)
        self.assertTrue(run.alive, "Post-impact immunity must cover overlapping hazards")
        self.assertEqual(run.invulnerable, 0)
        run.entities.append(overlapping_crate())
        run.update(FIXED_STEP)
        self.assertFalse(run.alive)

    def test_batteries_fill_energy_and_dash_protects_for_three_seconds(self):
        run = empty_run()
        self.assertFalse(run.dash())
        pickup(run, "battery")
        self.assertEqual(run.energy, 65)
        pickup(run, "battery")
        pickup(run, "battery")
        self.assertEqual(run.energy, 100, "Battery energy must stop at a full bar")
        run.entities.append(overlapping_crate())
        self.assertTrue(run.dash())
        self.assertEqual(run.energy, 0)
        self.assertEqual(run.dash_count, 1)
        self.assertFalse(run.dash())
        advance(run, 2.9)
        self.assertTrue(run.alive)
        self.assertTrue(run.is_dashing)
        # A hazard arriving at the end must be cleared by the exit grace period.
        run.entities.append(overlapping_crate())
        advance(run, 0.1)
        self.assertFalse(run.is_dashing)
        self.assertTrue(run.alive)
        self.assertGreater(run.invulnerable, 0)
        advance(run, 0.9)
        run.entities.append(overlapping_crate())
        run.update(FIXED_STEP)
        self.assertFalse(run.alive, "Protection must eventually end")

    def test_dash_speeds_world_collects_high_coins_and_returns_to_normal_travel(self):
        normal, dashing = empty_run(), empty_run()
        distant_coins = []
        for run in (normal, dashing):
            run.entities.append(Entity("coin", PLAYER_X + 150, GROUND - 180))
            distant = Entity("coin", 5000, GROUND - 300)
            run.entities.append(distant)
            distant_coins.append(distant)
        dashing.energy = 100
        self.assertTrue(dashing.dash())
        advance(normal, 0.6)
        advance(dashing, 0.6)
        self.assertEqual(normal.coins, 0)
        self.assertEqual(dashing.coins, 1, "Dash must attract high coins without a magnet pickup")
        self.assertEqual(dashing.magnet, 0)
        self.assertAlmostEqual(dashing.distance / normal.distance, 1.55, places=9)
        self.assertAlmostEqual((5000 - distant_coins[1].x) / (5000 - distant_coins[0].x), 1.55, places=9)
        for run in (normal, dashing):
            advance(run, 2.4)
        self.assertFalse(dashing.is_dashing)
        normal_distance, dash_distance = normal.distance, dashing.distance
        normal_coin_x, dash_coin_x = [coin.x for coin in distant_coins]
        advance(normal, 0.5)
        advance(dashing, 0.5)
        self.assertAlmostEqual(dashing.distance - dash_distance, normal.distance - normal_distance, places=9)
        self.assertAlmostEqual(dash_coin_x - distant_coins[1].x, normal_coin_x - distant_coins[0].x, places=9)
        self.assertEqual(dashing.speed, normal.speed)

    def test_thirty_coin_combo_starts_reward_zone_and_auto_collects(self):
        run = empty_run()
        for _ in range(29):
            pickup(run, "coin")
        self.assertFalse(run.is_bonus)
        run.entities.append(overlapping_crate())
        pickup(run, "coin")
        self.assertTrue(run.is_bonus)
        self.assertTrue(run.alive)
        self.assertIn("bonus", [event[0] for event in run.events])
        self.assertEqual(run.dash_count, 0)
        self.assertFalse(run.dash(), "Bonus and manual dash cannot overlap")
        run.entities.append(Entity("coin", PLAYER_X + 600, GROUND - 200))
        advance(run, 0.8)
        self.assertGreater(run.coins, 30, "The bonus must attract coins outside normal magnet range")
        advance(run, 7.3)
        self.assertFalse(run.is_bonus)
        self.assertTrue(run.alive)
        self.assertGreater(run.invulnerable, 0)


class SimulationTests(unittest.TestCase):
    def test_same_inputs_produce_same_motion_at_30_60_and_144_fps(self):
        results = []
        for fps in (30, 60, 144):
            run = empty_run(seed=17)
            events = []
            actions = ["jump", "jump", "slide", "release", "jump", "jump", "slide", "release"]
            for action in actions:
                if action == "jump":
                    run.jump()
                else:
                    run.set_slide(action == "slide")
                events.extend(advance(run, 0.5, fps=fps))
            results.append((run, events))
        reference, reference_events = results[0]
        for actual, events in results[1:]:
            for field in ("time", "distance", "speed", "player_y", "player_vy"):
                self.assertAlmostEqual(getattr(actual, field), getattr(reference, field), places=9, msg=field)
            for field in ("score", "jumps", "sliding", "alive"):
                self.assertEqual(getattr(actual, field), getattr(reference, field), field)
            self.assertEqual(events, reference_events)

    def test_stalled_frame_is_capped_and_invalid_elapsed_times_do_not_advance(self):
        stalled, bounded = empty_run(), empty_run()
        stalled.jump()
        bounded.jump()
        stalled.update(8)
        bounded.update(0.1)
        self.assertEqual(stalled.distance, bounded.distance)
        self.assertEqual(stalled.player_y, bounded.player_y)
        state = (bounded.time, bounded.distance, bounded.player_y)
        for dt in (0, -1, math.inf, -math.inf, math.nan):
            bounded.update(dt)
        self.assertEqual((bounded.time, bounded.distance, bounded.player_y), state)

    def test_input_events_survive_until_update_and_are_not_replayed(self):
        run = empty_run()
        run.jump()
        run.update(FIXED_STEP)
        self.assertEqual([event[0] for event in run.events], ["jump"])
        run.update(FIXED_STEP)
        self.assertEqual(run.events, [])

    def test_multiple_seeds_keep_action_recovery_time_at_top_speed(self):
        # Observe obstacles reaching the player on eight whole generated runs.
        # Ignore pickups so bonus zones cannot hide a bad section of the course.
        for seed in (0, 1, 2, 7, 19, 42, 99, 2026):
            with self.subTest(seed=seed):
                run = Run(seed=seed, bosses=False)
                run.invulnerable = 1000
                seen = []
                arrivals = []
                for _ in range(180 * 30):
                    run.entities[:] = [entity for entity in run.entities if entity.kind in OBSTACLES]
                    run.update(1 / 30)
                    for entity in run.entities:
                        if entity.kind in OBSTACLES and entity.x <= PLAYER_X and not any(entity is old for old in seen):
                            seen.append(entity)
                            arrivals.append(run.time)
                self.assertTrue(run.alive)
                self.assertEqual(run.speed, 620)
                self.assertGreater(len(arrivals), 50)
                for earlier, later in zip(arrivals, arrivals[1:]):
                    self.assertGreaterEqual(later - earlier, 2.0,
                                            "Consecutive actions leave less than two seconds to recover")

    def test_simple_reactive_player_survives_generated_courses(self):
        # This player has no invulnerability, extra energy, or course knowledge.
        # It reacts to the nearest visible action using only jump and slide.
        for seed in (0, 19, 2026):
            with self.subTest(seed=seed):
                run = Run(seed=seed, bosses=False)
                for _ in range(180 * 60):
                    upcoming = [entity for entity in run.entities
                                if entity.kind in OBSTACLES and not entity.collected
                                and entity.x + entity.w >= PLAYER_X]
                    obstacle = min(upcoming, key=lambda entity: entity.x, default=None)
                    gap = (obstacle.x - PLAYER_X - PLAYER_WIDTH) if obstacle else math.inf
                    run.set_slide(bool(obstacle and obstacle.kind == "drone" and gap < run.speed * 0.6))
                    if obstacle and obstacle.kind != "drone" and gap < run.speed * 0.3 and run.jumps == 0:
                        run.jump()
                    run.update(1 / 60)
                    self.assertTrue(run.alive, "Seed {} became unavoidable at {:.2f}s".format(seed, run.time))
                self.assertEqual(run.speed, 620)
                self.assertGreater(run.dodged, 20)


if __name__ == "__main__":
    unittest.main()
