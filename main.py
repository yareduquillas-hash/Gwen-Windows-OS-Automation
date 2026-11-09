from __future__ import annotations

import os
import sys
from pathlib import Path

from config import JarvisConfig
from utils.logging_config import setup_logging


_SINGLETON_SOCKET = None


def _asegurar_instancia_unica(port: int = 48729) -> bool:
    global _SINGLETON_SOCKET
    import socket
    try:
        _SINGLETON_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _SINGLETON_SOCKET.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def _notificar_duplicado() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "Gwen ya se encuentra en línea en segundo plano.",
                "Gwen Windows Pro",
                64,
            )
        except Exception:
            pass


def main() -> None:
    if not _asegurar_instancia_unica():
        _notificar_duplicado()
        sys.exit(0)

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)
    try:
        cfg = JarvisConfig().validated()
    except ValueError as exc:
        print(str(exc))
        print("\n💡 Copia .env.example a .env y configura las variables.")
        sys.exit(1)

    from config import HotConfig

    hot_cfg = HotConfig(cfg)

    setup_logging(hot_cfg.log_level, log_dir=hot_cfg.log_dir)
    hot_cfg.ensure_dirs()

    from database.connection import ConnectionManager
    db = ConnectionManager(hot_cfg.db_path)
    db.init()
    from database.schema import purgar_datos_antiguos
    purgar_datos_antiguos(db.conn)

    from jarvis import JarvisBot
    bot = JarvisBot(hot_cfg)

    import threading
    if not hot_cfg.api_key or len(hot_cfg.api_key) < 32:
        print("[!] API Server deshabilitado: JARVIS_API_KEY ausente o demasiado corta.")
    else:
        try:
            from api_server import run_api_server, set_bot_context
            set_bot_context(bot, hot_cfg)
            api_thread = threading.Thread(
                target=run_api_server,
                kwargs={
                    "host": hot_cfg.api_host,
                    "port": hot_cfg.api_port,
                    "ssl_keyfile": hot_cfg.api_ssl_keyfile or None,
                    "ssl_certfile": hot_cfg.api_ssl_certfile or None,
                },
                daemon=True,
            )
            api_thread.start()
            print(f"[+] Gwen API Server ejecutándose en {hot_cfg.api_host}:{hot_cfg.api_port}")
        except ImportError as exc:
            print(f"[!] API Server deshabilitado (dependencia no instalada: {exc})")

    bot.run()



if __name__ == "__main__":
    main()
