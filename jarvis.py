from __future__ import annotations

import logging
import threading
import time as _time
from typing import Callable

from telebot import TeleBot

from adapters import InputRouter, TelegramInputAdapter
from config import JarvisConfig
from modules.registry import ModuleRegistry
from modules.auth import Authorizer


log = logging.getLogger("jarvis")


class JarvisBot:
    def __init__(self, cfg: JarvisConfig) -> None:
        self.cfg = cfg
        self.bot = TeleBot(cfg.telegram_token)
        self.auth = Authorizer(cfg)
        self.registry = ModuleRegistry(cfg)
        self.input_router = InputRouter(self.registry, cfg)

        self._register_handlers()

    def _require_auth(self, handler):
        """Decorador interno: rechaza el mensaje si no está autorizado."""
        import functools
        @functools.wraps(handler)
        def wrapper(message):
            if not self.auth.check(message):
                self.auth.deny(message, self.bot)
                return
            try:
                handler(message)
            except Exception as exc:
                log.exception("Error no manejado en handler %s", handler.__name__)
                try:
                    self.bot.reply_to(message, f"Ocurrió un error inesperado al procesar la solicitud, {self.cfg.user_title}.")
                except Exception:
                    pass
        return wrapper

    def _register_handlers(self) -> None:
        bot = self.bot
        ra = self._require_auth
        bot.message_handler(commands=["start", "help"])(ra(self._on_start))
        bot.message_handler(commands=["config"])(ra(self._on_config))
        bot.message_handler(commands=["tareas"])(ra(self._on_tareas_list))
        bot.message_handler(commands=["eliminar_tarea"])(ra(self._on_tareas_delete))
        bot.message_handler(commands=["secciones"])(ra(self._on_secciones_list))
        bot.message_handler(commands=["seccion"])(ra(self._on_seccion_switch))
        bot.message_handler(commands=["memoria", "perfil"])(ra(self._on_memoria))
        bot.message_handler(commands=["contexto"])(ra(self._on_contexto))
        bot.message_handler(commands=["sh"])(ra(self._on_sh_command))
        bot.message_handler(commands=["shutdown"])(ra(self._on_shutdown))
        bot.message_handler(commands=["descargas"])(ra(self._on_descargas))
        bot.message_handler(commands=["descarga"])(ra(self._on_descarga))
        bot.message_handler(commands=["instala"])(ra(self._on_instala))
        bot.message_handler(commands=["protocolo_g", "protocolo_m"])(ra(self._on_protocolo_status))
        bot.message_handler(commands=["bateria"])(ra(self._on_bateria))
        bot.message_handler(commands=["volumen"])(ra(self._on_volumen))
        bot.message_handler(commands=["pausa","play","next","prev"])(ra(self._on_media))
        bot.message_handler(commands=["lanza", "oc_gfn"])(ra(self._on_lanza))
        bot.message_handler(commands=["wizard"])(ra(self._on_wizard))
        bot.message_handler(commands=["captura"])(ra(self._on_captura))
        bot.message_handler(commands=["sistema"])(ra(self._on_sistema_info))
        bot.message_handler(commands=["procesos"])(ra(self._on_procesos))
        bot.message_handler(commands=["ventanas"])(ra(self._on_ventanas))
        bot.message_handler(commands=["preset"])(ra(self._on_preset))
        bot.message_handler(commands=["modelo", "modelos"])(ra(self._on_modelo))
        bot.message_handler(commands=["drive","transfer","ruta","saltar","todo"])(ra(self._on_upload_action))
        bot.message_handler(commands=["reiniciar"])(ra(self._on_reiniciar))
        bot.message_handler(content_types=["text"])(ra(self._on_text))
        bot.message_handler(content_types=["voice"])(ra(self._on_voice))
        bot.message_handler(content_types=["document", "photo"])(ra(self._on_file))

    def run(self) -> None:
        from utils.scheduler import TaskScheduler
        self.scheduler = TaskScheduler(self.cfg, bot=self.bot)
        self.scheduler.start()

        log.info(
            "Gwen en linea, %s. A la espera de sus instrucciones.",
            self.cfg.full_name,
        )
        self.bot.infinity_polling(skip_pending=True)

    # ── Handlers ──

    def _on_start(self, message) -> None:
        help_text = self._build_help()
        log.info("Comando /start recibido de %s", message.chat.id)
        print(f"\n[Gwen System] Comando /start ejecutado para usuario {message.chat.id}:\n{help_text}\n")
        try:
            self.bot.reply_to(message, help_text, parse_mode="HTML")
        except Exception as exc:
            log.warning("Error enviando HTML help: %s. Reintentando texto plano...", exc)
            # Fallback en texto plano sin etiquetas
            import re
            plain_text = re.sub(r'<[^>]+>', '', help_text)
            self.bot.reply_to(message, plain_text)

    def _on_config(self, message) -> None:
        from modules.reconfig import ReconfigModule
        rm = ReconfigModule()
        rm._mostrar_config(message.chat.id, self.bot, self.cfg)

    def _on_text(self, message) -> None:
        texto = message.text.strip()
        if not texto:
            return
        log.info("Texto recibido de chat %s (longitud=%s)", message.chat.id, len(texto))
        event = TelegramInputAdapter.from_message(message, texto)
        self.input_router.dispatch(event, self.bot)

    def _on_voice(self, message) -> None:
        log.info("Voz de %s", message.chat.id)
        from modules.voz import VoiceModule
        VoiceModule.instance(self.cfg).handle_voice(message, self.bot, self.input_router)

    def _on_file(self, message) -> None:
        from modules.archivos import save_incoming_file
        save_incoming_file(message, self.bot, self.cfg)

    # ── Comandos delegados ──

    def _on_sh_command(self, message) -> None:
        from modules.sistema import handle_sh_command
        handle_sh_command(message, self.bot, self.cfg)

    def _on_shutdown(self, message) -> None:
        from modules.sistema import handle_shutdown
        handle_shutdown(message, self.bot, self.cfg, self.scheduler)

    def _on_tareas_list(self, message) -> None:
        from modules.tareas import list_tasks
        list_tasks(message, self.bot, self.cfg)

    def _on_tareas_delete(self, message) -> None:
        from modules.tareas import delete_task
        delete_task(message, self.bot, self.cfg)

    def _on_secciones_list(self, message) -> None:
        from modules.secciones import list_sections
        list_sections(message, self.bot)

    def _on_seccion_switch(self, message) -> None:
        from modules.secciones import switch_section_command
        switch_section_command(message, self.bot)

    def _on_memoria(self, message) -> None:
        from modules.memoria import show_memory
        show_memory(message, self.bot)

    def _on_contexto(self, message) -> None:
        from modules.memoria import show_context
        show_context(message, self.bot)

    def _on_descargas(self, message) -> None:
        from modules.descargas import handle_descargas_command
        handle_descargas_command(message, self.bot, self.cfg)

    def _on_descarga(self, message) -> None:
        from modules.descargas import handle_descarga_command
        handle_descarga_command(message, self.bot, self.cfg)

    def _on_instala(self, message) -> None:
        from modules.descargas import handle_instala_command
        handle_instala_command(message, self.bot, self.cfg)

    def _on_protocolo_status(self, message) -> None:
        from modules.protocolos import show_status
        show_status(message, self.bot, self.cfg)

    def _on_bateria(self, message) -> None:
        from plat_adapter import get_adapter
        p = get_adapter()
        data = p.get_battery()
        if "error" in data:
            self.bot.reply_to(message, "No disponible, Señor.")
        else:
            self.bot.reply_to(message, f"Batería: {data['percentage']} ({data.get('state','')})")

    def _on_wizard(self, message) -> None:
        from modules.wizard import WizardModule, _wizard_states
        w = WizardModule()
        w.handle(message.text.strip(), message.chat.id, self.bot, self.cfg, None)

    def _on_volumen(self, message) -> None:
        from plat_adapter import get_adapter
        p = get_adapter()
        arg = message.text.partition(" ")[2].strip()
        if not arg:
            vol = p.get_volume()
            self.bot.reply_to(message, f"Volumen: {vol}%" if vol >= 0 else "No disponible")
            return
        try:
            nivel = max(0, min(100, int(arg)))
            ok = p.set_volume(nivel)
            self.bot.reply_to(
                message,
                f"Volumen: {nivel}%" if ok else "No pude ajustar el volumen, Señor.",
            )
        except ValueError:
            self.bot.reply_to(message, "Indique un número, Señor. Ej: /volumen 50")

    def _on_media(self, message) -> None:
        from plat_adapter import get_adapter
        cmd = message.text.strip().lstrip("/").split()[0].lower()
        key_map = {"pausa": "pause", "play": "play", "next": "next", "prev": "prev"}
        p = get_adapter()
        p.send_media_key(key_map.get(cmd, cmd))
        self.bot.reply_to(message, f"{cmd.capitalize()} ejecutado, Señor.")

    def _on_lanza(self, message) -> None:
        game = message.text.partition(" ")[2].strip()
        if not game:
            self.bot.reply_to(message, "¿Qué juego? Ej: /lanza genshin impact")
            return
        from utils.gfn_engine import GFNEngine
        from plat_adapter import get_adapter
        e = GFNEngine(self.cfg)
        threading.Thread(
            target=e.launch_game,
            args=(game, message.chat.id, self.bot, self.cfg, get_adapter()),
            daemon=True,
        ).start()

    def _on_captura(self, message) -> None:
        from plat_adapter import get_adapter
        self.bot.reply_to(message, "Capturando...")
        img = get_adapter().take_screenshot()
        if img:
            import io
            self.bot.send_photo(message.chat.id, io.BytesIO(img))
        else:
            self.bot.reply_to(message, "No pude capturar, Señor.")

    def _on_sistema_info(self, message) -> None:
        from plat_adapter import get_adapter
        p = get_adapter()
        try:
            info = p.get_system_info()
            from datetime import datetime
            boot = datetime.fromtimestamp(info["boot_time"]).strftime("%H:%M %d/%m")
            msg = (f"CPU: {info['cpu_percent']}%\n"
                   f"RAM: {info['ram_used_gb']:.1f}/{info['ram_total_gb']:.1f} GB ({info['ram_percent']}%)\n"
                   f"Disco: {info['disk_free_gb']:.1f} GB libres ({info['disk_percent']}% usado)\n"
                   f"Uptime: desde {boot}")
            self.bot.reply_to(message, msg)
        except Exception as exc:
            self.bot.reply_to(message, f"Error: {exc}")

    def _on_procesos(self, message) -> None:
        from plat_adapter import get_adapter
        procs = get_adapter().get_running_processes(10)
        lines = [f"{p['name']} ({p['memory_mb']} MB)" for p in procs]
        self.bot.reply_to(message, "Top RAM:\n" + "\n".join(lines))

    def _on_ventanas(self, message) -> None:
        from plat_adapter import get_adapter
        wins = get_adapter().get_windows()
        if wins:
            self.bot.reply_to(message, "Ventanas:\n" + "\n".join(wins[:15]))
        else:
            self.bot.reply_to(message, "No detecto ventanas, Señor.")

    def _on_preset(self, message) -> None:
        name = message.text.partition(" ")[2].strip()
        if not name:
            presets = self.cfg.list_presets() if hasattr(self.cfg, 'list_presets') else {}
            lines = [f"/preset {n}" for n in presets.keys()]
            self.bot.reply_to(message, "Presets:\n" + "\n".join(lines) if lines else "Sin presets")
            return
        if hasattr(self.cfg, 'apply_preset'):
            ok = self.cfg.apply_preset(name)
            self.bot.reply_to(message, f"Preset '{name}' aplicado." if ok else f"No existe '{name}'.")

    def _on_modelo(self, message) -> None:
        from ai.models import MODELOS
        arg = message.text.partition(" ")[2].strip().lower()
        if not arg or arg == "listar":
            prov_act = getattr(self.cfg, "ai_provider", "nvidia")
            if prov_act == "nvidia":
                mod_act = getattr(self.cfg, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
            elif prov_act == "openrouter":
                mod_act = getattr(self.cfg, "openrouter_model", "")
            else:
                mod_act = getattr(self.cfg, "groq_model", "")

            lines = [
                f"Proveedor actual: {prov_act.upper()}",
                f"Modelo actual: {mod_act}",
                "",
                "Modelos disponibles:",
            ]
            for k, (prov, mod, desc) in MODELOS.items():
                marca = " ◀" if (prov == prov_act and mod == mod_act) else ""
                lines.append(f"/modelo {k:<10} → {desc}{marca}")
            self.bot.reply_to(message, "\n".join(lines))
            return
        if arg in MODELOS:
            prov, mod, desc = MODELOS[arg]
            if hasattr(self.cfg, "override"):
                self.cfg.override("ai_provider", prov)
                if prov == "nvidia":
                    self.cfg.override("nvidia_model", mod)
                elif prov == "openrouter":
                    self.cfg.override("openrouter_model", mod)
                elif prov == "groq":
                    self.cfg.override("groq_model", mod)
            else:
                setattr(self.cfg, "ai_provider", prov)
                if prov == "nvidia":
                    setattr(self.cfg, "nvidia_model", mod)
                elif prov == "openrouter":
                    setattr(self.cfg, "openrouter_model", mod)
                elif prov == "groq":
                    setattr(self.cfg, "groq_model", mod)
            self.bot.reply_to(message, f"Modelo cambiado a {desc} ({mod}), {self.cfg.user_title}.")
        else:
            self.bot.reply_to(message, f"Modelo '{arg}' no reconocido. Use /modelo para ver la lista.")

    def _on_upload_action(self, message) -> None:
        from modules.archivos import _handle_large_files_menu
        cmd = message.text.strip().lstrip("/").split()[0].lower()
        handled = _handle_large_files_menu(cmd, message.text, message.chat.id, self.bot, self.cfg)
        if not handled:
            self.bot.reply_to(message, "No hay archivos pendientes para procesar, Senor.")

    def _on_reiniciar(self, message) -> None:
        if (message.text or "").strip().lower() != "/reiniciar confirmar":
            self.bot.reply_to(
                message,
                "Reiniciar el servicio corta las tareas activas. Envie `/reiniciar confirmar` si esta seguro.",
            )
            return
        self.bot.reply_to(message, "Reiniciando, Señor.")
        import subprocess, sys, os
        try:
            self.bot.stop_polling()
        except Exception:
            pass
        try:
            from database.connection import ConnectionManager
            ConnectionManager.close_instance()
        except Exception:
            pass
        try:
            if hasattr(self, "scheduler") and self.scheduler:
                self.scheduler.stop()
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
        exe = sys.executable
        if exe.endswith("python.exe"):
            pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
            if os.path.isfile(pyw):
                exe = pyw
        kw = {"cwd": os.getcwd()}
        if os.name == "nt":
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen([exe, os.path.join(os.getcwd(), "main.py")], **kw)
        sys.exit(0)

    def _build_help(self) -> str:
        c = self.cfg
        overrides = c.list_overrides() if hasattr(c, 'list_overrides') else {}
        preset = c.active_preset if hasattr(c, 'active_preset') else None

        from modules.protocolos import get_protocolo as pa_fn
        from modules.secciones import get_seccion as sec_fn

        pa = pa_fn()
        _, sec_nombre = sec_fn()

        prov = getattr(c, "ai_provider", "nvidia")
        if prov == "nvidia":
            active_mod = getattr(c, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
        elif prov == "openrouter":
            active_mod = getattr(c, "openrouter_model", "")
        else:
            active_mod = getattr(c, "groq_model", "")

        lines = [
            f"⚡ <b>Gwen Windows Pro — Asistente Autoconsciente</b>\n",
            "┌─ 🤖 <b>Estado de IA</b> ────────────────────",
            f"│ Proveedor : <b>{prov.upper()}</b>",
            f"│ Modelo    : <code>{active_mod}</code>",
        ]
        if pa:
            lines.append(f"│ ▶ Protocolo {pa} ACTIVO")
        if preset:
            lines.append(f"│ 💾 Preset   : {preset}")
        if sec_nombre:
            lines.append(f"│ 📌 Sección  : {sec_nombre}")

        if overrides:
            lines.append("├─ Overrides ─────────────────────────")
            for k, v in overrides.items():
                lines.append(f"│ {k} = {v}")

        enabled = sum(1 for m in self.registry._modules if m.enabled)

        lines.extend([
            "├─ 🧩 <b>Módulos</b> ──────────────────────────",
            f"│ {enabled}/{len(self.registry._modules)} Módulos Activos",
            "├─ ⚙️ <b>Control de Sistema & Hardware</b> ──────",
            "│ /bateria      🔋 Estado de batería",
            "│ /sistema      📊 CPU, RAM, Disco y Uptime",
            "│ /procesos     💻 Procesos consumo RAM",
            "│ /ventanas     🪟 Lista de ventanas activas",
            "│ /captura      📸 Captura de pantalla",
            "│ /sh &lt;cmd&gt;     🐚 Ejecutar consola segura",
            "├─ 🎵 <b>Multimedia & Audio</b> ──────────────",
            "│ /volumen N    🔊 Ajustar volumen maestro",
            "│ /play /pausa  ⏯️ Control de reproducción",
            "│ /next /prev   ⏭️ Pista siguiente / anterior",
            "├─ 🎮 <b>Cloud Gaming</b> ─────────────────────",
            "│ /lanza &lt;juego&gt; 🎮 Lanzar GeForce NOW",
            "├─ 🧠 <b>Modelos de IA & Ajustes</b> ─────────",
            "│ /modelo       🤖 Cambiar modelo IA",
            "│ /config       ⚙️ Configuración activa",
            "│ /tareas       📅 Tareas programadas",
            "│ /memoria      🧠 Memoria persistente",
            "│ /secciones    📁 Secciones de contexto",
            "│ /descargas    📂 Gestión de descargas",
            "│ /reiniciar    🔄 Reiniciar servicio Gwen",
            "├─ 🎤 <b>Comandos de Voz</b> ──────────────────",
            "│ Envía una nota de audio directamente",
            "└────────────────────────────────────",
        ])
        return "\n".join(lines)
