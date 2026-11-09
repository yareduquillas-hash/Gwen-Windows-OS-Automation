from __future__ import annotations

import os
import unittest

from utils.secrets import SecretStore


@unittest.skipUnless(os.name == "nt", "Credential Manager solo existe en Windows")
class SecretStoreTests(unittest.TestCase):
    def test_round_trip_without_exposing_value(self):
        store = SecretStore(service_name="GwenWindowsProTests")
        self.assertTrue(store.available)
        name = "round_trip_test"
        value = "test-value-not-a-production-secret"
        try:
            self.assertTrue(store.set(name, value))
            self.assertEqual(store.get(name), value)
        finally:
            store.delete(name)


if __name__ == "__main__":
    unittest.main()
