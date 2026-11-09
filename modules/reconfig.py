from __future__ import annotations

import re

from modules.base import BaseModule
from modules.protocolos import get_protocolo
from modules.secciones import get_seccion


class ReconfigModule(BaseModule):
    nombre = "reconfig"
    prioridad = 5

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        triggers = (
            "muéstrame la configuración", "muestrame la configuracion",
            "configuración actual", "configuracion actual",
            "cambia el modelo", "cambiar modelo", "pon el modelo",
            "desactiva el módulo", "desactiva el modulo",
            "activa el módulo", "activa el modulo",
            "restaura configuración", "restaura configuracion",
            "restaurar configuración", "restaurar configuracion",
            "modo económico", "modo economico", "modo gaming",
            "modo noche", "modo ahorro",
            "guarda esta configuración", "guarda config",
            "carga el preset", "aplica el preset", "preset",
            "cambia el nombre", "cambiar nombre", "llámame", "llamame",
            "cambia el título", "cambiar título", "cambia titulo",
            "cambia el timeout", "timeout",
            "reiníciate", "reiniciate", "reiniciar",
            "qué overrides", "que overrides", "qué cambios",
            "mis presets", "lista presets", "qué presets",
        )
        return any(p in t for p in triggers)

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if any(p in t for p in ("muéstrame la configuración", "muestrame la configuracion",
                                  "configuración actual", "configuracion actual")):
            return self._mostrar_config(chat_id, bot, cfg)

        if any(p in t for p in ("qué overrides", "que overrides", "qué cambios")):
            return self._mostrar_overrides(chat_id, bot, cfg)

        if any(p in t for p in ("mis presets", "lista presets", "qué presets", "que presets")):
            return self._mostrar_presets(chat_id, bot, cfg)

        if any(p in t for p in ("modo económico", "modo economico", "modo ahorro")):
            return self._aplicar_preset("economico", chat_id, bot, cfg)

        if any(p in t for p in ("modo gaming",)):
            return self._aplicar_preset("gaming", chat_id, bot, cfg)

        if any(p in t for p in ("modo noche",)):
            return self._aplicar_preset("noche", chat_id, bot, cfg)

        if "preset" in t and any(p in t for p in ("carga", "aplica")):
            name = self._extraer_valor(texto, t, ("carga el preset ", "aplica el preset ", "preset "))
            if name:
                return self._aplicar_preset(name, chat_id, bot, cfg)

        for pref in ("guarda esta configuración", "guarda config", "guardar config",
                      "guardar configuración"):
            if pref in t:
                name = texto.split(pref, 1)[-1].strip().strip('"').strip("'") or "personalizado"
                self._guardar_preset(name, chat_id, bot, cfg)
                return True

        for pref in ("cambia el modelo", "cambiar modelo", "pon el modelo"):
            if pref in t:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                return self._cambiar_modelo(val, chat_id, bot, cfg)

        for pref in ("cambia el timeout", "timeout"):
            if pref in t:
                nums = re.findall(r"\d+", texto)
                if nums:
                    return self._cambiar_override("opencode_timeout", int(nums[0]), chat_id, bot, cfg)
                bot.send_message(chat_id, "Indíqueme un valor numérico en segundos, Señor.")
                return True

        for pref in ("cambia el nombre", "cambiar nombre", "llámame", "llamame"):
            if pref in t:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                if val:
                    return self._cambiar_override("user_name", val, chat_id, bot, cfg)

        for pref in ("cambia el título", "cambiar título", "cambia titulo"):
            if pref in t:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                if val:
                    return self._cambiar_override("user_title", val, chat_id, bot, cfg)

        if any(p in t for p in ("restaura configuración", "restaura configuracion",
                                  "restaurar configuración", "restaurar configuracion")):
            ok = cfg.restore_backup()
            bot.send_message(chat_id, "Configuración restaurada, Señor." if ok else "No hay backup disponible, Señor.")
            return True

        for pref in ("desactiva el módulo", "desactiva el modulo"):
            if pref in t:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                if val:
                    if val.lower() not in getattr(cfg, "modules_enabled", {}):
                        bot.send_message(chat_id, f"No conozco el módulo '{val}', Señor.")
                        return True
                    cfg.override(f"module_{val}", False)
                    bot.send_message(chat_id, f"Módulo '{val}' desactivado; se aplicará al reiniciar.")
                    return True

        for pref in ("activa el módulo", "activa el modulo"):
            if pref in t:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                if val:
                    if val.lower() not in getattr(cfg, "modules_enabled", {}):
                        bot.send_message(chat_id, f"No conozco el módulo '{val}', Señor.")
                        return True
                    cfg.override(f"module_{val}", True)
                    bot.send_message(chat_id, f"Módulo '{val}' activado; se aplicará al reiniciar.")
                    return True

        if any(p in t for p in ("reiníciate", "reiniciate", "reiniciar")):
            if not any(p in t for p in ("reiniciar confirmar", "reiniciate confirmar", "reiníciate confirmar")):
                bot.send_message(
                    chat_id,
                    "Reiniciar el servicio corta las tareas activas. Diga 'reiniciar confirmar' para continuar, Señor.",
                )
                return True
            bot.send_message(chat_id, "Reiniciando, Señor. Hasta ahora mismo.")
            self._reiniciar(bot, cfg)
            return True

        if "volumen" in t and "juego" in t:
            nums = re.findall(r"\d+", texto)
            if nums:
                return self._cambiar_override("gfn_gaming_volume", int(nums[0]), chat_id, bot, cfg)

        return False

    def _mostrar_config(self, chat_id, bot, cfg) -> bool:
        overrides = cfg.list_overrides()
        preset = cfg.active_preset
        proto = get_protocolo() or "ninguno"
        prov = getattr(cfg, "ai_provider", "nvidia")
        if prov == "nvidia":
            active_mod = getattr(cfg, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
        elif prov == "openrouter":
            active_mod = getattr(cfg, "openrouter_model", "")
        else:
            active_mod = getattr(cfg, "groq_model", "")

        lines = [
            f"⚙️ Configuración actual, {cfg.full_name}:",
            "",
            f"🤖 Proveedor IA:  {prov.upper()}",
            f"   Modelo activo: {active_mod}",
            f"   Protocolo:     {proto}",
            f"   Timeout:       {cfg.opencode_timeout}s",
            "",
            f"👤 Nombre:        {cfg.user_name}",
            f"   Título:        {cfg.user_title}",
            f"   Voz:           {cfg.tts_voice}",
            "",
            f"🎮 Vol. juego:    {cfg.gfn_gaming_volume}%",
            f"   Timeout cola:  {cfg.gfn_queue_timeout_minutes} min",
            f"   Juegos:        {', '.join(cfg.gfn_quick_games[:3])}",
            "",
            f"⚡ Rate limit:    {cfg.rate_limit_max_per_minute}/min",
            f"📁 Sección:       {(get_seccion(chat_id)[1]) or 'general'}",
        ]

        if preset:
            lines.append(f"\n💾 Preset activo: {preset}")
        if overrides:
            lines.append("\n⚡ Overrides activos:")
            for k, v in overrides.items():
                lines.append(f"   {k} = {v}")
            lines.append("\nPara restaurar: \"restaura configuración\"")

        bot.send_message(chat_id, "\n".join(lines))
        return True

    def _mostrar_overrides(self, chat_id, bot, cfg) -> bool:
        ov = cfg.list_overrides()
        if not ov:
            bot.send_message(chat_id, "No hay overrides activos, Señor. Todo está en su configuración base.")
        else:
            lines = ["⚡ Overrides activos:"] + [f"  {k} = {v}" for k, v in ov.items()]
            bot.send_message(chat_id, "\n".join(lines))
        return True

    def _mostrar_presets(self, chat_id, bot, cfg) -> bool:
        presets = cfg.list_presets()
        if not presets:
            bot.send_message(chat_id, "No hay presets guardados, Señor.")
            return True
        lines = ["💾 Presets disponibles:"]
        for name, settings in presets.items():
            marcador = " ◀ activo" if name == cfg.active_preset else ""
            keys = ", ".join(settings.keys())
            lines.append(f"  • {name}{marcador}  ({keys})")
        lines.append("\nUse \"activa el preset <nombre>\" para aplicar.")
        bot.send_message(chat_id, "\n".join(lines))
        return True

    def _aplicar_preset(self, name: str, chat_id, bot, cfg) -> bool:
        ok = cfg.apply_preset(name)
        if ok:
            bot.send_message(chat_id, f"Preset '{name}' aplicado, {cfg.user_title}.")
        else:
            bot.send_message(chat_id, f"No encontré el preset '{name}', Señor. Use \"mis presets\" para verlos.")
        return True

    def _guardar_preset(self, name: str, chat_id, bot, cfg) -> None:
        settings = {
            "ai_provider": cfg.ai_provider,
            "openrouter_model": cfg.openrouter_model,
            "groq_model": cfg.groq_model,
            "nvidia_model": getattr(cfg, "nvidia_model", ""),
            "gfn_gaming_volume": cfg.gfn_gaming_volume,
        }
        cfg.save_preset(name, settings)
        bot.send_message(chat_id, f"Configuración actual guardada como preset '{name}', Señor.")

    def _cambiar_override(self, key: str, value, chat_id, bot, cfg) -> bool:
        if key == "opencode_timeout" and (
            not isinstance(value, int) or not 1 <= value <= 900
        ):
            bot.send_message(chat_id, "El timeout debe estar entre 1 y 900 segundos, Señor.")
            return True
        if key == "gfn_gaming_volume" and (
            not isinstance(value, int) or not 0 <= value <= 100
        ):
            bot.send_message(chat_id, "El volumen de juego debe estar entre 0 y 100, Señor.")
            return True
        if key in {"user_name", "user_title"} and (not isinstance(value, str) or not value.strip() or len(value.strip()) > 40):
            bot.send_message(chat_id, "El texto de usuario no es valido, Señor.")
            return True
        cfg.override(key, value)
        bot.send_message(chat_id, f"{key} → {value}. Cambio aplicado, Señor.")
        return True

    def _cambiar_modelo(self, val: str, chat_id, bot, cfg) -> bool:
        if not val:
            bot.send_message(chat_id, "¿Qué modelo desea usar, Señor?")
            return True
        resolved = self._resolver_modelo(val)
        if resolved is None:
            bot.send_message(chat_id, f"Modelo '{val}' no esta en la lista permitida, Señor.")
            return True
        provider, model = resolved
        cfg.ai_provider = provider
        if provider == "openrouter":
            cfg.openrouter_model = model
        elif provider == "groq":
            cfg.groq_model = model
        elif provider == "nvidia":
            cfg.nvidia_model = model
        bot.send_message(chat_id, f"Modelo actualizado, Señor. Proveedor: {provider.upper()} ({model}).")
        return True

    def _resolver_modelo(self, nombre: str) -> tuple[str, str] | None:
        known = {
            "nv-flash": ("nvidia", "deepseek-ai/deepseek-v4-flash"),
            "nv-pro": ("nvidia", "deepseek-ai/deepseek-v4-pro"),
            "nv-llama": ("nvidia", "meta/llama-3.3-70b-instruct"),
            "nv-nemo": ("nvidia", "nvidia/llama-3.3-nemotron-super-49b-v1.5"),
            "nv-gemma": ("nvidia", "google/gemma-4-31b-it"),
            "auto": ("openrouter", "openrouter/free"),
            "r1": ("openrouter", "deepseek/deepseek-r1"),
            "ds": ("openrouter", "deepseek/deepseek-chat"),
            "gemma": ("openrouter", "google/gemma-4-31b-it:free"),
            "reasoning": ("openrouter", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
            "groq": ("groq", "llama-3.3-70b-versatile"),
        }
        n = nombre.lower().strip()
        for key, (prov, mod) in known.items():
            if key in n:
                return prov, mod
        return None

    def _extraer_valor(self, texto: str, t_lower: str, prefijos: tuple[str, ...]) -> str | None:
        for pref in prefijos:
            if pref in t_lower:
                val = texto.split(pref, 1)[-1].strip().strip('"').strip("'")
                return val if val else None
        return None

    def _reiniciar(self, bot, cfg=None) -> None:
        import subprocess
        import sys
        import os
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

        cwd = str(cfg.project_root) if cfg and hasattr(cfg, 'project_root') else os.getcwd()
        exe = sys.executable
        if exe.endswith("python.exe"):
            pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
            if os.path.isfile(pyw):
                exe = pyw
        kw = {"cwd": cwd}
        if os.name == "nt":
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen([exe, os.path.join(cwd, "main.py")], **kw)
        sys.exit(0)


MODULE_CLASS = ReconfigModule
