from __future__ import annotations

import time
import unittest

from adapters.policy import Capability, CapabilityPolicy, RiskLevel


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = CapabilityPolicy()

    def test_capability_risk_levels(self):
        self.assertEqual(self.policy.get_risk(Capability.SYSTEM_READ), RiskLevel.READ)
        self.assertEqual(self.policy.get_risk(Capability.FILE_UPLOAD), RiskLevel.EXTERNAL_UPLOAD)
        self.assertEqual(self.policy.get_risk(Capability.PROCESS_TERMINATE), RiskLevel.DESTRUCTIVE)
        self.assertEqual(self.policy.get_risk(Capability.SYSTEM_RESTART), RiskLevel.DESTRUCTIVE)

    def test_confirmation_lifecycle(self):
        user_id = "test-user-123"
        action = "restart"

        # Sin confirmacion previa
        self.assertFalse(self.policy.verify_confirmation(user_id, action))

        # Registrar confirmacion con TTL
        self.policy.request_confirmation(user_id, action, ttl_seconds=2.0)
        self.assertTrue(self.policy.verify_confirmation(user_id, action))

        # Ya fue consumida
        self.assertFalse(self.policy.verify_confirmation(user_id, action))

    def test_confirmation_expires(self):
        user_id = "test-user-exp"
        action = "kill_proc"

        self.policy.request_confirmation(user_id, action, ttl_seconds=0.05)
        time.sleep(0.06)
        self.assertFalse(self.policy.verify_confirmation(user_id, action))


if __name__ == "__main__":
    unittest.main()
