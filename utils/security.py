from __future__ import annotations
import re
import time as _time

PELIGRO_COMANDOS = (
    "rm -rf /", "sudo rm -rf", "mkfs", "dd if=",
    ":(){:|:&};:", "format c:", "format ",
    "shutdown /s", "del /f /s", "rd /s /q C:\\",
    "Remove-Item -Recurse", "Remove-Item -Force",
    "reg delete", "bcdedit", "netsh firewall",
    "cipher /w", "diskpart", "del /f /s /q",
    "rd /s /q", "rmdir /s",
)

_SHELL_METACHAR = re.compile(r'[;&|`${}()<>]')
_MAX_INPUT_LEN = 2000

def es_peligroso(texto: str) -> bool:
    tl = texto.lower()
    return any(p.lower() in tl for p in PELIGRO_COMANDOS)

def sanitizar_shell(texto: str) -> str:
    texto = texto[:_MAX_INPUT_LEN]
    texto = texto.replace('\x00', '')
    texto = texto.replace('\n', ' ').replace('\r', ' ')
    texto = _SHELL_METACHAR.sub('', texto)
    return texto.strip()

def es_longitud_valida(texto: str) -> bool:
    return len(texto) <= _MAX_INPUT_LEN
