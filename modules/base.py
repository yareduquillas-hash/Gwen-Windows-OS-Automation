from __future__ import annotations

from abc import ABC, abstractmethod


class BaseModule(ABC):
    nombre: str = "base"
    prioridad: int = 100
    enabled: bool = True

    @abstractmethod
    def can_handle(self, texto: str, cfg=None, chat_id: int | None = None) -> bool:
        ...

    @abstractmethod
    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        """Retorna True si manejó el mensaje, False para pasar al siguiente."""
        ...

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass
