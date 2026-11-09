import threading
from modules.base import BaseModule

_lock_secciones = threading.Lock()
_secciones_actuales: dict[int, tuple[int | None, str]] = {}


def set_seccion(sid: int | None, nombre: str = "", chat_id: int | None = None) -> None:
    key = chat_id or 0
    with _lock_secciones:
        _secciones_actuales[key] = (sid, (nombre or "").lower().strip())


def get_seccion(chat_id: int | None = None) -> tuple[int | None, str]:
    key = chat_id or 0
    with _lock_secciones:
        return _secciones_actuales.get(key, (None, ""))


class SeccionesModule(BaseModule):
    nombre = "secciones"
    prioridad = 20

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(t.startswith(p) for p in (
            "nueva seccion", "nueva sección", "seccion ", "sección ",
            "entra en seccion ", "entra en sección ",
            "entra a la seccion ", "entra a la sección ",
        )) or any(t == p for p in (
            "salir seccion", "salir sección", "seccion general",
            "sección general", "terminar seccion", "terminar sección",
        )) or t.startswith("descripcion de la seccion") or t.startswith("descripción de la sección")

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        from database.repositories.secciones import crear_seccion, obtener_por_nombre, listar_secciones, actualizar_descripcion
        from database.repositories.conversacion import contexto_seccion

        if t.startswith("nueva seccion") or t.startswith("nueva sección"):
            nombre = texto[13:].strip() if t.startswith("nueva sección") else texto[13:].strip()
            nombre = nombre.strip().strip('"').strip("'")
            if not nombre:
                bot.send_message(chat_id, "¿Qué nombre tendrá la nueva sección, Señor?")
                return True
            sid = crear_seccion(nombre)
            set_seccion(sid, nombre, chat_id)
            bot.send_message(chat_id,
                f"Sección \"{nombre}\" creada y activada, {cfg.full_name}. "
                "Para volver al modo general, diga \"salir sección\".")
            return True

        for pref in ("entra a la seccion ", "entra a la sección ",
                      "entra en seccion ", "entra en sección ",
                      "seccion ", "sección "):
            if t.startswith(pref):
                nombre = texto[len(pref):].strip().strip('"').strip("'")
                if not nombre:
                    bot.send_message(chat_id, "¿A qué sección desea entrar, Señor?")
                    return True
                sec = obtener_por_nombre(nombre)
                if not sec:
                    bot.send_message(chat_id,
                        f"No tengo una sección llamada \"{nombre}\", Señor. "
                        f"Puede crearla con \"nueva sección {nombre}\".")
                    return True
                set_seccion(sec["id"], sec["nombre"], chat_id)
                sid, sname = get_seccion(chat_id)
                ctx = contexto_seccion(sid, 5)
                msg = f"Entrando en la sección \"{sec['nombre']}\", {cfg.full_name}."
                if ctx:
                    msg += f"\nContexto reciente:\n{ctx}"
                bot.send_message(chat_id, msg)
                return True

        if any(t == p for p in ("salir seccion", "salir sección", "seccion general",
                                 "sección general", "terminar seccion", "terminar sección")):
            sid, sname = get_seccion(chat_id)
            if sid is None:
                bot.send_message(chat_id, "Ya está en modo general, Señor.")
                return True
            set_seccion(None, chat_id=chat_id)
            bot.send_message(chat_id, f"Saliendo de \"{sname}\". Modo general, {cfg.full_name}.")
            return True

        if t.startswith("descripcion de la seccion") or t.startswith("descripción de la sección"):
            nombre = texto.split("seccion" if "seccion" in t else "sección", 1)[1].strip().lstrip(":").strip()
            sid, _ = get_seccion(chat_id)
            if sid:
                actualizar_descripcion(sid, nombre)
                bot.send_message(chat_id, "Descripción actualizada, Señor.")
            return True

        return False


def list_sections(message, bot) -> None:
    from database.repositories.secciones import listar_secciones
    secciones = listar_secciones()
    if not secciones:
        bot.reply_to(message, "No hay secciones creadas, Señor.")
        return
    _, actual = get_seccion(message.chat.id)
    lineas = []
    for s in secciones:
        marca = " ◀" if s["nombre"] == actual else ""
        lineas.append(f"• {s['nombre']}{marca}")
    bot.reply_to(message, "Secciones:\n" + "\n".join(lineas))


def switch_section_command(message, bot) -> None:
    partes = (message.text or "").split(maxsplit=1)
    if len(partes) < 2:
        bot.reply_to(message, "Indíqueme el nombre de la sección, Señor (ej: /seccion cosas).")
        return
    nombre = partes[1].strip().lower()
    from database.repositories.secciones import crear_seccion, obtener_por_nombre
    sec = obtener_por_nombre(nombre)
    if not sec:
        sid = crear_seccion(nombre)
        set_seccion(sid, nombre, message.chat.id)
    else:
        set_seccion(sec["id"], sec["nombre"], message.chat.id)
    bot.reply_to(message, f"Cambiado a la sección \"{nombre}\", Señor.")


MODULE_CLASS = SeccionesModule
