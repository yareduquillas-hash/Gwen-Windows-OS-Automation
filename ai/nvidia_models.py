"""Registry autoconfigurable de modelos NVIDIA NIM.

Consulta la API de NVIDIA una vez, cachea el resultado 24h y valida
cualquier modelo contra la lista real. Si NVIDIA añade o elimina modelos,
este módulo se adapta solo sin tocar código.

Uso:
    from ai.nvidia_models import modelos_nvidia, es_modelo_valido, modelo_fallback
"""
from __future__ import annotations

import json
import logging
import os
import time as _time
import urllib.request
from pathlib import Path

log = logging.getLogger("jarvis.ai.nvidia")

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/models"
CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Modelos preferidos de Gwen en orden de prioridad de fallback
# (todos verificados como existentes en NVIDIA NIM el 2026-08-05)
PREFERIDOS = (
    "deepseek-ai/deepseek-v4-flash",
    "deepseek-ai/deepseek-v4-pro",
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "google/gemma-4-31b-it",
)

_cache_path: Path | None = None
_cache: dict | None = None


def _cache_file(cfg=None) -> Path:
    global _cache_path
    if _cache_path is None:
        data_dir = getattr(cfg, "data_dir", None)
        if data_dir is None:
            data_dir = Path(os.getenv("JARVIS_DATA_DIR", "data"))
        _cache_path = Path(data_dir) / "cache" / "nvidia_models.json"
    return _cache_path


def _leer_cache(cfg=None) -> dict | None:
    global _cache
    if _cache is not None:
        return _cache
    path = _cache_file(cfg)
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            # Cache válido por 24 horas
            if _time.time() - data.get("fetched_at", 0) < 86400:
                _cache = data
                return _cache
    except Exception as exc:
        log.debug("Cache NVIDIA corrupto: %s", exc)
    return None


def _guardar_cache(data: dict, cfg=None) -> None:
    global _cache
    data["fetched_at"] = _time.time()
    path = _cache_file(cfg)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        _cache = data
    except Exception as exc:
        log.warning("No se pudo guardar cache NVIDIA: %s", exc)


def _api_key(cfg=None) -> str:
    if cfg is not None:
        key = getattr(cfg, "nvidia_api_key", "") or ""
        if key:
            return key
    from utils.secrets import get_secret
    key = get_secret("NVIDIA_API_KEY")
    if key:
        return key
    # Fallback: cargar .env del proyecto (modo standalone)
    try:
        from dotenv import load_dotenv
        proyecto = Path(__file__).resolve().parent.parent
        load_dotenv(proyecto / ".env")
        key = get_secret("NVIDIA_API_KEY")
    except Exception:
        pass
    return key


def _consultar_api(cfg=None, timeout: int = 15) -> dict:
    """Consulta la API de NVIDIA y devuelve {model_id: True}."""
    key = _api_key(cfg)
    if not key:
        log.warning("NVIDIA_API_KEY no configurada. No se puede validar modelos.")
        return {}
    try:
        req = urllib.request.Request(
            NVIDIA_API_URL,
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ids = {m.get("id") for m in data.get("data", []) if m.get("id")}
        return {mid: True for mid in ids}
    except urllib.error.HTTPError as exc:
        log.warning("NVIDIA API HTTP %s: %s (¿key inválida?)", exc.code, exc.reason)
        return {}
    except Exception as exc:
        log.warning("No se pudo consultar modelos NVIDIA: %s", exc)
        return {}


def modelos_nvidia(cfg=None, refresh: bool = False) -> dict:
    """Devuelve dict {model_id: True} de modelos disponibles en NVIDIA."""
    if refresh:
        return _consultar_api(cfg)
    data = _leer_cache(cfg)
    if data and data.get("models"):
        return data["models"]
    models = _consultar_api(cfg)
    if models:
        _guardar_cache({"models": models}, cfg)
    return models


def es_modelo_valido(model_id: str, cfg=None) -> bool:
    """¿Existe este modelo en NVIDIA NIM?"""
    if not model_id:
        return False
    models = modelos_nvidia(cfg)
    return model_id in models


def modelo_fallback(modelo_pedido: str, cfg=None) -> str:
    """Devuelve un modelo válido partiendo del pedido; si no existe, el más cercano."""
    models = modelos_nvidia(cfg)

    # API caída o sin respuesta: nunca devolver un modelo no verificado.
    # La lista PREFERIDOS está verificada manualmente (2026-08-05).
    if not models:
        log.warning("API NVIDIA sin respuesta. Usando lista verificada manualmente.")
        return modelo_pedido if modelo_pedido in PREFERIDOS else PREFERIDOS[0]

    if modelo_pedido and modelo_pedido in models:
        return modelo_pedido
    # Buscar el preferido más cercano disponible
    for pref in PREFERIDOS:
        if pref in models:
            log.info("Modelo %s no disponible. Usando %s", modelo_pedido, pref)
            return pref
    # Último recurso: cualquier modelo de chat disponible
    for mid in models:
        if "instruct" in mid or "chat" in mid or "flash" in mid or "pro" in mid:
            log.info("Fallback genérico a %s", mid)
            return mid
    return modelo_pedido or "deepseek-ai/deepseek-v4-flash"


def modelos_validos_para_fallback(cfg=None) -> list[str]:
    """Lista de modelos NVIDIA verificados, en orden de prioridad."""
    models = modelos_nvidia(cfg)
    if not models:
        # Sin API disponible → usar preferidos conocidos (verificados manualmente)
        return list(PREFERIDOS)
    ordenados = [m for m in PREFERIDOS if m in models]
    extras = [m for m in models if "instruct" in m or "chat" in m]
    extras.sort()
    for e in extras:
        if e not in ordenados:
            ordenados.append(e)
    return ordenados


def validar_todo(cfg=None, refresh: bool = False) -> dict:
    """Devuelve informe {pedido: {existe, alternativas}} para debug."""
    models = modelos_nvidia(cfg, refresh=refresh)
    informe = {}
    for pid in PREFERIDOS + ("deepseek-ai/deepseek-v3", "deepseek-ai/deepseek-r1"):
        informe[pid] = {
            "existe": pid in models,
            "alternativa": modelo_fallback(pid, cfg) if pid not in models else None,
        }
    return informe
