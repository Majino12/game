"""Boss encounters tested through actual timing, projectiles, and player actions."""

import unittest

from runner.model import (
    BOSS_SPECS, Entity, FIXED_STEP, GROUND, OBSTACLES, PLAYER_WIDTH, PLAYER_X,
    Projectile, Run,
)


def isolated_run(seed=17, bosses=True, first_boss="bee"):
    # Combat/practice tests continue immediately after the victory animation.
    # Reward selection and its pause are covered separately in test_perks.
    run = Run(seed=seed, bosses=bosses, rewards=False, first_boss=first_boss)
    run.entities.clear()
    run._spawn_timer = 100000.0
    run.route.next_distance = float("inf")
    return run


def advance(run, seconds, fps=120):
    events = []
    for _ in range(round(seconds * fps)):
        run.update(1 / fps)
        events.extend(event[0] for event in run.events)
    return events


def until(run, condition, timeout=10, control=None):
    events = []
    for _ in range(round(timeout / FIXED_STEP)):
        if condition():
            return events
        if control:
            control(run)
        run.update(FIXED_STEP)
        events.extend(event[0] for event in run.events)
    if not condition():
        raise AssertionError("Condition not reached within {} seconds".format(timeout))
    return events


def encounter(active=False, kind="bee"):
    run = isolated_run(first_boss=kind)
    run.next_boss_distance = 0
    run.update(FIXED_STEP)
    if active:
        advance(run, 2)
    return run


def dodge_waves(run):
    upcoming = [p for p in run.projectiles
                if p.kind in ("boss_low", "boss_high", "boss_orb") and p.x + p.w >= PLAYER_X]
    wave = min(upcoming, key=lambda p: p.x, default=None)
    gap = wave.x - PLAYER_X - PLAYER_WIDTH if wave else float("inf")
    high = wave and (wave.kind == "boss_high" or (wave.kind == "boss_orb" and wave.y + wave.h < GROUND - 30))
    run.set_slide(bool(high and gap < abs(wave.vx) * 0.6))
    if wave and not high and gap < abs(wave.vx) * 0.3:
        if run.jumps == 0:
            run.jump()
        elif (run.boss.burst > 1 and run.jumps == 1 and run.player_vy > 0
              and run.player_y > GROUND - 140):
            run.jump()


class BossEntranceTests(unittest.TestCase):
    def test_first_boss_appears_at_distance_threshold_and_can_be_disabled(self):
        run = isolated_run()
        self.assertEqual(run.next_boss_distance, 350)
        until(run, lambda: run.distance >= 349, timeout=30)
        self.assertIsNone(run.boss)
        events = until(run, lambda: run.boss is not None, timeout=1)
        self.assertGreaterEqual(run.distance, 350)
        self.assertLess(run.distance, 351)
        self.assertEqual(events.count("boss_warning"), 1)
        self.assertEqual(run.boss.phase, "warning")
        disabled = isolated_run(bosses=False)
        disabled.next_boss_distance = 0
        advance(disabled, 30)
        self.assertIsNone(disabled.boss)
        self.assertFalse(disabled.bosses_enabled)

    def test_two_second_entrance_clears_hazards_and_cannot_fire(self):
        run = isolated_run()
        run.next_boss_distance = 0
        run.entities.append(Entity("crate", PLAYER_X, GROUND - 64, 62, 64))
        run.projectiles.append(Projectile("boss_low", PLAYER_X, GROUND - 44, 82, 44))
        run.set_fire(True)
        run.update(FIXED_STEP)
        self.assertTrue(run.alive)
        self.assertEqual(run.boss.timer, 2)
        self.assertFalse(run.fire())
        self.assertFalse(any(e.kind in OBSTACLES for e in run.entities))
        for _ in range(239):
            run.update(FIXED_STEP)
            self.assertEqual(run.boss.phase, "warning")
            self.assertEqual(run.projectiles, [])
            self.assertTrue(run.alive)
        run.update(FIXED_STEP)
        self.assertEqual(run.boss.phase, "fight")
        self.assertGreater(run.boss.telegraph, 1)
        self.assertEqual([p.kind for p in run.projectiles], ["shot"])

    def test_boss_waits_until_existing_dash_or_bonus_finishes(self):
        for timer_name in ("dash_timer", "bonus_timer"):
            with self.subTest(timer=timer_name):
                run = isolated_run()
                run.next_boss_distance = 0
                setattr(run, timer_name, 1)
                advance(run, 0.9)
                self.assertIsNone(run.boss)
                advance(run, 0.1)
                self.assertIsNotNone(run.boss)
                self.assertEqual(run.boss.phase, "warning")


