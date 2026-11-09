from __future__ import annotations

import time as _time
from datetime import datetime

from modules.base import BaseModule


class SistemaInfoModule(BaseModule):
    nombre = "sistema_info"
    prioridad = 55

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "cómo va el sistema", "como va el sistema", "estado del sistema",
            "info del sistema", "información del sistema", "diagnóstico",
            "qué tal va la pc", "rendimiento",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        bot.send_message(chat_id, "Analizando el sistema, Señor...")
        try:
            info = platform.get_system_info()
            boot = datetime.fromtimestamp(info["boot_time"]).strftime("%H:%M %d/%m")
            msg = (
                f"Estado del sistema, {cfg.user_title}:\n\n"
                f"🖥 CPU: {info['cpu_percent']}%\n"
                f"🧠 RAM: {info['ram_used_gb']:.1f} / {info['ram_total_gb']:.1f} GB ({info['ram_percent']}%)\n"
                f"💾 Disco: {info['disk_free_gb']:.1f} GB libres de {info['disk_total_gb']:.1f} GB ({info['disk_percent']}% usado)\n"
                f"⏱ Uptime: desde {boot}"
            )
            bot.send_message(chat_id, msg)
        except Exception as exc:
            bot.send_message(chat_id, f"No pude obtener información del sistema, Señor: {exc}")
        return True


MODULE_CLASS = SistemaInfoModule
