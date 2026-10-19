"""Exercise real SDL input and screen coordinates without touching user saves."""

import os
import unittest
from unittest import mock

import pygame

from runner.app import App
from runner.model import WIDTH, HEIGHT
from runner.storage import SaveData


class AppTests(unittest.TestCase):
    def setUp(self):
        environment = mock.patch.dict(os.environ, {
            "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
        })
        environment.start()
        self.addCleanup(environment.stop)
        reader = mock.patch("runner.app.load_save", side_effect=AssertionError(
            "Headless tests must not read the player's save"))
        writer = mock.patch("runner.app.save_data", side_effect=AssertionError(
            "Headless tests must not write the player's save"))
        self.load_save = reader.start()
        self.save_data = writer.start()
        self.addCleanup(reader.stop)
        self.addCleanup(writer.stop)
        self.addCleanup(pygame.quit)
        self.app = App(headless=True, seed=17)
        pygame.event.clear()

    def send(self, event_type, **attributes):
        pygame.event.post(pygame.event.Event(event_type, **attributes))
        self.app.events()

    def key_down(self, key):
        self.send(pygame.KEYDOWN, key=key)

    def key_up(self, key):
        self.send(pygame.KEYUP, key=key)

    def window_point(self, canvas_point):
        width, height = self.app.window.get_size()
        scale = min(width / WIDTH, height / HEIGHT)
        return (round((width - WIDTH * scale) / 2 + canvas_point[0] * scale),
                round((height - HEIGHT * scale) / 2 + canvas_point[1] * scale))

    def click_button(self, name, release=True):
        rect = next(rect for rect, action in self.app.buttons if action == name)
        position = self.window_point(rect.center)
        self.send(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
        if release:
            self.send(pygame.MOUSEBUTTONUP, button=1, pos=position)

    def test_headless_settings_and_settlement_never_access_user_save(self):
        self.assertEqual(self.app.data, SaveData())
        self.app.action("mute")
        self.app.start()
        self.app.run.coins = 12
        self.app.settle()
        self.assertEqual(self.app.data.total_coins, 12)
        self.load_save.assert_not_called()
        self.save_data.assert_not_called()

    def test_slide_remains_held_until_all_keyboard_keys_are_released(self):
        self.app.start()
        self.key_down(pygame.K_DOWN)
        self.key_down(pygame.K_s)
        self.assertTrue(self.app.run.sliding)
        self.key_up(pygame.K_s)
        self.assertTrue(self.app.run.sliding)
        self.key_up(pygame.K_DOWN)
        self.assertFalse(self.app.run.sliding)

    def test_unrelated_mouse_release_does_not_cancel_keyboard_slide(self):
        self.app.start()
        self.key_down(pygame.K_DOWN)
        self.send(pygame.MOUSEBUTTONUP, button=1, pos=(10, 10))
        self.assertTrue(self.app.run.sliding)
        self.key_up(pygame.K_DOWN)
        self.assertFalse(self.app.run.sliding)

    def test_mouse_slide_remains_held_after_keyboard_release(self):
        self.app.start()
        self.app.draw()
        self.click_button("slide", release=False)
        self.key_down(pygame.K_DOWN)
        self.key_up(pygame.K_DOWN)
        self.assertTrue(self.app.run.sliding)
        self.send(pygame.MOUSEBUTTONUP, button=1, pos=(10, 10))
        self.assertFalse(self.app.run.sliding)

    def test_focus_loss_pauses_simulation_and_clears_held_input(self):
        self.app.start()
        self.app.update(0.1)
        self.app.draw()
        self.click_button("slide", release=False)
        self.key_down(pygame.K_DOWN)
        before = (self.app.run.time, self.app.run.distance,
                  self.app.run.player_y, self.app.run.score)
        self.send(pygame.WINDOWFOCUSLOST)
        self.key_down(pygame.K_SPACE)
        for _ in range(10):
            self.app.update(0.1)
        self.assertEqual(self.app.scene, "pause")
        self.assertEqual((self.app.run.time, self.app.run.distance,
                          self.app.run.player_y, self.app.run.score), before)
        self.assertFalse(self.app.run.sliding)
        self.assertEqual(self.app.slide_keys, set())
        self.assertFalse(self.app.mouse_sliding)
        self.key_down(pygame.K_RETURN)
        self.app.update(0.1)
        self.assertEqual(self.app.scene, "run")
        self.assertGreater(self.app.run.time, before[0])
        self.assertFalse(self.app.run.sliding)

    def test_game_over_and_menu_cannot_bank_the_same_run_twice(self):
        self.app.start()
        run = self.app.run
        run.coins, run.distance, run.dash_count, run.score = 60, 520, 2, 1234
        run.alive = False
        self.app.update(0.1)
        self.assertEqual(self.app.scene, "over")
        self.assertEqual(self.app.reward, 75)
        self.assertEqual(self.app.data.total_coins, 135)
        self.app.settle()
        self.app.action("menu")
        self.app.settle()
        self.assertEqual(self.app.data.total_coins, 135)
        self.assertEqual(self.app.data.runs, 1)
        self.assertEqual(self.app.data.best_score, 1234)
        self.assertEqual(self.app.data.best_distance, 520)
        self.app.start()
        self.app.run.coins = 7
        self.app.action("pause")
        self.app.action("menu")
        self.assertEqual(self.app.data.total_coins, 142)
        self.assertEqual(self.app.data.runs, 2)

    def test_buttons_follow_letterboxed_window_coordinates(self):
        for size in ((800, 800), (1600, 720), (640, 360)):
            with self.subTest(size=size):
                self.app.window = pygame.display.set_mode(size, pygame.RESIZABLE)
                pygame.event.clear()
                self.app.scene = "menu"
                self.app.draw()
                canvas_center = (WIDTH / 2, HEIGHT / 2)
                mapped = self.app.pointer(self.window_point(canvas_center))
                self.assertAlmostEqual(mapped[0], canvas_center[0], delta=1)
                self.assertAlmostEqual(mapped[1], canvas_center[1], delta=1)
                if size == (800, 800):
                    self.send(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 30))
                    self.assertEqual(self.app.scene, "menu")
                self.click_button("start")
                self.assertEqual(self.app.scene, "run")

    def test_practice_can_be_opened_retried_and_never_banks_rewards(self):
        self.app.draw()
        self.click_button("practice")
        self.app.update(1 / 60)
        self.assertTrue(self.app.practice)
        self.assertIsNotNone(self.app.run.boss)
        self.assertEqual(self.app.run.boss.phase, "warning")
        self.app.run.coins = 70
        self.app.run.score = 10000
        self.app.run.boss.phase = "weak"
        self.app.run.boss.timer = 2.5
        self.app.run.boss.hp = 1
        self.key_down(pygame.K_k)
        for _ in range(45):
            self.app.update(.1)
        self.assertEqual(self.app.scene, "over")
        self.assertEqual(self.app.data, SaveData())
        self.key_down(pygame.K_RETURN)
        self.assertTrue(self.app.practice)
        self.assertEqual(self.app.scene, "run")
        self.assertEqual(self.app.run.boss_defeated, 0)

    def test_firing_combines_inputs_and_pause_clears_them(self):
        self.app.start(practice=True)
        self.app.update(1 / 60)
        for _ in range(20):
            self.app.update(.1)
        self.app.draw()
        self.key_down(pygame.K_k)
        self.key_down(pygame.K_x)
        self.key_up(pygame.K_k)
        self.app.update(.1)
        self.assertTrue(any(p.kind == "shot" for p in self.app.run.projectiles))
        self.click_button("fire", release=False)
        self.key_up(pygame.K_x)
        self.assertTrue(self.app.mouse_firing)
        self.app.action("pause")
        self.assertEqual(self.app.fire_keys, set())
        self.assertFalse(self.app.mouse_firing)
        self.app.run.projectiles.clear()
        self.app.action("resume")
        self.app.update(.1)
        self.assertFalse(any(p.kind == "shot" for p in self.app.run.projectiles))

    def test_workshop_purchase_changes_next_adventure_but_not_practice(self):
        self.app.data.total_coins = 80
        self.app.draw()
        self.click_button('workshop')
        self.app.draw()
        self.click_button('upgrade:dash')
        self.assertEqual(self.app.data.total_coins, 0)
        self.assertEqual(self.app.data.upgrades['dash'], 1)
        self.key_down(pygame.K_ESCAPE)
        self.app.start()
        self.app.run.energy = 100
        self.app.action('dash')
        self.assertAlmostEqual(self.app.run.dash_timer, 3.35)
        self.app.start(practice=True)
        self.app.action('dash')
        self.assertAlmostEqual(self.app.run.dash_timer, 3.0)

    def test_contract_bonus_is_banked_once_and_practice_does_not_progress(self):
        self.app.start()
        run = self.app.run
        run.distance, run.coins, run.boss_defeated = 1500, 250, 3
        self.app.action('pause')
        self.app.action('menu')
        self.assertEqual(self.app.contract_reward, 190)
        self.assertEqual(self.app.data.total_coins, 490)
        self.assertEqual(self.app.data.career_bosses, 3)
        self.app.settle()
        self.assertEqual(self.app.data.total_coins, 490)
        self.app.start(practice=True)
        self.app.run.distance, self.app.run.coins, self.app.run.boss_defeated = 9000, 900, 9
        self.app.settle()
        self.assertEqual(self.app.data.career_distance, 1500)
        self.assertEqual(self.app.data.career_coins, 250)
        self.assertEqual(self.app.data.career_bosses, 3)

    def test_actual_boss_victory_opens_frozen_perk_choice_and_keyboard_resumes(self):
        self.app.start()
        self.app.run.distance = 350
        self.app.update(.1)
        self.app.run.boss.phase = 'weak'
        self.app.run._damage_boss(1000)
        self.key_down(pygame.K_k)
        for _ in range(30):
            self.app.update(.1)
        self.assertEqual(self.app.scene, 'perks')
        self.assertEqual(len(self.app.run.perk_choices), 3)
        self.assertFalse(self.app.fire_keys)
        before = self.app.run.time
        self.app.update(.1)
        self.assertEqual(self.app.run.time, before)
        selected = self.app.run.perk_choices[0]
        self.key_down(pygame.K_1)
        self.assertEqual(self.app.scene, 'run')
        self.assertEqual(self.app.run.perks[selected], 1)
        self.app.update(.1)
        self.assertGreater(self.app.run.time, before)
        self.app.start()
        self.assertFalse(any(self.app.run.perks.values()))

    def test_leaving_perk_selection_banks_run_without_double_rewards(self):
        self.app.start()
        self.app.run.coins = 12
        self.app.run.perk_choices = ['wing', 'focus', 'magnet']
        self.app.update(.1)
        self.assertEqual(self.app.scene, 'perks')
        self.key_down(pygame.K_ESCAPE)
        self.assertEqual(self.app.scene, 'menu')
        self.assertEqual(self.app.data.total_coins, 12)
        self.assertEqual(self.app.data.runs, 1)
        self.app.action('menu')
        self.assertEqual(self.app.data.total_coins, 12)

    def test_window_close_during_perk_choice_banks_progress(self):
        self.app.start()
        self.app.run.coins = 9
        self.app.run.perk_choices = ['wing']
        self.app.update(.1)
        self.send(pygame.QUIT)
        self.assertFalse(self.app.running)
        self.assertEqual(self.app.data.total_coins, 9)
        self.assertEqual(self.app.data.runs, 1)


if __name__ == "__main__":
    unittest.main()
