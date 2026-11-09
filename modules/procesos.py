from __future__ import annotations

from modules.base import BaseModule


class ProcesosModule(BaseModule):
    nombre = "procesos"
    prioridad = 55

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "qué procesos", "que procesos", "procesos abiertos",
            "lista procesos", "mata", "matar", "termina el proceso",
            "cierra el programa",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if any(p in t for p in ("qué procesos", "que procesos", "procesos abiertos", "lista procesos")):
            procs = platform.get_running_processes(10)
            if not procs:
                bot.send_message(chat_id, "No pude listar procesos, Señor.")
                return True
            lineas = [f"• {p['name']} ({p['memory_mb']} MB)" for p in procs]
            bot.send_message(chat_id, "Procesos (top RAM):\n" + "\n".join(lineas))
            return True

        for pref in ("mata ", "matar ", "termina el proceso ", "cierra el programa "):
            if t.startswith(pref):
                nombre = texto[len(pref):].strip()
                if not nombre:
                    bot.send_message(chat_id, "¿Qué proceso desea terminar, Señor?")
                    return True
                if not nombre.lower().endswith(" confirmar"):
                    bot.send_message(
                        chat_id,
                        f"Para terminar exactamente '{nombre}', escriba: mata {nombre} confirmar",
                    )
                    return True
                nombre = nombre[: -len(" confirmar")].strip()
                if not nombre:
                    bot.send_message(chat_id, "Indique el nombre exacto del proceso, Señor.")
                    return True
                ok = platform.kill_process(nombre)
                bot.send_message(
                    chat_id,
                    "Proceso terminado, Señor."
                    if ok
                    else f"No encontré un único proceso exacto llamado \"{nombre}\", Señor.",
                )
                return True

        return False


MODULE_CLASS = ProcesosModule
