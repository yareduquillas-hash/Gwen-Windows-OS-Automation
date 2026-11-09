from __future__ import annotations

import logging
import os
import re
import threading
import uuid
from pathlib import Path

from modules.base import BaseModule

log = logging.getLogger("jarvis.archivos")

ARCHIVOS_BLOQUEADOS = (".env", ".db", ".log", ".pyc", ".key", ".pem", "__pycache__")
NOMBRES_SENSIBLES = {
    ".env",
    "gwen key.txt",
    "credentials.json",
    "google_token.json",
    "config_override.json",
    "jarvis_memoria.db",
}
MAX_INCOMING_FILE_BYTES = 50 * 1024 * 1024
_ultima_lista: dict[int, list[tuple[str, str]]] = {}

_pending_large_files: dict[int, list[str]] = {}
_lock_pending = threading.Lock()


def _ruta_segura(ruta: str, cfg) -> str | None:
    try:
        busca = Path(ruta).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not busca.is_file():
        return None
    nombre = busca.name.lower()
    if (
        nombre in NOMBRES_SENSIBLES
        or (
            any(token in nombre for token in ("credential", "token", "secret"))
            and busca.suffix.lower() in (".json", ".pem", ".p12", ".key")
        )
        or any(nombre.endswith(ext) for ext in ARCHIVOS_BLOQUEADOS)
        or nombre.startswith(".")
    ):
        return None

    permitidas = (
        Path(os.path.expanduser("~")).resolve(),
        Path(cfg.project_root).resolve(),
    )
    for raiz in permitidas:
        try:
            busca.relative_to(raiz)
            return str(busca)
        except ValueError:
            continue
    return None


def _buscar_archivo(termino: str, cfg) -> str | None:
    termino_lower = termino.lower()
    for raiz in (os.path.expanduser("~"), str(cfg.project_root)):
        for dirpath, dirs, archivos in os.walk(raiz):
            depth = dirpath.replace(raiz, "").count(os.sep)
            if depth > 4:
                continue
            skip_dirs = {".git", "node_modules", "__pycache__", ".cache", "appdata", "venv"}
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
            for archivo in archivos:
                if termino_lower in archivo.lower():
                    ruta = os.path.join(dirpath, archivo)
                    if _ruta_segura(ruta, cfg):
                        return ruta
    return None


def _directorio_seguro(ruta: str, cfg) -> str | None:
    try:
        directorio = Path(ruta).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not directorio.is_dir():
        return None
    bloqueados = {"appdata", "windows", "system32", "program files", ".git", "node_modules"}
    if any(parte.lower() in bloqueados for parte in directorio.parts):
        return None
    permitidas = (
        Path(os.path.expanduser("~")).resolve(),
        Path(cfg.project_root).resolve(),
    )
    for raiz in permitidas:
        try:
            directorio.relative_to(raiz)
            return str(directorio)
        except ValueError:
            continue
    return None


def save_incoming_file(message, bot, cfg) -> None:
    import time
    Path(cfg.archivos_dir).mkdir(parents=True, exist_ok=True)

    if message.document:
        archivo = message.document
        nombre = Path(archivo.file_name or f"documento_{int(time.time())}").name
    elif message.photo:
        archivo = message.photo[-1]
        nombre = f"foto_{int(time.time())}.jpg"
    else:
        return

    if not nombre or nombre.lower() in NOMBRES_SENSIBLES or nombre.startswith("."):
        bot.reply_to(message, "No acepto nombres de archivo sensibles u ocultos, Señor.")
        return

    try:
        file_info = bot.get_file(archivo.file_id)
        datos = bot.download_file(file_info.file_path)
        if len(datos) > MAX_INCOMING_FILE_BYTES:
            bot.reply_to(message, "El archivo supera el limite permitido de 50 MB, Señor.")
            return

        ruta = Path(cfg.archivos_dir).resolve() / f"{uuid.uuid4().hex}_{nombre}"
        with ruta.open("wb") as f:
            f.write(datos)
        size_kb = ruta.stat().st_size / 1024
        bot.reply_to(message, f"Archivo guardado, Señor: \"{nombre}\" ({size_kb:.1f} KB) en {cfg.archivos_dir}")
    except Exception as e:
        bot.reply_to(message, f"No pude guardar el archivo, Señor: {e}")