class BossCombatTests(unittest.TestCase):
    def test_attack_has_a_readable_telegraph_then_low_and_high_waves_are_avoidable(self):
        run = encounter(active=True)
        self.assertEqual(run.boss.attack, "low")
        advance(run, 1)
        self.assertEqual(run.boss.phase, "fight")
        self.assertGreater(run.boss.telegraph, 0)
        self.assertEqual(run.projectiles, [])
        events = until(run, lambda: any(p.kind == "boss_low" for p in run.projectiles), timeout=0.5)
        self.assertIn("boss_attack", events)
        self.assertEqual(run.boss.phase, "weak")
        seen_kinds = set()
        attack_events = 1
        for _ in range(12 * 120):
            seen_kinds.update(p.kind for p in run.projectiles)
            dodge_waves(run)
            run.update(FIXED_STEP)
            attack_events += sum(event[0] == "boss_attack" for event in run.events)
            self.assertTrue(run.alive, "A telegraphed wave must be avoidable by jump or slide")
        self.assertEqual(seen_kinds, {"boss_low", "boss_high"})
        self.assertGreaterEqual(attack_events, 4)
        self.assertEqual(run.boss.hp, run.boss.max_hp)
        self.assertFalse(run.shield)
        self.assertEqual(run.invulnerable, 0)

    def test_armor_and_weak_point_use_damage_at_actual_impact(self):
        run = encounter(active=True)
        full_hp = run.boss.hp
        self.assertTrue(run.fire())
        until(run, lambda: run.boss.hp < full_hp)
        self.assertEqual(run.boss.phase, "fight")
        self.assertEqual(full_hp - run.boss.hp, 2)
        until(run, lambda: run.boss.phase == "weak")
        armored_hp = run.boss.hp
        self.assertTrue(run.fire())
        until(run, lambda: run.boss.hp < armored_hp)
        self.assertEqual(armored_hp - run.boss.hp, 8)
        self.assertTrue(run.alive)

    def test_shot_fired_under_armor_can_hit_an_open_weak_point(self):
        run = encounter(active=True)
        advance(run, 1)
        self.assertEqual(run.boss.phase, "fight")
        self.assertTrue(run.fire())
        until(run, lambda: run.boss.hp < run.boss.max_hp)
        self.assertEqual(run.boss.phase, "weak")
        self.assertEqual(run.boss.max_hp - run.boss.hp, 8)

    def test_single_and_held_fire_share_cooldown_and_release_stops_new_shots(self):
        run = encounter(active=True)
        self.assertTrue(run.fire())
        self.assertFalse(run.fire())
        for _ in range(29):
            run.update(FIXED_STEP)
        self.assertFalse(run.fire())
        run.update(FIXED_STEP)
        self.assertTrue(run.fire())
        run.set_fire(True)
        events = advance(run, 1)
        self.assertEqual(events.count("shot"), 5, "One pending manual shot plus four held shots")
        run.set_fire(False)
        events = advance(run, 1)
        self.assertNotIn("shot", events)
        self.assertFalse(isolated_run().fire())

    def test_one_dash_hits_once_even_when_started_during_entrance(self):
        run = encounter()
        run.energy = 100
        full_hp = run.boss.hp
        self.assertTrue(run.dash())
        self.assertEqual(run.boss.hp, full_hp)
        events = advance(run, 3)
        self.assertEqual(run.boss.hp, full_hp - 25)
        self.assertEqual(events.count("boss_hit"), 1)
        self.assertFalse(run.is_dashing)
        run.energy = 100
        self.assertTrue(run.dash())
        advance(run, 0.2)
        self.assertEqual(run.boss.hp, full_hp - 50)
        self.assertEqual(run.dash_count, 2)

    def test_shield_absorbs_one_natural_wave_but_next_wave_can_kill(self):
        run = encounter(active=True)
        run.shield = True
        events = until(run, lambda: not run.shield, timeout=5)
        self.assertTrue(run.alive)
        self.assertEqual(events.count("shield"), 1)
        self.assertGreater(run.invulnerable, 0)
        events = until(run, lambda: not run.alive, timeout=5)
        self.assertEqual(events.count("hit"), 1)
        self.assertFalse(run.fire())
        old_state = (run.time, run.distance, run.boss.hp, run.boss.timer)
        run.set_fire(True)
        advance(run, 1)
        self.assertEqual((run.time, run.distance, run.boss.hp, run.boss.timer), old_state)
        restarted = Run(seed=17)
        self.assertTrue(restarted.alive)
        self.assertIsNone(restarted.boss)
        self.assertEqual(restarted.projectiles, [])
        self.assertEqual(restarted.boss_defeated, 0)
        self.assertEqual(restarted.next_boss_distance, 350)
        self.assertFalse(restarted.fire())

    def test_enraged_attack_still_gives_warning_and_is_dodgeable(self):
        run = encounter(active=True)
        run.boss.hp = 80
        self.assertTrue(run.fire())
        until(run, lambda: run.boss.enraged)
        until(run, lambda: run.boss.phase == "weak")
        until(run, lambda: run.boss.phase == "fight", control=dodge_waves)
        self.assertAlmostEqual(run.boss.telegraph, 1)
        self.assertEqual(run.boss.attack, "high")
        until(run, lambda: any(p.kind == "boss_high" for p in run.projectiles), control=dodge_waves)
        wave = next(p for p in run.projectiles if p.kind == "boss_high")
        self.assertEqual(abs(wave.vx), 560)
        for _ in range(3 * 120):
            dodge_waves(run)
            run.update(FIXED_STEP)
        self.assertTrue(run.alive)


