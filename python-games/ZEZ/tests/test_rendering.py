"""Render real assets and new UI branches with SDL dummy video, without files."""

import hashlib
import os
import unittest
from unittest import mock

import pygame

from runner.app import App
from runner.content import BOSS_SPECS
from runner.model import Entity, GROUND, HEIGHT, WIDTH
from runner.routes import MAPS


class RenderingTests(unittest.TestCase):
    def setUp(self):
        environment = mock.patch.dict(os.environ, {
            'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy',
        })
        environment.start()
        self.addCleanup(environment.stop)
        for name in ('load_save', 'save_data'):
            patcher = mock.patch('runner.app.' + name, side_effect=AssertionError('Rendering must not access player saves'))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(pygame.quit)
        self.app = App(headless=True, seed=17)
        pygame.event.clear()

    def fingerprint(self, rect=None):
        surface = self.app.canvas.subsurface(rect) if rect else self.app.canvas
        return hashlib.sha256(pygame.image.tobytes(surface, 'RGB')).digest()

    def test_four_map_worlds_render_distinct_scenes_with_all_controls_in_bounds(self):
        self.app.start()
        self.app.run.entities.clear()
        frames = set()
        for key in MAPS:
            with self.subTest(map=key):
                self.app.run.route.key = key
                self.app.draw()
                frames.add(self.fingerprint())
                actions = {action for _, action in self.app.buttons}
                self.assertTrue({'skill', 'dash', 'slide', 'jump'} <= actions)
                for rect, action in self.app.buttons:
                    self.assertTrue(pygame.Rect(0, 0, WIDTH, HEIGHT).contains(rect), action)
        self.assertEqual(len(frames), 4)

    def test_map_special_objects_change_the_real_world_image(self):
        self.app.start()
        self.app.run.entities.clear()
        crop = pygame.Rect(550, GROUND - 180, 180, 180)
        for key, entity in (
            ('meadow', Entity('spring', 600, GROUND - 16, 60, 16)),
            ('dunes', Entity('treasure', 600, GROUND - 130, 38, 32)),
            ('grove', Entity('glow', 600, GROUND - 60, 36, 36)),
            ('ruins', Entity('coin', 600, GROUND - 150, 24, 24)),
        ):
            with self.subTest(kind=entity.kind):
                self.app.run.route.key = key
                self.app.run.entities.clear()
                self.app.draw()
                before = self.fingerprint(crop)
                self.app.run.entities.append(entity)
                self.app.draw()
                self.assertNotEqual(self.fingerprint(crop), before)

    def test_maps_and_boss_selection_pages_render_in_both_languages(self):
        for language in ('zh', 'en'):
            for scene in ('menu', 'maps', 'practice'):
                with self.subTest(language=language, scene=scene):
                    self.app.lang = language
                    self.app.scene = scene
                    self.app.draw()
                    self.assertEqual(self.app.canvas.get_size(), (WIDTH, HEIGHT))
                    actions = {action for _, action in self.app.buttons}
                    if scene == 'practice':
                        self.assertTrue({'practice:' + kind for kind in BOSS_SPECS} <= actions)
                    elif scene == 'maps':
                        self.assertIn('menu', actions)
                    else:
                        self.assertTrue({'maps', 'practice', 'start'} <= actions)

    def test_crystal_locked_lane_warning_and_orb_render_from_real_boss_cycle(self):
        self.app.practice_boss = 'crystal'
        self.app.start(practice=True)
        self.app.update(1 / 60)
        boss = self.app.run.boss
        self.assertEqual(boss.kind, 'crystal')
        for _ in range(30):
            if boss.phase == 'fight':
                break
            self.app.update(.1)
        self.assertEqual(boss.phase, 'fight')
        self.assertEqual(boss.attack, 'aim')
        self.assertGreater(boss.telegraph, 0)
        lane = pygame.Rect(350, int(boss.target_y - 27), 500, 50)
        for language in ('zh', 'en'):
            self.app.lang = language
            self.app.draw()
            active_lane = self.fingerprint(lane)
            telegraph = boss.telegraph
            boss.telegraph = 0
            self.app.draw()
            inactive_lane = self.fingerprint(lane)
            boss.telegraph = telegraph
            self.assertNotEqual(active_lane, inactive_lane)
        for _ in range(20):
            if any(p.kind == 'boss_orb' for p in self.app.run.projectiles):
                break
            self.app.update(.1)
        self.assertTrue(any(p.kind == 'boss_orb' for p in self.app.run.projectiles))
        self.app.draw()
        self.assertIn('fire', {action for _, action in self.app.buttons})
        self.assertTrue(self.app.run.alive)

    def test_character_preview_argument_and_active_skill_render_for_each_runner(self):
        for character in ('beige', 'pink', 'purple'):
            with self.subTest(character=character):
                app = App(headless=True, seed=17, character=character, boss_kind='crystal')
                self.assertEqual(app.data.selected, character)
                self.assertEqual(app.practice_boss, 'crystal')
                app.start()
                self.assertEqual(app.run.character, character)
                app.action('skill')
                app.update(1 / 60)
                app.draw()
                self.assertGreater(app.run.skill_timer, 0)
                self.assertEqual(app.run.skill_count, 1)


if __name__ == '__main__':
    unittest.main()
