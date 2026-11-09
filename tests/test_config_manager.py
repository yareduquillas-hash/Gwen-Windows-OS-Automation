from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from utils.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_override_is_written_as_valid_json(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            manager = ConfigManager(SimpleNamespace(data_dir=Path(temp)))
            manager.override("user_name", "Tester")

            data = json.loads((Path(temp) / "config_override.json").read_text(encoding="utf-8"))
            self.assertEqual(data["overrides"]["user_name"], "Tester")
            self.assertTrue(list((Path(temp) / "config_backups").glob("backup_*.json")))


if __name__ == "__main__":
    unittest.main()
