from __future__ import annotations

raise SystemExit(
    "create_models.py esta obsoleto; edite ai/models.py y no sobrescriba el registro activo."
)

content = (
    "from __future__ import annotations\n"
    "\n"
    "# Registro centralizado de modelos disponibles\n"
    "# (provider, model_id, display_name)\n"
    "MODELOS: dict[str, tuple[str, str, str]] = {\n"
    "    \"auto\":      (\"openrouter\", \"openrouter/free\",                              \"Auto-Router Din\u00e1mico (Gratis)\"),\n"
    "    \"r1\":        (\"openrouter\", \"deepseek/deepseek-r1\",                        \"DeepSeek R1 (Razonamiento M\u00e1ximo)\"),\n"
    "    \"ds\":        (\"openrouter\", \"deepseek/deepseek-chat\",                      \"DeepSeek V3 Chat\"),\n"
    "    \"gemma\":     (\"openrouter\", \"google/gemma-4-31b-it:free\",                  \"Google Gemma 4 31B (Gratis)\"),\n"
    "    \"reasoning\": (\"openrouter\", \"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free\", \"Nemotron Reasoning (Gratis)\"),\n"
    "    \"groq\":      (\"groq\",       \"llama-3.3-70b-versatile\",                    \"Groq Llama 3.3 (Ultra-R\u00e1pido)\"),\n"
    "    \"opencode\":  (\"opencode\",   \"opencode-go/deepseek-v4-flash\",              \"OpenCode GO CLI (Legado)\"),\n"
    "}\n"
    "\n"
    "\n"
    "def resolver_modelo(alias: str) -> tuple[str, str, str] | None:\n"
    "    \"\"\"Retorna (provider, model_id, display_name) dado un alias, o None si no existe.\"\"\"\n"
    "    return MODELOS.get(alias.lower().strip())\n"
    "\n"
    "\n"
    "def modelos_para_help() -> str:\n"
    "    \"\"\"Genera texto de ayuda con los modelos disponibles.\"\"\"\n"
    "    lineas = []\n"
    "    for alias, (prov, mod, desc) in MODELOS.items():\n"
    "        lineas.append(f\"  /modelo {alias:<10} \u2192 {desc}\")\n"
    "    return \"\\n\".join(lineas)\n"
)

with open("ai/models.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
