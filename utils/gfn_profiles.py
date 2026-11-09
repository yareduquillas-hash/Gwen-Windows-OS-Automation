from __future__ import annotations

import base64
import ctypes
import json
import logging
import os
import threading
import time
import uuid
from ctypes import wintypes
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.gfn.profiles")

# ═══════════════════════════════════════════════════════
# Windows DPAPI Cifrado Seguro de Credenciales
# ═══════════════════════════════════════════════════════

class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _encrypt_dpapi(plaintext: str) -> str:
    """Cifra una cadena usando Windows DPAPI (CryptProtectData)."""
    if not plaintext:
        return ""
    if os.name != "nt" or not hasattr(ctypes, "windll"):
        # Fallback de codificación simple si no está en Windows
        return base64.b64encode(plaintext.encode("utf-8")).decode("ascii")

    raw_bytes = plaintext.encode("utf-8")
    blob_in = _DATA_BLOB()
    blob_in.cbData = len(raw_bytes)
    blob_in.pbData = ctypes.cast(
        ctypes.create_string_buffer(raw_bytes, len(raw_bytes)),
        ctypes.POINTER(ctypes.c_byte),
    )
    blob_out = _DATA_BLOB()

    crypt32 = ctypes.windll.crypt32
    # CryptProtectData(pDataIn, szDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
    success = crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        "GwenGFNCredential",
        None,
        None,
        None,
        0x01,  # CRYPTPROTECT_UI_FORBIDDEN
        ctypes.byref(blob_out),
    )
    if not success or not blob_out.pbData:
        raise OSError("Fallo al cifrar credencial con Windows DPAPI")

    try:
        encrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        return base64.b64encode(encrypted_bytes).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _decrypt_dpapi(ciphertext_b64: str) -> str:
    """Descifra una cadena protegida con Windows DPAPI (CryptUnprotectData)."""
    if not ciphertext_b64:
        return ""
    if os.name != "nt" or not hasattr(ctypes, "windll"):
        try:
            return base64.b64decode(ciphertext_b64.encode("ascii")).decode("utf-8")
        except Exception:
            return ""

    try:
        encrypted_bytes = base64.b64decode(ciphertext_b64.encode("ascii"))
    except Exception as exc:
        log.warning("Formato base64 inválido en credencial: %s", exc)
        return ""

    blob_in = _DATA_BLOB()
    blob_in.cbData = len(encrypted_bytes)
    blob_in.pbData = ctypes.cast(
        ctypes.create_string_buffer(encrypted_bytes, len(encrypted_bytes)),
        ctypes.POINTER(ctypes.c_byte),
    )
    blob_out = _DATA_BLOB()

    crypt32 = ctypes.windll.crypt32
    # CryptUnprotectData(pDataIn, ppszDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
    success = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0x01,  # CRYPTPROTECT_UI_FORBIDDEN
        ctypes.byref(blob_out),
    )
    if not success or not blob_out.pbData:
        log.warning("No se pudo descifrar la credencial con DPAPI")
        return ""

    try:
        decrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        return decrypted_bytes.decode("utf-8")
    except UnicodeDecodeError:
        log.warning("Error decodificando UTF-8 tras descifrar DPAPI")
        return ""
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


# ═══════════════════════════════════════════════════════
# Modelo de Datos y Perfiles de Juego
# ═══════════════════════════════════════════════════════

@dataclass
class GameProfile:
    id: str
    game_name: str
    profile_name: str
    account_email: str
    password_encrypted: str
    template_image: str | None = None
    click_coords: tuple[int, int] | None = None
    key_sequence: str = "EMAIL,TAB,PASSWORD,ENTER"
    created_at: float = field(default_factory=time.time)

    def to_public_dict(self) -> dict[str, Any]:
        """Devuelve representación pública del perfil sin exponer contraseñas."""
        return {
            "id": self.id,
            "game_name": self.game_name,
            "profile_name": self.profile_name,
            "account_email": self.account_email,
            "has_password": bool(self.password_encrypted),
            "template_image": self.template_image,
            "click_coords": self.click_coords,
            "key_sequence": self.key_sequence,
            "created_at": self.created_at,
        }

    def get_password(self) -> str:
        """Descifra y retorna la contraseña en tiempo de ejecución."""
        return _decrypt_dpapi(self.password_encrypted)


