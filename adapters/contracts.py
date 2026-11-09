from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class InputChannel(str, Enum):
    """Canal que origino una entrada de usuario."""

    TELEGRAM = "telegram"
    REST = "rest"
    WEBSOCKET = "websocket"
    VOICE = "voice"


@dataclass(frozen=True, slots=True)
class InboundMessage:
    """Mensaje normalizado antes de entrar al nucleo de comandos."""

    request_id: str
    channel: InputChannel
    user_id: str
    text: str
    received_at: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        channel: InputChannel,
        user_id: str | int,
        text: str,
        *,
        request_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        received_at: float | None = None,
    ) -> "InboundMessage":
        return cls(
            request_id=request_id or uuid.uuid4().hex,
            channel=channel,
            user_id=str(user_id),
            text=text,
            received_at=received_at if received_at is not None else time.time(),
            metadata=dict(metadata or {}),
        )


class TelegramInputAdapter:
    """Convierte un objeto de TeleBot en el contrato comun."""

    channel = InputChannel.TELEGRAM

    @classmethod
    def from_message(cls, message, text: str | None = None) -> InboundMessage:
        chat = getattr(message, "chat", None)
        chat_id = getattr(chat, "id", "unknown")
        message_id = getattr(message, "message_id", None)
        received_at = getattr(message, "date", None)
        return InboundMessage.create(
            cls.channel,
            chat_id,
            text if text is not None else (getattr(message, "text", "") or ""),
            request_id=f"telegram-{chat_id}-{message_id}" if message_id else None,
            received_at=float(received_at) if received_at else None,
            metadata={
                "chat_id": chat_id,
                "message_id": message_id,
                "content_type": getattr(message, "content_type", "text"),
            },
        )


class VoiceInputAdapter:
    """Representa texto transcrito sin mezclarlo con el transporte de salida."""

    channel = InputChannel.VOICE

    @classmethod
    def from_message(cls, message, transcript: str) -> InboundMessage:
        event = TelegramInputAdapter.from_message(message, transcript)
        return InboundMessage.create(
            cls.channel,
            event.user_id,
            transcript,
            request_id=event.request_id,
            received_at=event.received_at,
            metadata={**event.metadata, "source_channel": InputChannel.TELEGRAM.value},
        )


class RestInputAdapter:
    """Construye entradas para endpoints HTTP que ejecuten comandos."""

    channel = InputChannel.REST

    @classmethod
    def from_payload(
        cls,
        user_id: str | int,
        text: str,
        *,
        request_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> InboundMessage:
        return InboundMessage.create(
            cls.channel,
            user_id,
            text,
            request_id=request_id,
            metadata=metadata,
        )


class WebSocketInputAdapter:
    """Convierte un payload JSON de Android en una entrada normalizada."""

    channel = InputChannel.WEBSOCKET

    @classmethod
    def from_payload(
        cls,
        user_id: str | int,
        payload: Mapping[str, Any],
    ) -> InboundMessage:
        return InboundMessage.create(
            cls.channel,
            user_id,
            str(payload.get("text", "")),
            request_id=str(payload.get("request_id") or "") or None,
            metadata={"message_type": payload.get("type", "message")},
        )
