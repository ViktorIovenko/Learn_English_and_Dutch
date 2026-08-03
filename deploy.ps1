# deploy.ps1 — deploy Learn English & Dutch to EU server (204.168.186.69)
# Uploads CODE only. Database, audio files and migrations are never touched.
#
# Usage:
#   .\deploy.ps1              — full deploy (code + nginx + rebuild container)
#   .\deploy.ps1 -SkipBuild   — upload code only, skip container rebuild
#   .\deploy.ps1 -SkipNginx   — skip nginx config step
#
# For normal code-only updates, prefer:
#   .\deploy-changed.ps1 -WhatIf     — preview files that differ from the VPS
#   .\deploy-changed.ps1             — upload only differences and restart
# Add -IncludeInfrastructure only when Dockerfile, Compose or .env must change.

param(
    [switch]$SkipBuild,
    [switch]$SkipNginx
)

$Key  = "$HOME\Desktop\id_ed25519"
$EU   = "root@204.168.186.69"
$Dest = "/opt/learn-words"
$Src  = $PSScriptRoot
$SSH  = @("-i", $Key, "-o", "StrictHostKeyChecking=accept-new", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
          # Keep-alive: abort a stalled connection after ~30s instead of hanging forever.
          "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3")

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
foreach ($sub in @(
    "templates", "static", "__init__.py", "audio_gen.py", "audio_service.py",
    "auth_links.py", "family_tokens.py", "forms.py", "google_auth.py", "i18n.py",
    "models.py", "routes.py", "telegram_auth.py"
)) {
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

# Upload Android APK if it was built locally.
# Pick the NEWEST apk across all build locations (release, debug outputs, and the
# intermediates/ folder that Android Studio's "Run" button writes to).
$ApkCandidates = @(
    "$Src\android\app\build\outputs\apk\release\app-release.apk",
    "$Src\android\app\build\outputs\apk\debug\app-debug.apk",
    "$Src\android\app\build\intermediates\apk\release\app-release.apk",
    "$Src\android\app\build\intermediates\apk\debug\app-debug.apk"
)
$Apk = $ApkCandidates |
    Where-Object { Test-Path $_ } |
    Get-Item |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName
if ($Apk) {
    $ApkAge = (Get-Item $Apk).LastWriteTime
    Write-Host "   -> Android APK /static/downloads/learnwords.apk  (built $ApkAge)"
    Write-Host "      $Apk" -ForegroundColor DarkGray
    & ssh @SSH $EU "mkdir -p ${Dest}/app/static/downloads"
    & scp @SSH $Apk "${EU}:${Dest}/app/static/downloads/learnwords.apk"
} else {
    Write-Host "   WARN: Android APK not found. Build APK first to publish /static/downloads/learnwords.apk" -ForegroundColor Yellow
}

# Создаём файл persistence если ещё не существует или повреждён (нужен для Docker volume)
& ssh @SSH $EU "[ -s ${Dest}/data/bot_persistence.pkl ] || (rm -rf ${Dest}/data/bot_persistence.pkl && echo gAJ9cQAu | base64 -d > ${Dest}/data/bot_persistence.pkl)"
Write-Host "   OK" -ForegroundColor Green

# ── 3: Deploy nginx config ────────────────────────────────────────
if (-not $SkipNginx) {
    Write-Host "[3/4] Deploying nginx config (HTTPS)..."
    & scp @SSH "$Src\nginx\learn.conf" "${EU}:/opt/proxy/nginx/conf.d/learn.conf"
    & ssh @SSH $EU "docker exec proxy-nginx nginx -t && docker exec proxy-nginx nginx -s reload"
    Write-Host "   Nginx reloaded." -ForegroundColor Green
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