class BossVictoryTests(unittest.TestCase):
    def test_winning_shot_precedes_incoming_hit_and_rewards_only_once(self):
        run = encounter(active=True)
        until(run, lambda: run.boss.phase == "weak")
        run.boss.hp = 8
        run.invulnerable = 0
        run.shield = False
        points_before = run.score - int(run.distance * 5)
        run.projectiles[:] = [Projectile("boss_low", PLAYER_X, GROUND - 44, 82, 44),
                              Projectile("shot", run.boss.x, run.boss.y),
                              Projectile("shot", run.boss.x, run.boss.y)]
        run.update(FIXED_STEP)
        self.assertTrue(run.alive)
        self.assertEqual(run.boss.phase, "defeated")
        self.assertEqual(run.boss.hp, 0)
        self.assertEqual(run.boss_defeated, 1)
        self.assertEqual(run.coins, 50)
        self.assertEqual(run.score - int(run.distance * 5) - points_before, 500)
        self.assertEqual(run.energy, 100)
        self.assertTrue(run.shield)
        self.assertEqual(run.projectiles, [])
        self.assertEqual([event[0] for event in run.events].count("boss_defeated"), 1)
        self.assertAlmostEqual(run.next_boss_distance, run.distance + 600)
        self.assertFalse(run.fire())
        run.set_fire(True)
        events = advance(run, 2.5)
        self.assertIsNone(run.boss)
        self.assertNotIn("boss_defeated", events)
        self.assertNotIn("shot", events)
        self.assertEqual(run.coins, 50)
        self.assertEqual(run.boss_defeated, 1)
        self.assertGreater(run.invulnerable, 0)
        advance(run, 1.9)
        self.assertFalse(any(e.kind in OBSTACLES for e in run.entities))
        self.assertTrue(run.alive)
        advance(run, 0.2)
        self.assertTrue(any(e.kind in OBSTACLES for e in run.entities), "Normal running should resume after a safe exit")

    def test_boss_returns_after_the_next_distance_interval(self):
        run = encounter(active=True)
        run.set_fire(True)
        events = until(run, lambda: run.boss_defeated == 1, timeout=20, control=dodge_waves)
        self.assertTrue(run.alive)
        self.assertEqual(events.count("boss_defeated"), 1)
        first_boss = run.boss
        next_distance = run.next_boss_distance
        until(run, lambda: run.boss is None, timeout=3)
        run.set_fire(False)
        run.entities.clear()
        run._spawn_timer = 100000.0
        while run.distance + 1 < next_distance:
            run.update(FIXED_STEP)
            self.assertIsNone(run.boss)
        events = until(run, lambda: run.boss is not None, timeout=1)
        self.assertEqual(events.count("boss_warning"), 1)
        self.assertIsNot(run.boss, first_boss)
        self.assertEqual(run.boss.phase, "warning")
        self.assertEqual(run.boss.hp, run.boss.max_hp)
        self.assertEqual(run.boss.index, 2)
        self.assertIn(run.boss.kind, ("storm", "crystal"))
        self.assertEqual(run.boss.max_hp, 180)
        self.assertEqual(run.boss.attack, BOSS_SPECS[run.boss.kind]["attacks"][0])
        self.assertEqual(run.boss_defeated, 1)
        self.assertGreaterEqual(run.distance, next_distance)

    def test_encounter_and_held_fire_are_consistent_at_30_60_and_144_fps(self):
        for kind in BOSS_SPECS:
            with self.subTest(kind=kind):
                results = []
                for fps in (30, 60, 144):
                    run = isolated_run(first_boss=kind)
                    run.next_boss_distance = 0
                    run.invulnerable = 100
                    run.set_fire(True)
                    events = advance(run, 8, fps)
                    results.append((run, events))
                reference, reference_events = results[0]
                for actual, events in results[1:]:
                    for field in ("time", "distance", "speed", "player_y", "player_vy"):
                        self.assertAlmostEqual(getattr(actual, field), getattr(reference, field), places=9, msg=field)
                    for field in ("score", "coins", "boss_defeated", "alive"):
                        self.assertEqual(getattr(actual, field), getattr(reference, field), field)
                    self.assertEqual(actual.boss, reference.boss)
                    self.assertEqual(actual.projectiles, reference.projectiles)
                    self.assertEqual(events, reference_events)


