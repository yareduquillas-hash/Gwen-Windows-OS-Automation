from __future__ import annotations

import re

from modules.base import BaseModule


class VolumenModule(BaseModule):
    nombre = "volumen"
    prioridad = 65

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        prefijos = ("volumen", "vol", "sube volumen", "baja volumen",
                     "pon volumen", "silencia", "silenciar")
        return any(t.startswith(p) for p in prefijos) or any(
            q in t for q in ("cual es el volumen", "cómo está el volumen",
                             "como esta el volumen", "nivel de volumen")
        )

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if "silencia" in t or "silenciar" in t:
            if "micro" in t or "micrófono" in t:
                bot.send_message(
                    chat_id,
                    "El control de mute del micrófono todavía no está disponible; no modificaré el volumen maestro, Señor.",
                )
            else:
                platform.set_volume(0)
                bot.send_message(chat_id, "Volumen silenciado, Señor.")
            return True

        if any(q in t for q in ("cual es el volumen", "cómo está el volumen",
                                  "como esta el volumen", "nivel de volumen")):
            vol = platform.get_volume()
            if vol >= 0:
                bot.send_message(chat_id, f"Volumen actual: {vol}%, {cfg.user_title}.")
            else:
                bot.send_message(chat_id, "No pude obtener el volumen, Señor.")
            return True

        nums = re.findall(r"\d+", t)
        if not nums:
            bot.send_message(chat_id, "Indíqueme un valor numérico, Señor (ej: \"volumen 50\").")
            return True
        nivel = max(0, min(100, int(nums[0])))
        ok = platform.set_volume(nivel)
        bot.send_message(chat_id, f"Volumen ajustado al {nivel}%, Señor." if ok else "No pude ajustar el volumen, Señor.")
        return True


MODULE_CLASS = VolumenModule
