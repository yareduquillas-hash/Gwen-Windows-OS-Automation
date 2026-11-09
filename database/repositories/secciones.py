from __future__ import annotations

import time as _time

from database.connection import ConnectionManager


def crear_seccion(nombre: str, descripcion: str = "") -> int:
    db = ConnectionManager()
    existente = db.fetchone(
        "SELECT id FROM secciones WHERE nombre = ?", (nombre.lower().strip(),)
    )
    if existente:
        return existente["id"]
    cur = db.execute(
        "INSERT INTO secciones (nombre, descripcion, creada_ts) VALUES (?, ?, ?)",
        (nombre.lower().strip(), descripcion, _time.time()),
    )
    return cur.lastrowid


def obtener_por_nombre(nombre: str) -> dict | None:
    db = ConnectionManager()
    row = db.fetchone(
        "SELECT id, nombre, descripcion FROM secciones WHERE nombre = ?",
        (nombre.lower().strip(),),
    )
    return dict(row) if row else None


def listar_secciones() -> list[dict]:
    db = ConnectionManager()
    rows = db.fetchall("SELECT id, nombre, descripcion FROM secciones ORDER BY id")
    return [dict(r) for r in rows]


def actualizar_descripcion(seccion_id: int, descripcion: str) -> None:
    db = ConnectionManager()
    db.execute("UPDATE secciones SET descripcion = ? WHERE id = ?", (descripcion, seccion_id))
