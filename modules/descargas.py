from __future__ import annotations

import logging
import ipaddress
import os
import pathlib
import socket
import shutil
import stat
import tempfile
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from modules.base import BaseModule

log = logging.getLogger("jarvis.descargas")

MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024
MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024


def _host_publico(hostname: str) -> bool:
    """Evita destinos locales para reducir SSRF desde el comando de descarga."""
    hostname = hostname.strip("[]").lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except OSError:
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    return True


def _asegurar_dir(cfg) -> None:
    pathlib.Path(cfg.descargas_dir).mkdir(parents=True, exist_ok=True)


def _descargar_archivo(url: str, chat_id: int, cfg, bot) -> bool:
    _asegurar_dir(cfg)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        bot.send_message(chat_id, "Solo acepto URLs HTTP o HTTPS, Señor.")
        return False
    if parsed.username or parsed.password or not parsed.hostname or not _host_publico(parsed.hostname):
        bot.send_message(chat_id, "El destino de la descarga no es publico o no es valido, Señor.")
        return False

    nombre = Path(urllib.parse.unquote(parsed.path)).name
    nombre = nombre.replace("\x00", "").strip()
    if not nombre or nombre in (".", ".."):
        nombre = "descarga"
    nombre = "".join("_" if char in '<>:"/\\|?*' else char for char in nombre)
    nombre = nombre[:180]

    download_dir = Path(cfg.descargas_dir).resolve()
    ruta = (download_dir / nombre).resolve()
    try:
        ruta.relative_to(download_dir)
    except ValueError:
        bot.send_message(chat_id, "La ruta de descarga no es valida, Señor.")
        return False
    if ruta.exists():
        ruta = download_dir / f"{ruta.stem}_{uuid.uuid4().hex[:8]}{ruta.suffix}"

    temporal = None
    try:
        bot.send_message(chat_id, f"Descargando {nombre}...")
        with urllib.request.urlopen(url, timeout=30) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise ValueError("el archivo supera el limite de 500 MB")

            with tempfile.NamedTemporaryFile(
                dir=download_dir, prefix=".download-", delete=False
            ) as output:
                temporal = Path(output.name)
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError("el archivo supera el limite de 500 MB")
                    output.write(chunk)

        os.replace(temporal, ruta)
        size_mb = ruta.stat().st_size / 1024 / 1024
        if size_mb == 0:
            ruta.unlink(missing_ok=True)
            bot.send_message(chat_id, "El archivo descargado está vacío, Señor.")
            return False
        bot.send_message(chat_id, f"Descargado: {nombre} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        if temporal:
            temporal.unlink(missing_ok=True)
        bot.send_message(chat_id, f"No pude descargar, Señor: {e}")
        return False


def _instalar_programa(nombre: str, chat_id: int, cfg, bot) -> None:
    import subprocess
    _asegurar_dir(cfg)
    download_dir = Path(cfg.descargas_dir).resolve()
    ruta = (download_dir / Path(nombre).name).resolve()
    try:
        ruta.relative_to(download_dir)
    except ValueError:
        bot.send_message(chat_id, "La ruta del instalador no es valida, Señor.")
        return
    if not ruta.is_file():
        bot.send_message(chat_id, f"No encuentro \"{nombre}\" en la carpeta de descargas, Señor.")
        return

    if os.getenv("JARVIS_ALLOW_INSTALLERS", "false").lower() not in ("1", "true", "yes"):
        bot.send_message(
            chat_id,
            "La ejecucion automatica de instaladores esta deshabilitada por seguridad, Señor.",
        )
        return

    lower_name = ruta.name.lower()
    ext = ruta.suffix.lower()
    try:
        if ext == ".deb":
            if os.name != "posix":
                bot.send_message(chat_id, f"Los archivos .deb solo pueden instalarse en entornos Linux, {cfg.user_title}.")
                return
            bot.send_message(chat_id, f"Instalando {nombre}...")
            r = subprocess.run(["sudo", "dpkg", "-i", str(ruta)], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                subprocess.run(["sudo", "apt", "install", "-f", "-y"], capture_output=True, timeout=60)
            bot.send_message(chat_id, f"Instalado {nombre}, Señor.")
        elif ext in (".exe", ".msi"):
            bot.send_message(chat_id, f"Ejecutando instalador {nombre}...")
            if ext == ".exe":
                command = [str(ruta), "/S"]
            else:
                command = ["msiexec.exe", "/i", str(ruta), "/quiet", "/norestart"]
            subprocess.run(command, shell=False, capture_output=True, timeout=120)
            bot.send_message(chat_id, f"Instalador ejecutado, Señor.")
        elif ext in (".appimage", ".sh", ".run", ".bin"):
            os.chmod(ruta, 0o755)
            bot.send_message(chat_id, f"Permisos de ejecución concedidos a {nombre}, Señor.")
        elif lower_name.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".tar")):
            import tarfile
            dest = download_dir / ruta.name.rsplit(".", 1)[0]
            _extract_tar_safely(ruta, dest)
            bot.send_message(chat_id, f"Extraído {nombre} en {dest}, Señor.")
        elif ext == ".zip":
            import zipfile
            dest = download_dir / ruta.stem
            _extract_zip_safely(ruta, dest)
            bot.send_message(chat_id, f"Extraído {nombre} en {dest}, Señor.")
        else:
            bot.send_message(chat_id, f"No reconozco el formato de {nombre}, Señor.")
    except Exception as e:
        bot.send_message(chat_id, f"Error al instalar {nombre}: {e}")


def _safe_archive_target(destination: Path, member_name: str) -> Path:
    destination = destination.resolve()
    target = (destination / member_name).resolve()
    target.relative_to(destination)
    return target


