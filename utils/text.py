from __future__ import annotations


def truncar_telegram(texto: str, limite: int = 4000) -> str:
    if len(texto) <= limite:
        return texto
    return texto[:limite] + "\n... (truncado)"


def escapar_markdown(texto: str) -> str:
    chars = r"_*[]()~`>#+-=|{}.!"
    for c in chars:
        texto = texto.replace(c, f"\\{c}")
    return texto
