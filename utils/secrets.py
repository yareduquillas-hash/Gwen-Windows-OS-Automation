"""Acceso a secretos sin mantenerlos en el codigo ni en logs."""
from __future__ import annotations

import ctypes
import logging
import os
from ctypes import wintypes

log = logging.getLogger("jarvis.secrets")

_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_SERVICE_NAME = "GwenWindowsPro"


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class SecretStore:
    """Almacen Windows Credential Manager para credenciales genericas."""

    def __init__(self, service_name: str = _SERVICE_NAME):
        self.service_name = service_name
        self._available = os.name == "nt" and hasattr(ctypes, "windll")
        self._advapi32 = None
        if self._available:
            self._advapi32 = ctypes.windll.advapi32
            self._advapi32.CredWriteW.argtypes = [
                ctypes.POINTER(_Credential),
                wintypes.DWORD,
            ]
            self._advapi32.CredWriteW.restype = wintypes.BOOL
            self._advapi32.CredReadW.argtypes = [
                wintypes.LPWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(ctypes.POINTER(_Credential)),
            ]
            self._advapi32.CredReadW.restype = wintypes.BOOL
            self._advapi32.CredDeleteW.argtypes = [
                wintypes.LPWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
            ]
            self._advapi32.CredDeleteW.restype = wintypes.BOOL
            self._advapi32.CredFree.argtypes = [ctypes.c_void_p]
            self._advapi32.CredFree.restype = None

    @property
    def available(self) -> bool:
        return self._available and self._advapi32 is not None

    def _target(self, name: str) -> str:
        return f"{self.service_name}/{name}"

    def get(self, name: str) -> str:
        if not self.available:
            return ""
        credential_ptr = ctypes.POINTER(_Credential)()
        try:
            ok = self._advapi32.CredReadW(
                self._target(name),
                _CRED_TYPE_GENERIC,
                0,
                ctypes.byref(credential_ptr),
            )
            if not ok or not credential_ptr:
                return ""
            credential = credential_ptr.contents
            raw = ctypes.string_at(
                credential.CredentialBlob,
                credential.CredentialBlobSize,
            )
            return raw.decode("utf-8")
        except OSError:
            log.debug("Credential Manager no pudo leer el secreto %s", name, exc_info=True)
            return ""
        except UnicodeDecodeError:
            log.warning("Credential Manager devolvio un secreto con encoding invalido: %s", name)
            return ""
        finally:
            if credential_ptr:
                self._advapi32.CredFree(credential_ptr)

    def set(self, name: str, value: str) -> bool:
        if not self.available or not value:
            return False
        raw = value.encode("utf-8")
        blob = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        credential = _Credential()
        credential.Type = _CRED_TYPE_GENERIC
        credential.TargetName = self._target(name)
        credential.CredentialBlobSize = len(raw)
        credential.CredentialBlob = ctypes.cast(
            blob,
            ctypes.POINTER(ctypes.c_ubyte),
        )
        credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = "Gwen"
        try:
            return bool(self._advapi32.CredWriteW(ctypes.byref(credential), 0))
        except OSError:
            return False

    def delete(self, name: str) -> bool:
        if not self.available:
            return False
        try:
            return bool(
                self._advapi32.CredDeleteW(
                    self._target(name),
                    _CRED_TYPE_GENERIC,
                    0,
                )
            )
        except OSError:
            return False


_STORE = SecretStore()


def get_secret(name: str, env_name: str | None = None) -> str:
    """Lee Credential Manager primero y usa .env solo como fallback temporal."""
    stored = _STORE.get(name)
    if stored:
        return stored
    return os.getenv(env_name or name, "")


def set_secret(name: str, value: str) -> bool:
    return _STORE.set(name, value)


def secret_store_available() -> bool:
    return _STORE.available
