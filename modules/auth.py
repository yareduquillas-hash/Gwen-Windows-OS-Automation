from __future__ import annotations

import logging
import time as _time
from collections import defaultdict

log = logging.getLogger("jarvis.auth")


class Authorizer:
    def __init__(self, cfg):
        self.chat_id = cfg.telegram_chat_id
        self.max_age = cfg.message_max_age_seconds
        self.rate_limit = cfg.rate_limit_max_per_minute
        self._timestamps: defaultdict[int, list[float]] = defaultdict(list)

    def check(self, message) -> bool:
        if message.chat.id != self.chat_id:
            return False
        if int(_time.time()) - message.date > self.max_age:
            log.info("Mensaje ignorado por antigüedad")
            return False

        now = _time.time()
        window = [t for t in self._timestamps[message.chat.id] if now - t < 60]
        window.append(now)
        self._timestamps[message.chat.id] = window
        if len(window) > self.rate_limit:
            log.warning("Rate limit excedido para %s", message.chat.id)
            return False
        return True

    def deny(self, message, bot) -> None:
        if message.chat.id != self.chat_id:
            bot.reply_to(
                message,
                "Disculpe la intromisión, pero no tengo el placer de conocerle. "
                "El acceso a mis sistemas está reservado.",
            )
