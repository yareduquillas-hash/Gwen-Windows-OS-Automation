from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import threading
import time as _time
import uuid
from pathlib import Path

log = logging.getLogger("jarvis.config")


class ConfigManager:
    def __init__(self, cfg):
        self._cfg = cfg
        settings_dir = getattr(cfg, "settings_dir", cfg.data_dir)
        self._path = Path(settings_dir) / "config_override.json"
        self._backup_dir = Path(settings_dir) / "config_backups"
        self.presets: dict[str, dict] = {}
        self.overrides: dict[str, object] = {}
        self.active_preset: str | None = None
        self._lock = threading.RLock()
        self._load()

    def override(self, key: str, value) -> None:
        with self._lock:
            self._backup()
            self.overrides[key] = value
            self.active_preset = None
            self._save()

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            self._backup()
            if key:
                self.overrides.pop(key, None)
            else:
                self.overrides.clear()
                self.active_preset = None
            self._save()

    def apply_preset(self, name: str) -> bool:
        with self._lock:
            if name not in self.presets:
                return False
            self._backup()
            self.overrides = dict(self.presets[name])
            self.active_preset = name
            self._save()
            return True

    def save_preset(self, name: str, settings: dict) -> None:
        with self._lock:
            self.presets[name] = dict(settings)
            self._save()

    def delete_preset(self, name: str) -> bool:
        with self._lock:
            if name not in self.presets:
                return False
            del self.presets[name]
            if self.active_preset == name:
                self.active_preset = None
            self._save()
            return True

    def restore_backup(self) -> bool:
        with self._lock:
            backups = sorted(self._backup_dir.glob("backup_*.json"), reverse=True)
            if not backups:
                return False
            try:
                data = json.loads(backups[0].read_text(encoding="utf-8"))
                self.overrides = data.get("overrides", {})
                self.presets = data.get("presets", {})
                self.active_preset = data.get("active_preset")
                self._save()
                return True
            except Exception as exc:
                log.warning("Error restaurando backup: %s", exc)
                return False

    def _backup(self) -> None:
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = _time.strftime("%Y%m%d_%H%M%S")
            backup_path = self._backup_dir / f"backup_{timestamp}_{uuid.uuid4().hex[:8]}.json"
            data = {
                "overrides": self.overrides,
                "presets": self.presets,
                "active_preset": self.active_preset,
            }
            self._atomic_write(backup_path, data)
            all_backups = sorted(self._backup_dir.glob("backup_*.json"))
            for old in all_backups[:-20]:
                old.unlink()
        except Exception as exc:
            log.warning("Error creando backup: %s", exc)

    def _load(self) -> None:
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self.overrides = data.get("overrides", {})
                self.presets = data.get("presets", {})
                self.active_preset = data.get("active_preset")
            else:
                self._init_default_presets()
                self._save()
        except Exception as exc:
            log.warning("Error cargando overrides: %s", exc)
            self.overrides = {}
            self.presets = {}
            self.active_preset = None

    def _init_default_presets(self) -> None:
        self.presets = {
            "economico": {
                "ai_provider": "openrouter",
                "openrouter_model": "google/gemma-4-31b-it:free",
                "gfn_gaming_volume": 50,
            },
            "gaming": {
                "ai_provider": "openrouter",
                "openrouter_model": "openrouter/free",
                "gfn_gaming_volume": 85,
            },
            "pro": {
                "ai_provider": "openrouter",
                "openrouter_model": "deepseek/deepseek-r1",
            },
            "noche": {
                "gfn_gaming_volume": 30,
            },
        }

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "overrides": self.overrides,
                "presets": self.presets,
                "active_preset": self.active_preset,
            }
            self._atomic_write(self._path, data)
        except Exception as exc:
            log.warning("Error guardando overrides: %s", exc)

    @staticmethod
    def _atomic_write(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, indent=2, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and temporary.exists():
                temporary.unlink(missing_ok=True)
