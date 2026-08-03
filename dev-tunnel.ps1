param(
    [string]$Key = "$HOME\Desktop\id_ed25519",
    [string]$Server = "root@204.168.186.69",
    [int]$LocalPort = 7001,
    [int]$RemotePort = 17001
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Key -PathType Leaf)) {
    throw "SSH key not found: $Key"
}

$listener = Get-NetTCPConnection -State Listen -LocalPort $LocalPort -ErrorAction SilentlyContinue
if (-not $listener) {
    Write-Warning "Nothing is listening on local port $LocalPort yet. Start the Flask project first."
}

Write-Host "Opening learn.iovenko.eu development tunnel..." -ForegroundColor Cyan
Write-Host "VPS 172.18.0.1:$RemotePort -> local 127.0.0.1:$LocalPort"
Write-Host "Keep this window open. Press Ctrl+C to close the tunnel."

& ssh `
    -i $Key `
    -N `
    -T `
    -o ExitOnForwardFailure=yes `
    -o ServerAliveInterval=15 `
    -o ServerAliveCountMax=3 `
    -R "172.18.0.1:${RemotePort}:127.0.0.1:${LocalPort}" `
    $Server

if ($LASTEXITCODE -ne 0) {
    throw "SSH tunnel stopped with exit code $LASTEXITCODE"
}
