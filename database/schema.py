from __future__ import annotations

import logging
import sqlite3

log = logging.getLogger("jarvis.db")


SCHEMA_VERSION = 1

_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS memoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        tipo TEXT NOT NULL,
        contenido TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS perfil (
        clave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        rol TEXT NOT NULL,
        texto TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tareas_programadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creada_ts REAL NOT NULL,
        tipo TEXT NOT NULL,
        hora TEXT,
        minuto TEXT,
        intervalo_seg INTEGER,
        proxima_ejecucion REAL,
        comando TEXT NOT NULL,
        activa INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS secciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        creada_ts REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversacion_secciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seccion_id INTEGER NOT NULL,
        ts REAL NOT NULL,
        rol TEXT NOT NULL,
        texto TEXT NOT NULL,
        FOREIGN KEY (seccion_id) REFERENCES secciones(id)
    )
    """,
]

_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_conversacion_ts ON conversacion(ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_tareas_proxima ON tareas_programadas(proxima_ejecucion, activa)",
    "CREATE INDEX IF NOT EXISTS idx_conv_secciones ON conversacion_secciones(seccion_id, id DESC)",
    "CREATE INDEX IF NOT EXISTS idx_memoria_tipo ON memoria(tipo, ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_memoria_ts ON memoria(ts)",
]

_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_ts REAL NOT NULL
)
"""


def apply_schema(conn: sqlite3.Connection) -> None:
    current = _current_version(conn)

    if current < 1:
        _apply_v1(conn)

    log.info("Schema v%s aplicado en %s", SCHEMA_VERSION, conn.execute("PRAGMA database_list").fetchone()[2])


def _current_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()
        return row[0] if row and row[0] else 0
    except sqlite3.OperationalError:
        return 0


def _apply_v1(conn: sqlite3.Connection) -> None:
    import time

    conn.execute(_VERSION_TABLE)

    for table_sql in _TABLES:
        conn.execute(table_sql)

    for index_sql in _INDICES:
        try:
            conn.execute(index_sql)
        except sqlite3.OperationalError:
            pass

    conn.execute(
        "INSERT INTO schema_version (version, applied_ts) VALUES (?, ?)",
        (1, time.time()),
    )
    conn.commit()


def purgar_datos_antiguos(conn: sqlite3.Connection, dias: int = 180) -> None:
    """Elimina registros más antiguos que `dias` días de las tablas principales."""
    import time

    corte_ts = time.time() - dias * 86400
    tablas = [
        ("conversacion", "ts"),
        ("conversacion_secciones", "ts"),
        ("memoria", "ts"),
    ]
    for tabla, col_ts in tablas:
        try:
            cursor = conn.execute(
                f"DELETE FROM {tabla} WHERE {col_ts} < ?",
                (corte_ts,),
            )
            eliminados = cursor.rowcount
            if eliminados:
                log.info("purgar_datos_antiguos: %d registros eliminados de '%s'", eliminados, tabla)
        except sqlite3.OperationalError as exc:
            log.warning("purgar_datos_antiguos: error en tabla '%s': %s", tabla, exc)
    conn.commit()
