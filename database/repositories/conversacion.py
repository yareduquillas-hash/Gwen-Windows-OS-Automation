from __future__ import annotations

import time as _time

from database.connection import ConnectionManager


def guardar_conversacion(rol: str, texto: str, seccion_id: int | None = None) -> None:
    db = ConnectionManager()
    db.execute(
        "INSERT INTO conversacion (ts, rol, texto) VALUES (?, ?, ?)",
        (_time.time(), rol, texto),
    )
    if seccion_id is not None:
        db.execute(
            "INSERT INTO conversacion_secciones (seccion_id, ts, rol, texto) VALUES (?, ?, ?, ?)",
            (seccion_id, _time.time(), rol, texto),
        )


def contexto_reciente(limite: int = 10) -> str:
    db = ConnectionManager()
    rows = db.fetchall(
        "SELECT rol, texto FROM conversacion ORDER BY id DESC LIMIT ?",
        (limite,),
    )
    rows = list(reversed(rows))
    return "\n".join(f"({r['rol']}) {r['texto']}" for r in rows)


def contexto_seccion(seccion_id: int, limite: int = 10) -> str:
    db = ConnectionManager()
    rows = db.fetchall(
        "SELECT rol, texto FROM conversacion_secciones "
        "WHERE seccion_id = ? ORDER BY id DESC LIMIT ?",
        (seccion_id, limite),
    )
    rows = list(reversed(rows))
    return "\n".join(f"({r['rol']}) {r['texto']}" for r in rows)