class ArchivosModule(BaseModule):
    nombre = "archivos"
    prioridad = 75

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        triggers_busqueda = (
            "busca y envíame", "busca y enviame", "busca el archivo",
            "encuentra y manda", "encuentra y mándame", "búscame y envíamelo",
            "buscame y enviame", "buscame el archivo", "encuentra el archivo",
            "mándame el archivo", "busca el documento", "busca los archivos",
            "busca las fotos", "busca el video", "busca el vídeo",
            "find and send", "/drive", "/transfer", "/ruta", "/saltar",
        )
        if any(p in t for p in triggers_busqueda):
            return True
        return any(t.startswith(p) for p in (
            "listame", "lístame", "que archivos hay en", "qué archivos hay en",
            "que hay en", "qué hay en", "muestrame archivos de", "muéstrame archivos de",
            "archivos de", "archivos en", "enviame ", "envíame ", "envia ",
            "envía ", "dame ", "send ", "pasame ", "pásame ",
        ))

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        ultima_lista = _ultima_lista.get(chat_id, [])

        for pref in ("listame", "lístame", "listame archivos", "lístame archivos",
                      "que archivos hay en", "qué archivos hay en", "que hay en",
                      "qué hay en", "muestrame archivos de", "muéstrame archivos de",
                      "archivos de", "archivos en"):
            if t.startswith(pref):
                dir_pedido = texto[len(pref):].strip().strip('"').strip("'") or "~"
                ruta_abs = _directorio_seguro(dir_pedido, cfg)
                if not ruta_abs:
                    bot.send_message(chat_id, f"No encuentro el directorio '{dir_pedido}', Señor.")
                    return True
                archivos = []
                for f in sorted(os.listdir(ruta_abs)):
                    full = os.path.join(ruta_abs, f)
                    if os.path.isfile(full) and _ruta_segura(full, cfg):
                        archivos.append((f, full))
                if not archivos:
                    bot.send_message(chat_id, f"No encuentro archivos en '{dir_pedido}', Señor.")
                    return True
                _ultima_lista[chat_id] = archivos
                lineas = [f"{i}. {nom}" for i, (nom, _) in enumerate(archivos, 1)]
                lineas.append("")
                lineas.append("Puede enviarme uno con: 'envíame el que dice X' o 'envíame número N'.")
                bot.send_message(chat_id, "Archivos encontrados:\n" + "\n".join(lineas))
                return True

        for pref in ("enviame ", "envíame ", "envia ", "envía ", "dame ", "send ", "pasame ", "pásame "):
            if t.startswith(pref):
                termino = texto[len(pref):].strip().strip('"').strip("'")
                if not termino:
                    bot.send_message(chat_id, "¿Qué archivo desea que le envíe, Señor?")
                    return True

                ruta_enviar = None
                nombre_mostrar = None

                if ultima_lista and termino.lower() in ("ese", "esa", "eso"):
                    nombre_mostrar, ruta_enviar = ultima_lista[-1]

                if not ruta_enviar and ultima_lista and termino.isdigit():
                    idx = int(termino) - 1
                    if 0 <= idx < len(ultima_lista):
                        nombre_mostrar, ruta_enviar = ultima_lista[idx]

                if not ruta_enviar and ultima_lista:
                    for q in ("el que dice ", "el que di"):
                        if termino.lower().startswith(q):
                            busq = termino.lower()[len(q):].strip()
                            for nom, rut in ultima_lista:
                                if busq in nom.lower():
                                    nombre_mostrar, ruta_enviar = nom, rut
                                    break

                if not ruta_enviar:
                    ruta_enviar = _ruta_segura(termino, cfg)
                    if ruta_enviar:
                        nombre_mostrar = os.path.basename(ruta_enviar)

                if not ruta_enviar:
                    ruta_enviar = _buscar_archivo(termino, cfg)
                    if ruta_enviar:
                        nombre_mostrar = os.path.basename(ruta_enviar)

                if not ruta_enviar and ultima_lista:
                    for nom, rut in ultima_lista:
                        if termino.lower() in nom.lower():
                            nombre_mostrar, ruta_enviar = nom, rut
                            break

                if ruta_enviar:
                    try:
                        with open(ruta_enviar, "rb") as f:
                            bot.send_document(chat_id, f, visible_file_name=nombre_mostrar)
                        bot.send_message(chat_id, f"Ahí tiene, Señor: {nombre_mostrar}")
                    except Exception as e:
                        bot.send_message(chat_id, f"No pude enviar el archivo, Señor: {e}")
                else:
                    bot.send_message(chat_id,
                        f"No encontré ningún archivo '{termino}' en su sistema, Señor.")
                return True

        # ── Manejar archivos grandes pendientes ──
        with _lock_pending:
            has_pending = bool(_pending_large_files.get(chat_id))
        if has_pending:
            return _handle_large_files_menu(t, texto, chat_id, bot, cfg)

        # ── Búsqueda con IA ──
        ia_triggers = (
            "busca y envíame", "busca y enviame", "busca el archivo",
            "encuentra y manda", "encuentra y mándame", "búscame y envíamelo",
            "buscame y enviame", "buscame el archivo", "encuentra el archivo",
            "mándame el archivo", "busca el documento", "busca los archivos",
            "busca las fotos", "busca el video", "busca el vídeo",
            "find and send",
        )
        if any(p in t for p in ia_triggers):
            query = texto.strip()
            for pfx in ia_triggers:
                if pfx in t:
                    query = texto.lower().split(pfx, 1)[-1].strip().strip('"').strip("'")
                    if not query:
                        query = texto.strip()
                    break
            _ai_file_search(query, chat_id, bot, cfg)
            return True

        return False