def _extract_zip_safely(source: Path, destination: Path) -> None:
    import zipfile

    destination.mkdir(parents=True, exist_ok=True)
    total_size = 0
    with zipfile.ZipFile(source, "r") as archive:
        for member in archive.infolist():
            target = _safe_archive_target(destination, member.filename)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            total_size += member.file_size
            if total_size > MAX_EXTRACTED_BYTES:
                raise ValueError("el contenido extraido supera el limite de 1 GB")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source_file, target.open("wb") as target_file:
                shutil.copyfileobj(source_file, target_file)


def _extract_tar_safely(source: Path, destination: Path) -> None:
    import tarfile

    destination.mkdir(parents=True, exist_ok=True)
    total_size = 0
    with tarfile.open(source) as archive:
        for member in archive.getmembers():
            target = _safe_archive_target(destination, member.name)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or stat.S_ISLNK(member.mode):
                raise ValueError(f"tipo de miembro TAR no permitido: {member.name}")
            total_size += member.size
            if total_size > MAX_EXTRACTED_BYTES:
                raise ValueError("el contenido extraido supera el limite de 1 GB")
            source_file = archive.extractfile(member)
            if source_file is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source_file, target.open("wb") as target_file:
                shutil.copyfileobj(source_file, target_file)


class DescargasModule(BaseModule):
    nombre = "descargas"
    prioridad = 72

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        return any(t.startswith(p) for p in (
            "descarga ", "descargar ", "descargame ",
            "instala ", "instalar ", "instalame ",
        )) or t in ("lista descargas", "listar descargas", "descargas",
                     "que descargas tengo", "qué descargas tengo",
                     "muestrame las descargas", "muéstrame las descargas")

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()

        for sep in (" e instala", " e instalalo", " e instalar", " y instala", " y instalalo", " y instalar"):
            if sep in t:
                if os.getenv("JARVIS_ALLOW_INSTALLERS", "false").lower() not in ("1", "true", "yes"):
                    bot.send_message(
                        chat_id,
                        "La descarga con instalacion automatica esta deshabilitada por seguridad, Señor.",
                    )
                    return True
                partes = t.split(sep, 1)
                url = partes[0].replace("descarga", "", 1).replace("descargar", "", 1).replace("descargame", "", 1).strip().strip('"').strip("'")
                if not url or not url.startswith("http"):
                    bot.send_message(chat_id, "Debe proporcionar una URL válida, Señor.")
                    return True
                if _descargar_archivo(url, chat_id, cfg, bot):
                    nombre = url.split("/")[-1].split("?")[0] or "archivo"
                    _instalar_programa(nombre, chat_id, cfg, bot)
                return True

        for pref in ("descarga ", "descargar ", "descargame "):
            if t.startswith(pref):
                url = texto[len(pref):].strip().strip('"').strip("'")
                if not url:
                    bot.send_message(chat_id, "¿Qué URL desea que descargue, Señor?")
                    return True
                _descargar_archivo(url, chat_id, cfg, bot)
                return True

        for pref in ("instala ", "instalar ", "instalame "):
            if t.startswith(pref):
                nombre = texto[len(pref):].strip().strip('"').strip("'")
                if not nombre:
                    bot.send_message(chat_id, "¿Qué programa desea instalar, Señor?")
                    return True
                _instalar_programa(nombre, chat_id, cfg, bot)
                return True

        if t in ("lista descargas", "listar descargas", "descargas",
                  "que descargas tengo", "qué descargas tengo",
                  "muestrame las descargas", "muéstrame las descargas"):
            _asegurar_dir(cfg)
            archivos = [f for f in os.listdir(str(cfg.descargas_dir))
                        if os.path.isfile(os.path.join(str(cfg.descargas_dir), f))]
            if not archivos:
                bot.send_message(chat_id, "No hay archivos en descargas, Señor.")
                return True
            lineas = [f"• {f} ({os.path.getsize(os.path.join(str(cfg.descargas_dir), f)) / 1024 / 1024:.1f} MB)" for f in archivos]
            bot.send_message(chat_id, "Archivos en descargas:\n" + "\n".join(lineas))
            return True

        return False


def handle_descargas_command(message, bot, cfg) -> None:
    _asegurar_dir(cfg)
    archivos = [f for f in os.listdir(str(cfg.descargas_dir))
                if os.path.isfile(os.path.join(str(cfg.descargas_dir), f))]
    if not archivos:
        bot.reply_to(message, "No hay archivos en descargas, Señor.")
        return
    lineas = [f"• {f} ({os.path.getsize(os.path.join(str(cfg.descargas_dir), f)) / 1024 / 1024:.1f} MB)" for f in archivos]
    bot.reply_to(message, "Archivos en descargas:\n" + "\n".join(lineas))


def handle_descarga_command(message, bot, cfg) -> None:
    partes = (message.text or "").split(maxsplit=1)
    if len(partes) < 2:
        bot.reply_to(message, "Indíqueme la URL a descargar, Señor (ej: /descarga https://...).")
        return
    _descargar_archivo(partes[1].strip().strip('"').strip("'"), message.chat.id, cfg, bot)


def handle_instala_command(message, bot, cfg) -> None:
    partes = (message.text or "").split(maxsplit=1)
    if len(partes) < 2:
        bot.reply_to(message, "Indíqueme el nombre del archivo a instalar (ej: /instala programa.deb).")
        return
    _instalar_programa(partes[1].strip().strip('"').strip("'"), message.chat.id, cfg, bot)


MODULE_CLASS = DescargasModule
