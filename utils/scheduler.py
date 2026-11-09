from __future__ import annotations

import logging
import threading
import time as _time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import JarvisConfig

log = logging.getLogger("jarvis.scheduler")
_ACTIVE_SCHEDULER = None
_ACTIVE_LOCK = threading.Lock()


class TaskScheduler:
    def __init__(self, cfg: JarvisConfig, bot=None):
        self.cfg = cfg
        self._bot = bot
        self._wake_event = threading.Event()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        global _ACTIVE_SCHEDULER
        if self._running:
            return
        self._running = True
        with _ACTIVE_LOCK:
            _ACTIVE_SCHEDULER = self
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log.info("Scheduler iniciado")

    def notify(self) -> None:
        self._wake_event.set()

    def stop(self) -> None:
        global _ACTIVE_SCHEDULER
        self._running = False
        self._wake_event.set()
        with _ACTIVE_LOCK:
            if _ACTIVE_SCHEDULER is self:
                _ACTIVE_SCHEDULER = None

    def _loop(self) -> None:
        while self._running:
            try:
                from database.repositories.tareas import obtener_tareas, actualizar_proxima, desactivar_tarea
                tareas = obtener_tareas(activas=True)

                if not tareas:
                    self._wake_event.wait(timeout=30)
                    self._wake_event.clear()
                    continue

                ahora = _time.time()
                proximo_ts = float("inf")

                due_tasks = []
                for t in tareas:
                    texec = t.get("proxima_ejecucion")
                    if texec is None:
                        continue
                    if ahora >= texec:
                        due_tasks.append(t)
                    else:
                        proximo_ts = min(proximo_ts, texec)

                for t in due_tasks:
                    self._ejecutar(t)
                    self._reschedule(t, actualizar_proxima, desactivar_tarea)

                sleep_time = max(1, proximo_ts - _time.time())
                self._wake_event.wait(timeout=sleep_time)
                self._wake_event.clear()

            except Exception as exc:
                log.error("Error en scheduler: %s", exc)
                self._wake_event.wait(timeout=30)
                self._wake_event.clear()

    def _ejecutar(self, tarea: dict) -> None:
        comando = tarea["comando"]
        chat_id = self.cfg.telegram_chat_id
        log.info("Ejecutando tarea #%s (comando_chars=%s)", tarea.get("id"), len(comando))
        try:
            from ai.direct_ai_runner import ejecutar_ia_directa

            bot = self._bot
            if bot is None:
                log.error("Scheduler sin instancia de bot disponible. Tarea #%s cancelada.", tarea.get("id"))
                return

            bot.send_message(chat_id, f"{self.cfg.full_name}, ejecuto la tarea programada: \"{comando}\"")
            ejecutar_ia_directa(comando, chat_id, bot, self.cfg)
        except Exception as exc:
            log.error("Error ejecutando tarea #%s: %s", tarea.get("id"), exc)

    def _reschedule(self, tarea: dict, actualizar_proxima, desactivar_tarea) -> None:
        from utils.scheduler import _calcular_proxima

        tid = tarea["id"]
        tipo = tarea["tipo"]

        if tipo == "una_vez":
            desactivar_tarea(tid)
        elif tipo == "intervalo":
            nueva = _time.time() + max(1, tarea.get("intervalo_seg", 3600) or 3600)
            actualizar_proxima(tid, nueva)
        elif tipo == "diaria":
            nueva = _calcular_proxima(
                "diaria",
                tarea.get("hora"),
                tarea.get("minuto"),
                timezone=getattr(self.cfg, "timezone", None),
            )
            actualizar_proxima(tid, nueva)


def get_active_scheduler():
    with _ACTIVE_LOCK:
        return _ACTIVE_SCHEDULER


def _calcular_proxima(tipo: str, hora: str | None = None, minuto: str | None = None,
                       intervalo_seg: int | None = None,
                       timezone: str | None = None) -> float:
    if tipo == "intervalo":
        return _time.time() + max(1, intervalo_seg or 3600)
    if tipo in ("diaria", "una_vez"):
        try:
            h = int(hora or "0")
            m = int(minuto or "0")
            zone = ZoneInfo(timezone) if timezone else None
            ahora = datetime.now(zone)
            proxima = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
        except (ValueError, TypeError, KeyError):
            return _time.time() + 3600
        if proxima <= ahora:
            proxima += timedelta(days=1)
        return proxima.timestamp()
    return _time.time() + 3600
