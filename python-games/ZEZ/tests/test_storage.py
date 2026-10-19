"""Persistence tests use temporary directories, never a player's real save."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from runner.storage import SaveData, load_save, purchase, save_data, save_path


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested" / "save.json"

    def write_raw(self, payload):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(payload, encoding="utf-8")

    def test_missing_save_has_independent_defaults(self):
        first = load_save(self.path)
        first.unlocked.append("pink")
        self.assertEqual(load_save(self.path), SaveData())
        self.assertFalse(self.path.exists())

    def test_round_trip_all_fields_and_version(self):
        original = SaveData(best_score=6540, best_distance=420, total_coins=80,
                            runs=4, selected="pink", unlocked=["beige", "pink"],
                            muted=True, language="en")
        self.assertTrue(save_data(original, self.path))
        self.assertEqual(load_save(self.path), original)
        self.assertEqual(json.loads(self.path.read_text())["version"], 2)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_broken_json_is_preserved_and_backed_up(self):
        original = '{"best_score": 450, truncated'
        self.write_raw(original)
        self.assertEqual(load_save(self.path), SaveData())
        self.assertEqual(self.path.read_text(), original)
        backups = list(self.path.parent.glob("save.json.corrupt-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), original)

    def test_invalid_values_are_rejected(self):
        for payload in ({"best_score": True}, {"total_coins": -3},
                        {"runs": "5"}, {"best_distance": 1.2},
                        {"version": True}, {"version": 3},
                        {"unlocked": ["injected"]}, {"muted": 1},
                        {"selected": []}, {"language": []}, []):
            with self.subTest(payload=payload):
                self.write_raw(json.dumps(payload))
                self.assertEqual(load_save(self.path), SaveData())

    def test_locked_character_and_duplicate_ownership_are_repaired(self):
        self.write_raw(json.dumps({"selected": "purple", "unlocked": ["pink", "pink"]}))
        loaded = load_save(self.path)
        self.assertEqual(loaded.selected, "beige")
        self.assertEqual(loaded.unlocked, ["beige", "pink"])

    def test_failed_atomic_replace_keeps_existing_save_and_cleans_temp(self):
        self.assertTrue(save_data(SaveData(best_score=12), self.path))
        with mock.patch("runner.storage.os.replace", side_effect=PermissionError("read only")):
            self.assertFalse(save_data(SaveData(best_score=99), self.path))
        self.assertEqual(load_save(self.path).best_score, 12)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_unreadable_file_and_failed_backup_do_not_crash(self):
        self.write_raw("bad json")
        with mock.patch("runner.storage.shutil.copy2", side_effect=PermissionError):
            self.assertEqual(load_save(self.path), SaveData())
        with mock.patch("pathlib.Path.open", side_effect=PermissionError):
            self.assertEqual(load_save(self.path), SaveData())

    def test_invalid_in_memory_data_does_not_replace_save(self):
        self.assertTrue(save_data(SaveData(best_score=9), self.path))
        self.assertFalse(save_data(SaveData(total_coins=True), self.path))
        self.assertEqual(load_save(self.path).best_score, 9)

    def test_override_directory(self):
        with mock.patch.dict(os.environ, {"ZEZ_SAVE_DIR": self.directory.name}):
            self.assertEqual(save_path(), Path(self.directory.name) / "save.json")
            self.assertTrue(save_data(SaveData(runs=3)))
            self.assertEqual(load_save().runs, 3)

    def test_platform_paths(self):
        base = Path(self.directory.name)
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("pathlib.Path.home", return_value=base):
            with mock.patch("runner.storage.sys.platform", "darwin"):
                self.assertEqual(save_path(), base / "Library/Application Support/ZEZ/save.json")
            with mock.patch("runner.storage.sys.platform", "win32"):
                self.assertEqual(save_path(), base / "AppData/Local/ZEZ/save.json")
            with mock.patch("runner.storage.sys.platform", "linux"):
                self.assertEqual(save_path(), base / ".local/share/zez/save.json")
                with mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(base / "custom")}):
                    self.assertEqual(save_path(), base / "custom/zez/save.json")

    def test_purchase_charges_once_and_can_select_owned_character(self):
        data = SaveData(total_coins=350)
        self.assertTrue(purchase(data, "pink"))
        self.assertEqual(data.total_coins, 250)
        self.assertEqual(data.selected, "pink")
        self.assertTrue(purchase(data, "pink"))
        self.assertEqual(data.total_coins, 250)
        self.assertTrue(purchase(data, "purple"))
        self.assertEqual(data.total_coins, 0)
        self.assertTrue(purchase(data, "beige"))
        self.assertEqual(data.selected, "beige")
        self.assertEqual(data.unlocked, ["beige", "pink", "purple"])

    def test_rejected_purchase_does_not_change_save(self):
        data = SaveData(total_coins=99)
        self.assertFalse(purchase(data, "pink"))
        self.assertFalse(purchase(data, "unknown"))
        self.assertEqual(data, SaveData(total_coins=99))


if __name__ == "__main__":
    unittest.main()
