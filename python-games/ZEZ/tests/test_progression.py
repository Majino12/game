"""Workshop and career rewards never touch an actual player's save."""

from copy import deepcopy
from dataclasses import asdict
import json
import math
from pathlib import Path
import tempfile
import unittest

from runner.storage import (
    MAX_PROGRESS, SaveData, buy_upgrade, contract_status, load_save,
    record_progress, save_data, upgrade_price,
)


class ProgressionSaveTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "save.json"

    def test_v1_and_unversioned_saves_keep_wallet_characters_records_and_settings(self):
        original = {"best_score": 9876, "best_distance": 1920,
                    "total_coins": 817, "runs": 14, "selected": "purple",
                    "unlocked": ["beige", "pink", "purple"],
                    "muted": True, "language": "en"}
        for version in (None, 1):
            with self.subTest(version=version):
                payload = dict(original)
                if version is not None:
                    payload["version"] = version
                self.path.write_text(json.dumps(payload), encoding="utf-8")
                loaded = load_save(self.path)
                for key, value in original.items():
                    self.assertEqual(getattr(loaded, key), value, key)
                self.assertEqual(loaded.upgrades, {"magnet": 0, "recharge": 0, "dash": 0})
                self.assertEqual(loaded.career_distance, 0)
                self.assertEqual(loaded.career_coins, 0)
                self.assertEqual(loaded.career_bosses, 0)
                self.assertEqual(loaded.contract_claims, {"distance": 0, "coins": 0, "bosses": 0})
                self.assertTrue(save_data(loaded, self.path))
                self.assertEqual(json.loads(self.path.read_text())["version"], 2)
                self.assertEqual(load_save(self.path), loaded)

    def test_progression_round_trip_retains_levels_and_claimed_rewards(self):
        data = SaveData(total_coins=1000)
        self.assertTrue(buy_upgrade(data, "magnet"))
        self.assertTrue(buy_upgrade(data, "magnet"))
        self.assertTrue(buy_upgrade(data, "dash"))
        record_progress(data, 3100.75, 600, 4)
        self.assertTrue(save_data(data, self.path))
        loaded = load_save(self.path)
        self.assertEqual(loaded, data)
        self.assertEqual(record_progress(loaded, 0, 0, 0)["bonus"], 0)
        self.assertEqual(loaded.total_coins, data.total_coins)

    def test_corrupt_new_fields_are_repaired_without_discarding_old_wallet(self):
        payload = {"version": 2, "total_coins": 735, "best_score": 1200,
                   "selected": "purple", "unlocked": ["beige", "purple"],
                   "upgrades": {"magnet": True, "recharge": 4, "dash": -1, "unknown": 3},
                   "career_distance": float("nan"), "career_coins": True,
                   "career_bosses": -8, "contract_claims": [1, 2, 3]}
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_save(self.path)
        self.assertEqual(loaded.total_coins, 735)
        self.assertEqual(loaded.best_score, 1200)
        self.assertEqual(loaded.selected, "purple")
        self.assertEqual(loaded.unlocked, ["beige", "purple"])
        self.assertEqual(loaded.upgrades, {"magnet": 0, "recharge": 0, "dash": 0})
        self.assertEqual([item["progress"] for item in contract_status(loaded)], [0, 0, 0])
        self.assertTrue(save_data(loaded, self.path))
        self.assertNotIn("NaN", self.path.read_text())

    def test_malformed_nested_fields_and_overstated_claims_are_safe(self):
        payload = {"version": 2, "total_coins": 99, "upgrades": ["magnet", 3],
                   "career_distance": 3000, "career_coins": 500, "career_bosses": 3,
                   "contract_claims": {"distance": 999999, "coins": 2, "bosses": 1}}
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        data = load_save(self.path)
        self.assertEqual(data.upgrades, {"magnet": 0, "recharge": 0, "dash": 0})
        self.assertEqual(data.contract_claims, {"distance": 2, "coins": 2, "bosses": 1})
        self.assertEqual(record_progress(data, 0, 0, 0)["bonus"], 0)
        self.assertEqual(data.total_coins, 99)

    def test_nested_default_values_are_not_shared_between_players(self):
        first, second = SaveData(), SaveData()
        first.upgrades["magnet"] = 2
        first.contract_claims["coins"] = 3
        self.assertEqual(second.upgrades["magnet"], 0)
        self.assertEqual(second.contract_claims["coins"], 0)


class UpgradeTests(unittest.TestCase):
    def test_each_upgrade_charges_three_tiers_and_stops_at_level_three(self):
        data = SaveData(total_coins=1560)
        for key in ("magnet", "recharge", "dash"):
            for level, price in enumerate((80, 160, 280), start=1):
                self.assertEqual(upgrade_price(data, key), price)
                wallet_before = data.total_coins
                self.assertTrue(buy_upgrade(data, key))
                self.assertEqual(data.total_coins, wallet_before - price)
                self.assertEqual(data.upgrades[key], level)
            before = deepcopy(data)
            self.assertIsNone(upgrade_price(data, key))
            self.assertFalse(buy_upgrade(data, key))
            self.assertEqual(data, before)
        self.assertEqual(data.total_coins, 0)

    def test_insufficient_money_or_unknown_upgrade_has_no_side_effect(self):
        data = SaveData(total_coins=79)
        for key in ("magnet", "unknown", None, [], True):
            with self.subTest(key=key):
                before = deepcopy(data)
                self.assertFalse(buy_upgrade(data, key))
                self.assertEqual(data, before)
        self.assertIsNone(upgrade_price(data, "unknown"))
        data.total_coins = True
        self.assertFalse(buy_upgrade(data, "dash"))
        self.assertEqual(data.upgrades["dash"], 0)

    def test_price_is_read_only_and_invalid_levels_do_not_crash(self):
        for malformed in (None, [], {"magnet": []}, {"magnet": math.nan}, {"magnet": 300}):
            with self.subTest(upgrades=malformed):
                data = SaveData(total_coins=80, upgrades=deepcopy(malformed))
                self.assertEqual(upgrade_price(data, "magnet"), 80)
                self.assertEqual(data.upgrades, malformed)
                self.assertTrue(buy_upgrade(data, "magnet"))
                self.assertEqual(data.upgrades["magnet"], 1)
                self.assertEqual(data.total_coins, 0)


