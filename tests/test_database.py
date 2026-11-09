from __future__ import annotations

import unittest

from database.connection import ConnectionManager


class DatabaseTests(unittest.TestCase):
    def test_write_detection_skips_comments(self):
        self.assertTrue(ConnectionManager._is_write("-- note\n INSERT INTO test VALUES (1)"))
        self.assertTrue(ConnectionManager._is_write("/* note */ UPDATE test SET value = 1"))
        self.assertFalse(ConnectionManager._is_write("SELECT * FROM test"))


if __name__ == "__main__":
    unittest.main()
