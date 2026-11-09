from __future__ import annotations

import logging

from .contracts import InboundMessage

log = logging.getLogger("jarvis.adapters.router")


class InputRouter:
    """Frontera unica entre adaptadores de entrada y ModuleRegistry."""

    def __init__(self, registry, cfg, max_text_chars: int = 4000):
        self.registry = registry
        self.cfg = cfg
        self.max_text_chars = max_text_chars

    def dispatch(self, event: InboundMessage, bot) -> bool:
        text = (event.text or "").strip()
        if not text:
            return False

        if len(text) > self.max_text_chars:
            self._reply(
                bot,
                event,
                f"El mensaje supera el limite de {self.max_text_chars} caracteres.",
            )
            return False

        try:
            chat_id = int(event.user_id)
        except (TypeError, ValueError):
            log.warning("user_id invalido en request_id=%s", event.request_id)
            self._reply(bot, event, "No pude identificar al usuario de la solicitud.")
            return False

        log.debug(
            "Entrada normalizada request_id=%s channel=%s user_id=%s",
            event.request_id,
            event.channel.value,
            chat_id,
        )
        self.registry.dispatch(text, chat_id, bot)
        return True

    @staticmethod
    def _reply(bot, event: InboundMessage, text: str) -> None:
        try:
            bot.send_message(int(event.user_id), text)
        except (TypeError, ValueError, AttributeError):
            log.warning("No se pudo responder request_id=%s", event.request_id)
