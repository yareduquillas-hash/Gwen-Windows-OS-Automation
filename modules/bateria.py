from __future__ import annotations

from modules.base import BaseModule

BATERIA_FRASES = (
    "batería", "bateria", "estado de la batería", "estado de la bateria",
    "cuanta bateria", "cuánta batería", "nivel de batería", "nivel de bateria",
    "porcentaje de batería", "porcentaje de bateria",
)


class BateriaModule(BaseModule):
    nombre = "bateria"
    prioridad = 85

    def can_handle(self, texto: str) -> bool:
        return any(f in texto.lower() for f in BATERIA_FRASES)

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        data = platform.get_battery()
        if "error" in data:
            bot.send_message(chat_id, f"No encontré datos de la batería, {cfg.user_title}.")
        else:
            pct = data.get("percentage", "?")
            state = data.get("state", "")
            msg = f"Batería: {pct}"
            if state:
                msg += f" ({state})"
            bot.send_message(chat_id, f"{msg}, {cfg.full_name}.")
        return True


MODULE_CLASS = BateriaModule
