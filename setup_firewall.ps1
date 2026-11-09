# Script de habilitación de Firewall para Gwen API (Puerto 8000)
# Requiere ejecutar como Administrador

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[!] Por favor ejecuta este script como Administrador." -ForegroundColor Red
    exit 1
}

$rule = Get-NetFirewallRule -DisplayName "Gwen API Server" -ErrorAction SilentlyContinue

if ($null -eq $rule) {
    New-NetFirewallRule -DisplayName "Gwen API Server" `
        -Direction Inbound -Protocol TCP -LocalPort 8000 `
        -Action Allow -Profile Private -RemoteAddress LocalSubnet
    Write-Host "[OK] Regla de Firewall creada: solo perfil privado y subred local." -ForegroundColor Green
} else {
    Set-NetFirewallRule -DisplayName "Gwen API Server" `
        -Action Allow -Profile Private -RemoteAddress LocalSubnet
    Write-Host "[OK] Regla existente actualizada: solo perfil privado y subred local." -ForegroundColor Green
}
