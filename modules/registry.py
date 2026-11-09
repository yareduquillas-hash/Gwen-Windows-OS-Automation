from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

from .base import BaseModule

log = logging.getLogger("jarvis.modules")


class ModuleRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self._modules: list[BaseModule] = []
        self._discover()

    def _discover(self) -> None:
        import modules as pkg
        pkg_dir = Path(pkg.__path__[0])

        for _, name, _ in pkgutil.iter_modules([str(pkg_dir)]):
            if name in ("base", "registry", "auth", "__init__"):
                continue
            if not self.cfg.is_module_enabled(name):
                log.info("Módulo '%s' desactivado en .env", name)
                continue
            self._load_module(name)

        self._modules.sort(key=lambda m: m.prioridad)
        log.info("Registry: %s módulos listos", len(self._modules))

    def _load_module(self, name: str) -> bool:
        if any(
            module.__class__.__module__.rsplit(".", 1)[-1].lower() == name.lower()
            for module in self._modules
        ):
            return True
        try:
            mod = importlib.import_module(f"modules.{name}")
            cls = getattr(mod, "MODULE_CLASS", None)
            if cls is None:
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                        cls = obj
                        break
            if cls is None:
                log.warning("Módulo '%s' no tiene clase BaseModule", name)
                return False
            instance = cls()
            instance.nombre = instance.nombre or name
            self._modules.append(instance)
            log.info("Módulo cargado: %s (prioridad %s)", instance.nombre, instance.prioridad)
            return True
        except Exception as exc:
            log.warning("Error al cargar módulo '%s': %s", name, exc)
            return False

    def dispatch(self, texto: str, chat_id: int, bot) -> None:
        from database.repositories.conversacion import guardar_conversacion
        from modules.secciones import get_seccion

        sec_id, _ = get_seccion(chat_id)
        guardar_conversacion("usuario", texto, seccion_id=sec_id)

        for module in self._modules:
            if not module.enabled:
                continue
            try:
                try:
                    can = module.can_handle(texto, self.cfg, chat_id)
                except TypeError:
                    try:
                        can = module.can_handle(texto, self.cfg)
                    except TypeError:
                        can = module.can_handle(texto)
                if can:
                    handled = module.handle(texto, chat_id, bot, self.cfg, self._get_platform())
                    if handled:
                        return
            except Exception as exc:
                log.error("Módulo '%s' falló: %s", module.nombre, exc)

        self._fallback_ai(texto, chat_id, bot)

    def _fallback_ai(self, texto: str, chat_id: int, bot) -> None:
        try:
            from ai.direct_ai_runner import ejecutar_ia_directa
            ejecutar_ia_directa(texto, chat_id, bot, self.cfg)
        except Exception as exc:
            log.warning("Ejecución IA directa falló: %s", exc)

    def _get_platform(self):
        from plat_adapter import get_adapter
        if not hasattr(self, "_plat"):
            self._plat = get_adapter()
        return self._plat

    def set_module_enabled(self, name: str, enabled: bool) -> bool:
        """Actualiza un modulo ya cargado sin reconstruir el proceso."""
        wanted = name.lower().strip()
        for module in self._modules:
            module_name = module.__class__.__module__.rsplit(".", 1)[-1].lower()
            if module.nombre.lower() == wanted or module_name == wanted:
                module.enabled = enabled
                if enabled:
                    module.on_enable()
                else:
                    module.on_disable()
                return True
        if enabled and self._load_module(wanted):
            self._modules.sort(key=lambda m: m.prioridad)
            return True
        return False

    def module_status(self) -> dict[str, bool]:
        status = dict(getattr(self.cfg, "modules_enabled", {}))
        status.update({
            module.__class__.__module__.rsplit(".", 1)[-1]: bool(module.enabled)
            for module in self._modules
        })
        return status
