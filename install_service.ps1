# Gwen Windows Pro — Registro de Auto-arranque (Task Scheduler)
param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = "Gwen_Windows_Pro"
$WscriptExe = "wscript.exe"
$SmartScript = Join-Path $ProjectRoot "launch_smart.vbs"

if ($Remove) {
    Write-Host "Eliminando tarea programada $TaskName..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F 2>&1 | Out-Null
    Write-Host "  Eliminada" -ForegroundColor Green
    exit 0
}

Write-Host "Registrando Gwen para auto-arranque tras login..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction -Execute $WscriptExe `
    -Argument "`"$SmartScript`"" `
    -WorkingDirectory $ProjectRoot

$trigger = New-ScheduledTaskTrigger -AtLogon

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Days 7)

Register-ScheduledTask -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Gwen Windows Pro — Asistente Telegram con IA" `
    -Force | Out-Null

Write-Host ""
Write-Host "Gwen arrancara automaticamente cada vez que inicies sesion." -ForegroundColor Green
Write-Host "  Reinicia la PC y al hacer login Gwen estara viva." -ForegroundColor Green
Write-Host ""
Write-Host "Para eliminar: .\install_service.ps1 -Remove" -ForegroundColor Gray
Write-Host "Para comprobar: schtasks /query /tn Gwen_Windows_Pro" -ForegroundColor Gray

