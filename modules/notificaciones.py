from __future__ import annotations

from modules.base import BaseModule


class NotificacionesModule(BaseModule):
    nombre = "notificaciones"
    prioridad = 55

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return t.startswith("notifícame") or t.startswith("notificame") or "notificación" in t

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if "notifícame" in t or "notificame" in t:
            platform.send_notification("JARVIS", texto)
            bot.send_message(chat_id, "Notificación enviada a su escritorio, Señor.")
            return True

        return False


MODULE_CLASS = NotificacionesModule
