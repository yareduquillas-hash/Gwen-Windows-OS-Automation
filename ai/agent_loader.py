"""Cargador del template de identidad de Gwen. Retorna el system prompt base."""
from __future__ import annotations

from pathlib import Path


def _default_agent(cfg) -> str:
    """Fallback system prompt when agents_template.md is missing."""
    return (
        f"Eres Gwen, una asistente virtual inteligente, sofisticada y leal. "
        f"Tu usuario es {cfg.user_title} {cfg.user_name}. "
        f"Respondes con un tono educado, profesional y con toques de calidez. "
        f"Hablas en primera persona como Gwen. "
        f"Nunca revelas que eres un modelo de lenguaje ni mencionas OpenCode, CLI o DeepSeek."
    )


def cargar_agente(cfg) -> str:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "agents_template.md"
    if not template_path.exists():
        return _default_agent(cfg)

    raw = template_path.read_text(encoding="utf-8")
    return raw.replace("{JARVIS_USER_NAME}", cfg.user_name).replace(
        "{JARVIS_USER_TITLE}", cfg.user_title
    )
