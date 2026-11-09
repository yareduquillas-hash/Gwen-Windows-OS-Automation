from __future__ import annotations

import random
import threading

from modules.base import BaseModule

_wizard_states: dict[int, dict] = {}
_lock_wizard = threading.Lock()

WIZARD_STEPS = [
    {
        "key": "user_name",
        "ask": [
            "Buenas. Soy Gwen, su asistente virtual.",
            "",
            "Vamos a configurar unas cosas rapidas.",
            "",
            "Paso 1/3: ¿Como quiere que le llame?",
            "(ej: Tony, Maria, Admin...)",
        ],
        "default": "Admin",
        "validate": lambda v: v and len(v.strip()) <= 30,
        "error": "Nombre muy largo (max 30 caracteres). Intente de nuevo.",
    },
    {
        "key": "user_title",
        "ask": [
            "Paso 2/3: ¿Y como debo dirigirme a usted?",
            "Por ejemplo: Senor, Jefe, Maestro, Amo, Capitan...",
        ],
        "default": "Senor",
        "validate": lambda v: v and len(v.strip()) <= 20,
        "error": "Titulo muy largo (max 20 caracteres). Intente de nuevo.",
    },
    {
        "key": "gfn_gaming_volume",
        "ask": [
            "Paso 3/3: ¿Volumen por defecto al lanzar juegos con GeForce NOW?",
            "Indique un numero del 0 al 100.",
        ],
        "default": "75",
        "validate": lambda v: v.strip().isdigit() and 0 <= int(v.strip()) <= 100,
        "error": "Debe ser un numero entre 0 y 100. Intente de nuevo.",
    },
]


