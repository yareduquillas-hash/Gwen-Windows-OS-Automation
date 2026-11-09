from __future__ import annotations

import logging
import os
import shlex
import subprocess

from modules.base import BaseModule
from utils.security import es_peligroso
from utils.text import truncar_telegram

log = logging.getLogger("jarvis.sistema")

ALLOWED_SHELL_COMMANDS = {"hostname", "ipconfig", "tasklist", "ver", "whoami"}


class SistemaModule(BaseModule):
    nombre = "sistema"
    prioridad = 15

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "apágate", "apagate", "cierra sesion", "cierra el bot",
            "adios jarvis", "adios gwen", "bloquea la pantalla", "bloquear pantalla",
            "apaga el sistema", "reinicia", "suspende",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        disparadores_apagado = ("apágate", "apagate", "apagate jarvis", "apagate gwen", "cierra sesion",
                                 "cierra el bot", "adios jarvis", "adios gwen")
        if any(d in t for d in disparadores_apagado):
            bot.send_message(
                chat_id,
                f"Apagarse es una decisión seria, {cfg.full_name}. "
                "Si está seguro, envíe `/shutdown confirmar`.",
            )
            return True
        if "bloquea" in t and "pantalla" in t:
            ok = platform.lock_screen()
            bot.send_message(chat_id, "Pantalla bloqueada, Señor." if ok else "No pude bloquear la pantalla, Señor.")
            return True
        return False


def handle_sh_command(message, bot, cfg) -> None:
    comando = message.text.partition(" ")[2].strip()
    if not comando:
        bot.reply_to(message, "Señor, ¿pretende que adivine el comando? Indíquelo tras /sh.")
        return
    if es_peligroso(comando):
        bot.reply_to(
            message,
            f"⚠️ {cfg.full_name}, ese comando está bloqueado por seguridad y no será ejecutado.",
        )
        return

    if os.getenv("JARVIS_ALLOW_SHELL", "false").lower() not in ("1", "true", "yes"):
        bot.reply_to(
            message,
            "La consola remota esta deshabilitada por seguridad. Use una capacidad especifica, Señor.",
        )
        return

    try:
        args = shlex.split(comando, posix=False)
    except ValueError:
        bot.reply_to(message, "No pude interpretar los argumentos del comando, Señor.")
        return
    if not args:
        bot.reply_to(message, "Indique un comando de consulta permitido, Señor.")
        return

    command_name = args[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if command_name not in ALLOWED_SHELL_COMMANDS:
        bot.reply_to(
            message,
            "Ese comando no esta permitido. Solo se aceptan consultas basicas de sistema, Señor.",
        )
        return

    bot.reply_to(message, f"Como ordene, Señor. Ejecutando...")
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    try:
        resultado = subprocess.run(
            args, shell=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30, **kw
        )
        salida = resultado.stdout.strip()
        errores = resultado.stderr.strip()
        cuerpo = salida + ("\n[stderr]\n" + errores if errores else "")
        if not cuerpo:
            cuerpo = "(El comando se ejecutó sin emitir salida, Señor.)"
    except subprocess.TimeoutExpired:
        cuerpo = "Treinta segundos de espera han sido suficientes, Señor. El comando se ha cancelado."
    except Exception as exc:
        cuerpo = f"Un imprevisto ha surgido, Señor: {exc}"
    bot.send_message(message.chat.id, f"```\n{truncar_telegram(cuerpo)}\n```", parse_mode="Markdown")


def handle_shutdown(message, bot, cfg, scheduler) -> None:
    texto = (message.text or "").strip().lower()
    if "/shutdown confirmar" not in texto:
        bot.reply_to(
            message,
            f"Apagarse es una decisión seria, {cfg.full_name}. "
            "Si está seguro, envíe `/shutdown confirmar`.",
        )
        return
    bot.reply_to(message, f"Como ordene, {cfg.full_name}. Apagando Gwen. Hasta la próxima, Señor.")
    if scheduler:
        try:
            scheduler.stop()
        except Exception:
            pass
    try:
        bot.stop_polling()
    except Exception:
        pass
    try:
        from database.connection import ConnectionManager
        ConnectionManager.close_instance()
    except Exception:
        pass
    try:
        import psutil
        current = psutil.Process()
        for child in current.children(recursive=True):
            try:
                child.terminate()
            except Exception:
                pass
    except Exception:
        pass
    import sys
    sys.exit(0)


MODULE_CLASS = SistemaModule
