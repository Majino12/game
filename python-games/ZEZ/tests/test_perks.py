"""Per-run choices, workshop effects and the reward pause through real play rules."""

from copy import deepcopy
import unittest

from runner.model import Boss, Entity, FIXED_STEP, GROUND, PERKS, PLAYER_X, Projectile, Run


def empty_run(**kwargs):
    run = Run(seed=23, **kwargs)
    run.entities.clear()
    run._spawn_timer = 100000.0
    return run


def advance(run, seconds, fps=120):
    events = []
    for _ in range(round(seconds * fps)):
        run.update(1 / fps)
        events.extend(event[0] for event in run.events)
    return events


def collect(run, kind):
    run.entities.append(Entity(kind, PLAYER_X + 12, GROUND - 45))
    run.update(FIXED_STEP)


def finish_boss(run):
    """Land the final legitimate shot, then let the victory animation finish."""
    run.boss = Boss(hp=2, phase="fight", timer=20, telegraph=20)
    run.projectiles.append(Projectile("shot", run.boss.x, run.boss.y))
    run.update(FIXED_STEP)
    return advance(run, 2.5)


def grant(run, key):
    """Select a displayed card to isolate its effect from random offer draws."""
    run.perk_choices = [key]
    if not run.choose_perk(key):
        raise AssertionError("Valid perk selection failed: " + key)


