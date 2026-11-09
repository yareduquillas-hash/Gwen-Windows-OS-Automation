from __future__ import annotations

# Registro centralizado de modelos disponibles
# (provider, model_id, display_name)
# Los modelos NVIDIA se validan dinámicamente contra la API real
# (ver ai/nvidia_models.py — autoconfigurable con cache 24h)
MODELOS: dict[str, tuple[str, str, str]] = {
    "nv-flash":  ("nvidia",     "deepseek-ai/deepseek-v4-flash",               "NVIDIA NIM - DeepSeek V4 Flash (Ultra Rápido)"),
    "nv-pro":    ("nvidia",     "deepseek-ai/deepseek-v4-pro",                 "NVIDIA NIM - DeepSeek V4 Pro (Máxima Potencia)"),
    "nv-llama":  ("nvidia",     "meta/llama-3.3-70b-instruct",                 "NVIDIA NIM - Llama 3.3 70B (Fallback sólido)"),
    "nv-nemo":   ("nvidia",     "nvidia/llama-3.3-nemotron-super-49b-v1.5",    "NVIDIA NIM - Nemotron Super 49B (Razonamiento)"),
    "nv-gemma":  ("nvidia",     "google/gemma-4-31b-it",                       "NVIDIA NIM - Gemma 4 31B (Económico)"),
    "flash-0731":("openrouter", "deepseek/deepseek-v4-flash-0731",             "DeepSeek V4 Flash 0731 (Edición Especial)"),
    "silicon":   ("siliconflow","deepseek-ai/DeepSeek-V4-Flash",               "SiliconFlow - DeepSeek V4 Flash 0731"),
    "ds":        ("openrouter", "deepseek/deepseek-chat",                      "DeepSeek V3 Chat (OpenRouter)"),
    "groq":      ("groq",       "llama-3.3-70b-versatile",                    "Groq Llama 3.3 (Ultra-Rápido)"),
}


def resolver_modelo(alias: str) -> tuple[str, str, str] | None:
    """Retorna (provider, model_id, display_name) dado un alias, o None si no existe."""
    return MODELOS.get(alias.lower().strip())


def modelos_para_help() -> str:
    """Genera texto de ayuda con los modelos disponibles."""
    lineas = []
    for alias, (prov, mod, desc) in MODELOS.items():
        lineas.append(f"  /modelo {alias:<10} → {desc}")
    return "\n".join(lineas)


def modelo_nvidia_valido(alias: str, cfg=None) -> str:
    """Retorna el model_id real (validado contra NVIDIA) para un alias 'nv-*'.
    Si el modelo del alias ya no existe en NVIDIA, devuelve un fallback automático."""
    from ai.nvidia_models import es_modelo_valido, modelo_fallback

    entry = MODELOS.get(alias.lower().strip())
    if not entry or entry[0] != "nvidia":
        return entry[1] if entry else ""
    model_id = entry[1]
    if es_modelo_valido(model_id, cfg):
        return model_id
    return modelo_fallback(model_id, cfg)
