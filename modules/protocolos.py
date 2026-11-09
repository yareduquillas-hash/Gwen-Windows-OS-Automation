import threading
from modules.base import BaseModule

_lock_protocolos = threading.Lock()
protocolo_activo: str | None = None


def set_protocolo(proto: str | None) -> None:
    global protocolo_activo
    with _lock_protocolos:
        protocolo_activo = proto


def get_protocolo() -> str | None:
    with _lock_protocolos:
        return protocolo_activo


def _update_cfg(cfg, key: str, val: str) -> None:
    if hasattr(cfg, "override"):
        cfg.override(key, val)
    else:
        setattr(cfg, key, val)


class ProtocolosModule(BaseModule):
    nombre = "protocolos"
    prioridad = 35

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return "protocolo g" in t or "protocolo m" in t

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        if "protocolo g" in t and "activar" in t and "desactivar" not in t:
            set_protocolo("G")
            _update_cfg(cfg, "ai_provider", "nvidia")
            _update_cfg(cfg, "nvidia_model", "nvidia/llama-3.3-nemotron-super-49b-v1.5")
            bot.send_message(chat_id,
                f"Protocolo G activado, {cfg.full_name}. "
                "Delegaré las tareas a NVIDIA NIM Nemotron Super 49B (Razonamiento Profundo).")
            return True

        if "protocolo g" in t and "desactivar" in t:
            set_protocolo(None)
            _update_cfg(cfg, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
            bot.send_message(chat_id,
                f"Protocolo G desactivado, {cfg.full_name}. "
                "Vuelvo a la configuración estándar (DeepSeek V4 Flash).")
            return True

        if "protocolo m" in t and "activar" in t and "desactivar" not in t:
            set_protocolo("M")
            _update_cfg(cfg, "ai_provider", "nvidia")
            _update_cfg(cfg, "nvidia_model", "deepseek-ai/deepseek-v4-pro")
            bot.send_message(chat_id,
                f"Protocolo M activado, {cfg.full_name}. "
                "Delegaré las tareas a NVIDIA NIM DeepSeek V4 Pro (Máxima Potencia).")
            return True

        if "protocolo m" in t and "desactivar" in t:
            set_protocolo(None)
            _update_cfg(cfg, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
            bot.send_message(chat_id,
                f"Protocolo M desactivado, {cfg.full_name}. "
                "Vuelvo a la configuración estándar (DeepSeek V4 Flash).")
            return True

        return False


def show_status(message, bot, cfg) -> None:
    prov = getattr(cfg, "ai_provider", "nvidia")
    if prov == "nvidia":
        active_mod = getattr(cfg, "nvidia_model", "deepseek-ai/deepseek-v4-flash")
    elif prov == "openrouter":
        active_mod = getattr(cfg, "openrouter_model", "")
    else:
        active_mod = getattr(cfg, "groq_model", "")

    proto = get_protocolo()
    if proto == "G":
        bot.reply_to(message, f"Protocolo G: ACTIVADO ({active_mod}), {cfg.full_name}.")
    elif proto == "M":
        bot.reply_to(message, f"Protocolo M: ACTIVADO ({active_mod}), {cfg.full_name}.")
    else:
        bot.reply_to(message, f"Proveedor: {prov.upper()} | Modelo activo: {active_mod}.")


MODULE_CLASS = ProtocolosModule
