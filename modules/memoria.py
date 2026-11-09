from __future__ import annotations

from modules.base import BaseModule


class MemoriaModule(BaseModule):
    nombre = "memoria"
    prioridad = 30

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(t.startswith(p) for p in (
            "recuerda que ", "recuerda ", "guarda esto: ", "guarda ", "aprende que ",
        )) or any(p in t for p in (
            "qué sabes de mí", "que sabes de mi", "qué recuerdas",
            "que recuerdas", "dime lo que sabes", "dime tu memoria",
            "contexto", "última conversación", "ultima conversacion",
            "qué hablamos", "que hablamos", "de qué hablamos", "de que hablamos",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        from database.repositories.perfil import aprender, obtener_todo
        from database.repositories.eventos import guardar_evento
        from database.repositories.conversacion import contexto_reciente

        for pref in ("recuerda que ", "recuerda ", "guarda esto: ", "guarda ", "aprende que "):
            if t.startswith(pref):
                dato = texto[len(pref):].strip().strip('"').strip("'")
                if not dato:
                    bot.send_message(chat_id, "¿Qué dato desea que aprenda, Señor?")
                    return True
                clave = f"dato_{abs(hash(dato))}"
                aprender(clave, dato)
                guardar_evento("aprendizaje", dato)
                bot.send_message(chat_id, f"Anotado, {cfg.full_name}: \"{dato}\" quedará en mi memoria.")
                return True

        if any(p in t for p in ("qué sabes de mí", "que sabes de mi", "qué recuerdas",
                                 "que recuerdas", "dime lo que sabes", "dime tu memoria")):
            todo = obtener_todo()
            if not todo:
                bot.send_message(chat_id, "Mi memoria de usted está vacía, Señor.")
            else:
                resumen = "\n".join(f"• {v}" for v in todo.values())
                bot.send_message(chat_id, f"Esto es lo que sé, {cfg.user_title}:\n{resumen}")
            return True

        if any(p in t for p in ("contexto", "última conversación", "ultima conversacion",
                                 "qué hablamos", "que hablamos", "de qué hablamos",
                                 "de que hablamos")):
            ctx = contexto_reciente(10)
            if ctx:
                bot.send_message(chat_id, f"Contexto reciente, Señor:\n{ctx}")
            else:
                bot.send_message(chat_id, "No hay conversación previa, Señor.")
            return True

        return False


def show_memory(message, bot) -> None:
    from database.repositories.perfil import obtener_todo
    todo = obtener_todo()
    if not todo:
        bot.reply_to(message, "Mi memoria de usted está vacía, Señor.")
    else:
        resumen = "\n".join(f"• {v}" for v in todo.values())
        bot.reply_to(message, f"Mi memoria de usted, Señor:\n{resumen}")


def show_context(message, bot) -> None:
    from database.repositories.conversacion import contexto_reciente
    ctx = contexto_reciente(10)
    bot.reply_to(message, f"Últimas interacciones, Señor:\n{ctx}" if ctx else "No hay conversación previa.")


MODULE_CLASS = MemoriaModule
