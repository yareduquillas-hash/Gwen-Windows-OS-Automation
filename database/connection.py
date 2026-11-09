from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger("jarvis.db")


class ConnectionManager:
    _instance: ConnectionManager | None = None
    _lock = threading.Lock()
    _write_lock = threading.Lock()
    _conn_lock = threading.RLock()

    def __new__(cls, db_path: Path | str = ":memory:") -> ConnectionManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._db_path = Path(db_path)
                    cls._instance._conn: sqlite3.Connection | None = None
        return cls._instance

    @property
    def conn(self) -> sqlite3.Connection:
        with self._conn_lock:
            if self._conn is None:
                self._conn = sqlite3.connect(
                    str(self._db_path), check_same_thread=False
                )
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA synchronous=NORMAL")
                self._conn.execute("PRAGMA cache_size=-8000")
                self._conn.execute("PRAGMA foreign_keys=ON")
                self._conn.row_factory = sqlite3.Row
            return self._conn

    @property
    def db_path(self) -> Path:
        return self._db_path

    def init(self) -> None:
        from .schema import apply_schema
        apply_schema(self.conn)

    def execute(self, sql: str, params: tuple | dict | None = None):
        is_write = self._is_write(sql)
        if is_write:
            with self._write_lock:
                with self._conn_lock:
                    cur = self.conn.execute(sql, params or ())
                    self.conn.commit()
                    return cur
        with self._conn_lock:
            return self.conn.execute(sql, params or ())

    @staticmethod
    def _is_write(sql: str) -> bool:
        """Detecta escrituras aun cuando el SQL tenga comentarios iniciales."""
        remaining = sql.lstrip()
        while remaining:
            if remaining.startswith("--"):
                newline = remaining.find("\n")
                remaining = remaining[newline + 1 :].lstrip() if newline >= 0 else ""
                continue
            if remaining.startswith("/*"):
                end = remaining.find("*/", 2)
                remaining = remaining[end + 2 :].lstrip() if end >= 0 else ""
                continue
            break
        return remaining.upper().startswith(
            ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "REPLACE", "ALTER")
        )

    def fetchone(self, sql: str, params: tuple | dict | None = None):
        with self._conn_lock:
            return self.conn.execute(sql, params or ()).fetchone()

    def fetchall(self, sql: str, params: tuple | dict | None = None):
        with self._conn_lock:
            return self.conn.execute(sql, params or ()).fetchall()

    def close(self) -> None:
        with self._write_lock:
            with self._conn_lock:
                if self._conn:
                    self._conn.close()
                    self._conn = None

    @classmethod
    def close_instance(cls) -> None:
        instance = cls._instance
        if instance is not None:
            instance.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            with self._conn_lock:
                self.conn.commit()