class CareerContractTests(unittest.TestCase):
    def test_contracts_accumulate_across_runs_and_do_not_bank_raw_run_income(self):
        data = SaveData(total_coins=10, best_score=25, best_distance=30, runs=2)
        first = record_progress(data, 600.25, 100, 1)
        self.assertEqual(first["bonus"], 0)
        self.assertEqual(first["completed"], [])
        self.assertEqual(data.total_coins, 10)
        second = record_progress(data, 899.75, 150, 2)
        self.assertEqual(second["bonus"], 190)
        self.assertEqual(second["completed_levels"], 3)
        self.assertEqual(data.total_coins, 200)
        self.assertEqual(data.contract_claims, {"distance": 1, "coins": 1, "bosses": 1})
        self.assertEqual((data.best_score, data.best_distance, data.runs), (25, 30, 2))
        third = record_progress(data, 500, 10, 1)
        self.assertEqual(third["bonus"], 0)
        status = {item["key"]: item for item in contract_status(data)}
        self.assertEqual((status["distance"]["progress"], status["distance"]["target"]), (2000, 3000))
        self.assertEqual((status["coins"]["progress"], status["coins"]["target"]), (260, 500))
        self.assertEqual((status["bosses"]["progress"], status["bosses"]["target"]), (4, 6))

    def test_crossing_many_thresholds_awards_each_new_level_once(self):
        data = SaveData()
        result = record_progress(data, 4500, 1000, 6)
        self.assertEqual(result["bonus"], 520)
        self.assertEqual(result["completed_levels"], 9)
        self.assertEqual(len(result["completed"]), 3)
        completed = {item["key"]: item for item in result["completed"]}
        self.assertEqual(completed["distance"]["levels"], 3)
        self.assertEqual(completed["coins"]["levels"], 4)
        self.assertEqual(completed["bosses"]["levels"], 2)
        self.assertEqual(sum(item["bonus"] for item in result["completed"]), 520)
        self.assertEqual(record_progress(data, 0, 0, 0)["bonus"], 0)
        self.assertEqual(data.total_coins, 520)
        result = record_progress(data, 1500, 0, 0)
        self.assertEqual(result["bonus"], 40)
        self.assertEqual(result["completed"][0]["level"], 4)

    def test_contract_coin_rewards_never_feed_their_own_progress(self):
        data = SaveData(total_coins=250)
        result = record_progress(data, 0, 250, 0)
        self.assertEqual(result["bonus"], 50)
        self.assertEqual(data.total_coins, 300)
        self.assertEqual(data.career_coins, 250)
        self.assertEqual(record_progress(data, 0, 200, 0)["bonus"], 0)
        self.assertEqual(data.career_coins, 450)
        self.assertEqual(data.total_coins, 300)
        self.assertEqual(record_progress(data, 0, 50, 0)["bonus"], 50)
        self.assertEqual(data.career_coins, 500)
        self.assertEqual(data.total_coins, 350)

    def test_status_has_localized_labels_next_targets_and_no_side_effects(self):
        data = SaveData()
        before = asdict(data)
        rows = contract_status(data)
        self.assertEqual([row["key"] for row in rows], ["distance", "coins", "bosses"])
        self.assertEqual([row["target"] for row in rows], [1500, 250, 3])
        self.assertEqual([row["reward"] for row in rows], [40, 50, 100])
        for row in rows:
            self.assertTrue(row["title"])
            self.assertTrue(row["title_en"])
            self.assertEqual(row["level"], 0)
            self.assertEqual(row["progress"], 0)
        self.assertEqual(asdict(data), before)

    def test_invalid_values_are_ignored_without_resetting_valid_progress(self):
        data = SaveData(career_distance=200.5, career_coins=20, career_bosses=1, total_coins=88)
        invalid = (None, True, False, -1, float("nan"), float("inf"),
                   -float("inf"), "250", [], {}, MAX_PROGRESS + 1)
        for value in invalid:
            with self.subTest(value=value):
                result = record_progress(data, value, value, value)
                self.assertEqual(result["bonus"], 0)
                self.assertEqual(result["completed"], [])
                self.assertEqual((data.career_distance, data.career_coins, data.career_bosses), (200.5, 20, 1))
                self.assertEqual(data.total_coins, 88)
        result = record_progress(data, 0.5, 1.5, 1.5)
        self.assertEqual((result["distance"], result["coins"], result["bosses"]), (0.5, 0, 0))

    def test_counter_saturation_is_finite_and_does_not_allocate_per_level(self):
        data = SaveData(career_distance=MAX_PROGRESS - 10, career_coins=MAX_PROGRESS - 10,
                        career_bosses=MAX_PROGRESS - 10)
        result = record_progress(data, 20, 20, 20)
        self.assertEqual((result["distance"], result["coins"], result["bosses"]), (10, 10, 10))
        self.assertEqual((data.career_distance, data.career_coins, data.career_bosses), (MAX_PROGRESS,) * 3)
        self.assertLessEqual(len(result["completed"]), 3)
        self.assertTrue(math.isfinite(data.career_distance))
        self.assertEqual(record_progress(data, 20, 20, 20)["bonus"], 0)


if __name__ == "__main__":
    unittest.main()
