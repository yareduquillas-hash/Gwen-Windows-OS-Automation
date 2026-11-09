from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from utils.secrets import get_secret

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent


def _env_bool(key: str, default: bool = True) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("1", "true", "yes", "on")


def _env_path(key: str, default: str) -> Path:
    raw = os.getenv(key, default)
    p = Path(raw)
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return p.resolve()


def _env_storage_path(key: str, default: str) -> Path:
    raw = os.path.expandvars(os.getenv(key, default))
    p = Path(raw)
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return p.resolve()


def _env_expand(key: str, default: str) -> str:
    return os.path.expandvars(os.getenv(key, default))


def _parse_region(raw: str) -> tuple[int, int, int, int] | None:
    if not raw or not raw.strip():
        return None
    parts = raw.strip().split(",")
    if len(parts) == 4:
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            return None
    return None


@dataclass
class JarvisConfig:
    project_root: Path = field(default=_PROJECT_ROOT, init=False)

    # ── API Server (App Android) ──
    api_port: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_API_PORT", "8000"))
    )
    api_key: str = field(
        default_factory=lambda: get_secret("JARVIS_API_KEY")
    )
    api_host: str = field(
        default_factory=lambda: os.getenv("JARVIS_API_HOST", "127.0.0.1")
    )
    api_ssl_keyfile: str = field(
        default_factory=lambda: _env_expand("JARVIS_API_SSL_KEYFILE", "")
    )
    api_ssl_certfile: str = field(
        default_factory=lambda: _env_expand("JARVIS_API_SSL_CERTFILE", "")
    )

    # ── Telegram (obligatorio) ──
    telegram_token: str = field(
        default_factory=lambda: get_secret("JARVIS_TELEGRAM_TOKEN")
    )
    telegram_chat_id: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_TELEGRAM_CHAT_ID", "0"))
    )

    # ── Personalización ──
    user_name: str = field(
        default_factory=lambda: os.getenv("JARVIS_USER_NAME", "Usuario")
    )
    user_title: str = field(
        default_factory=lambda: os.getenv("JARVIS_USER_TITLE", "Señor")
    )
    lang: str = field(
        default_factory=lambda: os.getenv("JARVIS_LANG", "es-ES")
    )
    tts_voice: str = field(
        default_factory=lambda: os.getenv("JARVIS_TTS_VOICE", "es-ES-AlvaroNeural")
    )

    # ── IA / Proveedores ──
    ai_provider: str = field(
        default_factory=lambda: os.getenv("JARVIS_AI_PROVIDER", "nvidia")
    )
    nvidia_api_key: str = field(
        default_factory=lambda: get_secret("NVIDIA_API_KEY")
    )
    nvidia_model: str = field(
        default_factory=lambda: os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash")
    )
    siliconflow_api_key: str = field(
        default_factory=lambda: get_secret("SILICONFLOW_API_KEY")
    )
    siliconflow_model: str = field(
        default_factory=lambda: os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    )
    openrouter_api_key: str = field(
        default_factory=lambda: get_secret("OPENROUTER_API_KEY")
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731")
    )
    groq_api_key: str = field(
        default_factory=lambda: get_secret("GROQ_API_KEY")
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )
    model_base: str = field(
        default_factory=lambda: os.getenv(
            "OPENCODE_MODEL_BASE", "opencode-go/deepseek-v4-flash"
        )
    )
    model_g: str = field(
        default_factory=lambda: os.getenv(
            "OPENCODE_MODEL_G", "opencode-go/deepseek-v4-pro"
        )
    )
    model_m: str = field(
        default_factory=lambda: os.getenv(
            "OPENCODE_MODEL_M", "opencode-go/qwen3.7-max"
        )
    )
    opencode_timeout: int = field(
        default_factory=lambda: int(os.getenv("OPENCODE_TIMEOUT", "300"))
    )
    opencode_bin: str = field(
        default_factory=lambda: _env_expand(
            "OPENCODE_BIN",
            r"%APPDATA%\npm\node_modules\opencode-ai\node_modules\opencode-windows-x64\bin\opencode.exe",
        )
    )

    # ── Spotify (opcional) ──
    spotify_client_id: str = field(
        default_factory=lambda: os.getenv("SPOTIFY_CLIENT_ID", "")
    )
    spotify_client_secret: str = field(
        default_factory=lambda: get_secret("SPOTIFY_CLIENT_SECRET")
    )
    spotify_redirect_uri: str = field(
        default_factory=lambda: os.getenv(
            "SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"
        )
    )

    # ── Voz / STT (opcional) ──
    stt_google_api_key: str = field(
        default_factory=lambda: get_secret("STT_GOOGLE_API_KEY")
    )

    # ── GeForce NOW (opcional) ──
    gfn_executable: str = field(
        default_factory=lambda: _env_expand(
            "GFN_EXECUTABLE",
            "%LOCALAPPDATA%\\NVIDIA Corporation\\GeForceNOW\\CEF\\GeForceNOW.exe",
        )
    )
    gfn_gaming_volume: int = field(
        default_factory=lambda: int(os.getenv("GFN_GAMING_VOLUME", "75"))
    )
    gfn_queue_timeout_minutes: int = field(
        default_factory=lambda: int(os.getenv("GFN_QUEUE_TIMEOUT_MINUTES", "20"))
    )
    gfn_queue_poll_interval: int = field(
        default_factory=lambda: int(os.getenv("GFN_QUEUE_POLL_INTERVAL", "15"))
    )
    gfn_action_delay: int = field(
        default_factory=lambda: int(os.getenv("GFN_ACTION_DELAY", "6"))
    )
    gfn_quick_games: list[str] = field(
        default_factory=lambda: [
            g.strip()
            for g in os.getenv(
                "GFN_QUICK_GAMES",
                "Fortnite,Apex Legends,Cyberpunk 2077,Destiny 2",
            ).split(",")
            if g.strip()
        ]
    )
    # DEPRECADO: legado del motor OCR v2. Sin uso desde gfn v3.
    gfn_queue_region: tuple[int, int, int, int] | None = field(
        default_factory=lambda: _parse_region(os.getenv("GFN_QUEUE_REGION", ""))
    )

    # ── Rutas ──
    data_dir: Path = field(
        default_factory=lambda: _env_path("JARVIS_DATA_DIR", "data")
    )
    descargas_dir: Path = field(
        default_factory=lambda: _env_path("JARVIS_DESCARGAS_DIR", "data/descargas")
    )
    archivos_dir: Path = field(
        default_factory=lambda: _env_path("JARVIS_ARCHIVOS_DIR", "data/archivos")
    )
    cache_dir: Path = field(
        default_factory=lambda: _env_path("JARVIS_CACHE_DIR", "data/cache")
    )
    log_dir: Path = field(
        default_factory=lambda: _env_storage_path(
            "JARVIS_LOG_DIR",
            r"%APPDATA%\GwenWindowsPro\logs",
        )
    )
    settings_dir: Path = field(
        default_factory=lambda: _env_storage_path(
            "JARVIS_SETTINGS_DIR",
            r"%APPDATA%\GwenWindowsPro\settings",
        )
    )
    google_credentials_file: Path = field(
        default_factory=lambda: _env_storage_path(
            "GOOGLE_CREDENTIALS_FILE",
            r"%APPDATA%\GwenWindowsPro\credentials.json",
        )
    )
    google_token_file: Path = field(
        default_factory=lambda: _env_storage_path(
            "GOOGLE_TOKEN_FILE",
            r"%APPDATA%\GwenWindowsPro\google_token.json",
        )
    )

    # ── Módulos habilitados ──
    modules_enabled: dict[str, bool] = field(
        default_factory=lambda: {
            "bateria": _env_bool("MODULE_BATERIA"),
            "medios": _env_bool("MODULE_MEDIOS"),
            "volumen": _env_bool("MODULE_VOLUMEN"),
            "portapapeles": _env_bool("MODULE_CLIPBOARD"),
            "archivos": _env_bool("MODULE_ARCHIVOS"),
            "descargas": _env_bool("MODULE_DESCARGAS"),
            "memoria": _env_bool("MODULE_MEMORIA"),
            "secciones": _env_bool("MODULE_SECCIONES"),
            "tareas": _env_bool("MODULE_TAREAS"),
            "protocolos": _env_bool("MODULE_PROTOCOLOS"),
            "voz": _env_bool("MODULE_VOZ"),
            "capturas": _env_bool("MODULE_CAPTURAS"),
            "ventanas": _env_bool("MODULE_VENTANAS"),
            "procesos": _env_bool("MODULE_PROCESOS"),
            "sistema_info": _env_bool("MODULE_SISTEMA_INFO"),
            "notificaciones": _env_bool("MODULE_NOTIFICACIONES"),
            "wizard": _env_bool("MODULE_WIZARD", True),
            "sistema": _env_bool("MODULE_SISTEMA", True),
            "reconfig": _env_bool("MODULE_RECONFIG", True),
            "conversacion": _env_bool("MODULE_CONVERSACION", True),
            "geforcenow": _env_bool("MODULE_GEFORCENOW"),
        }
    )

    # ── Comportamiento ──
    rate_limit_max_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_MAX_PER_MINUTE", "10"))
    )
    message_max_age_seconds: int = field(
        default_factory=lambda: int(os.getenv("MESSAGE_MAX_AGE_SECONDS", "15"))
    )
    context_max_chars: int = field(
        default_factory=lambda: int(os.getenv("CONTEXT_MAX_CHARS", "2000"))
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    timezone: str = field(
        default_factory=lambda: os.getenv("TIMEZONE", "America/Mexico_City")
    )

    @property
    def full_name(self) -> str:
        return f"{self.user_title} {self.user_name}"

    @property
    def db_path(self) -> Path:
        return _env_storage_path(
            "JARVIS_DB_PATH",
            r"%APPDATA%\GwenWindowsPro\jarvis_memoria.db",
        )

    @property
    def tts_cache_dir(self) -> Path:
        return self.cache_dir / "tts"

    @property
    def assets_dir(self) -> Path:
        return self.data_dir / "assets"

    def is_module_enabled(self, name: str) -> bool:
        return self.modules_enabled.get(name, False)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.ai_provider not in {"nvidia", "siliconflow", "openrouter", "groq"}:
            errors.append("JARVIS_AI_PROVIDER no esta soportado")
        if not self.telegram_token or self.telegram_token.startswith("pon_tu_"):
            errors.append("JARVIS_TELEGRAM_TOKEN no configurado en .env")
        if self.telegram_chat_id == 0:
            errors.append("JARVIS_TELEGRAM_CHAT_ID no configurado en .env")
        if not isinstance(self.telegram_chat_id, int) or self.telegram_chat_id <= 0:
            errors.append("JARVIS_TELEGRAM_CHAT_ID debe ser un número válido")
        if not isinstance(self.opencode_timeout, int) or self.opencode_timeout <= 0:
            errors.append("OPENCODE_TIMEOUT debe ser un número positivo")
        if self.gfn_gaming_volume not in range(0, 101):
            errors.append("GFN_GAMING_VOLUME debe estar entre 0 y 100")
        if self.rate_limit_max_per_minute < 0:
            errors.append("RATE_LIMIT_MAX_PER_MINUTE no puede ser negativo")
        if bool(self.api_ssl_keyfile) != bool(self.api_ssl_certfile):
            errors.append("JARVIS_API_SSL_KEYFILE y JARVIS_API_SSL_CERTFILE deben configurarse juntos")
        if self.api_ssl_keyfile and not Path(self.api_ssl_keyfile).is_file():
            errors.append("JARVIS_API_SSL_KEYFILE no existe")
        if self.api_ssl_certfile and not Path(self.api_ssl_certfile).is_file():
            errors.append("JARVIS_API_SSL_CERTFILE no existe")
        if self.api_host not in {"127.0.0.1", "localhost", "::1"} and not (
            self.api_ssl_keyfile and self.api_ssl_certfile
        ):
            errors.append("La API remota requiere TLS configurado")
        if self.ai_provider == "openrouter" and (not self.openrouter_api_key or self.openrouter_api_key.startswith("pon_tu_")):
            errors.append("OPENROUTER_API_KEY no configurado en Credential Manager o .env (ai_provider=openrouter)")
        if self.ai_provider == "groq" and (not self.groq_api_key or self.groq_api_key.startswith("pon_tu_")):
            errors.append("GROQ_API_KEY no configurado en Credential Manager o .env (ai_provider=groq)")
        if self.ai_provider == "nvidia" and (not self.nvidia_api_key or self.nvidia_api_key.startswith("pon_tu_")):
            errors.append("NVIDIA_API_KEY no configurado en Credential Manager o .env (ai_provider=nvidia)")
        if self.ai_provider == "siliconflow" and (not self.siliconflow_api_key or self.siliconflow_api_key.startswith("pon_tu_")):
            errors.append("SILICONFLOW_API_KEY no configurado en Credential Manager o .env (ai_provider=siliconflow)")
        return errors

    def validated(self) -> "JarvisConfig":
        errors = self.validate()
        if errors:
            header = "❌ Errores de configuración en .env:\n"
            raise ValueError(header + "\n".join(f"  • {e}" for e in errors))
        return self

    def ensure_dirs(self) -> None:
        for d in (
            self.data_dir,
            self.descargas_dir,
            self.archivos_dir,
            self.cache_dir,
            self.tts_cache_dir,
            self.assets_dir,
            self.log_dir,
            self.settings_dir,
            self.db_path.parent,
        ):
            d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════
# HotConfig — Overrides en caliente sin tocar .env
# ═══════════════════════════════════════════════════════

class HotConfig:
    def __init__(self, base: JarvisConfig):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_manager", None)
        self._ensure_manager()
        object.__setattr__(self, "_overrides", dict(self._manager.overrides))
        object.__setattr__(self, "_active_preset", self._manager.active_preset)

    def _ensure_manager(self):
        if object.__getattribute__(self, "_manager") is None:
            from utils.config_manager import ConfigManager
            mgr = ConfigManager(self._base)
            object.__setattr__(self, "_manager", mgr)

    def __getattr__(self, name: str):
        _ov = object.__getattribute__(self, "_overrides")
        if name in _ov:
            return _ov[name]
        return getattr(object.__getattribute__(self, "_base"), name)

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        _base = object.__getattribute__(self, "_base")
        if hasattr(_base, name):
            setattr(_base, name, value)
            self.override(name, value)
        else:
            self.override(name, value)

    def override(self, key: str, value) -> None:
        self._manager.override(key, value)
        object.__setattr__(self, "_overrides", dict(self._manager.overrides))
        object.__setattr__(self, "_active_preset", self._manager.active_preset)

    def reset(self, key: str | None = None) -> None:
        self._manager.reset(key)
        object.__setattr__(self, "_overrides", dict(self._manager.overrides))
        object.__setattr__(self, "_active_preset", self._manager.active_preset)

    def list_overrides(self) -> dict:
        return dict(self._overrides)

    @property
    def active_preset(self) -> str | None:
        return object.__getattribute__(self, "_active_preset")

    @property
    def full_name(self) -> str:
        return f"{self.user_title} {self.user_name}"

    def is_module_enabled(self, name: str) -> bool:
        overrides = object.__getattribute__(self, "_overrides")
        override_key = f"module_{name}"
        if override_key in overrides:
            return bool(overrides[override_key])
        return object.__getattribute__(self, "_base").is_module_enabled(name)

    @property
    def wizard_completed(self) -> bool:
        return object.__getattribute__(self, "_overrides").get("_wizard_completed", False)

    def mark_wizard_completed(self) -> None:
        self._manager.override("_wizard_completed", True)
        object.__setattr__(self, "_overrides", dict(self._manager.overrides))

    def apply_preset(self, name: str) -> bool:
        ok = self._manager.apply_preset(name)
        if ok:
            object.__setattr__(self, "_overrides", dict(self._manager.overrides))
            object.__setattr__(self, "_active_preset", self._manager.active_preset)
        return ok

    def save_preset(self, name: str, settings: dict) -> None:
        self._manager.save_preset(name, settings)

    def restore_backup(self) -> bool:
        ok = self._manager.restore_backup()
        if ok:
            object.__setattr__(self, "_overrides", dict(self._manager.overrides))
            object.__setattr__(self, "_active_preset", self._manager.active_preset)
        return ok

    def list_presets(self) -> dict:
        return dict(self._manager.presets)
