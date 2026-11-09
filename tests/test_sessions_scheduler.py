from __future__ import annotations

import time
import unittest

from modules.secciones import get_seccion, set_seccion
from utils.scheduler import _calcular_proxima


class SessionSchedulerTests(unittest.TestCase):
    def test_sections_are_isolated_by_chat(self):
        set_seccion(1, "uno", chat_id=101)
        set_seccion(2, "dos", chat_id=202)
        self.assertEqual(get_seccion(101), (1, "uno"))
        self.assertEqual(get_seccion(202), (2, "dos"))
        set_seccion(None, chat_id=101)
        set_seccion(None, chat_id=202)

    def test_zero_interval_is_clamped(self):
        next_run = _calcular_proxima("intervalo", intervalo_seg=0)
        self.assertGreaterEqual(next_run, time.time())


if __name__ == "__main__":
    unittest.main()
