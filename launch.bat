@echo off
title Gwen Windows Pro
color 0A

cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║          Gwen Windows Pro                   ║
echo ║          v2.0 — Visual AI Edition            ║
echo ╚══════════════════════════════════════════════╝
echo.

:: Verificar .env
if not exist ".env" (
    echo [!] .env no encontrado. Copiando desde .env.example...
    copy ".env.example" ".env" >nul
    echo [!] EDITA el archivo .env con tu token y chat_id de Telegram
    notepad .env
    echo.
)

:: Diagnóstico rápido
powershell -ExecutionPolicy Bypass -File ".\check_deps.ps1"

echo.
echo ══════════════════════════════════════════════
echo   Iniciando Gwen en segundo plano (sin consola)...
echo ══════════════════════════════════════════════
echo.

start "" pythonw main.py

echo Gwen está en ejecución en segundo plano.
timeout /t 3 >nul
