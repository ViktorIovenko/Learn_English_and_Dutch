# deploy.ps1 — deploy Learn English & Dutch to EU server (204.168.186.69)
# Uploads CODE only. Database, audio files and migrations are never touched.
#
# Usage:
#   .\deploy.ps1              — full deploy (code + nginx + rebuild container)
#   .\deploy.ps1 -SkipBuild   — upload code only, skip container rebuild
#   .\deploy.ps1 -SkipNginx   — skip nginx config step

param(
    [switch]$SkipBuild,
    [switch]$SkipNginx
)

$Key  = "$HOME\Desktop\id_ed25519"
$EU   = "root@204.168.186.69"
$Dest = "/opt/learn-words"
$Src  = $PSScriptRoot
$SSH  = @("-i", $Key, "-o", "StrictHostKeyChecking=accept-new", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15")

Write-Host "=== Deploy Learn-Words -> EU (code only) ===" -ForegroundColor Cyan

# ── 1: Check connection ───────────────────────────────────────────
Write-Host "`n[1/4] Connecting to EU server..."
& ssh @SSH $EU "echo ok"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Cannot connect to server" -ForegroundColor Red; exit 1 }
Write-Host "   OK" -ForegroundColor Green

# ── 2: Upload source code (no data, no audio) ────────────────────
Write-Host "[2/4] Uploading source code..."

# Upload bot/ and top-level py/config files as-is
foreach ($item in @("bot", "config.py", "db_init.py", "requirements.txt", "run.py", "Dockerfile", ".dockerignore")) {
    $local = "$Src\$item"
    if (Test-Path $local) {
        Write-Host "   -> $item"
        & scp @SSH -r $local "${EU}:${Dest}/"
    }
}

# Upload app/ but skip static/audio (lives in a Docker volume on the server)
Write-Host "   -> app/ (excluding static/audio)"
& ssh @SSH $EU "mkdir -p ${Dest}/app"
foreach ($sub in @("templates", "static", "__init__.py", "audio_gen.py", "models.py", "routes.py")) {
    $local = "$Src\app\$sub"
    if (Test-Path $local) {
        if ($sub -eq "static") {
            # Upload static subfolders/files one by one, skip audio/
            & ssh @SSH $EU "mkdir -p ${Dest}/app/static"
            Get-ChildItem "$Src\app\static" | Where-Object { $_.Name -ne "audio" } | ForEach-Object {
                Write-Host "      -> static/$($_.Name)"
                & scp @SSH -r $_.FullName "${EU}:${Dest}/app/static/"
            }
        } else {
            & scp @SSH -r $local "${EU}:${Dest}/app/"
        }
    }
}

& scp @SSH "$Src\docker-compose.eu.yml" "${EU}:${Dest}/docker-compose.yml"
& scp @SSH "$Src\.env.eu"               "${EU}:${Dest}/.env"
Write-Host "   OK" -ForegroundColor Green

# ── 3: Deploy nginx config ────────────────────────────────────────
if (-not $SkipNginx) {
    Write-Host "[3/4] Deploying nginx config (HTTPS)..."
    & scp @SSH "$Src\nginx\learn.conf" "${EU}:/opt/family-call/nginx/conf.d/learn.conf"
    & ssh @SSH $EU "cd /opt/family-call && docker compose exec -T nginx nginx -t && docker compose restart nginx"
    Write-Host "   Nginx restarted." -ForegroundColor Green
} else {
    Write-Host "[3/4] Nginx skipped (-SkipNginx)."
}

# ── 4: Build and start container ─────────────────────────────────
if (-not $SkipBuild) {
    Write-Host "[4/4] Building and starting container..."
    & ssh @SSH $EU "cd ${Dest} && docker compose up --build -d"
    Start-Sleep 3
    & ssh @SSH $EU "cd ${Dest} && docker compose ps"
} else {
    Write-Host "[4/4] Build skipped (-SkipBuild)."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE  (data untouched)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
