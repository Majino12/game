"""Character abilities and map integration exercised without a display."""

import unittest

from runner.model import (Boss, Entity, FIXED_STEP, GROUND, HEROES, OBSTACLES,
                          PLAYER_X, Projectile, Run, SPECIAL_KINDS)


def empty_run(character="beige", **kwargs):
    run = Run(seed=17, bosses=False, character=character, **kwargs)
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


class CharacterSkillTests(unittest.TestCase):
    def test_each_character_has_a_ready_skill_and_bilingual_description(self):
        self.assertEqual(set(HEROES), {"beige", "pink", "purple"})
        for key, info in HEROES.items():
            with self.subTest(character=key):
                for field in ("name", "name_en", "skill", "skill_en", "desc", "desc_en", "color"):
                    self.assertTrue(info[field])
                run = empty_run(key)
                self.assertEqual(run.character, key)
                self.assertEqual(run.skill_cooldown, 0)
                self.assertTrue(run.skill())
                self.assertEqual(run.skill_cooldown, info["cooldown"])
                self.assertEqual(run.skill_count, 1)
                self.assertFalse(run.skill())
                self.assertEqual(advance(run, FIXED_STEP).count("skill"), 1)
                self.assertNotIn("skill", advance(run, FIXED_STEP))
        for unknown in ("missing", None, []):
            self.assertEqual(empty_run(unknown).character, "beige")

    def test_cream_clears_only_near_hazards_and_preserves_rewards_and_player_shots(self):
        run = empty_run()
        close = Entity("crate", PLAYER_X + 30, GROUND - 64, 62, 64)
        far = Entity("crate", PLAYER_X + 400, GROUND - 64, 62, 64)
        coin = Entity("coin", PLAYER_X + 30, GROUND - 45)
        run.entities.extend((close, far, coin))
        shot = Projectile("shot", PLAYER_X, GROUND - 36)
        distant = Projectile("boss_low", PLAYER_X + 600, GROUND - 44, 82, 44)
        run.projectiles[:] = [shot, distant, Projectile("boss_orb", PLAYER_X, GROUND - 54, 54, 54)]
        self.assertTrue(run.skill())
        self.assertTrue(close.collected)
        self.assertFalse(far.collected)
        self.assertFalse(coin.collected)
        self.assertEqual(run.projectiles, [shot, distant])
        self.assertTrue(run.shield)
        self.assertEqual(run.skill_timer, 1.2)
        self.assertEqual(run.invulnerable, 1.2)

    def test_cream_protection_expires_then_shield_is_consumed_once(self):
        run = empty_run()
        run.skill()
        advance(run, 1.2)
        self.assertEqual(run.invulnerable, 0)
        self.assertEqual(run.skill_timer, 0)
        run.entities.append(Entity("crate", PLAYER_X + 12, GROUND - 64, 62, 64))
        events = advance(run, FIXED_STEP)
        self.assertTrue(run.alive)
        self.assertFalse(run.shield)
        self.assertEqual(events.count("shield"), 1)
        advance(run, 1)
        run.entities.append(Entity("crate", PLAYER_X + 12, GROUND - 64, 62, 64))
        advance(run, FIXED_STEP)
        self.assertFalse(run.alive)

    def test_berry_launches_from_air_and_restores_air_jump_without_stacking_magnet(self):
        run = empty_run("pink")
        run.jump()
        advance(run, 0.15)
        run.jump()
        run.set_slide(True)
        run.magnet = 6
        self.assertTrue(run.skill())
        self.assertEqual(run.player_vy, -900)
        self.assertEqual(run.jumps, 1)
        self.assertFalse(run.sliding)
        self.assertFalse(run._slide_held)
        self.assertEqual(run.magnet, 6)
        self.assertEqual(run.invulnerable, 0.8)
        self.assertTrue(run.jump())
        self.assertFalse(run.jump())
        ground = empty_run("pink")
        self.assertTrue(ground.skill())
        self.assertEqual(ground.magnet, 4)
        advance(ground, FIXED_STEP)
        self.assertLess(ground.player_y, GROUND)

    def test_nova_clears_enemy_shots_and_visible_forward_obstacles_and_caps_energy(self):
        run = empty_run("purple")
        behind = Entity("spike", PLAYER_X - 100, GROUND - 40, 74, 40)
        visible = Entity("crate", 800, GROUND - 64, 62, 64)
        future = Entity("drone", 1500, GROUND - 104, 88, 52)
        reward = Entity("glow", 800, GROUND - 60, 36, 36)
        run.entities[:] = [behind, visible, future, reward]
        shot = Projectile("shot", 800, 300)
        run.projectiles[:] = [shot, Projectile("boss_low", 1600, 536, 82, 44)]
        run.energy = 90
        self.assertTrue(run.skill())
        self.assertEqual(run.energy, 100)
        self.assertEqual(run.projectiles, [shot])
        self.assertEqual([e.collected for e in run.entities], [False, True, False, False])
        self.assertEqual(run.invulnerable, 0.5)

    def test_nova_damage_is_once_and_respects_entrance_and_defeat_rewards(self):
        for phase in ("warning", "fight", "weak", "defeated"):
            with self.subTest(phase=phase):
                run = empty_run("purple")
                run.boss = Boss(phase=phase, hp=100)
                run.skill()
                self.assertEqual(run.boss.hp, 65 if phase in ("fight", "weak") else 100)
                run.skill()
                self.assertEqual(run.boss.hp, 65 if phase in ("fight", "weak") else 100)
        winner = empty_run("purple", rewards=False)
        winner.boss = Boss(phase="weak", hp=35)
        self.assertTrue(winner.skill())
        self.assertEqual(winner.boss.phase, "defeated")
        self.assertEqual(winner.boss_defeated, 1)
        self.assertEqual(winner.coins, 50)
        self.assertEqual(winner.energy, 100)
        self.assertTrue(winner.shield)
        events = advance(winner, 2.5)
        self.assertEqual(events.count("boss_defeated"), 1)
        self.assertEqual(winner.coins, 50)
        self.assertEqual(winner.boss_defeated, 1)

    def test_pause_death_and_reward_choice_reject_every_skill_without_spending_cooldown(self):
        for character in HEROES:
            for blocked in ("pause", "dead", "choice"):
                with self.subTest(character=character, blocked=blocked):
                    run = empty_run(character)
                    if blocked == "pause":
                        run.set_paused(True)
                    elif blocked == "dead":
                        run.alive = False
                    else:
                        run.perk_choices = ["wing"]
                    self.assertFalse(run.skill())
                    self.assertEqual(run.skill_count, 0)
                    self.assertEqual(run.skill_cooldown, 0)
                    self.assertEqual(run.energy, 30)
                    self.assertEqual(run.projectiles, [])

    def test_pause_and_choices_freeze_cooldown_and_clear_held_inputs(self):
        run = empty_run("pink")
        run.skill()
        advance(run, 0.5)
        run.set_fire(True)
        run.set_slide(True)
        run.set_paused(True)
        state = (run.time, run.distance, run.player_y, run.skill_cooldown, run.skill_timer)
        self.assertFalse(run._fire_held)
        self.assertFalse(run._slide_held)
        self.assertFalse(run.jump())
        run.energy = 100
        self.assertFalse(run.dash())
        advance(run, 3)
        self.assertEqual((run.time, run.distance, run.player_y, run.skill_cooldown, run.skill_timer), state)
        run.set_paused(False)
        run.perk_choices = ["wing"]
        advance(run, 3)
        self.assertEqual((run.time, run.distance, run.player_y, run.skill_cooldown, run.skill_timer), state)
        self.assertTrue(run.choose_perk("wing"))
        advance(run, 9.5)
        self.assertEqual(run.skill_cooldown, 0)
        self.assertTrue(run.skill())
        self.assertEqual(run.skill_count, 2)

    def test_skill_cooldowns_reset_on_restart_and_have_no_frame_rate_drift(self):
        for character in HEROES:
            results = []
            for fps in (30, 60, 144):
                run = empty_run(character)
                run.skill()
                events = advance(run, HEROES[character]["cooldown"], fps)
                self.assertEqual(run.skill_cooldown, 0)
                self.assertTrue(run.skill())
                events += advance(run, 0.5, fps)
                results.append((run, events))
            reference, reference_events = results[0]
            for actual, events in results[1:]:
                for field in ("time", "distance", "player_y", "player_vy", "skill_cooldown", "skill_timer"):
                    self.assertAlmostEqual(getattr(actual, field), getattr(reference, field), places=9)
                self.assertEqual(events, reference_events)
            restarted = Run(character=character)
            self.assertEqual((restarted.skill_count, restarted.skill_cooldown, restarted.skill_timer), (0, 0, 0))