class BossVarietyTests(unittest.TestCase):
    def test_successive_bosses_use_a_nonrepeating_seeded_bag_and_capped_health(self):
        run = isolated_run()
        seen = []
        for index in range(1, 11):
            with self.subTest(index=index):
                run.distance = run.next_boss_distance
                run.update(FIXED_STEP)
                hp = min(240, 160 + (index - 1) * 20)
                seen.append(run.boss.kind)
                self.assertEqual((run.boss.index, run.boss.hp), (index, hp))
                self.assertEqual(run.boss.max_hp, hp)
                advance(run, 2)
                run.boss.hp = 2
                run.projectiles.append(Projectile("shot", run.boss.x, run.boss.y))
                run.update(FIXED_STEP)
                self.assertEqual(run.boss.phase, "defeated")
                advance(run, 2.5)
                self.assertIsNone(run.boss)
                self.assertEqual(run.perk_choices, [])
                self.assertEqual(run.boss_defeated, index)
                self.assertEqual(run.coins, index * 50)
        self.assertEqual(seen[0], "bee")
        self.assertTrue(all(a != b for a, b in zip(seen, seen[1:])))
        for start in (1, 4, 7):
            self.assertEqual(set(seen[start:start + 3]), set(BOSS_SPECS))
        same_seed = Run(seed=17)
        self.assertEqual(seen, [same_seed._next_boss_kind(i) for i in range(1, 11)])

    def test_storm_has_readable_sequence_and_keeps_recovery_time(self):
        run = encounter(kind="storm")
        self.assertEqual(run.boss.kind, "storm")
        advance(run, 2)
        self.assertEqual(run.boss.attack, "high")
        attacks = []
        warnings = []
        previous_phase = "warning"
        for _ in range(20 * 120):
            if run.boss.phase == "fight" and previous_phase != "fight":
                warnings.append(run.boss.telegraph)
            previous_phase = run.boss.phase
            dodge_waves(run)
            run.update(FIXED_STEP)
            if any(event[0] == "boss_attack" for event in run.events):
                attacks.append((run.boss.attack, run.time))
                waves = [p for p in run.projectiles if p.kind.startswith("boss_")]
                self.assertEqual(len(waves), 2)
                self.assertEqual(waves[0].kind, waves[1].kind)
                self.assertAlmostEqual(waves[1].x - waves[0].x, 130)
            self.assertTrue(run.alive)
            self.assertFalse(run.shield)
        self.assertEqual([kind for kind, _ in attacks[:5]], ["high", "low", "low", "high", "high"])
        self.assertTrue(all(warning >= 1 for warning in warnings))
        self.assertTrue(all(later[1] - earlier[1] >= 3.5 for earlier, later in zip(attacks, attacks[1:])))

    def test_all_guardians_are_dodgeable_without_defenses_when_enraged(self):
        for kind in BOSS_SPECS:
            with self.subTest(kind=kind):
                run = encounter(active=True, kind=kind)
                run.boss.enraged = True
                for _ in range(25 * 120):
                    dodge_waves(run)
                    run.update(FIXED_STEP)
                    self.assertTrue(run.alive, (kind, run.time, run.boss.attack))
                    self.assertFalse(run.shield)
                self.assertEqual(run.invulnerable, 0)

    def test_crystal_locks_height_at_warning_and_orb_keeps_its_lane(self):
        run = encounter(active=True, kind="crystal")
        self.assertEqual(run.boss.attack, "aim")
        self.assertEqual(run.boss.target_y, GROUND - 36)
        locked = run.boss.target_y
        run.jump()
        advance(run, 0.4)
        self.assertEqual(run.boss.target_y, locked)
        until(run, lambda: run.boss.phase == "weak")
        orb = next(p for p in run.projectiles if p.kind == "boss_orb")
        self.assertEqual((orb.w, orb.h, orb.vx, orb.vy), (54, 54, -500, 0))
        self.assertEqual(orb.y + orb.h / 2, locked)
        advance(run, 0.2)
        self.assertEqual(orb.y + orb.h / 2, locked)
        # A high airborne position is clamped to a readable, bounded lane.
        run.player_y = GROUND - 300
        run.boss.attack = "aim"
        run._begin_telegraph(run.boss)
        self.assertEqual(run.boss.target_y, GROUND - 180)
        run.player_y = GROUND
        run.sliding = True
        run._begin_telegraph(run.boss)
        self.assertEqual(run.boss.target_y, GROUND - 30)

    def test_practice_override_and_unknown_first_boss(self):
        for chosen in ("bee", "storm", "crystal", "unknown", None):
            with self.subTest(chosen=chosen):
                run = isolated_run(first_boss=chosen)
                run.next_boss_distance = 0
                run.update(FIXED_STEP)
                self.assertEqual(run.boss.kind, chosen if chosen in BOSS_SPECS else "bee")
                self.assertEqual(run.boss.index, 1)
                self.assertEqual(run.boss.max_hp, 160)


if __name__ == "__main__":
    unittest.main()
