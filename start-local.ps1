param(
    [int]$Port = 7001
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
$RunFile = Join-Path $Root "run.py"
$LocalUrl = "http://127.0.0.1:$Port/"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Virtual environment not found: $Python"
}
if (-not (Test-Path -LiteralPath $RunFile -PathType Leaf)) {
    throw "Application entry point not found: $RunFile"
}

$listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($listener) {
    $ownerPid = ($listener | Select-Object -First 1).OwningProcess
    throw "Port $Port is already in use by PID $ownerPid. Stop that process or run: .\start-local.ps1 -Port 7002"
}

$env:FLASK_HOST = "127.0.0.1"
$env:FLASK_PORT = [string]$Port
$env:FLASK_DEBUG = "0"
$env:PUBLIC_BASE_URL = $LocalUrl.TrimEnd("/")

$pythonCode = "from run import app; app.run(host='127.0.0.1', port=$Port, debug=False, use_reloader=False)"

Write-Host "Starting Learn Words locally..." -ForegroundColor Cyan
Write-Host "Open: $LocalUrl" -ForegroundColor Green
Write-Host "Telegram bot polling is disabled for this local run."
Write-Host "Press Ctrl+C to stop the project." -ForegroundColor Yellow

Push-Location $Root
try {
    & $Python -c $pythonCode
    if ($LASTEXITCODE -ne 0) {
        throw "Local project stopped with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    Write-Host "Local project stopped." -ForegroundColor Cyan
}