class MapIntegrationTests(unittest.TestCase):
    def test_map_change_waits_for_landing_and_preserves_gravity_in_midair(self):
        run = empty_run()
        run.route._bag = ["ruins", "dunes", "grove"]
        run.route.next_distance = 0
        run.jump()
        initial_vy = run.player_vy
        run.update(FIXED_STEP)
        self.assertEqual(run.route.key, "meadow")
        self.assertAlmostEqual(run.player_vy, initial_vy + 2100 * FIXED_STEP)
        events = advance(run, 1)
        self.assertEqual(run.route.key, "ruins")
        self.assertEqual(events.count("route_changed"), 1)
        self.assertEqual(run.jumps, 0)
        run.jump()
        initial_vy = run.player_vy
        run.update(FIXED_STEP)
        self.assertAlmostEqual(run.player_vy, initial_vy + 1650 * FIXED_STEP)

    def test_dash_bonus_boss_and_reward_selection_delay_map_switch(self):
        for blocked in ("dash", "bonus", "boss", "choice"):
            with self.subTest(blocked=blocked):
                run = empty_run()
                run.route.next_distance = 0
                if blocked == "dash":
                    run.dash_timer = 2
                elif blocked == "bonus":
                    run.bonus_timer = 2
                elif blocked == "boss":
                    run.boss = Boss()
                else:
                    run.perk_choices = ["wing"]
                advance(run, 1)
                self.assertEqual(run.route.key, "meadow")
                run.dash_timer = run.bonus_timer = 0
                run.boss = None
                run.perk_choices.clear()
                run.update(FIXED_STEP)
                self.assertNotEqual(run.route.key, "meadow")

    def test_map_change_clears_close_hazards_and_keeps_a_safe_spawn_delay(self):
        run = empty_run()
        run.route.next_distance = 0
        run.entities.append(Entity("crate", PLAYER_X + 12, GROUND - 64, 62, 64))
        run.update(FIXED_STEP)
        self.assertTrue(run.alive)
        self.assertFalse(any(e.kind in OBSTACLES for e in run.entities))
        self.assertAlmostEqual(run._spawn_timer, 2.65)
        advance(run, 2.6)
        self.assertFalse(any(e.kind in OBSTACLES for e in run.entities))
        advance(run, 0.1)
        self.assertTrue(any(e.kind in OBSTACLES for e in run.entities))

    def test_spring_only_launches_from_ground_and_preserves_remaining_air_jump(self):
        grounded, airborne = empty_run(), empty_run()
        for run in (grounded, airborne):
            run.entities.append(Entity("spring", PLAYER_X + 10, GROUND - 16, 60, 16))
        airborne.player_y = GROUND - 1
        airborne.player_vy = -100
        airborne.jumps = 1
        events = advance(grounded, FIXED_STEP)
        advance(airborne, FIXED_STEP)
        self.assertEqual(events.count("spring"), 1)
        self.assertEqual(grounded.player_vy, -950)
        self.assertEqual(grounded.jumps, 1)
        self.assertTrue(grounded.jump())
        self.assertFalse(airborne.entities[0].collected)
        self.assertNotEqual(airborne.player_vy, -950)
        self.assertTrue(grounded.alive)

    def test_treasure_and_glow_are_collected_once_without_advancing_combo(self):
        for kind, expected_coins, expected_energy in (("treasure", 15, 45), ("glow", 0, 50)):
            with self.subTest(kind=kind):
                run = empty_run()
                run.combo = 4
                run.entities.append(Entity(kind, PLAYER_X + 12, GROUND - 45, 36, 36))
                events = advance(run, FIXED_STEP)
                self.assertEqual((run.coins, run.energy, run.combo), (expected_coins, expected_energy, 4))
                self.assertEqual(events.count(kind), 1)
                if kind == "treasure":
                    self.assertEqual(run.score - int(run.distance * 5), 150)
                else:
                    self.assertEqual(run.magnet, 3)
                advance(run, 1)
                self.assertEqual(run.coins, expected_coins)
                self.assertEqual(run.energy, expected_energy)

    def test_special_segments_are_separated_from_hazards_and_ruins_raise_jump_arcs(self):
        for map_key, special in (("meadow", "spring"), ("dunes", "treasure"), ("grove", "glow"), ("ruins", "air_coins")):
            run = empty_run()
            run.route.key = map_key
            run._pattern_count = 3
            run._last_obstacle_world_x = -10000
            run._spawn_pattern()
            hazard = next(e for e in run.entities if e.kind in OBSTACLES)
            if special == "air_coins":
                high = [e for e in run.entities if e.kind == "coin" and e.x > hazard.x + 400]
                self.assertEqual(len(high), 5)
                self.assertTrue(all(e.y < GROUND - 230 for e in high))
            else:
                item = next(e for e in run.entities if e.kind == special)
                self.assertEqual(item.x - hazard.x, 450)
                self.assertGreater(item.x - hazard.x - hazard.w, 350)
                if special == "spring":
                    reward_coins = [e for e in run.entities if e.kind == "coin" and e.x > item.x]
                    self.assertEqual(len(reward_coins), 5)
                    self.assertEqual(reward_coins[0].x + 12 - item.x, 60)
                    self.assertEqual(reward_coins[-1].x + 12 - item.x, 260)
        base, ruins = empty_run(), empty_run()
        ruins.route.key = "ruins"
        for run in (base, ruins):
            run._pattern_count = 0
            run._spawn_pattern()
        base_arc = [e.y for e in base.entities if e.kind == "coin"][:9]
        ruins_arc = [e.y for e in ruins.entities if e.kind == "coin"][:9]
        self.assertEqual([b - r for b, r in zip(base_arc, ruins_arc)], [45] * 9)
        self.assertFalse(OBSTACLES & SPECIAL_KINDS)

    def test_spring_reserves_landing_and_reaction_before_the_next_hazard_in_either_gravity(self):
        for speed, elapsed in ((350, 0), (620, 180)):
            generated = empty_run()
            generated.speed = speed
            generated.time = elapsed
            generated._pattern_count = 3
            generated._spawn_pattern()
            spring_world = generated._last_spring_world_x
            generated.distance = 100
            generated.entities.clear()
            generated._spawn_pattern()
            hazard = next(e for e in generated.entities if e.kind in OBSTACLES)
            gap = generated.distance * 25 + hazard.x - spring_world
            self.assertGreaterEqual(gap, (speed + 15) * 1.6 + 70)
            for route_key in ("meadow", "ruins"):
                with self.subTest(speed=speed, route=route_key):
                    run = empty_run()
                    run.time = elapsed
                    run.speed = speed
                    run.route.key = route_key
                    following = Entity("crate", PLAYER_X + 10 + gap, GROUND - 64, 62, 64)
                    run.entities[:] = [Entity("spring", PLAYER_X + 10, GROUND - 16, 60, 16), following]
                    run.update(FIXED_STEP)
                    self.assertEqual(run.jumps, 1)
                    for _ in range(180):
                        run.update(FIXED_STEP)
                        if run.jumps == 0:
                            break
                    self.assertEqual(run.jumps, 0)
                    self.assertTrue(run.alive)
                    self.assertGreater(following.x - PLAYER_X - 52, run.speed * 0.3)


if __name__ == "__main__":
    unittest.main()
