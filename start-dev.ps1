<#
.SYNOPSIS
    Starts (or restarts) everything needed to run the Ticket System locally:
    PostgreSQL service, the FastAPI backend, and the Vite frontend dev server.

.PARAMETER Restart
    Kill any backend/frontend processes already listening on their ports first,
    then start fresh. Without this switch, already-running services are left alone.

.EXAMPLE
    .\start-dev.ps1
    .\start-dev.ps1 -Restart
#>
param(
    [switch]$Restart
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$BackendPort = 8000
$FrontendPort = 5173
$PgServiceName = "postgresql-x64-17"

function Write-Section($text) {
    Write-Host ""
    Write-Host "== $text ==" -ForegroundColor Cyan
}

function Stop-ProcessOnPort([int]$Port) {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        Write-Host "  Stopping process $procId on port $Port" -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    if ($procIds) { Start-Sleep -Seconds 1 }
}

function Test-PortListening([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

# --- 1. PostgreSQL -----------------------------------------------------------
Write-Section "PostgreSQL"
$pgService = Get-Service -Name $PgServiceName -ErrorAction SilentlyContinue
if (-not $pgService) {
    Write-Host "Service '$PgServiceName' not found. If your Postgres install uses a different" -ForegroundColor Red
    Write-Host "service name, edit `$PgServiceName at the top of this script, or start it yourself." -ForegroundColor Red
} elseif ($pgService.Status -eq "Running") {
    Write-Host "Already running." -ForegroundColor Green
} else {
    Write-Host "Starting service '$PgServiceName'..." -ForegroundColor Yellow
    try {
        Start-Service -Name $PgServiceName -ErrorAction Stop
        Write-Host "Started." -ForegroundColor Green
    } catch {
        Write-Host "Could not start it automatically (likely needs an elevated/admin PowerShell)." -ForegroundColor Red
        Write-Host "Start it yourself: Start-Service $PgServiceName  (from an admin prompt)" -ForegroundColor Red
    }
}

# --- 2. Optional restart -------------------------------------------------------
if ($Restart) {
    Write-Section "Restarting backend / frontend"
    Stop-ProcessOnPort $BackendPort
    Stop-ProcessOnPort $FrontendPort
}

# --- 3. Backend (FastAPI / uvicorn) -------------------------------------------
Write-Section "Backend (FastAPI)"
if (Test-PortListening $BackendPort) {
    Write-Host "Already running on port $BackendPort." -ForegroundColor Green
} else {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Host "No virtualenv found at .venv\Scripts\python.exe." -ForegroundColor Red
        Write-Host "Set it up first: python -m venv .venv; .venv\Scripts\pip install -e `".[dev]`"" -ForegroundColor Red
    } else {
        Write-Host "Starting on port $BackendPort in a new window..." -ForegroundColor Yellow
        $cmd = "Set-Location '$RepoRoot'; & '$venvPython' -m uvicorn app.main:app --reload --port $BackendPort"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal
    }
}

# --- 4. Frontend (Vite) --------------------------------------------------------
Write-Section "Frontend (Vite)"
if (Test-PortListening $FrontendPort) {
    Write-Host "Already running on port $FrontendPort." -ForegroundColor Green
} else {
    $frontendDir = Join-Path $RepoRoot "frontend"
    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "frontend\node_modules not found." -ForegroundColor Red
        Write-Host "Set it up first: cd frontend; npm install" -ForegroundColor Red
    } else {
        Write-Host "Starting on port $FrontendPort in a new window..." -ForegroundColor Yellow
        $cmd = "Set-Location '$frontendDir'; npm run dev"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal
    }
}

Write-Section "Done"
Write-Host "Backend:   http://localhost:$BackendPort  (interactive docs at /docs)"
Write-Host "Frontend:  http://localhost:$FrontendPort"
Write-Host ""
Write-Host "Re-run with -Restart to force-restart the backend/frontend windows." -ForegroundColor DarkGray