class PerkChoiceTests(unittest.TestCase):
    def test_victory_offers_three_unique_available_perks_only_after_exit(self):
        run = empty_run()
        run.perks["wing"] = 1
        run.boss = Boss(hp=2, phase="fight", timer=20, telegraph=20)
        run.projectiles.extend([Projectile("shot", run.boss.x, run.boss.y),
                                Projectile("shot", run.boss.x, run.boss.y)])
        run.update(FIXED_STEP)
        self.assertEqual(run.perk_choices, [])
        self.assertEqual(run.boss_defeated, 1)
        self.assertEqual(run.coins, 50)
        self.assertEqual(run.score - int(run.distance * 5), 500)
        self.assertEqual([event[0] for event in run.events].count("boss_defeated"), 1)
        advance(run, 2.4)
        self.assertEqual(run.perk_choices, [])
        events = advance(run, 0.1)
        self.assertIsNone(run.boss)
        self.assertEqual(len(run.perk_choices), 3)
        self.assertEqual(len(set(run.perk_choices)), 3)
        self.assertNotIn("wing", run.perk_choices)
        self.assertNotIn("supply", run.perk_choices)
        self.assertEqual(events.count("perk_ready"), 1)
        advance(run, 10)
        self.assertEqual(run.coins, 50)
        self.assertEqual(run.boss_defeated, 1)

    def test_choice_freezes_time_timers_entities_and_all_gameplay_input(self):
        run = empty_run()
        run.set_fire(True)
        run.magnet = 8
        finish_boss(run)
        self.assertTrue(run.perk_choices)
        fields = ("time", "distance", "score", "coins", "combo", "energy", "magnet",
                  "dash_timer", "invulnerable", "player_y", "player_vy", "jumps",
                  "sliding", "entities", "projectiles", "perk_choices")
        before = deepcopy({key: getattr(run, key) for key in fields})
        self.assertFalse(run.jump())
        self.assertFalse(run.dash())
        self.assertFalse(run.fire())
        run.set_slide(True)
        run.set_fire(True)
        advance(run, 30, fps=30)
        self.assertEqual({key: getattr(run, key) for key in fields}, before)
        self.assertEqual(run._accumulator, 0)
        self.assertFalse(run._slide_held)
        self.assertFalse(run._fire_held)

    def test_invalid_and_repeated_selection_are_noops_valid_choice_resumes_safely(self):
        run = empty_run()
        finish_boss(run)
        choice = run.perk_choices[0]
        before = (dict(run.perks), list(run.perk_choices), run.coins, run.time)
        for invalid in ("unknown", "supply", "", None, []):
            self.assertFalse(run.choose_perk(invalid))
            self.assertEqual((run.perks, run.perk_choices, run.coins, run.time), before)
        self.assertTrue(run.choose_perk(choice))
        self.assertEqual(run.perks[choice], 1)
        self.assertEqual(run.perk_choices, [])
        self.assertGreaterEqual(run.invulnerable, 1.2)
        self.assertFalse(run.choose_perk(choice))
        events = advance(run, 1)
        self.assertEqual(events.count("perk_chosen"), 1)
        self.assertAlmostEqual(run.time - before[3], 1)
        self.assertTrue(run.alive)
        self.assertFalse(any(e.kind in ("crate", "spike", "drone") for e in run.entities))

    def test_last_available_perk_and_repeatable_full_level_supply(self):
        run = empty_run(upgrades={"magnet": 3})
        for key in run.perks:
            run.perks[key] = PERKS[key]["max_level"]
        run.perks["focus"] -= 1
        finish_boss(run)
        self.assertEqual(run.perk_choices, ["focus"])
        self.assertTrue(run.choose_perk("focus"))
        full_levels = dict(run.perks)
        for _ in range(2):
            finish_boss(run)
            self.assertEqual(run.perk_choices, ["supply"])
            coins = run.coins
            self.assertTrue(run.choose_perk("supply"))
            self.assertEqual(run.coins, coins + 40)
            self.assertEqual(run.magnet, 13)
            self.assertEqual(run.perks, full_levels)
            self.assertFalse(run.choose_perk("supply"))

    def test_practice_skips_choices_and_restart_clears_per_run_progress(self):
        practice = empty_run(rewards=False)
        events = finish_boss(practice)
        self.assertEqual(practice.perk_choices, [])
        self.assertNotIn("perk_ready", events)
        time = practice.time
        advance(practice, 1)
        self.assertGreater(practice.time, time)
        old = empty_run(upgrades={"dash": 2})
        grant(old, "wing")
        grant(old, "capacitor")
        restarted = Run(seed=23, upgrades=old.upgrades)
        self.assertTrue(all(level == 0 for level in restarted.perks.values()))
        self.assertEqual(restarted.perk_choices, [])
        self.assertEqual(restarted.boss_defeated, 0)
        self.assertEqual(restarted.energy, 30)
        self.assertEqual(restarted.upgrades["dash"], 2)
        self.assertEqual(restarted.max_jumps, 2)

    def test_offer_boundary_and_choices_are_identical_across_frame_rates(self):
        results = []
        for fps in (30, 60, 144):
            run = empty_run(upgrades={"recharge": 2})
            run.boss = Boss(hp=2, phase="fight", timer=20, telegraph=20)
            run.projectiles.append(Projectile("shot", run.boss.x, run.boss.y))
            events = advance(run, 5, fps)
            frozen = (run.time, run.distance, run.score, run.coins, list(run.perk_choices))
            advance(run, 3, fps)
            self.assertEqual((run.time, run.distance, run.score, run.coins, run.perk_choices), frozen)
            self.assertTrue(run.choose_perk(run.perk_choices[0]))
            events.extend(advance(run, 1, fps))
            results.append((frozen, run.time, run.distance, run.perks, events))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])