def _ai_file_search(query: str, chat_id: int, bot, cfg) -> None:
    from utils.security import es_peligroso
    from utils.file_uploader import split_files

    if es_peligroso(query):
        bot.send_message(chat_id, f"Esa consulta de búsqueda contiene comandos o parámetros bloqueados por seguridad, {cfg.user_title}.")
        return

    bot.send_message(chat_id, f"Buscando archivos locales, {cfg.user_title}...")
    paths = _buscar_archivos_permitidos(query, cfg)
    pequenos, grandes, __ = split_files(paths)

    if not pequenos and not grandes:
        bot.send_message(chat_id, f"No encontre archivos seguros para '{query}', Senor.")
        return

    enviados = 0
    for p in pequenos:
        try:
            nombre = os.path.basename(p)
            with open(p, "rb") as f:
                bot.send_document(chat_id, f, visible_file_name=nombre)
            enviados += 1
        except Exception as exc:
            log.warning("Error enviando %s: %s", p, exc)

    if grandes:
        with _lock_pending:
            _pending_large_files[chat_id] = list(grandes)

    if enviados > 0 or not grandes:
        bot.send_message(chat_id, f"Enviados {enviados} archivo(s), {cfg.user_title}.")

    if grandes:
        _show_large_files_menu(grandes, chat_id, bot, cfg)


def _buscar_archivos_permitidos(query: str, cfg, max_results: int = 30) -> list[str]:
    """Busca por nombre sin ejecutar comandos ni delegar acceso de disco a la IA."""
    terminos = [t for t in re.findall(r"[\w.-]+", query.lower()) if len(t) >= 2]
    if not terminos:
        return []

    home = Path(os.path.expanduser("~"))
    nombres_raiz = (
        "Desktop", "Escritorio", "Documents", "Documentos", "Downloads",
        "Descargas", "Pictures", "Imagenes", "Videos", "Music", "Musica",
    )
    raices = []
    for nombre in nombres_raiz:
        raiz = home / nombre
        if raiz.is_dir() and raiz not in raices:
            raices.append(raiz)

    encontrados: list[str] = []
    ignoradas = {".git", "node_modules", "__pycache__", ".cache", "appdata", "venv"}
    for raiz in raices:
        for dirpath, dirs, archivos in os.walk(raiz):
            dirs[:] = [d for d in dirs if d.lower() not in ignoradas]
            for nombre in archivos:
                if not any(termino in nombre.lower() for termino in terminos):
                    continue
                ruta = _ruta_segura(os.path.join(dirpath, nombre), cfg)
                if ruta:
                    encontrados.append(ruta)
                    if len(encontrados) >= max_results:
                        return encontrados
    return encontrados


def _parse_file_paths(texto: str) -> list[str]:
    paths = []
    for line in texto.splitlines():
        line = line.strip().strip('"').strip("'").strip("`")
        if not line:
            continue
        if re.match(r"^[A-Za-z]:[\\/].+\.\w{1,10}$", line):
            if os.path.isfile(line):
                paths.append(line)
            elif os.path.isfile(os.path.expanduser(line)):
                paths.append(os.path.expanduser(line))
    return paths


def _show_large_files_menu(rutas: list[str], chat_id: int, bot, cfg) -> None:
    from utils.file_uploader import get_file_size_mb

    lines = [f"Quedan {len(rutas)} archivo(s) grande(s) ({'>50MB'}):"]
    for i, r in enumerate(rutas, 1):
        mb = get_file_size_mb(r)
        lines.append(f"\n  {i}. {os.path.basename(r)} ({mb:.0f} MB)")
    lines.append("\n¿Que hago con cada uno?")
    lines.append("/drive    → Google Drive (necesita credenciales)")
    lines.append("/transfer → transfer.sh (temporal, 14 dias)")
    lines.append("/ruta     → Copiar ruta al portapapeles")
    lines.append("/saltar   → Ignorar este archivo")
    lines.append("/todo     → Aplicar a TODOS los pendientes")
    bot.send_message(chat_id, "\n".join(lines))


