from __future__ import annotations

from modules.base import BaseModule


class MediosModule(BaseModule):
    nombre = "medios"
    prioridad = 60

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "pausa", "pausar", "pause", "play", "reanuda", "reanudar",
            "continua", "dale play", "siguiente", "next", "skip",
            "anterior", "prev", "previous", "atras", "retrocede",
            "pausa la musica", "reanuda la musica",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if any(p in t for p in ("pausa", "pausar", "pause", "pausa la musica")):
            ok = platform.send_media_key("pause")
            bot.send_message(chat_id, "Música pausada, Señor." if ok else "No pude pausar, Señor.")
            return True

        if any(p in t for p in ("reanuda", "reanudar", "play", "continua", "dale play", "reanuda la musica")):
            ok = platform.send_media_key("play")
            bot.send_message(chat_id, "Reanudando, Señor." if ok else "No pude reanudar, Señor.")
            return True

        if any(p in t for p in ("siguiente", "next", "skip", "saltar")):
            ok = platform.send_media_key("next")
            bot.send_message(chat_id, "Siguiente pista, Señor." if ok else "No pude avanzar, Señor.")
            return True

        if any(p in t for p in ("anterior", "prev", "previous", "atras", "retrocede")):
            ok = platform.send_media_key("prev")
            bot.send_message(chat_id, "Retrocediendo, Señor." if ok else "No pude retroceder, Señor.")
            return True

        return False


MODULE_CLASS = MediosModule
