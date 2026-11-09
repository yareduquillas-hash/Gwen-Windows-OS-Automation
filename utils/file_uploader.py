from __future__ import annotations

import logging
import os
import subprocess
import threading
from abc import ABC, abstractmethod
from pathlib import Path

log = logging.getLogger("jarvis.uploader")

TELEGRAM_MAX_MB = 50
BLOCKED_FILE_NAMES = {
    ".env",
    "gwen key.txt",
    "credentials.json",
    "google_token.json",
    "config_override.json",
    "jarvis_memoria.db",
}


# ═══════════════════════════════════════════════════════
# Base
# ═══════════════════════════════════════════════════════

class BaseUploader(ABC):
    @abstractmethod
    def upload(self, path: str, progress_cb=None) -> str | None:
        """Retorna URL pública o None si falla."""

    @abstractmethod
    def is_available(self) -> bool:
        """¿Este backend está configurado y listo?"""


# ═══════════════════════════════════════════════════════
# Google Drive
# ═══════════════════════════════════════════════════════

class GoogleDriveUploader(BaseUploader):
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None
        self._flow = None

    def is_available(self) -> bool:
        return os.path.isfile(self.credentials_path)

    def _get_flow(self):
        if self._flow is None:
            from google_auth_oauthlib.flow import InstalledAppFlow
            self._flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/drive.file"],
            )
            self._flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        return self._flow

    def get_auth_url(self) -> str | None:
        try:
            flow = self._get_flow()
            url, _ = flow.authorization_url(prompt="consent", access_type="offline")
            return url
        except Exception as exc:
            log.warning("Google auth URL error: %s", exc)
            return None

    def authenticate(self, code: str) -> bool:
        try:
            flow = self._get_flow()
            flow.fetch_token(code=code)
            creds = flow.credentials
            token_dir = os.path.dirname(self.token_path)
            if token_dir:
                os.makedirs(token_dir, exist_ok=True)
            with open(self.token_path, "w") as f:
                f.write(creds.to_json())
            self._flow = None
            self._service = None
            return True
        except Exception as exc:
            log.warning("Google auth error: %s", exc)
            self._flow = None
            return False

    def _get_service(self):
        if self._service is not None:
            return self._service
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            if not os.path.isfile(self.token_path):
                return None
            creds = Credentials.from_authorized_user_file(self.token_path)
            self._service = build("drive", "v3", credentials=creds)
            return self._service
        except Exception as exc:
            log.warning("Google service error: %s", exc)
            return None

    def upload(self, path: str, progress_cb=None) -> str | None:
        try:
            from googleapiclient.http import MediaFileUpload
            service = self._get_service()
            if service is None:
                return None

            nombre = os.path.basename(path)
            file_metadata = {"name": nombre}
            media = MediaFileUpload(path, resumable=True)
            uploaded = service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()

            file_id = uploaded.get("id")
            if file_id:
                # El archivo queda privado por defecto. Publicarlo seria una
                # decision de politica y no una consecuencia de subirlo.
                return f"https://drive.google.com/file/d/{file_id}/view"
            return None
        except Exception as exc:
            log.warning("Google upload error: %s", exc)
            return None

    def upload_with_progress(self, path: str, progress_cb) -> str | None:
        import io
        try:
            from googleapiclient.http import MediaIoBaseUpload
            service = self._get_service()
            if service is None:
                return None

            nombre = os.path.basename(path)
            total = os.path.getsize(path)
            uploaded_bytes = [0]

            class _ProgressFile(io.FileIO):
                def read(self, size=-1):
                    chunk = super().read(size)
                    uploaded_bytes[0] += len(chunk)
                    if progress_cb:
                        progress_cb(uploaded_bytes[0], total)
                    return chunk

            media = MediaIoBaseUpload(
                _ProgressFile(path, "rb"), mimetype="application/octet-stream", resumable=True
            )
            file_metadata = {"name": nombre}

            uploaded = service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()

            file_id = uploaded.get("id")
            if file_id:
                return f"https://drive.google.com/file/d/{file_id}/view"
            return None
        except Exception as exc:
            log.warning("Google upload error: %s", exc)
            return None


# ═══════════════════════════════════════════════════════
# transfer.sh
# ═══════════════════════════════════════════════════════

class TransferShUploader(BaseUploader):
    def __init__(self, base_url: str = "https://transfer.sh", max_days: int = 14):
        self.base_url = base_url.rstrip("/")
        self.max_days = max_days

    def is_available(self) -> bool:
        return True

    def upload(self, path: str, progress_cb=None) -> str | None:
        try:
            import requests
            nombre = os.path.basename(path)
            url = f"{self.base_url}/{nombre}"
            total = os.path.getsize(path)
            uploaded_bytes = [0]

            def _progress(monitor):
                uploaded_bytes[0] = monitor.bytes_read
                if progress_cb:
                    progress_cb(uploaded_bytes[0], total)

            from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
            with open(path, "rb") as f:
                encoder = MultipartEncoder(fields={"file": (nombre, f)})
                monitor = MultipartEncoderMonitor(encoder, _progress)
                resp = requests.put(
                    url, data=monitor, headers={"Content-Type": monitor.content_type}, timeout=600
                )
            if resp.status_code == 200:
                return resp.text.strip()
            return None
        except ImportError:
            return self._upload_curl(path, progress_cb)
        except Exception as exc:
            log.warning("transfer.sh error: %s", exc)
            return self._upload_curl(path, progress_cb)

    def _upload_curl(self, path: str, progress_cb=None) -> str | None:
        try:
            nombre = os.path.basename(path)
            url = f"{self.base_url}/{nombre}"
            kw = {}
            if os.name == "nt":
                kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            result = subprocess.run(
                ["curl", "--upload-file", path, url, "--max-time", "600"],
                capture_output=True, text=True, encoding="utf-8", timeout=620, **kw
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as exc:
            log.warning("transfer.sh curl fallback error: %s", exc)
            return None


# ═══════════════════════════════════════════════════════
# Portapapeles
# ═══════════════════════════════════════════════════════

class ClipboardPath:
    @staticmethod
    def copy(path: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(path)
            return True
        except Exception:
            return False


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def is_safe_to_send(path: str) -> bool:
    try:
        resolved = Path(path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    if not resolved.is_file():
        return False

    nombre = resolved.name.lower()
    blocked_ext = (".env", ".db", ".log", ".pyc", ".key", ".pem")
    if (
        nombre in BLOCKED_FILE_NAMES
        or (
            any(token in nombre for token in ("credential", "token", "secret"))
            and resolved.suffix.lower() in (".json", ".pem", ".p12", ".key")
        )
        or any(nombre.endswith(ext) for ext in blocked_ext)
        or nombre.startswith(".")
    ):
        return False
    blocked_dirs = {"appdata", "windows", "system32", "__pycache__", ".git", "node_modules"}
    if any(part.lower() in blocked_dirs for part in resolved.parts):
        return False
    return True


def split_files(paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    pequenos = []
    grandes = []
    bloqueados = []
    for p in paths:
        if not os.path.isfile(p):
            continue
        if not is_safe_to_send(p):
            bloqueados.append(p)
            continue
        if get_file_size_mb(p) > TELEGRAM_MAX_MB:
            grandes.append(p)
        else:
            pequenos.append(p)
    return pequenos, grandes, bloqueados