def _handle_large_files_menu(t: str, texto: str, chat_id: int, bot, cfg) -> bool:
    from utils.file_uploader import (
        GoogleDriveUploader, TransferShUploader, ClipboardPath, get_file_size_mb
    )

    with _lock_pending:
        pending = _pending_large_files.get(chat_id, [])
        if not pending:
            bot.send_message(chat_id, "No hay archivos pendientes, Senor.")
            return True

        path = pending[0]
    nombre = os.path.basename(path)
    mb = get_file_size_mb(path)

    action = None
    if t in ("/drive", "drive"):
        action = "drive"
    elif t in ("/transfer", "transfer"):
        action = "transfer"
    elif t in ("/ruta", "ruta"):
        action = "ruta"
    elif t in ("/saltar", "saltar"):
        action = "saltar"
    elif t in ("/todo", "todo"):
        action = "todo"

    if not action:
        match = re.match(r"^(\d+)$", t)
        if match and 1 <= int(match.group(1)) <= len(pending):
            idx = int(match.group(1)) - 1
            with _lock_pending:
                selected = pending.pop(idx)
                pending.insert(0, selected)
                snapshot = list(pending)
            _show_large_files_menu(snapshot, chat_id, bot, cfg)
            return True
        return False

    def _procesar_archivo(p: str) -> str | None:
        if action == "drive":
            drive = GoogleDriveUploader(
                str(cfg.google_credentials_file),
                str(cfg.google_token_file),
            )
            if not drive.is_available():
                return "GOOGLE_NO_CREDS"
            return drive.upload(p)

        if action == "transfer":
            ts = TransferShUploader()
            return ts.upload(p)

        if action == "ruta":
            ClipboardPath.copy(p)
            return "CLIPBOARD"

        if action == "saltar":
            return "SKIP"

        return None

    if action == "todo":
        with _lock_pending:
            to_process = list(_pending_large_files.pop(chat_id, []))
        results = []
        for p in to_process:
            bot.send_message(chat_id, f"Procesando {os.path.basename(p)} ({get_file_size_mb(p):.0f} MB)...")
            r = _procesar_archivo(p)
            results.append((os.path.basename(p), r, get_file_size_mb(p)))

        lines = ["Resultados:"]
        for nom, result, sz in results:
            if result and result not in ("SKIP", "CLIPBOARD", "GOOGLE_NO_CREDS"):
                lines.append(f"  ✅ {nom} ({sz:.0f}MB) → {result}")
            elif result == "CLIPBOARD":
                lines.append(f"  📋 {nom} — ruta copiada al portapapeles")
            elif result == "GOOGLE_NO_CREDS":
                lines.append(f"  ⚠️ {nom} — Google Drive no configurado. Use /transfer")
            elif result == "SKIP":
                lines.append(f"  ⏭️ {nom} — saltado")
            else:
                lines.append(f"  ❌ {nom} — fallo la subida")
        bot.send_message(chat_id, "\n".join(lines))
        return True

    bot.send_message(chat_id, f"Procesando {nombre} ({mb:.0f} MB)...")
    result = _procesar_archivo(path)
    with _lock_pending:
        pending = _pending_large_files.get(chat_id, [])
        if pending and pending[0] == path:
            pending.pop(0)
        quedan = list(pending)
        if not pending:
            _pending_large_files.pop(chat_id, None)

    if result and result not in ("SKIP", "CLIPBOARD", "GOOGLE_NO_CREDS"):
        bot.send_message(chat_id, f"✅ {nombre} → {result}")
    elif result == "CLIPBOARD":
        bot.send_message(chat_id, f"📋 Ruta de {nombre} copiada al portapapeles.")
    elif result == "GOOGLE_NO_CREDS":
        bot.send_message(chat_id,
            f"⚠️ Google Drive no configurado. Coloque credentials.json en {cfg.google_credentials_file}\n"
            "O use /transfer en su lugar.")
    elif result == "SKIP":
        bot.send_message(chat_id, f"⏭️ {nombre} saltado.")
    else:
        bot.send_message(chat_id, f"❌ No pude subir {nombre}. Intente /transfer o /ruta.")

    if quedan:
        _show_large_files_menu(quedan, chat_id, bot, cfg)
    else:
        bot.send_message(chat_id, "Todos los archivos procesados, Senor.")
    return True


MODULE_CLASS = ArchivosModule
