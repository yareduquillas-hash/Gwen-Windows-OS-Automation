from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger("jarvis.voz")


class VoiceModule:
    _instance = None

    @classmethod
    def instance(cls, cfg):
        if cls._instance is None:
            cls._instance = cls(cfg)
        return cls._instance

    def __init__(self, cfg):
        self.cfg = cfg
        self.voice = cfg.tts_voice

    def handle_voice(self, message, bot, router) -> None:
        bot.reply_to(message, "Un momento, Señor. Proceso su nota de voz.")
        try:
            file_info = bot.get_file(message.voice.file_id)
            texto = self._transcribir(file_info, bot)
        except Exception as exc:
            bot.send_message(message.chat.id, f"No he logrado transcribir el audio, Señor: {exc}")
            return

        if not texto:
            bot.send_message(message.chat.id,
                "No he logrado entender el audio, Señor. Quizás la modulación de su voz excede mi capacidad auditiva.")
            return

        bot.send_message(message.chat.id, f"He entendido, Señor: \"{texto}\"")
        from adapters import VoiceInputAdapter
        router.dispatch(VoiceInputAdapter.from_message(message, texto), bot)

    def texto_a_voz(self, texto: str) -> str:
        current_voice = getattr(self.cfg, 'tts_voice', self.voice)
        cache_key = hashlib.sha256(f"{current_voice}:{texto}".encode()).hexdigest()
        cache_file = self.cfg.tts_cache_dir / f"{cache_key}.ogg"
        if cache_file.exists():
            return str(cache_file)

        import edge_tts
        from pydub import AudioSegment

        tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name

        async def _gen():
            comunicar = edge_tts.Communicate(texto, current_voice)
            await comunicar.save(tmp_mp3)
        asyncio.run(_gen())

        audio = AudioSegment.from_mp3(tmp_mp3)
        audio.export(str(cache_file), format="ogg", codec="libopus")

        try:
            os.remove(tmp_mp3)
        except OSError:
            pass

        return str(cache_file)

    def enviar_nota_de_voz(self, chat_id: int, texto: str, bot) -> None:
        try:
            ruta = self.texto_a_voz(texto)
            with open(ruta, "rb") as audio:
                bot.send_voice(chat_id, audio)
        except Exception as exc:
            bot.send_message(chat_id, f"No he podido generar mi nota de voz, Señor: {exc}")

    def _transcribir(self, file_info, bot) -> str:
        import speech_recognition as sr

        try:
            datos_ogg = bot.download_file(file_info.file_path)
            archivo_ogg = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
            archivo_ogg.write(datos_ogg)
            archivo_ogg.close()
            archivo_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

            from pydub import AudioSegment
            audio = AudioSegment.from_ogg(archivo_ogg.name)
            audio.export(archivo_wav, format="wav")

            reconocedor = sr.Recognizer()
            with sr.AudioFile(archivo_wav) as fuente:
                datos = reconocedor.record(fuente)
            texto = reconocedor.recognize_google(datos, language=self.cfg.lang)

            try:
                os.remove(archivo_ogg.name)
            except OSError:
                pass
            try:
                os.remove(archivo_wav)
            except OSError:
                pass
            return texto
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
        except Exception as exc:
            log.warning("Error transcripción: %s", exc)
            return ""


from modules.base import BaseModule


class VozModule(BaseModule):
    nombre = "voz"
    prioridad = 90

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in ("dilo en voz", "repítelo", "repitelo", "háblame", "hablame"))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        VoiceModule.instance(cfg).enviar_nota_de_voz(chat_id, texto, bot)
        return True


MODULE_CLASS = VozModule
