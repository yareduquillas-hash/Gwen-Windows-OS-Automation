from __future__ import annotations

import unittest
from types import SimpleNamespace

from adapters import (
    InputChannel,
    InputRouter,
    TelegramInputAdapter,
    WebSocketInputAdapter,
)


class FakeRegistry:
    def __init__(self):
        self.calls = []

    def dispatch(self, text, chat_id, bot):
        self.calls.append((text, chat_id, bot))


class FakeBot:
    def __init__(self):
        self.messages = []

    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


class AdapterTests(unittest.TestCase):
    def test_telegram_message_is_normalized(self):
        message = SimpleNamespace(
            chat=SimpleNamespace(id=42),
            message_id=7,
            date=1700000000,
            content_type="text",
            text="  hola  ",
        )

        event = TelegramInputAdapter.from_message(message)

        self.assertEqual(event.channel, InputChannel.TELEGRAM)
        self.assertEqual(event.user_id, "42")
        self.assertEqual(event.text, "  hola  ")
        self.assertEqual(event.request_id, "telegram-42-7")

    def test_websocket_payload_is_normalized(self):
        event = WebSocketInputAdapter.from_payload(
            999999,
            {"type": "message", "text": "estado", "request_id": "req-1"},
        )

        self.assertEqual(event.channel, InputChannel.WEBSOCKET)
        self.assertEqual(event.user_id, "999999")
        self.assertEqual(event.request_id, "req-1")

    def test_router_dispatches_normalized_message(self):
        registry = FakeRegistry()
        bot = FakeBot()
        router = InputRouter(registry, cfg=None)
        event = WebSocketInputAdapter.from_payload(99, {"text": "bateria"})

        self.assertTrue(router.dispatch(event, bot))
        self.assertEqual(registry.calls[0][0:2], ("bateria", 99))

    def test_router_rejects_oversized_message(self):
        registry = FakeRegistry()
        bot = FakeBot()
        router = InputRouter(registry, cfg=None, max_text_chars=4)
        event = WebSocketInputAdapter.from_payload(99, {"text": "12345"})

        self.assertFalse(router.dispatch(event, bot))
        self.assertEqual(registry.calls, [])
        self.assertEqual(bot.messages[0][0], 99)


if __name__ == "__main__":
    unittest.main()
