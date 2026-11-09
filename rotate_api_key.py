"""Genera una clave nueva para la API local y la guarda en Credential Manager."""
from __future__ import annotations

import secrets
import argparse

from utils.secrets import SecretStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--show",
        action="store_true",
        help="muestra la clave una sola vez para introducirla en Android",
    )
    args = parser.parse_args()
    store = SecretStore()
    if not store.available:
        print("Windows Credential Manager no esta disponible.")
        return 1
    token = secrets.token_urlsafe(32)
    if not store.set("JARVIS_API_KEY", token) or store.get("JARVIS_API_KEY") != token:
        print("No se pudo guardar la nueva clave.")
        return 1
    print("Nueva JARVIS_API_KEY almacenada en Credential Manager.")
    if args.show:
        print("Muestra unica para introducirla en Android, no la compartas:")
        print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
