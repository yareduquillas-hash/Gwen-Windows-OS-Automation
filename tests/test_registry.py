from __future__ import annotations

import unittest

from modules.registry import ModuleRegistry


class RegistryConfig:
    modules_enabled = {"bateria": False}

    @staticmethod
    def is_module_enabled(name: str) -> bool:
        return RegistryConfig.modules_enabled.get(name, False)


class RegistryTests(unittest.TestCase):
    def test_disabled_module_can_be_loaded_and_enabled(self):
        registry = ModuleRegistry(RegistryConfig())

        self.assertFalse(registry.module_status()["bateria"])
        self.assertTrue(registry.set_module_enabled("bateria", True))
        self.assertTrue(registry.module_status()["bateria"])


if __name__ == "__main__":
    unittest.main()
