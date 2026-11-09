from __future__ import annotations

from database.connection import ConnectionManager


def aprender(clave: str, valor: str) -> None:
    db = ConnectionManager()
    db.execute(
        "INSERT OR REPLACE INTO perfil (clave, valor) VALUES (?, ?)",
        (clave, valor),
    )


def recordar(clave: str) -> str:
    db = ConnectionManager()
    row = db.fetchone("SELECT valor FROM perfil WHERE clave = ?", (clave,))
    return row["valor"] if row else ""


def obtener_todo() -> dict[str, str]:
    db = ConnectionManager()
    rows = db.fetchall("SELECT clave, valor FROM perfil")
    return {r["clave"]: r["valor"] for r in rows}
