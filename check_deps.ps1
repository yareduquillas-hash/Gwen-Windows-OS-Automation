# JARVIS Windows Pro — Diagnóstico de Dependencias
# Uso: .\check_deps.ps1                → chequeo completo
#      .\check_deps.ps1 -Module voz    → solo módulo voz
#      .\check_deps.ps1 -Json          → salida JSON
#      .\check_deps.ps1 -Verbose       → detalles extra

param(
    [string]$Module,
    [switch]$Json,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# ── Definición de dependencias por módulo ──
$ModuleDeps = @{
    "core"        = @{ system = @("python","pip"); pip = @("pytelegrambotapi","python-dotenv") }
    "voz"         = @{ system = @("ffmpeg"); pip = @("edge-tts","pydub","SpeechRecognition","pyaudio") }
    "bateria"     = @{ system = @(); pip = @() }
    "medios"      = @{ system = @(); pip = @("pyautogui") }
    "volumen"     = @{ system = @(); pip = @("pycaw","comtypes") }
    "clipboard"   = @{ system = @(); pip = @("pyperclip") }
    "capturas"    = @{ system = @(); pip = @("pyautogui","Pillow") }
    "ventanas"    = @{ system = @(); pip = @("pygetwindow") }
    "procesos"    = @{ system = @(); pip = @("psutil") }
    "sistema_info"= @{ system = @(); pip = @("psutil") }
    "notificaciones" = @{ system = @(); pip = @("win10toast") }
    "archivos"    = @{ system = @(); pip = @() }
    "descargas"   = @{ system = @(); pip = @() }
    "memoria"     = @{ system = @(); pip = @() }
    "secciones"   = @{ system = @(); pip = @() }
    "tareas"      = @{ system = @(); pip = @() }
    "protocolos"  = @{ system = @(); pip = @() }
    "ai"          = @{ system = @("git","opencode"); pip = @() }
    "geforcenow"  = @{ system = @(); pip = @("psutil","pygetwindow") }
}

# ── Funciones de verificación ──
function Test-SystemDep($name) {
    return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

function Test-PipDep($name) {
    try {
        $null = pip show $name 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-EnvVar($name) {
    if (-not (Test-Path ".env")) { return $false }
    $content = Get-Content ".env" -Raw
    $pattern = "^$name\s*=\s*(.+)$"
    $match = [regex]::Match($content, $pattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
    if (-not $match.Success) { return $false }
    $val = $match.Groups[1].Value.Trim().Trim('"').Trim("'")
    return -not [string]::IsNullOrEmpty($val) -and $val -notlike "pon_tu_*" -and $val -ne "0"
}

# ── Verificar un módulo ──
function Check-Module($modName) {
    $deps = $ModuleDeps[$modName]
    if (-not $deps) { return @{ name = $modName; status = "unknown" } }

    $missingSys = @()
    $missingPip = @()
    $warnings = @()

    foreach ($s in $deps.system) {
        if (-not (Test-SystemDep $s)) {
            $missingSys += $s
        }
    }
    foreach ($p in $deps.pip) {
        if (-not (Test-PipDep $p)) {
            $missingPip += $p
        }
    }

    $status = "ok"
    if ($missingSys.Count -gt 0 -or $missingPip.Count -gt 0) {
        $status = "fail"
    }

    return @{
        name = $modName
        status = $status
        missing_sys = $missingSys
        missing_pip = $missingPip
        warnings = $warnings
    }
}

# ── Si se pidió un módulo específico ──
if ($Module) {
    $result = Check-Module $Module
    if ($Json) {
        $result | ConvertTo-Json -Depth 3
    } else {
        Write-Host "Módulo: $($result.name)" -ForegroundColor Cyan
        Write-Host "Estado: $($result.status)" -ForegroundColor $(if($result.status -eq "ok"){"Green"}else{"Red"})
        if ($result.missing_sys.Count -gt 0) {
            Write-Host "Sistema faltante: $($result.missing_sys -join ', ')" -ForegroundColor Red
            if ("opencode" -in $result.missing_sys) {
                Write-Host "  → Instalar: npm install -g opencode" -ForegroundColor Gray
            }
            if ("ffmpeg" -in $result.missing_sys) {
                Write-Host "  → Instalar: winget install Gyan.FFmpeg" -ForegroundColor Gray
            }
        }
        if ($result.missing_pip.Count -gt 0) {
            Write-Host "Pip faltante: $($result.missing_pip -join ', ')" -ForegroundColor Red
            Write-Host "  → Instalar: pip install $($result.missing_pip -join ' ')" -ForegroundColor Gray
        }
    }
    exit
}

# ── Chequeo completo ──
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  JARVIS Windows Pro — Diagnóstico de Dependencias" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Sistema
Write-Host "┌─ SISTEMA ──────────────────────────────────────────┐"
$sysDeps = @(
    @{n="Python"; c="python --version 2>&1"},
    @{n="pip"; c="pip --version 2>&1"},
    @{n="ffmpeg"; c=""},
    @{n="git"; c=""},
    @{n="opencode CLI"; c=""}
)
$sysOk = 0; $sysFail = 0
foreach ($d in $sysDeps) {
    $ok = Test-SystemDep ($d.n -split " ")[0].ToLower()
    if ($ok) {
        Write-Host " ✅ $($d.n)" -ForegroundColor Green
        $sysOk++
    } else {
        Write-Host " ❌ $($d.n)" -ForegroundColor Red
        $sysFail++
    }
}
Write-Host "└────────────────────────────────────────────────────┘"
Write-Host ""

# Pip por grupo
$groups = @{
    "CORE" = @("pytelegrambotapi","python-dotenv")
    "VOZ" = @("edge-tts","pydub","SpeechRecognition","pyaudio")
    "WINDOWS" = @("pyautogui","pygetwindow","pycaw","comtypes","psutil","pyperclip","Pillow","win10toast")
    "GEFORCE NOW" = @("psutil","pygetwindow")
    "API SERVER"  = @("fastapi","uvicorn","websockets")
}

foreach ($g in $groups.GetEnumerator()) {
    Write-Host "┌─ PIP: $($g.Key) ────────────────────────────────────┐"
    $ok = 0; $fail = 0
    foreach ($p in $g.Value) {
        if (Test-PipDep $p) {
            Write-Host " ✅ $p" -ForegroundColor Green
            $ok++
        } else {
            Write-Host " ❌ $p" -ForegroundColor Red
            $fail++
        }
    }
    Write-Host "└────────────────────────────────────────────────────┘"
    Write-Host ""
}

# Configuración
Write-Host "┌─ CONFIGURACIÓN ────────────────────────────────────┐"
$envVars = @("JARVIS_TELEGRAM_TOKEN","JARVIS_TELEGRAM_CHAT_ID","SPOTIFY_CLIENT_ID","GFN_EXECUTABLE")
$envOk = 0; $envFail = 0
if (Test-Path ".env") {
    Write-Host " ✅ .env encontrado" -ForegroundColor Green
    $envOk++
    foreach ($v in $envVars) {
        if (Test-EnvVar $v) {
            Write-Host " ✅ $v" -ForegroundColor $(if($v -like "*SPOTIFY*" -or $v -like "*GFN*"){"DarkYellow"}else{"Green"})
            $envOk++
        } else {
            $icon = if ($v -like "*SPOTIFY*" -or $v -like "*GFN*") { "⚠️" } else { "❌" }
            $color = if ($v -like "*SPOTIFY*" -or $v -like "*GFN*") { "DarkYellow" } else { "Red" }
            Write-Host " $icon $v (no configurado)" -ForegroundColor $color
            if ($v -notlike "*SPOTIFY*" -and $v -notlike "*GFN*") { $envFail++ }
        }
    }
} else {
    Write-Host " ❌ .env no encontrado. Copie .env.example a .env" -ForegroundColor Red
    $envFail++
}
Write-Host "└────────────────────────────────────────────────────┘"
Write-Host ""

# Módulos
Write-Host "┌─ ESTADO POR MÓDULO ───────────────────────────────┐"
$modOk = 0; $modFail = 0; $modWarn = 0
$results = @()
foreach ($mod in $ModuleDeps.Keys | Sort-Object) {
    $r = Check-Module $mod
    $results += $r
    $icon = if ($r.status -eq "ok") { "✅" } else { "❌" }
    $color = if ($r.status -eq "ok") { "Green" } else { "Red" }
    Write-Host " $icon $($mod.PadRight(20))" -ForegroundColor $color -NoNewline
    if ($mod -in @("bateria","volumen","clipboard","capturas","ventanas","procesos","sistema_info","notificaciones")) {
        Write-Host ""
    } elseif ($mod -in @("geforcenow","descargas","archivos","memoria","secciones")) {
        Write-Host ""
    } else {
        Write-Host ""
    }
    if ($r.status -eq "ok") { $modOk++ } else { $modFail++ }
}
Write-Host "└────────────────────────────────────────────────────┘"
Write-Host ""

# Json output
if ($Json) {
    $results | ConvertTo-Json -Depth 3
    exit
}

# Resumen
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
$totalOk = $modOk; $totalFail = $modFail
Write-Host "  Resultado: $totalOk ✅ | $totalFail ❌" -ForegroundColor $(if($totalFail -eq 0){"Green"}else{"Yellow"})
Write-Host "  Módulos funcionales: $totalOk / $($ModuleDeps.Count)" -ForegroundColor White

if ($totalFail -gt 0) {
    Write-Host ""
    Write-Host "  Módulos NO funcionales:" -ForegroundColor Red
    foreach ($r in $results) {
        if ($r.status -ne "ok") {
            Write-Host "    ❌ $($r.name)" -ForegroundColor Red
            if ($r.missing_sys.Count -gt 0) {
                Write-Host "       Sistema: $($r.missing_sys -join ', ')" -ForegroundColor Gray
            }
            if ($r.missing_pip.Count -gt 0) {
                Write-Host "       Pip: pip install $($r.missing_pip -join ' ')" -ForegroundColor Gray
            }
        }
    }
}

Write-Host "──────────────────────────────────────────────────────────" -ForegroundColor Cyan
if ($totalFail -eq 0) {
    Write-Host "  ¡Todo listo! Ejecute: python main.py" -ForegroundColor Green
} else {
    Write-Host "  Para instalar lo que falta, ejecute: .\setup.ps1" -ForegroundColor Yellow
}
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
