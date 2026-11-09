from __future__ import annotations

import asyncio
import base64
import hmac
import io
import logging
import os
import secrets
import time
from collections import defaultdict, deque
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

log = logging.getLogger("jarvis.api")

app = FastAPI(title="Gwen / Jarvis API Engine", version="3.0")


def _cors_origins() -> list[str]:
    configured = os.getenv(
        "JARVIS_API_CORS_ORIGINS",
        "http://localhost,capacitor://localhost",
    )
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        log.warning("JARVIS_API_CORS_ORIGINS no puede usar wildcard; CORS queda cerrado")
        return []
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

_API_RATE_LIMIT = 60
_API_RATE_WINDOW_SECONDS = 60
_api_requests: defaultdict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def api_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _api_requests[client]
        while window and now - window[0] >= _API_RATE_WINDOW_SECONDS:
            window.popleft()
        if len(window) >= _API_RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes"},
                headers={"Retry-After": "60"},
            )
        window.append(now)
    return await call_next(request)

security = HTTPBearer(auto_error=False)


class VolumeBody(BaseModel):
    level: int = Field(default=50, ge=0, le=100)


class MediaBody(BaseModel):
    key: str = Field(default="play", min_length=1, max_length=20)


class ModelBody(BaseModel):
    alias: str = Field(min_length=1, max_length=40)


class ConfigPatchBody(BaseModel):
    key: str = Field(min_length=1, max_length=40)
    value: Any


class GFNProfileBody(BaseModel):
    id: str | None = None
    game_name: str = Field(min_length=1, max_length=100)
    profile_name: str = Field(min_length=1, max_length=100)
    account_email: str = Field(min_length=1, max_length=150)
    password: str | None = Field(default=None, max_length=200)
    template_image: str | None = None
    click_coords: list[int] | None = None
    key_sequence: str = Field(default="EMAIL,TAB,PASSWORD,ENTER", max_length=100)


ALLOWED_CONFIG_KEYS = {
    "user_name",
    "user_title",
    "ai_provider",
    "nvidia_model",
    "siliconflow_model",
    "openrouter_model",
    "groq_model",
    "gfn_gaming_volume",
    "gfn_queue_timeout_minutes",
    "opencode_timeout",
}
ALLOWED_MEDIA_KEYS = {"play", "pause", "next", "prev", "stop", "previous"}


def _redact_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    sensitive_words = ("key", "token", "secret", "password", "credential")
    return {
        key: "[redacted]"
        if any(word in key.lower() for word in sensitive_words)
        else value
        for key, value in overrides.items()
    }

_bot_instance = None
_cfg_instance = None
_input_router = None


def set_bot_context(bot_obj, cfg_obj) -> None:
    global _bot_instance, _cfg_instance, _input_router
    from adapters import InputRouter

    _bot_instance = bot_obj
    _cfg_instance = cfg_obj
    _input_router = InputRouter(bot_obj.registry, cfg_obj)


def _configured_api_token() -> str:
    token = ""
    if _cfg_instance and hasattr(_cfg_instance, "api_key") and _cfg_instance.api_key:
        token = _cfg_instance.api_key
    if not token or token.startswith("pon_tu_"):
        try:
            from utils.secrets import SecretStore
            store = SecretStore()
            token = store.get("JARVIS_API_KEY")
        except Exception:
            pass
    if not token or token.startswith("pon_tu_"):
        token = os.getenv("JARVIS_API_KEY", "")

    if not token or token.startswith("pon_tu_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JARVIS_API_KEY no configurada en Credential Manager o .env",
        )

    if len(token) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JARVIS_API_KEY debe tener al menos 32 caracteres",
        )
    return token


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> bool:
    expected_token = _configured_api_token()

    if not credentials or not hmac.compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API inválido o no proporcionado",
        )
    return True


# ── REST ENDPOINTS ──


@app.get("/api/v1/ping")
async def ping():
    return {"status": "ok", "ts": time.time(), "service": "Gwen/Jarvis API"}


@app.get("/api/v1/system", dependencies=[Depends(verify_token)])
async def system_info():
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_adapter().get_system_info)


@app.get("/api/v1/battery", dependencies=[Depends(verify_token)])
async def battery():
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_adapter().get_battery)


@app.get("/api/v1/processes", dependencies=[Depends(verify_token)])
async def processes(limit: int = Query(default=20, ge=1, le=100)):
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    procs = await loop.run_in_executor(
        None, lambda: get_adapter().get_running_processes(limit)
    )
    return {"processes": procs}


