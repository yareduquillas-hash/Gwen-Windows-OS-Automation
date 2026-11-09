from __future__ import annotations

import random

from modules.base import BaseModule

RESPUESTAS = {
    "saludo": [
        "Buenos días, {full_name}. ¿En qué puedo asistirle?",
        "{full_name}. Le escucho.",
        "A sus órdenes, {full_name}.",
        "Buenas. ¿Qué desea hoy, {full_name}?",
        "Aquí estoy. ¿En qué le ayudo?",
    ],
    "gracias": [
        "De nada, Señor. Para eso estoy.",
        "No hay de qué. Es mi función.",
        "Un placer servirle, {full_name}.",
    ],
    "despedida": [
        "Hasta la próxima, Señor.",
        "Que tenga un excelente día, {full_name}.",
        "Gwen permanecerá en espera. Hasta pronto.",
        "Hasta luego, {full_name}.",
    ],
    "confirmacion": [
        "Entendido, Señor.",
        "Como ordene.",
        "Perfecto, {full_name}.",
        "De acuerdo.",
    ],
    "identidad": [
        "Soy Gwen, su asistente virtual. Gestiono su PC Windows con módulos para batería, archivos, GFN, IA y más. Envíe /start para ver los comandos.",
        "Gwen, a su servicio, {full_name}. Controlo su laptop, archivos, juegos y más desde Telegram. ¿En qué puedo ayudarle?",
        "Soy un bot de Telegram que controla remotamente esta PC Windows. Tengo módulos para batería, sistema, archivos, GFN, IA y mucho más.",
    ],
    "estado": [
        "Siempre presente, Señor. ¿Qué necesita?",
        "En línea y operativo, {full_name}.",
        "Activo y a la espera de sus instrucciones.",
    ],
    "capacidades": [
        "Puedo: /bateria, /sistema, /volumen, /captura, /procesos, /ventanas, /lanza juego, buscar archivos con IA, subir a Drive, controlar medios, programar tareas, cambiar modelos IA y más. Envíe /start para la guía completa.",
    ],
}

PATRONES = {
    "saludo": (
        "hola", "ola", "buenos días", "buenos dias", "buenas tardes",
        "buenas noches", "hey", "qué tal", "que tal", "como estas",
        "cómo estás", "hello", "hi", "buenas", "saludos",
    ),
    "gracias": (
        "gracias", "thank you", "te lo agradezco", "thanks", "ty",
        "muchas gracias", "gracias gwen", "gracias jarvis", "muy amable",
    ),
    "despedida": (
        "adiós", "adios", "hasta luego", "nos vemos", "chao", "bye",
        "hasta mañana", "hasta pronto", "me voy", "me despido",
    ),
    "confirmacion": (
        "sí", "si", "ok", "okey", "vale", "de acuerdo", "entendido",
        "perfecto", "claro", "bien", "correcto", "okey", "oka", "oki",
        "dale", "va", "genial", "excelente", "bueno",
    ),
    "identidad": (
        "qué eres", "que eres", "quien eres", "quién eres", "cómo funcionas",
        "como funcionas", "qué haces", "que haces",
        "qué puedes hacer", "que puedes hacer", "para qué sirves",
        "para que sirves", "qué eres tú", "que eres tu", "quién te creó",
        "quien te creo",
    ),
    "estado": (
        "estás ahí", "estas ahi", "me escuchas", "sigues vivo",
        "funcionas", "estás despierto", "estas despierto",
        "estás en línea", "estas en linea", "sigues ahí", "sigues ahi",
        "estás", "estas",
    ),
    "capacidades": (
        "qué comandos tienes", "que comandos tienes", "lista de comandos",
        "qué sabes hacer", "que sabes hacer", "ayuda", "help",
        "qué opciones hay", "que opciones hay",
    ),
}


class ConversacionModule(BaseModule):
    nombre = "conversacion"
    prioridad = 95

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip().rstrip("?!.¡¿,")
        if t.startswith("jarvis,") or t.startswith("gwen,"):
            return False
        for patrones in PATRONES.values():
            if t in patrones:
                return True
            if any(p.lstrip("?!.¡¿,") == t for p in patrones):
                return True
        return False

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip().rstrip("?!.¡¿,")
        for categoria, patrones in PATRONES.items():
            if t in patrones or any(p.lstrip("?!.¡¿,") == t for p in patrones):
                respuesta = random.choice(RESPUESTAS[categoria])
                respuesta = respuesta.format(full_name=cfg.full_name)
                bot.send_message(chat_id, respuesta)
                return True
        return False


MODULE_CLASS = ConversacionModule
