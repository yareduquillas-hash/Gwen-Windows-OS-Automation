from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from modules.archivos import _ruta_segura
from modules.descargas import _host_publico, _safe_archive_target
from utils.file_uploader import is_safe_to_send


class FileSecurityTests(unittest.TestCase):
    def test_sensitive_file_is_not_sendable(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            secret = root / "credentials.json"
            secret.write_text("{}", encoding="utf-8")
            cfg = SimpleNamespace(project_root=root)

            self.assertIsNone(_ruta_segura(str(secret), cfg))
            self.assertFalse(is_safe_to_send(str(secret)))

    def test_regular_file_inside_root_is_allowed(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            regular = root / "nota.txt"
            regular.write_text("ok", encoding="utf-8")
            cfg = SimpleNamespace(project_root=root)

            self.assertEqual(_ruta_segura(str(regular), cfg), str(regular.resolve()))
            self.assertTrue(is_safe_to_send(str(regular)))

    def test_archive_cannot_escape_destination(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            destination = Path(temp) / "extract"
            destination.mkdir()
            with self.assertRaises(ValueError):
                _safe_archive_target(destination, "../outside.txt")

    def test_download_rejects_private_host(self):
        self.assertFalse(_host_publico("127.0.0.1"))
        self.assertFalse(_host_publico("localhost"))


if __name__ == "__main__":
    unittest.main()