@app.get("/api/v1/windows", dependencies=[Depends(verify_token)])
async def windows():
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    wins = await loop.run_in_executor(None, get_adapter().get_windows)
    return {"windows": wins}


@app.get("/api/v1/volume", dependencies=[Depends(verify_token)])
async def get_volume():
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    vol = await loop.run_in_executor(None, get_adapter().get_volume)
    return {"volume": vol}


@app.post("/api/v1/volume", dependencies=[Depends(verify_token)])
async def set_volume(body: VolumeBody):
    from plat_adapter import get_adapter

    level = body.level
    loop = asyncio.get_running_loop()
    ok = await loop.run_in_executor(None, lambda: get_adapter().set_volume(level))
    if not ok:
        raise HTTPException(status_code=503, detail="Control de volumen no disponible")
    return {"ok": True, "volume": level}


@app.post("/api/v1/media", dependencies=[Depends(verify_token)])
async def media_key(body: MediaBody):
    from plat_adapter import get_adapter

    key = body.key.lower()
    if key not in ALLOWED_MEDIA_KEYS:
        raise HTTPException(status_code=400, detail="Tecla multimedia no permitida")
    loop = asyncio.get_running_loop()
    ok = await loop.run_in_executor(None, lambda: get_adapter().send_media_key(key))
    if not ok:
        raise HTTPException(status_code=503, detail="Control multimedia no disponible")
    return {"ok": True, "executed": key}


@app.get("/api/v1/screenshot", dependencies=[Depends(verify_token)])
async def screenshot():
    from plat_adapter import get_adapter

    loop = asyncio.get_running_loop()
    img_bytes = await loop.run_in_executor(None, get_adapter().take_screenshot)
    if not img_bytes:
        raise HTTPException(status_code=500, detail="Error capturando pantalla")
    return Response(content=img_bytes, media_type="image/png")


# ── GFN Auto-Login & Profile Management ──

@app.get("/gfn", response_class=FileResponse)
async def gfn_web_ui():
    from pathlib import Path
    ui_path = Path(__file__).resolve().parent / "data" / "web" / "gfn" / "index.html"
    if not ui_path.is_file():
        raise HTTPException(status_code=404, detail="Interfaz web GFN no encontrada")
    return FileResponse(ui_path)


@app.get("/api/v1/gfn/profiles", dependencies=[Depends(verify_token)])
async def list_gfn_profiles(game: str | None = None):
    from utils.gfn_profiles import GFNProfileManager
    mgr = GFNProfileManager()
    profs = mgr.list_profiles(game)
    return {"profiles": [p.to_public_dict() for p in profs]}


@app.post("/api/v1/gfn/profiles", dependencies=[Depends(verify_token)])
async def save_gfn_profile(body: GFNProfileBody):
    from utils.gfn_profiles import GFNProfileManager
    mgr = GFNProfileManager()
    coords = tuple(body.click_coords) if body.click_coords and len(body.click_coords) == 2 else None
    prof = mgr.create_or_update_profile(
        game_name=body.game_name,
        profile_name=body.profile_name,
        account_email=body.account_email,
        password_plain=body.password,
        template_image=body.template_image,
        click_coords=coords,
        key_sequence=body.key_sequence,
        profile_id=body.id,
    )
    return {"ok": True, "profile": prof.to_public_dict()}