class WizardModule(BaseModule):
    nombre = "wizard"
    prioridad = 3

    def can_handle(self, texto: str, cfg=None, chat_id: int | None = None) -> bool:
        t = texto.lower().strip()
        with _lock_wizard:
            has_state = chat_id is not None and chat_id in _wizard_states
        if t == "/wizard" or t.startswith("/wizard "):
            return True
        if has_state:
            return True
        if cfg and hasattr(cfg, 'wizard_completed') and not cfg.wizard_completed:
            return True
        return False

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if t.startswith("/wizard"):
            args = t.split(maxsplit=1)
            if len(args) > 1 and args[1] in ("salir", "cancelar", "exit"):
                with _lock_wizard:
                    _wizard_states.pop(chat_id, None)
                bot.send_message(chat_id, "Wizard cancelado. Puede reanudarlo con /wizard.")
                return True
            with _lock_wizard:
                _wizard_states[chat_id] = {"step": 0, "answers": {}}
            return self._show_current_step(chat_id, bot, cfg)

        with _lock_wizard:
            in_wizard = chat_id in _wizard_states
        if in_wizard:
            if t.startswith("/") and not t.startswith("/wizard"):
                if t in ("/cancelar", "/cancel", "/salir", "/exit"):
                    with _lock_wizard:
                        _wizard_states.pop(chat_id, None)
                    bot.send_message(chat_id, "Wizard cancelado.")
                    return True
                # Permitir que otros comandos con / se ejecuten normalmente
                return False
            return self._handle_step(t, chat_id, bot, cfg)

        if hasattr(cfg, "wizard_completed") and not cfg.wizard_completed:
            if t.startswith("/"):
                return False
            with _lock_wizard:
                _wizard_states[chat_id] = {"step": 0, "answers": {}}
            return self._show_current_step(chat_id, bot, cfg)

        return False

    def _show_current_step(self, chat_id, bot, cfg) -> bool:
        with _lock_wizard:
            state = _wizard_states.get(chat_id)
        if not state:
            return False

        step_idx = state["step"]

        if step_idx >= len(WIZARD_STEPS):
            return self._confirm(chat_id, bot, cfg)

        step = WIZARD_STEPS[step_idx]
        if callable(step["ask"]):
            msg = step["ask"](cfg)
        elif isinstance(step["ask"], list):
            msg = "\n".join(step["ask"])
        else:
            msg = step["ask"]

        if step.get("skip_allowed"):
            msg += f"\n\n(Envie '/wizard saltar' para usar el valor por defecto: {step['default']})"

        bot.send_message(chat_id, msg)
        return True

    def _handle_step(self, texto: str, chat_id, bot, cfg) -> bool:
        with _lock_wizard:
            state = _wizard_states.get(chat_id)
        if not state:
            return False

        t = texto.lower().strip()
        step_idx = state["step"]

        if t in ("/wizard saltar", "saltar"):
            step = WIZARD_STEPS[step_idx]
            with _lock_wizard:
                state["answers"][step["key"]] = step["default"]
                state["step"] += 1
                next_step = state["step"]
            if next_step >= len(WIZARD_STEPS):
                return self._confirm(chat_id, bot, cfg)
            return self._show_current_step(chat_id, bot, cfg)

        if step_idx >= len(WIZARD_STEPS):
            return self._handle_confirm(t, chat_id, bot, cfg)

        step = WIZARD_STEPS[step_idx]

        if not isinstance(step.get("validate"), type(None)):
            if not step["validate"](texto):
                bot.send_message(chat_id, step["error"])
                return True

        with _lock_wizard:
            state["answers"][step["key"]] = texto.strip()
            state["step"] += 1
            next_step = state["step"]

        if next_step >= len(WIZARD_STEPS):
            return self._confirm(chat_id, bot, cfg)

        return self._show_current_step(chat_id, bot, cfg)

    def _confirm(self, chat_id, bot, cfg) -> bool:
        with _lock_wizard:
            state = _wizard_states.get(chat_id)
            answers = dict(state["answers"]) if state else None
        if answers is None:
            return False
        lines = [
            "Perfecto. Asi queda su configuracion:",
            "",
            f"  Nombre:    {answers.get('user_name', 'Admin')}",
            f"  Titulo:    {answers.get('user_title', 'Senor')}",
            f"  Vol. juego: {answers.get('gfn_gaming_volume', '75')}%",
            "",
            "¿Correcto?",
            "  'si' → guardar y terminar",
            "  'reiniciar' → volver a empezar",
        ]
        bot.send_message(chat_id, "\n".join(lines))
        return True

    def _handle_confirm(self, texto: str, chat_id, bot, cfg) -> bool:
        with _lock_wizard:
            state = _wizard_states.get(chat_id)
            answers = dict(state["answers"]) if state else None
        if answers is None:
            return False

        t = texto.lower().strip().rstrip("?!.¡¿,")

        if t in ("si", "sí", "ok", "vale", "si si", "correcto"):
            nombre = answers.get("user_name", "Admin")
            titulo = answers.get("user_title", "Senor")
            vol = answers.get("gfn_gaming_volume", "75")

            cfg.override("user_name", nombre)
            cfg.override("user_title", titulo)
            cfg.override("gfn_gaming_volume", int(vol))
            cfg.mark_wizard_completed()

            full = f"{titulo} {nombre}"
            with _lock_wizard:
                _wizard_states.pop(chat_id, None)

            lineas = [
                f"¡Bienvenido, {full}!",
                "",
                "Gwen a su entera disposicion.",
                "Envie /start para ver los comandos disponibles.",
            ]
            saludos = [
                "¿En que puedo ayudarle hoy?",
                "Lista para asistirle en lo que necesite.",
                "Su sistema esta en linea y operativo.",
                "Es un placer estar a su servicio.",
            ]
            lineas.append(random.choice(saludos))

            bot.send_message(chat_id, "\n".join(lineas))
            return True

        if t in ("reiniciar", "no", "volver", "otra vez"):
            with _lock_wizard:
                _wizard_states[chat_id] = {"step": 0, "answers": {}}
            return self._show_current_step(chat_id, bot, cfg)

        bot.send_message(chat_id, "Responda 'si' para guardar o 'reiniciar' para volver a empezar.")
        return True


MODULE_CLASS = WizardModule
