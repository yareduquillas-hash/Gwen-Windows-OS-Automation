from __future__ import annotations

import time as _time

from database.connection import ConnectionManager


def guardar_tarea(tipo: str, hora: str | None, minuto: str | None,
                  intervalo_seg: int | None, proxima: float, comando: str) -> int:
    db = ConnectionManager()
    cur = db.execute(
        "INSERT INTO tareas_programadas "
        "(creada_ts, tipo, hora, minuto, intervalo_seg, proxima_ejecucion, comando, activa) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
        (_time.time(), tipo, hora, minuto, intervalo_seg, proxima, comando),
    )
    return cur.lastrowid


def obtener_tareas(activas: bool = True) -> list[dict]:
    db = ConnectionManager()
    if activas:
        rows = db.fetchall(
            "SELECT id, tipo, hora, minuto, intervalo_seg, proxima_ejecucion, comando, activa "
            "FROM tareas_programadas WHERE activa = 1 AND proxima_ejecucion IS NOT NULL ORDER BY id"
        )
    else:
        rows = db.fetchall(
            "SELECT id, tipo, hora, minuto, intervalo_seg, proxima_ejecucion, comando, activa "
            "FROM tareas_programadas ORDER BY id"
        )
    return [dict(r) for r in rows]


def desactivar_tarea(tarea_id: int) -> None:
    db = ConnectionManager()
    db.execute("UPDATE tareas_programadas SET activa = 0 WHERE id = ?", (tarea_id,))


def actualizar_proxima(tarea_id: int, proxima: float) -> None:
    db = ConnectionManager()
    db.execute(
        "UPDATE tareas_programadas SET proxima_ejecucion = ? WHERE id = ?",
        (proxima, tarea_id),
    )
