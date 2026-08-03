# Incremental production deploy for Learn Words.
# Uploads only files whose content differs from the VPS copy.
# Source-only changes are copied into the running container without rebuilding
# the image. Dependency or Docker configuration changes trigger a real build.

param(
    [switch]$SkipNginx,
    [switch]$IncludeInfrastructure,
    [switch]$ForceBuild,
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Key = "$HOME\Desktop\id_ed25519"
$Server = "root@204.168.186.69"
$Dest = "/opt/learn-words"
$Service = "learn-words"
$Root = $PSScriptRoot
$RemoteNginx = "/opt/proxy/nginx/conf.d/learn.conf"
$ApkRemotePath = "app/static/downloads/learnwords.apk"
$SshOptions = @(
    "-i", $Key,
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=10",
    "-o", "ServerAliveCountMax=3"
)

function Invoke-Ssh([string]$Command) {
    & ssh @SshOptions $Server $Command
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }
}

function Invoke-SshCapture([string]$Command) {
    $output = & ssh @SshOptions $Server $Command
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }
    return @($output)
}

function Get-LocalHash([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Add-DeployFile(
    [System.Collections.Generic.List[object]]$List,
    [string]$LocalPath,
    [string]$DisplayPath,
    [string]$RemotePath,
    [bool]$BuildSensitive = $false,
    [bool]$RecreateSensitive = $false
) {
    if (-not (Test-Path -LiteralPath $LocalPath -PathType Leaf)) {
        return
    }
    $List.Add([pscustomobject]@{
        LocalPath = $LocalPath
        DisplayPath = $DisplayPath.Replace("\", "/")
        RemotePath = $RemotePath.Replace("\", "/")
        LocalHash = Get-LocalHash $LocalPath
        BuildSensitive = $BuildSensitive
        RecreateSensitive = $RecreateSensitive
    })
}

if (-not (Test-Path -LiteralPath $Key -PathType Leaf)) {
    throw "SSH key not found: $Key"
}

Write-Host "=== Incremental deploy Learn-Words -> EU ===" -ForegroundColor Cyan
Write-Host "Comparing local files with $Server..."

$files = [System.Collections.Generic.List[object]]::new()

foreach ($folder in @("bot", "app")) {
    $folderPath = Join-Path $Root $folder
    if (-not (Test-Path -LiteralPath $folderPath -PathType Container)) {
        continue
    }
    Get-ChildItem -LiteralPath $folderPath -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($Root.Length).TrimStart("\").Replace("\", "/")
        if ($relative -like "app/static/audio/*" -or
            $relative -eq $ApkRemotePath -or
            $relative -like "*/AGENTS.md" -or
            $relative -like "*/__pycache__/*" -or
            $relative -like "*.pyc" -or
            $relative -like "*.pyo") {
            return
        }
        Add-DeployFile $files $_.FullName $relative $relative
    }
}

foreach ($name in @("config.py", "db_init.py", "run.py")) {
    Add-DeployFile $files (Join-Path $Root $name) $name $name
}

Add-DeployFile $files (Join-Path $Root "requirements.txt") "requirements.txt" "requirements.txt" $true
if ($IncludeInfrastructure) {
    Add-DeployFile $files (Join-Path $Root "Dockerfile") "Dockerfile" "Dockerfile" $true
    Add-DeployFile $files (Join-Path $Root ".dockerignore") ".dockerignore" ".dockerignore" $true
    Add-DeployFile $files (Join-Path $Root "docker-compose.eu.yml") "docker-compose.eu.yml" "docker-compose.yml" $true $true
    Add-DeployFile $files (Join-Path $Root ".env.eu") ".env.eu" ".env" $false $true
}

# Publish the newest locally built application APK. Instrumentation-test APKs
# are intentionally excluded; only installable debug/release app artifacts count.
$apkCandidates = @(
    (Join-Path $Root "android\app\build\outputs\apk\release\app-release.apk"),
    (Join-Path $Root "android\app\build\outputs\apk\debug\app-debug.apk"),
    (Join-Path $Root "android\app\build\intermediates\apk\release\app-release.apk"),
    (Join-Path $Root "android\app\build\intermediates\apk\debug\app-debug.apk")
)
$apk = $apkCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    ForEach-Object { Get-Item -LiteralPath $_ } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

# Never publish an APK built before the current Android sources/configuration.
$androidSourceRoots = @(
    (Join-Path $Root "android\app\src"),
    (Join-Path $Root "android\app\build.gradle"),
    (Join-Path $Root "android\build.gradle"),
    (Join-Path $Root "android\gradle.properties"),
    (Join-Path $Root "android\settings.gradle")
)
$latestAndroidSource = $androidSourceRoots |
    ForEach-Object {
        if (Test-Path -LiteralPath $_ -PathType Container) {
            Get-ChildItem -LiteralPath $_ -Recurse -File
        } elseif (Test-Path -LiteralPath $_ -PathType Leaf) {
            Get-Item -LiteralPath $_
        }
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($apk -and $latestAndroidSource -and $apk.LastWriteTime -lt $latestAndroidSource.LastWriteTime) {
    Write-Host "Android APK is older than current Android sources and will not be published." -ForegroundColor Yellow
    Write-Host "  APK: $($apk.LastWriteTime)" -ForegroundColor DarkGray
    Write-Host "  Newest source: $($latestAndroidSource.LastWriteTime) ($($latestAndroidSource.FullName))" -ForegroundColor DarkGray
    $apk = $null
}
$apkLocalHash = if ($apk) { Get-LocalHash $apk.FullName } else { "" }

$remoteHashCommand = @'
set -eu
cd /opt/learn-words
if [ -d bot ]; then
    find bot -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -exec sha256sum {} +
fi
if [ -d app ]; then
    find app -type f ! -path 'app/static/audio/*' ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -exec sha256sum {} +
fi
for file in config.py db_init.py run.py requirements.txt Dockerfile .dockerignore docker-compose.yml .env; do
    if [ -f "$file" ]; then sha256sum "$file"; fi
done
'@

$remoteHashes = @{}
foreach ($line in (Invoke-SshCapture $remoteHashCommand)) {
    if ($line -match '^([0-9a-fA-F]{64})\s+\*?(.+)$') {
        $remotePath = $Matches[2].TrimStart("./")
        $remoteHashes[$remotePath] = $Matches[1].ToLowerInvariant()
    }
}

$changed = @(
    $files | Where-Object {
        -not $remoteHashes.ContainsKey($_.RemotePath) -or
        $remoteHashes[$_.RemotePath] -ne $_.LocalHash
    }
)
$apkServerChanged = [bool]$apk -and (
    -not $remoteHashes.ContainsKey($ApkRemotePath) -or
    $remoteHashes[$ApkRemotePath] -ne $apkLocalHash
)

# The source directory on the VPS and the running container are independent:
# `docker compose restart` does not copy host files into an existing image.
# Compare the actual /app contents as well so an old container cannot look current.
$containerHashCommand = @'
set -eu
cd /opt/learn-words
container_id=$(docker compose ps -q learn-words)
if [ -z "$container_id" ]; then exit 0; fi
docker exec -i "$container_id" sh -s <<'CONTAINER_HASHES'
cd /app
if [ -d bot ]; then
    find bot -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -exec sha256sum {} +
fi
if [ -d app ]; then
    find app -type f ! -path 'app/static/audio/*' ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -exec sha256sum {} +
fi
for file in config.py db_init.py run.py requirements.txt Dockerfile; do
    if [ -f "$file" ]; then sha256sum "$file"; fi
done
CONTAINER_HASHES
'@

$containerHashes = @{}
foreach ($line in (Invoke-SshCapture $containerHashCommand)) {
    if ($line -match '^([0-9a-fA-F]{64})\s+\*?(.+)$') {
        $containerPath = $Matches[2].TrimStart("./")
        $containerHashes[$containerPath] = $Matches[1].ToLowerInvariant()
    }
}

$containerComparable = @($files | Where-Object {
    $_.RemotePath -like "bot/*" -or
    $_.RemotePath -like "app/*" -or
    $_.RemotePath -in @("config.py", "db_init.py", "run.py", "requirements.txt", "Dockerfile")
})
$containerDrift = @($containerComparable | Where-Object {
    -not $containerHashes.ContainsKey($_.RemotePath) -or
    $containerHashes[$_.RemotePath] -ne $_.LocalHash
})
$containerDependencyDrift = [bool]($containerDrift | Where-Object {
    $_.RemotePath -in @("requirements.txt", "Dockerfile")
})
$apkContainerDrift = [bool]$apk -and (
    -not $containerHashes.ContainsKey($ApkRemotePath) -or
    $containerHashes[$ApkRemotePath] -ne $apkLocalHash
)

$nginxChanged = $false
$localNginx = Join-Path $Root "nginx\learn.conf"
if (-not $SkipNginx -and (Test-Path -LiteralPath $localNginx -PathType Leaf)) {
    $remoteNginxHash = ""
    $nginxHashOutput = Invoke-SshCapture "if [ -f '$RemoteNginx' ]; then sha256sum '$RemoteNginx'; fi"
    foreach ($line in $nginxHashOutput) {
        if ($line -match '^([0-9a-fA-F]{64})\s+') {
            $remoteNginxHash = $Matches[1].ToLowerInvariant()
            break
        }
    }
    $nginxChanged = (Get-LocalHash $localNginx) -ne $remoteNginxHash
}

if (-not $changed.Count -and -not $containerDrift.Count -and -not $nginxChanged -and
    -not $apkServerChanged -and -not $apkContainerDrift -and -not $ForceBuild) {
    if (-not $apk) {
        Write-Host "Android APK not found. Build the APK locally to publish it." -ForegroundColor Yellow
    }
    Write-Host "No changed production files found. Nothing to deploy." -ForegroundColor Green
    exit 0
}

if ($changed.Count) {
    Write-Host "Files to upload to the VPS:" -ForegroundColor Yellow
    foreach ($file in $changed) {
        Write-Host "  $($file.DisplayPath)"
    }
}
if ($containerDrift.Count) {
    Write-Host "Files missing or outdated inside the running container:" -ForegroundColor Yellow
    foreach ($file in $containerDrift) {
        Write-Host "  $($file.DisplayPath)"
    }
}
if ($nginxChanged) {
    Write-Host "  nginx/learn.conf"
}
if ($apkServerChanged -or $apkContainerDrift) {
    Write-Host "  Android APK -> $ApkRemotePath" -ForegroundColor Yellow
    Write-Host "    $($apk.FullName) (built $($apk.LastWriteTime))" -ForegroundColor DarkGray
} elseif (-not $apk) {
    Write-Host "  [Android APK not found; server APK will not be changed]" -ForegroundColor Yellow
}
if ($containerDependencyDrift) {
    Write-Host "  [container dependencies are outdated; Docker build required]" -ForegroundColor Yellow
}
if ($ForceBuild) {
    Write-Host "  [forced Docker build]"
}

if ($WhatIf) {
    Write-Host "WhatIf: no files uploaded and no services restarted." -ForegroundColor Cyan
    exit 0
}

foreach ($file in $changed) {
    if ($file.RemotePath -notmatch '^[A-Za-z0-9._/-]+$') {
        throw "Unsafe remote path: $($file.RemotePath)"
    }
    $remoteParent = Split-Path -Parent $file.RemotePath
    if ($remoteParent) {
        Invoke-Ssh "mkdir -p '$Dest/$($remoteParent.Replace('\', '/'))'"
    }
    & scp @SshOptions $file.LocalPath "${Server}:${Dest}/$($file.RemotePath)"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not upload $($file.DisplayPath)"
    }
}

if ($apkServerChanged) {
    Invoke-Ssh "mkdir -p '$Dest/app/static/downloads'"
    & scp @SshOptions $apk.FullName "${Server}:${Dest}/${ApkRemotePath}"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not upload Android APK"
    }
}

if ($apkServerChanged -or $apkContainerDrift) {
    $apkCopyCommands = @(
        "set -eu",
        "cd '$Dest'",
        "container_id=`$(docker compose ps -q '$Service')",
        'test -n "$container_id"',
        'docker exec "$container_id" mkdir -p /app/app/static/downloads',
        "docker cp '$Dest/$ApkRemotePath' `"`$container_id`":'/app/$ApkRemotePath'"
    )
    Invoke-Ssh ($apkCopyCommands -join "`n")
    Write-Host "Android APK published without restarting the service." -ForegroundColor Green
}

if ($nginxChanged) {
    & scp @SshOptions $localNginx "${Server}:${RemoteNginx}"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not upload nginx/learn.conf"
    }
    Invoke-Ssh "docker exec proxy-nginx nginx -t && docker exec proxy-nginx nginx -s reload"
    Write-Host "Nginx configuration reloaded." -ForegroundColor Green
}

$needsBuild = $ForceBuild -or $containerDependencyDrift -or [bool]($changed | Where-Object BuildSensitive)
$needsRecreate = [bool]($changed | Where-Object RecreateSensitive)
$runtimeFiles = @($files | Where-Object {
    -not $_.BuildSensitive -and -not $_.RecreateSensitive
} | Where-Object {
    $file = $_
    [bool]($changed | Where-Object RemotePath -eq $file.RemotePath) -or
    [bool]($containerDrift | Where-Object RemotePath -eq $file.RemotePath)
})

if ($needsBuild) {
    Write-Host "Dependency or Docker configuration changed: rebuilding image." -ForegroundColor Yellow
    Write-Host "System/Python packages shown below are installed on the VPS; they are not uploaded from this PC." -ForegroundColor DarkYellow
    Invoke-Ssh "cd '$Dest' && docker compose up --build -d && docker compose ps"
} elseif ($needsRecreate) {
    Write-Host "Environment changed: recreating container without rebuilding the image." -ForegroundColor Yellow
    Invoke-Ssh "cd '$Dest' && docker compose up -d --force-recreate --no-build && docker compose ps"
} elseif ($runtimeFiles.Count) {
    $copyCommands = [System.Collections.Generic.List[string]]::new()
    $copyCommands.Add("set -eu")
    $copyCommands.Add("cd '$Dest'")
    $copyCommands.Add("container_id=`$(docker compose ps -q '$Service')")
    $copyCommands.Add('test -n "$container_id"')
    foreach ($file in $runtimeFiles) {
        $parent = Split-Path -Parent $file.RemotePath
        if ($parent) {
            $copyCommands.Add("docker exec `"`$container_id`" mkdir -p '/app/$($parent.Replace('\', '/'))'")
        }
        $copyCommands.Add("docker cp '$Dest/$($file.RemotePath)' `"`$container_id`":'/app/$($file.RemotePath)'")
    }
    $copyCommands.Add("docker compose restart '$Service'")
    $copyCommands.Add("docker compose ps '$Service'")
    Invoke-Ssh ($copyCommands -join "`n")
    Write-Host "Source files copied into the existing container; Docker build was skipped." -ForegroundColor Green
}

Write-Host "Incremental deployment completed." -ForegroundColor Green
