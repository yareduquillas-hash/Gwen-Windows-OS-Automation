from __future__ import annotations

import time as _time

from database.connection import ConnectionManager


def guardar_evento(tipo: str, contenido: str) -> None:
    db = ConnectionManager()
    db.execute(
        "INSERT INTO memoria (ts, tipo, contenido) VALUES (?, ?, ?)",
        (_time.time(), tipo, contenido),
    )


def obtener_eventos(tipo: str | None = None, limite: int = 50) -> list:
    db = ConnectionManager()
    if tipo:
        rows = db.fetchall(
            "SELECT ts, tipo, contenido FROM memoria WHERE tipo = ? ORDER BY id DESC LIMIT ?",
            (tipo, limite),
        )
    else:
        rows = db.fetchall(
            "SELECT ts, tipo, contenido FROM memoria ORDER BY id DESC LIMIT ?",
            (limite,),
        )
    return [dict(r) for r in rows]
