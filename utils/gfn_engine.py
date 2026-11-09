from __future__ import annotations

import logging
import os
import re
import time as _time
import threading
from datetime import datetime
from pathlib import Path

log = logging.getLogger("jarvis.gfn")

DESKTOP = os.path.expandvars(r"%USERPROFILE%\Desktop")


class GFNEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.delay = getattr(cfg, 'gfn_action_delay', 6)
        self._cancel_events: dict[str, threading.Event] = {}
        self._active_monitors = {}
        self._state_errors: dict[str, int] = {}
        self._last_queue_info: dict | None = None

    def _get_cancel_event(self, game_name: str | None = None) -> threading.Event:
        key = (game_name or "__global__").lower()
        if key not in self._cancel_events:
            self._cancel_events[key] = threading.Event()
        return self._cancel_events[key]

    # ── Detección por Log de NVIDIA (debug.log) + Ventana (0% CPU / 0 MB RAM) ──
    #
    # Fuente de verdad: %LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log
    #   - onSessionSetupProgress(state: 1, queue: N, eta: M) → cola activa
    #   - Silencio en el log + ventana GFN visible → juego en vivo (STREAMING)
    #   - onStopResult(result: N) → sesión terminada (CLOSED)

    def _get_window_state(self, game_name: str | None = None) -> str:
        """Determina el estado real de la sesión GFN usando el debug.log de NVIDIA.
        Si el log no existe o no tiene entradas, fallback a detección por ventana.
        Retorna: 'STREAMING', 'QUEUE', o 'CLOSED'."""
        key = (game_name or "__global__").lower()
        try:
            import pygetwindow as gw

            log_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log"),
                os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOWStreamer\debug.log"),
            ]

            last_queue_ts = None
            last_queue_num = None
            last_queue_eta = None
            last_stop_ts = None

            for log_path in log_paths:
                if not os.path.isfile(log_path):
                    continue
                try:
                    with open(log_path, "rb") as f:
                        f.seek(0, os.SEEK_END)
                        size = f.tell()
                        f.seek(max(0, size - 16384))
                        raw = f.read().decode("utf-8", errors="ignore")
                except (OSError, PermissionError):
                    continue

                for line in raw.splitlines():
                    if "onSessionSetupProgress" in line:
                        m_ts = re.search(r"(\d{2}:\d{2}:\d{2})", line)
                        m_q = re.search(r"queue:\s*(\d+)", line)
                        m_e = re.search(r"eta:\s*(\d+)", line)
                        if m_ts:
                            last_queue_ts = m_ts.group(1)
                        if m_q:
                            last_queue_num = m_q.group(1)
                        if m_e:
                            last_queue_eta = m_e.group(1)

                    if "onStopResult" in line:
                        m_ts = re.search(r"(\d{2}:\d{2}:\d{2})", line)
                        if m_ts:
                            last_stop_ts = m_ts.group(1)

                break

            has_gfn_window = False
            for win in gw.getAllWindows():
                if not win.visible or win.isMinimized:
                    continue
                w = win.title.lower()
                if "geforce now" in w:
                    has_gfn_window = True
                    break

            now = datetime.now()

            if last_queue_ts is not None or last_stop_ts is not None:
                t_queue = None
                t_stop = None

                try:
                    today = now.date()
                    if last_queue_ts:
                        h, m, s = map(int, last_queue_ts.split(":"))
                        t_queue = datetime(today.year, today.month, today.day, h, m, s)
                except (ValueError, AttributeError):
                    pass

                try:
                    today = now.date()
                    if last_stop_ts:
                        h, m, s = map(int, last_stop_ts.split(":"))
                        t_stop = datetime(today.year, today.month, today.day, h, m, s)
                except (ValueError, AttributeError):
                    pass

                if t_stop and t_queue and t_stop >= t_queue:
                    self._state_errors[key] = 0
                    return "CLOSED"
                if t_stop and not t_queue:
                    self._state_errors[key] = 0
                    return "CLOSED"

                if t_queue and (now - t_queue).total_seconds() < 10:
                    self._state_errors[key] = 0
                    if last_queue_num is not None:
                        self._last_queue_info = {
                            "position": last_queue_num,
                            "eta_ms": last_queue_eta or "0",
                            "updated": now.isoformat(),
                        }
                    return "QUEUE"

                if t_queue and (now - t_queue).total_seconds() >= 10:
                    if has_gfn_window:
                        self._state_errors[key] = 0
                        return "STREAMING"
                    self._state_errors[key] = 0
                    return "CLOSED"

            if has_gfn_window:
                self._state_errors[key] = 0
                return "QUEUE"

            self._state_errors[key] = 0
            return "CLOSED"

        except Exception as exc:
            err_count = self._state_errors.get(key, 0) + 1
            self._state_errors[key] = err_count
            log.warning("Error comprobando estado (%d/3 consecutivos): %s", err_count, exc)
            if err_count >= 3:
                return "CLOSED"
            return "QUEUE"

    def is_open(self) -> bool:
        return self._get_window_state() != "CLOSED"

    def open(self) -> bool:
        if self.is_open():
            return True
        shortcut = self._find_shortcut()
        if shortcut:
            return self._launch_shortcut(shortcut)
        return False

    # ── Accesos directos ──

    def _find_shortcut(self, name: str | None = None) -> str | None:
        userprofile = os.environ.get("USERPROFILE", r"C:\Users\admin")
        onedrive = os.environ.get("ONEDRIVE")
        desktop_dirs = [
            DESKTOP,
            os.path.join(userprofile, "Desktop"),
            os.path.join(userprofile, "Escritorio"),
        ]
        if onedrive:
            desktop_dirs.extend([
                os.path.join(onedrive, "Desktop"),
                os.path.join(onedrive, "Escritorio"),
            ])
        desktop_dirs = list(dict.fromkeys(d for d in desktop_dirs if os.path.exists(d)))

        if name:
            name_clean = name.lower().strip().strip('"').strip("'").strip("!.").strip()
            words = [w for w in re.findall(r'\b\w+\b', name_clean) if len(w) > 0]

            # 1. Coincidencias exactas prioritarias
            for d in desktop_dirs:
                exact_patterns = [
                    os.path.join(d, f"{name_clean} en GeForce NOW.lnk"),
                    os.path.join(d, f"{name_clean}.lnk"),
                ]
                for p in exact_patterns:
                    if os.path.isfile(p):
                        return p

            # 2. Ranking con coincidencia de palabras completas (\b) y prioridad GFN
            candidates: list[tuple[int, str]] = []
            for d in desktop_dirs:
                for f in os.listdir(d):
                    if not f.lower().endswith(".lnk"):
                        continue

                    f_stem = f[:-4].lower()
                    f_path = os.path.join(d, f)
                    score = 0
                    is_gfn = "geforce now" in f_stem or "gfn" in f_stem

                    # Coincidencia de la frase completa como palabra(s) delimitadas
                    pattern_phrase = r'\b' + re.escape(name_clean) + r'\b'
                    if re.search(pattern_phrase, f_stem):
                        score += 150
                        if f_stem.startswith(name_clean):
                            score += 50

                    # Coincidencia de palabras individuales completas
                    if words:
                        matched_words = sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', f_stem))
                        if matched_words == len(words):
                            score += 100
                        elif matched_words > 0:
                            score += matched_words * 20

                    # Bonus prioritario para accesos directos de GeForce NOW
                    if is_gfn and score > 0:
                        score += 120

                    if score > 0:
                        candidates.append((score, f_path))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                log.info("Mejor acceso directo encontrado para '%s': %s (score=%d)", name, candidates[0][1], candidates[0][0])
                return candidates[0][1]

            return None

        for d in desktop_dirs:
            generic = os.path.join(d, "NVIDIA GeForce NOW.lnk")
            if os.path.isfile(generic):
                return generic
            for f in os.listdir(d):
                if f.lower().endswith(".lnk") and "geforce" in f.lower():
                    return os.path.join(d, f)
        return None

    def _launch_shortcut(self, path: str) -> bool:
        try:
            os.startfile(path)
            return True
        except Exception as exc:
            log.warning("No se pudo abrir el acceso directo %s: %s", path, exc)
            return False

    # ── Monitoreo Ultra-Liviano Basado en Debug Log ──

    def _queue_monitor(
        self,
        game_name: str,
        chat_id: int,
        bot,
        cfg,
        platform,
        profile_name: str | None = None,
    ) -> None:
        cancel_ev = self._get_cancel_event(game_name)
        cancel_ev.clear()
        start = _time.time()
        timeout = getattr(cfg, 'gfn_queue_timeout_minutes', 30) * 60
        poll = getattr(cfg, 'gfn_queue_poll_interval', 15)

        bot.send_message(
            chat_id,
            f"🎮 *Monitoreando acceso para {game_name}*\n"
            f"Le informaré la posición exacta en cola y tan pronto el juego esté listo, {cfg.user_title}."
        )

        ciclos_cola = 0
        self._active_monitors[game_name.lower()] = start

        try:
            while _time.time() - start < timeout:
                if cancel_ev.is_set():
                    bot.send_message(chat_id, f"⏹ Monitoreo para *{game_name}* cancelado.")
                    return

                state = self._get_window_state(game_name)

                # 1. El juego inició streaming real (silencio de log + ventana activa)
                if state == "STREAMING":
                    bot.send_message(
                        chat_id,
                        f"🟢 *¡{game_name} ha iniciado la transmisión, {cfg.user_title}!*\n"
                        f"Preparando la sesión..."
                    )
                    if getattr(cfg, 'gfn_gaming_volume', 0) > 0:
                        try:
                            platform.set_volume(cfg.gfn_gaming_volume)
                        except Exception:
                            pass

                    # Comprobar si existe perfil de autologin configurado para este juego
                    from utils.gfn_profiles import GFNProfileManager
                    from utils.gfn_autologin import GFNAutoLogin

                    mgr = GFNProfileManager()
                    prof = mgr.find_profile_for_game(game_name, profile_name)

                    if prof and (prof.account_email or prof.password_encrypted):
                        autologin = GFNAutoLogin(mgr)
                        autologin.wait_and_autologin(prof, chat_id, bot)
                    else:
                        bot.send_message(
                            chat_id,
                            f"🎮 *¡{game_name} listo para jugar!* (Sin perfil de autologin configurado)."
                        )

                    while not cancel_ev.is_set():
                        _time.sleep(10)
                        if self._get_window_state(game_name) == "CLOSED":
                            log.info("Juego %s cerrado por el usuario. Hilo autodestruido.", game_name)
                            return
                    return

                # 2. Cola o lanzador activo
                elif state == "QUEUE":
                    ciclos_cola += 1
                    if ciclos_cola % 4 == 0:
                        elapsed = int(_time.time() - start)
                        if self._last_queue_info:
                            pos = self._last_queue_info.get("position", "?")
                            eta_ms = self._last_queue_info.get("eta_ms", "0")
                            try:
                                eta_s = int(eta_ms) // 1000
                                eta_text = f", ~{eta_s}s estimados" if eta_s > 0 else ""
                            except Exception:
                                eta_text = ""
                            bot.send_message(
                                chat_id,
                                f"⏳ Cola para *{game_name}*: *{pos}* jugadores por delante{eta_text} ({elapsed//60}m {elapsed%60}s transcurridos)..."
                            )
                        else:
                            bot.send_message(
                                chat_id,
                                f"⏳ Esperando turno en cola para *{game_name}* ({elapsed//60}m {elapsed%60}s transcurridos)..."
                            )

                # 3. Se cerró la aplicación durante la cola (autodestrucción silenciosa)
                elif state == "CLOSED" and ciclos_cola > 2:
                    log.info("GeForce NOW cerrado durante la espera. Hilo autodestruido.")
                    return

                _time.sleep(poll)
        finally:
            self._active_monitors.pop(game_name.lower(), None)

    def launch_game(
        self,
        name: str,
        chat_id: int,
        bot,
        cfg,
        platform,
        profile_name: str | None = None,
    ) -> None:
        cancel_ev = self._get_cancel_event(name)
        cancel_ev.clear()
        game_shortcut = self._find_shortcut(name)

        if not game_shortcut:
            bot.send_message(
                chat_id,
                f"❌ No encontré el acceso directo de *{name}* en su escritorio, {cfg.user_title}.\n\n"
                f"📌 *Requisito:* Asegúrese de que exista el acceso directo de GeForce NOW en el escritorio."
            )
            return

        bot.send_message(chat_id, f"🎮 Lanzando *{name}* desde el acceso directo del escritorio...")
        if not self._launch_shortcut(game_shortcut):
            bot.send_message(chat_id, f"❌ No pude ejecutar el acceso directo de {name}, {cfg.user_title}.")
            return

        bot.send_message(
            chat_id,
            f"🔄 Acceso directo iniciado. Supervisando *{name}*..."
        )
        threading.Thread(
            target=self._queue_monitor,
            args=(name, chat_id, bot, cfg, platform, profile_name),
            daemon=True,
        ).start()

    def check_queue_status(self, chat_id: int, bot, cfg, platform) -> None:
        """Consulta instantánea en 0ms del estado actual."""
        state = self._get_window_state()

        if state == "STREAMING":
            bot.send_message(chat_id, f"🟢 ¡Ya hay un juego en transmisión activa, {cfg.user_title}!")
        elif state == "QUEUE":
            if self._last_queue_info:
                pos = self._last_queue_info.get("position", "?")
                bot.send_message(
                    chat_id,
                    f"⏳ Posición en la cola de GeForce NOW: *{pos}* jugadores por delante, {cfg.user_title}."
                )
            elif self._active_monitors:
                game = list(self._active_monitors.keys())[0].title()
                start = list(self._active_monitors.values())[0]
                elapsed = int(_time.time() - start)
                bot.send_message(
                    chat_id,
                    f"⏳ Sigues en la cola de GeForce NOW para *{game}* ({elapsed//60}m {elapsed%60}s esperando), {cfg.user_title}."
                )
            else:
                bot.send_message(chat_id, f"⏳ La aplicación de GeForce NOW está activa en pantalla, {cfg.user_title}.")
        else:
            bot.send_message(chat_id, f"🔍 No detecto ninguna cola ni transmisión activa de GeForce NOW en este momento.")

    def cancel_queue(self, game_name: str | None = None) -> None:
        if game_name:
            key = game_name.lower()
            if key in self._cancel_events:
                self._cancel_events[key].set()
        else:
            for ev in self._cancel_events.values():
                ev.set()
