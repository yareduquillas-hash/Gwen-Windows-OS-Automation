from __future__ import annotations

from modules.base import BaseModule


class VentanasModule(BaseModule):
    nombre = "ventanas"
    prioridad = 55

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "qué ventanas", "que ventanas", "ventanas abiertas",
            "minimiza todo", "minimizar todo", "escritorio",
            "enfoca", "trae al frente", "maximiza",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if any(p in t for p in ("qué ventanas", "que ventanas", "ventanas abiertas")):
            ventanas = platform.get_windows()
            if not ventanas:
                bot.send_message(chat_id, "No detecto ventanas abiertas, Señor.")
                return True
            lista = "\n".join(f"• {w}" for w in ventanas[:20])
            bot.send_message(chat_id, f"Ventanas abiertas:\n{lista}")
            return True

        if any(p in t for p in ("minimiza todo", "minimizar todo", "escritorio")):
            platform.minimize_all()
            bot.send_message(chat_id, "Todo minimizado, Señor.")
            return True

        for pref in ("enfoca ", "trae al frente "):
            if t.startswith(pref):
                titulo = texto[len(pref):].strip()
                if not titulo:
                    bot.send_message(chat_id, "¿Qué ventana desea enfocar, Señor?")
                    return True
                ok = platform.focus_window(titulo)
                bot.send_message(chat_id, f"Ventana enfocada, Señor." if ok else f"No encontré \"{titulo}\", Señor.")
                return True

        return False


MODULE_CLASS = VentanasModule
