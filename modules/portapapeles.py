from __future__ import annotations

from modules.base import BaseModule


class PortapapelesModule(BaseModule):
    nombre = "clipboard"
    prioridad = 70

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(t.startswith(p) for p in (
            "copia ", "copiar ", "copiar al portapapeles ",
            "copia al portapapeles ", "portapapeles ",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        for pref in ("copia al portapapeles ", "copiar al portapapeles ",
                      "copia ", "copiar ", "portapapeles "):
            if t.startswith(pref):
                contenido = texto[len(pref):].strip().strip('"').strip("'")
                if not contenido:
                    bot.send_message(chat_id, "¿Qué texto desea copiar, Señor?")
                    return True
                if platform.copy_to_clipboard(contenido):
                    bot.send_message(chat_id, f"Copiado al portapapeles, Señor: \"{contenido}\"")
                else:
                    bot.send_message(chat_id, "No pude copiar al portapapeles, Señor.")
                return True
        return False


MODULE_CLASS = PortapapelesModule
