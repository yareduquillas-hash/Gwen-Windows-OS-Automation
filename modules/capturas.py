from __future__ import annotations

from modules.base import BaseModule


class CapturasModule(BaseModule):
    nombre = "capturas"
    prioridad = 55

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "haz una captura", "haz captura", "captura de pantalla",
            "screenshot", "captura la pantalla", "toma una captura",
            "envíame una captura", "mándame una captura",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        bot.send_message(chat_id, "Capturando pantalla, Señor...")
        img_bytes = platform.take_screenshot()
        if img_bytes is None:
            bot.send_message(chat_id, "No pude capturar la pantalla, Señor.")
            return True
        import io
        bot.send_photo(chat_id, io.BytesIO(img_bytes))
        return True


MODULE_CLASS = CapturasModule