@app.delete("/api/v1/gfn/profiles/{profile_id}", dependencies=[Depends(verify_token)])
async def delete_gfn_profile(profile_id: str):
    from utils.gfn_profiles import GFNProfileManager
    mgr = GFNProfileManager()
    ok = mgr.delete_profile(profile_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return {"ok": True, "deleted_id": profile_id}


@app.post("/api/v1/gfn/profiles/{profile_id}/capture-template", dependencies=[Depends(verify_token)])
async def capture_profile_template(profile_id: str):
    from utils.gfn_profiles import GFNProfileManager
    mgr = GFNProfileManager()
    prof = mgr.get_profile(profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    try:
        import pyautogui
        template_file = mgr.templates_dir / f"template_{profile_id}.png"
        img = pyautogui.screenshot()
        img.save(template_file, format="PNG")

        updated = mgr.create_or_update_profile(
            game_name=prof.game_name,
            profile_name=prof.profile_name,
            account_email=prof.account_email,
            template_image=str(template_file),
            click_coords=prof.click_coords,
            key_sequence=prof.key_sequence,
            profile_id=profile_id,
        )
        return {"ok": True, "profile": updated.to_public_dict(), "template_path": str(template_file)}
    except Exception as exc:
        log.error("Error capturando plantilla visual: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error capturando plantilla: {exc}")


@app.get("/api/v1/models", dependencies=[Depends(verify_token)])
async def list_models():
    from ai.models import MODELOS

    active_provider = _cfg_instance.ai_provider if _cfg_instance else "openrouter"
    model_by_provider = {
        "nvidia": "nvidia_model",
        "siliconflow": "siliconflow_model",
        "openrouter": "openrouter_model",
        "groq": "groq_model",
        "opencode": "model_base",
    }
    active_model = getattr(
        _cfg_instance,
        model_by_provider.get(active_provider, "model_base"),
        "",
    )
    return {
        "active_provider": active_provider,
        "active_model": active_model,
        "models": {
            k: {"provider": v[0], "model_id": v[1], "description": v[2]}
            for k, v in MODELOS.items()
        },
    }


@app.post("/api/v1/model", dependencies=[Depends(verify_token)])
async def switch_model(body: ModelBody):
    from ai.models import MODELOS

    alias = body.alias.lower().strip()
    if alias not in MODELOS:
        raise HTTPException(
            status_code=400, detail=f"Modelo '{alias}' no reconocido"
        )
    prov, mod, desc = MODELOS[alias]
    if _cfg_instance:
        _cfg_instance.override("ai_provider", prov)
        model_key = {
            "nvidia": "nvidia_model",
            "siliconflow": "siliconflow_model",
            "openrouter": "openrouter_model",
            "groq": "groq_model",
            "opencode": "model_base",
        }.get(prov)
        if model_key:
            _cfg_instance.override(model_key, mod)
    return {"ok": True, "provider": prov, "model": mod, "description": desc}


@app.get("/api/v1/config", dependencies=[Depends(verify_token)])
async def get_config():
    if not _cfg_instance:
        return {}
    overrides = (
        _cfg_instance.list_overrides()
        if hasattr(_cfg_instance, "list_overrides")
        else {}
    )
    return {
        "user_name": getattr(_cfg_instance, "user_name", ""),
        "user_title": getattr(_cfg_instance, "user_title", ""),
        "ai_provider": getattr(_cfg_instance, "ai_provider", ""),
        "overrides": _redact_overrides(overrides),
        "preset": getattr(_cfg_instance, "active_preset", None),
    }


@app.patch("/api/v1/config", dependencies=[Depends(verify_token)])
async def patch_config(body: ConfigPatchBody):
    if not _cfg_instance:
        raise HTTPException(status_code=500, detail="Configuración no disponible")
    key = body.key
    val = body.value
    if key not in ALLOWED_CONFIG_KEYS:
        if not key.startswith("module_") or key[7:].lower() not in getattr(_cfg_instance, "modules_enabled", {}):
            raise HTTPException(status_code=400, detail="Clave de configuracion no permitida")

        if not isinstance(val, bool):
            raise HTTPException(status_code=422, detail="El estado del modulo debe ser booleano")
        _cfg_instance.override(key, val)
        if _bot_instance and hasattr(_bot_instance, "registry"):
            _bot_instance.registry.set_module_enabled(key[7:], val)
        return {"ok": True, "key": key, "value": val}

    if key in {"user_name", "user_title"}:
        if not isinstance(val, str) or not val.strip() or len(val.strip()) > 40:
            raise HTTPException(status_code=422, detail="Texto de usuario invalido")
    elif key == "ai_provider":
        if val not in {"nvidia", "siliconflow", "openrouter", "groq"}:
            raise HTTPException(status_code=422, detail="Proveedor no permitido")
    elif key.endswith("_model"):
        if not isinstance(val, str) or not val.strip() or len(val) > 200:
            raise HTTPException(status_code=422, detail="Modelo invalido")
    else:
        if not isinstance(val, int):
            raise HTTPException(status_code=422, detail="El valor debe ser entero")
        ranges = {
            "gfn_gaming_volume": (0, 100),
            "gfn_queue_timeout_minutes": (1, 240),
            "opencode_timeout": (1, 900),
        }
        low, high = ranges[key]
        if not low <= val <= high:
            raise HTTPException(status_code=422, detail="Valor fuera de rango")

    _cfg_instance.override(key, val)
    return {"ok": True, "key": key, "value": val}


@app.get("/api/v1/modules", dependencies=[Depends(verify_token)])
async def list_modules():
    if not _cfg_instance:
        return {"modules": {}}
    if _bot_instance and hasattr(_bot_instance, "registry"):
        return {"modules": _bot_instance.registry.module_status()}
    return {"modules": getattr(_cfg_instance, "modules_enabled", {})}


# ── WEBSOCKET ENTRANCE ──


class DummyBotSender:
    def __init__(self, websocket: WebSocket, loop: asyncio.AbstractEventLoop, chat_id: int):
        self.websocket = websocket
        self.loop = loop
        self.chat_id = chat_id

    @staticmethod
    async def _safe_send(websocket: WebSocket, payload: dict) -> None:
        try:
            await websocket.send_json(payload)
        except Exception as exc:
            log.warning("Error enviando por WebSocket: %s", exc)

    def _schedule_send(self, payload: dict) -> None:
        """Devuelve una respuesta al loop async desde un worker sincronico."""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._safe_send(self.websocket, payload), self.loop
            )
            future.add_done_callback(self._log_future_error)
        except RuntimeError as exc:
            log.warning("No se pudo programar respuesta WebSocket: %s", exc)

    @staticmethod
    def _log_future_error(future) -> None:
        try:
            future.result()
        except Exception as exc:
            log.warning("Error en respuesta WebSocket: %s", exc)

    def reply_to(self, message, text):
        self._schedule_send(
            {"type": "response", "text": text, "ts": time.time()}
        )

    def send_message(self, chat_id, text):
        self._schedule_send(
            {"type": "response", "text": text, "ts": time.time()}
        )

    def send_photo(self, chat_id, photo_stream):
        if hasattr(photo_stream, "getvalue"):
            b64_img = base64.b64encode(photo_stream.getvalue()).decode("utf-8")
        else:
            b64_img = base64.b64encode(photo_stream.read()).decode("utf-8")
        self._schedule_send(
            {
                "type": "image",
                "data": b64_img,
                "media_type": "image/png",
                "ts": time.time(),
            }
        )


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    try:
        expected_token = _configured_api_token()
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    provided_token = websocket.headers.get("authorization", "")
    if provided_token.lower().startswith("bearer "):
        provided_token = provided_token[7:].strip()
    if (
        not hmac.compare_digest(provided_token, expected_token)
    ):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    log.info("App Android conectada mediante WebSocket")

    loop = asyncio.get_running_loop()
    connection_user_id = -(secrets.randbelow(2_000_000_000) + 1)
    dummy_sender = DummyBotSender(websocket, loop, connection_user_id)
    message_times: deque[float] = deque()

    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                await websocket.send_json({"type": "error", "text": "Payload invalido."})
                continue
            msg_type = data.get("type", "message")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": time.time()})
                continue

            if msg_type == "message":
                raw_text = data.get("text", "")
                if not isinstance(raw_text, str):
                    await websocket.send_json({"type": "error", "text": "Texto invalido."})
                    continue
                text = raw_text.strip()
                if not text:
                    continue
                now = time.monotonic()
                while message_times and now - message_times[0] >= 60:
                    message_times.popleft()
                if len(message_times) >= 30:
                    await websocket.send_json(
                        {"type": "error", "text": "Demasiados mensajes. Espere un minuto."}
                    )
                    continue
                message_times.append(now)
                if len(text) > 4000:
                    await websocket.send_json(
                        {"type": "error", "text": "Mensaje demasiado largo."}
                    )
                    continue

                log.info("Mensaje de Android WS recibido")

                if _input_router:
                    from adapters import WebSocketInputAdapter

                    event = WebSocketInputAdapter.from_payload(connection_user_id, data)
                    await loop.run_in_executor(
                        None,
                        _input_router.dispatch,
                        event,
                        dummy_sender,
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "response",
                            "text": f"Gwen respondió: '{text}' (Modo API)",
                            "ts": time.time(),
                        }
                    )
    except WebSocketDisconnect:
        log.info("App Android desconectada de WebSocket")
    except Exception as exc:
        log.error("Error en WebSocket: %s", exc)


def run_api_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    ssl_keyfile: str | None = None,
    ssl_certfile: str | None = None,
) -> None:
    import uvicorn

    if bool(ssl_keyfile) != bool(ssl_certfile):
        raise ValueError("TLS requiere JARVIS_API_SSL_KEYFILE y JARVIS_API_SSL_CERTFILE")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