class GFNProfileManager:
    """Gestor persistente de perfiles de juegos de GeForce NOW."""

    _instance: GFNProfileManager | None = None
    _lock = threading.Lock()

    def __new__(cls, storage_path: Path | str | None = None) -> GFNProfileManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_manager(storage_path)
        return cls._instance

    def _init_manager(self, storage_path: Path | str | None = None) -> None:
        if storage_path is None:
            appdata = os.getenv("APPDATA", os.path.expanduser("~"))
            self.base_dir = Path(appdata) / "GwenWindowsPro"
        else:
            self.base_dir = Path(storage_path)
        
        self.profiles_file = self.base_dir / "gfn_profiles.json"
        self.templates_dir = self.base_dir / "templates"
        self._profiles: dict[str, GameProfile] = {}
        self._rw_lock = threading.RLock()
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        with self._rw_lock:
            if not self.profiles_file.exists():
                self._profiles = {}
                return
            try:
                data = json.loads(self.profiles_file.read_text(encoding="utf-8"))
                profiles = {}
                for item in data.get("profiles", []):
                    prof = GameProfile(
                        id=item["id"],
                        game_name=item["game_name"],
                        profile_name=item["profile_name"],
                        account_email=item.get("account_email", ""),
                        password_encrypted=item.get("password_encrypted", ""),
                        template_image=item.get("template_image"),
                        click_coords=tuple(item["click_coords"]) if item.get("click_coords") else None,
                        key_sequence=item.get("key_sequence", "EMAIL,TAB,PASSWORD,ENTER"),
                        created_at=item.get("created_at", time.time()),
                    )
                    profiles[prof.id] = prof
                self._profiles = profiles
            except Exception as exc:
                log.warning("Error cargando perfiles GFN: %s", exc)
                self._profiles = {}

    def _save(self) -> None:
        with self._rw_lock:
            self._ensure_dirs()
            data = {
                "version": 1,
                "updated_at": time.time(),
                "profiles": [asdict(p) for p in self._profiles.values()],
            }
            tmp_path = self.profiles_file.with_suffix(".tmp")
            try:
                tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp_path, self.profiles_file)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

    def list_profiles(self, game_name: str | None = None) -> list[GameProfile]:
        with self._rw_lock:
            all_profs = list(self._profiles.values())
            if game_name:
                wanted = game_name.lower().strip()
                return [p for p in all_profs if wanted in p.game_name.lower() or p.game_name.lower() in wanted]
            return all_profs

    def get_profile(self, profile_id: str) -> GameProfile | None:
        with self._rw_lock:
            return self._profiles.get(profile_id)

    def find_profile_for_game(self, game_name: str, profile_name: str | None = None) -> GameProfile | None:
        """Busca el perfil más adecuado para un juego."""
        with self._rw_lock:
            matches = self.list_profiles(game_name)
            if not matches:
                return None
            if profile_name:
                pname = profile_name.lower().strip()
                for p in matches:
                    if pname in p.profile_name.lower():
                        return p
            # Por defecto retorna el primero configurado
            return matches[0]

    def create_or_update_profile(
        self,
        game_name: str,
        profile_name: str,
        account_email: str,
        password_plain: str | None = None,
        template_image: str | None = None,
        click_coords: tuple[int, int] | None = None,
        key_sequence: str = "EMAIL,TAB,PASSWORD,ENTER",
        profile_id: str | None = None,
    ) -> GameProfile:
        with self._rw_lock:
            pid = profile_id or uuid.uuid4().hex[:12]
            existing = self._profiles.get(pid)
            
            if password_plain is not None:
                pwd_encrypted = _encrypt_dpapi(password_plain)
            elif existing:
                pwd_encrypted = existing.password_encrypted
            else:
                pwd_encrypted = ""

            prof = GameProfile(
                id=pid,
                game_name=game_name.strip(),
                profile_name=profile_name.strip(),
                account_email=account_email.strip(),
                password_encrypted=pwd_encrypted,
                template_image=template_image or (existing.template_image if existing else None),
                click_coords=click_coords or (existing.click_coords if existing else None),
                key_sequence=key_sequence,
                created_at=existing.created_at if existing else time.time(),
            )
            self._profiles[pid] = prof
            self._save()
            log.info("Perfil GFN guardado: %s (%s - %s)", pid, prof.game_name, prof.profile_name)
            return prof

    def delete_profile(self, profile_id: str) -> bool:
        with self._rw_lock:
            if profile_id in self._profiles:
                deleted = self._profiles.pop(profile_id)
                self._save()
                log.info("Perfil GFN eliminado: %s", profile_id)
                return True
            return False
