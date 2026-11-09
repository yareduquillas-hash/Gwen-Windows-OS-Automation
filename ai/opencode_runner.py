"""Runner del CLI de OpenCode GO. Fallback cuando el HTTP directo no está disponible."""
from __future__ import annotations

import logging
import os
import subprocess
import time as _time

from utils.security import es_peligroso
from utils.text import truncar_telegram

log = logging.getLogger("jarvis.ai")


def _resolver_opencode(cfg) -> str:
    bin_path = os.path.expandvars(cfg.opencode_bin)
    if os.path.isfile(bin_path):
        return bin_path
    return "opencode"


def ejecutar_opencode(texto: str, chat_id: int, bot, cfg) -> None:
    if es_peligroso(texto):
        bot.send_message(
            chat_id,
            f"{cfg.full_name}, cancelo la tarea por seguridad: contiene instrucciones "
            "destructivas sobre el sistema.",
        )
        return

    from modules.protocolos import get_protocolo
    from ai.prompt_builder import construir_prompt

    protocolo_activo = get_protocolo()
    if protocolo_activo == "G":
        modelos = [cfg.model_g, cfg.model_base]
    elif protocolo_activo == "M":
        modelos = [cfg.model_m, cfg.model_base]
    else:
        modelos = [cfg.model_base]

    tarea = construir_prompt(texto, cfg, chat_id)
    exito = False
    ultimo_error = ""

    for i, modelo in enumerate(modelos):
        if i > 0:
            bot.send_message(chat_id, f"El modelo anterior ha fallado. Reintentando con {modelo}...")
        else:
            bot.send_message(chat_id, f"Inmediatamente, Señor. Derivo la tarea a {modelo}.")

        log.info("opencode run modelo=%s tarea_chars=%s", modelo, len(tarea))
        opencode_exe = _resolver_opencode(cfg)

        kw = {}
        if os.name == "nt":
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        try:
            resultado = subprocess.run(
                [opencode_exe, "run", tarea, "--model", modelo, "--auto"],
                capture_output=True, text=True, encoding="utf-8",
                timeout=cfg.opencode_timeout, **kw
            )
            log.info("rc=%s stdout=%s", resultado.returncode, resultado.stdout[:300])

            respuesta = resultado.stdout.strip()
            stderr = resultado.stderr.strip()

            # Limpiar posibles encabezados de CLI de OpenCode
            clean_lines = []
            for line in respuesta.splitlines():
                if line.strip().startswith(("[OpenCode]", "Session initialized", "Using model:", "Thinking...", "opencode run")):
                    continue
                clean_lines.append(line)
            respuesta = "\n".join(clean_lines).strip()

            errores_api = ("ResourceExhausted", "limit reached", "UnknownError",
                           "Internal Server Error")
            es_error = resultado.returncode != 0 or any(
                e in (stderr + (respuesta or "")) for e in errores_api
            )

            if es_error:
                ultimo_error = stderr or respuesta or "sin detalle"
                log.warning("Modelo %s falló: %s", modelo, ultimo_error)
                if get_protocolo() is not None and any(
                    x in ultimo_error for x in ("ResourceExhausted", "limit reached")
                ):
                    log.info("Desactivando protocolo por límite agotado")
                continue

            exito = True
            respuesta = truncar_telegram(respuesta)
            bot.send_message(chat_id, respuesta, parse_mode="Markdown")

            from modules.voz import VoiceModule
            if len(respuesta) < 600:
                try:
                    VoiceModule.instance(cfg).enviar_nota_de_voz(chat_id, respuesta[:500], bot)
                except Exception:
                    pass
            break

        except subprocess.TimeoutExpired:
            ultimo_error = "TimeoutExpired"
            continue
        except Exception as exc:
            ultimo_error = str(exc)
            continue

    if not exito:
        if "ResourceExhausted" in ultimo_error or "limit reached" in ultimo_error:
            bot.send_message(
                chat_id,
                f"{cfg.full_name}, todos los modelos han agotado su cupo. "
                "Le sugiero esperar a la renovación de límites.",
            )
        else:
            bot.send_message(
                chat_id,
                f"Todos los modelos han fallado, Señor. Último error:\n```{ultimo_error[:500]}```",
                parse_mode="Markdown",
            )
