# Gwen Windows Pro - Installer
# Run PowerShell as administrator only when firewall or auto-start is needed.

param(
    [switch]$SkipPip,
    [switch]$SkipWinget,
    [switch]$SkipService
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Gwen Windows Pro - Installation" -ForegroundColor Cyan

Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python was not found. Install Python 3.10 or newer."
    exit 1
}
Write-Host (python --version 2>&1) -ForegroundColor Green

Write-Host "[2/7] Checking pip..." -ForegroundColor Yellow
python -m pip --version

if (-not $SkipPip) {
    Write-Host "[3/7] Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
} else {
    Write-Host "[3/7] Skipping pip installation." -ForegroundColor Gray
}

Write-Host "[4/7] Checking ffmpeg..." -ForegroundColor Yellow
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg -and -not $SkipWinget) {
    winget install -e --id Gyan.FFmpeg --accept-source-agreements
    $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
}
if ($ffmpeg) {
    Write-Host "ffmpeg is available." -ForegroundColor Green
} else {
    Write-Warning "ffmpeg is not available. Voice features may be disabled."
}

Write-Host "[5/7] Checking GeForce NOW..." -ForegroundColor Yellow
Write-Host "The current engine reads NVIDIA debug.log and does not require OCR." -ForegroundColor Green

Write-Host "[6/7] Checking optional OpenCode CLI..." -ForegroundColor Yellow
$opencode = Get-Command opencode -ErrorAction SilentlyContinue
if ($opencode) {
    Write-Host "OpenCode CLI is available." -ForegroundColor Green
} else {
    Write-Warning "OpenCode CLI is not installed. The HTTP IA providers remain available."
}

Write-Host "[7/7] Preparing local configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warning "Created .env from .env.example. Configure secrets before starting."
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

$dirs = @("data", "data\descargas", "data\archivos", "data\cache\tts", "data\assets")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "Installation checks completed." -ForegroundColor Green
Write-Host "Next: configure secrets, run python migrate_secrets.py, then .\check_deps.ps1 and python main.py." -ForegroundColor Gray

if (-not $SkipService) {
    $response = Read-Host "Install auto-start task now? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        & (Join-Path -Path $ProjectRoot -ChildPath "install_service.ps1")
    }
}
