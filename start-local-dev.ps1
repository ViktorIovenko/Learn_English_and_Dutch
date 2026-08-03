param(
    [int]$Port = 7001
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Virtual environment not found: $Python"
}

$env:FLASK_HOST = "127.0.0.1"
$env:FLASK_PORT = [string]$Port
$env:FLASK_DEBUG = "0"
$env:PUBLIC_BASE_URL = "https://learn.iovenko.eu"

Write-Host "Starting Learn Words locally on 127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "Open a second PowerShell window and run .\dev-tunnel.ps1"
Write-Host "Close this window or press Ctrl+C to stop the local project."

& $Python (Join-Path $Root "run.py")
exit $LASTEXITCODE