class PerkEffectTests(unittest.TestCase):
    def test_wing_grants_exactly_one_extra_jump_and_caps_level(self):
        run = empty_run(bosses=False)
        grant(run, "wing")
        self.assertEqual(run.max_jumps, 3)
        for _ in range(3):
            self.assertTrue(run.jump())
            advance(run, 0.1)
        self.assertFalse(run.jump())
        advance(run, 1.5)
        self.assertEqual(run.jumps, 0)
        run.perk_choices = ["wing"]
        self.assertFalse(run.choose_perk("wing"))
        self.assertEqual(run.perks["wing"], 1)

    def test_focus_only_changes_weak_point_damage(self):
        run = empty_run()
        for _ in range(3):
            grant(run, "focus")
        for phase, damage in (("fight", 2), ("weak", 14)):
            run.boss = Boss(phase=phase, timer=20, telegraph=20)
            run.projectiles.append(Projectile("shot", run.boss.x, run.boss.y))
            run.update(FIXED_STEP)
            self.assertEqual(run.boss.hp, 160 - damage)

    def test_capacitor_stacks_with_workshop_recharge_and_energy_caps(self):
        run = empty_run(bosses=False, upgrades={"recharge": 3})
        for _ in range(3):
            grant(run, "capacitor")
        collect(run, "coin")
        self.assertEqual(run.energy, 37.5)
        run.energy = 99
        collect(run, "coin")
        self.assertEqual(run.energy, 100)

    def test_tempo_fires_more_shots_without_bypassing_shared_cooldown(self):
        counts = []
        for levels in (0, 3):
            run = empty_run()
            for _ in range(levels):
                grant(run, "tempo")
            run.boss = Boss(phase="fight", timer=20, telegraph=20)
            run.set_fire(True)
            self.assertTrue(run.fire())
            self.assertFalse(run.fire())
            events = advance(run, 2)
            counts.append(events.count("shot"))
        self.assertGreater(counts[1], counts[0])
        self.assertLessEqual(counts[1], 14)

    def test_magnet_extends_active_attraction_but_does_not_attract_without_power(self):
        counts = []
        for level, active in ((0, True), (3, True), (3, False)):
            run = empty_run(bosses=False)
            for _ in range(level):
                grant(run, "magnet")
            if active:
                collect(run, "magnet")
            run.entities.append(Entity("coin", PLAYER_X + 230, GROUND - 450))
            advance(run, 1)
            counts.append(run.coins)
        self.assertEqual(counts, [0, 1, 0])

    def test_combo_extends_timeout_without_changing_reward_threshold(self):
        run = empty_run(bosses=False)
        for _ in range(3):
            grant(run, "combo")
        collect(run, "coin")
        advance(run, 5.9)
        self.assertEqual(run.combo, 1)
        self.assertFalse(run.is_bonus)
        advance(run, 0.2)
        self.assertEqual(run.combo, 0)
        for _ in range(30):
            collect(run, "coin")
        self.assertTrue(run.is_bonus)


class WorkshopEffectTests(unittest.TestCase):
    def test_levels_are_copied_clamped_and_invalid_types_do_not_grant_power(self):
        incoming = {"magnet": 99, "recharge": -2, "dash": 2, "unknown": 3}
        run = empty_run(upgrades=incoming)
        self.assertEqual(run.upgrades, {"magnet": 3, "recharge": 0, "dash": 2})
        incoming["dash"] = 0
        self.assertEqual(run.upgrades["dash"], 2)
        for invalid in (True, 1.5, "3", None, []):
            with self.subTest(value=invalid):
                run = empty_run(upgrades={"magnet": invalid, "recharge": invalid, "dash": invalid})
                self.assertEqual(run.upgrades, {"magnet": 0, "recharge": 0, "dash": 0})

    def test_each_workshop_level_changes_real_pickups_and_dash_duration(self):
        for level in range(4):
            with self.subTest(level=level):
                run = empty_run(bosses=False, upgrades={"magnet": level, "recharge": level, "dash": level})
                collect(run, "magnet")
                self.assertEqual(run.magnet, 7 + 2 * level)
                collect(run, "coin")
                self.assertEqual(run.energy, 33 + 0.5 * level)
                run.energy = 100
                self.assertTrue(run.dash())
                expected = 3 + 0.35 * level
                self.assertAlmostEqual(run.dash_timer, expected)
                advance(run, expected - 0.05)
                self.assertTrue(run.is_dashing)
                advance(run, 0.05)
                self.assertFalse(run.is_dashing)
                self.assertGreater(run.invulnerable, 0)


if __name__ == "__main__":
    unittest.main()
