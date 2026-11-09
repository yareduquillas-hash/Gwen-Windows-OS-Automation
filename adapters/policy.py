from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .contracts import InputChannel

log = logging.getLogger("jarvis.policy")


class RiskLevel(str, Enum):
    """Nivel de impacto o riesgo operacional de una capacidad."""

    READ = "read"
    WRITE = "write"
    EXTERNAL_UPLOAD = "external_upload"
    DESTRUCTIVE = "destructive"


class Capability(str, Enum):
    """Capacidades operativas del sistema."""

    SYSTEM_READ = "system.read"
    SCREEN_CAPTURE = "screen.capture"
    MEDIA_CONTROL = "media.control"
    FILE_READ = "file.read"
    FILE_UPLOAD = "file.upload"
    PROCESS_TERMINATE = "process.terminate"
    SYSTEM_POWER = "system.power"
    SYSTEM_RESTART = "system.restart"
    SHELL_EXECUTE = "shell.execute"


CAPABILITY_RISK_MAP: Mapping[Capability, RiskLevel] = {
    Capability.SYSTEM_READ: RiskLevel.READ,
    Capability.SCREEN_CAPTURE: RiskLevel.READ,
    Capability.MEDIA_CONTROL: RiskLevel.WRITE,
    Capability.FILE_READ: RiskLevel.READ,
    Capability.FILE_UPLOAD: RiskLevel.EXTERNAL_UPLOAD,
    Capability.PROCESS_TERMINATE: RiskLevel.DESTRUCTIVE,
    Capability.SYSTEM_POWER: RiskLevel.DESTRUCTIVE,
    Capability.SYSTEM_RESTART: RiskLevel.DESTRUCTIVE,
    Capability.SHELL_EXECUTE: RiskLevel.DESTRUCTIVE,
}


@dataclass
class PendingConfirmation:
    action_key: str
    created_at: float
    ttl_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


class CapabilityPolicy:
    """Validador central de capacidades, auditoria y confirmaciones."""

    _instance: CapabilityPolicy | None = None
    _lock = threading.Lock()

    def __new__(cls) -> CapabilityPolicy:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._pending = {}
                    cls._instance._pending_lock = threading.RLock()
        return cls._instance

    @staticmethod
    def get_risk(capability: Capability) -> RiskLevel:
        return CAPABILITY_RISK_MAP.get(capability, RiskLevel.DESTRUCTIVE)

    def requires_confirmation(self, capability: Capability) -> bool:
        return self.get_risk(capability) == RiskLevel.DESTRUCTIVE

    def request_confirmation(
        self,
        user_id: str | int,
        action_key: str,
        ttl_seconds: float = 60.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Registra una intencion de accion que requiere confirmacion explicita."""
        uid = str(user_id)
        with self._pending_lock:
            if uid not in self._pending:
                self._pending[uid] = {}
            self._pending[uid][action_key] = PendingConfirmation(
                action_key=action_key,
                created_at=time.time(),
                ttl_seconds=ttl_seconds,
                metadata=metadata or {},
            )
            log.info("Confirmacion solicitada para user=%s accion=%s (TTL=%ss)", uid, action_key, ttl_seconds)

    def verify_confirmation(self, user_id: str | int, action_key: str) -> bool:
        """Valida y consume la confirmacion pendiente."""
        uid = str(user_id)
        with self._pending_lock:
            user_pending = self._pending.get(uid, {})
            pending = user_pending.get(action_key)
            if not pending:
                return False
            if pending.is_expired:
                user_pending.pop(action_key, None)
                log.warning("Confirmacion expirada para user=%s accion=%s", uid, action_key)
                return False
            user_pending.pop(action_key, None)
            log.info("Confirmacion aceptada para user=%s accion=%s", uid, action_key)
            return True

    def cancel_confirmation(self, user_id: str | int, action_key: str | None = None) -> None:
        uid = str(user_id)
        with self._pending_lock:
            if uid in self._pending:
                if action_key:
                    self._pending[uid].pop(action_key, None)
                else:
                    self._pending[uid].clear()

    @staticmethod
    def audit(
        capability: Capability,
        user_id: str | int,
        channel: InputChannel | str,
        details: str,
        status: str = "ALLOWED",
    ) -> None:
        risk = CAPABILITY_RISK_MAP.get(capability, RiskLevel.DESTRUCTIVE).value.upper()
        ch = channel.value if isinstance(channel, InputChannel) else str(channel)
        log.info(
            "[AUDIT] capability=%s risk=%s user=%s channel=%s status=%s details='%s'",
            capability.value,
            risk,
            user_id,
            ch,
            status,
            details,
        )
