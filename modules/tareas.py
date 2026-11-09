from __future__ import annotations

import datetime as _datetime
import re as _re
import time as _time

from modules.base import BaseModule


class TareasModule(BaseModule):
    nombre = "tareas"
    prioridad = 25

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(p in t for p in (
            "todos los días", "todos los dias", "a las ", "cada ",
            "recuérdame", "recuerdame", "avísame", "avisame", "prográmame", "programame",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        parseo = _parsear_tarea(texto)
        if parseo is None:
            return False
        tipo, hora, minuto, intervalo_seg, comando = parseo
        from database.repositories.tareas import guardar_tarea
        from database.repositories.eventos import guardar_evento
        from utils.scheduler import _calcular_proxima, get_active_scheduler

        proxima = _calcular_proxima(
            tipo,
            hora,
            minuto,
            intervalo_seg,
            timezone=getattr(cfg, "timezone", None),
        )
        tid = guardar_tarea(tipo, hora, minuto, intervalo_seg, proxima, comando)
        guardar_evento("tarea_programada", f"{tipo}: {comando}")
        scheduler = get_active_scheduler()
        if scheduler:
            scheduler.notify()

        if tipo == "intervalo":
            desc = f"cada {intervalo_seg // 3600}h" if intervalo_seg >= 3600 else f"cada {intervalo_seg // 60}min"
        elif tipo == "diaria":
            desc = f"todos los días a las {hora}:{(minuto or '00').zfill(2)}"
        else:
            desc = f"a las {hora}:{(minuto or '00').zfill(2)}"
        prox_desc = _datetime.datetime.fromtimestamp(proxima).strftime("%H:%M del %d/%m")
        bot.send_message(chat_id, f"Programado, {cfg.full_name}: \"{comando}\" — {desc}. Próxima ejecución: {prox_desc}.")
        return True


def _parsear_tarea(texto: str):
    t = texto.lower().strip()
    palabras_clave = ("haz", "reproduce", "ejecuta", "envía", "envia", "recuerdame",
                       "recuérdame", "avísame", "avisame", "dime", "abre", "ponme")

    m = _re.search(r"todos los d[ií]as?\s+a\s+las?\s+(\d{1,2})(?::(\d{2}))?\s*(.*)", t)
    if m:
        hora, minuto, resto = m.group(1), m.group(2) or "0", m.group(3).strip()
        if int(hora) > 23 or int(minuto) > 59:
            return None
        comando = _extraer_comando(resto, texto, t)
        return ("diaria", hora, minuto, None, comando) if comando else None

    m = _re.search(r"\ba\s+las?\s+(\d{1,2})(?::(\d{2}))?\s+(.*)", t)
    if m:
        hora, minuto, resto = m.group(1), m.group(2) or "0", m.group(3).strip()
        if int(hora) > 23 or int(minuto) > 59:
            return None
        if not any(p in resto for p in palabras_clave):
            return None
        comando = _extraer_comando(resto, texto, t)
        return ("una_vez", hora, minuto, None, comando) if comando else None

    m = _re.search(r"cada\s+(\d+)\s+(minuto|minutos|hora|horas|segundo|segundos)\s+(.*)", t)
    if m:
        cantidad, unidad, resto = int(m.group(1)), m.group(2), m.group(3).strip()
        if cantidad <= 0:
            return None
        mult = 60 if "minuto" in unidad else 3600 if "hora" in unidad else 1
        comando = _extraer_comando(resto, texto, t)
        return ("intervalo", None, None, cantidad * mult, comando) if comando else None

    return None


def _extraer_comando(resto: str, texto_original: str, t_lower: str) -> str:
    idx = t_lower.find(resto)
    cmd = texto_original[idx:idx + len(resto)].strip() if idx >= 0 else resto
    for pref in ("haz que ", "haz ", "que ", "reproducir ", "ejecuta ", "ejecutar ", "envía ", "envia "):
        if cmd.lower().startswith(pref):
            cmd = cmd[len(pref):]
            break
    return cmd.strip()


def list_tasks(message, bot, cfg) -> None:
    from database.repositories.tareas import obtener_tareas
    filas = obtener_tareas(activas=False)
    if not filas:
        bot.reply_to(message, f"No tengo tareas programadas, {cfg.full_name}.")
        return
    lineas = []
    for f in filas:
        estado = "✅" if f["activa"] else "❌"
        tipo = f["tipo"]
        if tipo == "intervalo":
            desc = f"cada {f['intervalo_seg']}s"
        elif tipo == "diaria":
            desc = f"diaria a las {f['hora']}:{(f['minuto'] or '00').zfill(2)}"
        else:
            desc = f"una vez a las {f['hora']}:{(f['minuto'] or '00').zfill(2)}"
        prox = _datetime.datetime.fromtimestamp(f['proxima_ejecucion']).strftime("%H:%M %d/%m") if f.get('proxima_ejecucion') else "?"
        lineas.append(f"{estado} #{f['id']} [{desc}] → \"{f['comando']}\" (próx: {prox})")
    bot.reply_to(message, "Tareas programadas:\n" + "\n".join(lineas))


def delete_task(message, bot, cfg) -> None:
    partes = (message.text or "").split()
    if len(partes) < 2:
        bot.reply_to(message, "Indíqueme el número de tarea, Señor (ej: /eliminar_tarea 3).")
        return
    try:
        tid = int(partes[1])
    except ValueError:
        bot.reply_to(message, "El ID debe ser numérico, Señor.")
        return
    from database.repositories.tareas import desactivar_tarea
    desactivar_tarea(tid)
    bot.reply_to(message, f"Tarea #{tid} eliminada, {cfg.full_name}.")


MODULE_CLASS = TareasModule
