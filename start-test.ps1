param(
    [int]$LocalPort = 7001,
    [string]$Server = "root@204.168.186.69",
    [string]$Key = "$HOME\Desktop\id_ed25519"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
$RunFile = Join-Path $Root "run.py"
$TunnelConfig = Join-Path $Root "nginx\learn.tunnel.conf"
$PublicUrl = "https://learn.iovenko.eu/"
$LocalUrl = "http://127.0.0.1:$LocalPort/"
$RemotePort = 17001
$RemoteTempConfig = "/tmp/learn-words-tunnel.conf"

$SshOptions = @(
    "-i", $Key,
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=10",
    "-o", "ServerAliveCountMax=3"
)

$LocalProcess = $null
$TunnelProcess = $null
$RemotePrepared = $false

function Write-Step([string]$Text) {
    Write-Host "`n== $Text ==" -ForegroundColor Cyan
}

function Invoke-Ssh([string]$Command) {
    & ssh @SshOptions $Server $Command
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }
}

function Wait-HttpReady(
    [string]$Url,
    [int]$Attempts = 20,
    [int]$DelaySeconds = 1,
    [System.Diagnostics.Process]$Process = $null,
    [System.Diagnostics.Process]$SecondaryProcess = $null
) {
    $lastError = ""
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        if ($Process -and $Process.HasExited) {
            throw "Process stopped before $Url became available (exit code $($Process.ExitCode))."
        }
        if ($SecondaryProcess -and $SecondaryProcess.HasExited) {
            throw "Required process stopped before $Url became available (exit code $($SecondaryProcess.ExitCode))."
        }
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                return
            }
            $lastError = "HTTP $($response.StatusCode)"
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds $DelaySeconds
    }
    throw "$Url is not ready: $lastError"
}

function Wait-RemoteTunnelListener([System.Diagnostics.Process]$Process) {
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        if ($Process.HasExited) {
            throw "SSH tunnel stopped during startup (exit code $($Process.ExitCode))."
        }
        & ssh @SshOptions $Server "ss -H -ltn | grep -q '172.18.0.1:${RemotePort}'" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "VPS listener 172.18.0.1:$RemotePort did not appear."
}

function Wait-RemoteTunnelHttp([System.Diagnostics.Process]$Process) {
    for ($attempt = 1; $attempt -le 15; $attempt++) {
        if ($Process.HasExited) {
            throw "SSH tunnel stopped before its HTTP check (exit code $($Process.ExitCode))."
        }
        $remoteCheck = "curl -fsS -o /dev/null --max-time 5 http://172.18.0.1:${RemotePort}/ " +
            "&& timeout 8 docker exec proxy-nginx sh -c " +
            "'wget -q -O /dev/null -T 5 http://172.18.0.1:${RemotePort}/'"
        & ssh @SshOptions $Server $remoteCheck 2>$null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "Local HTTP is not reachable through VPS tunnel 172.18.0.1:$RemotePort."
}

function Restore-Production {
    if (-not $RemotePrepared) {
        return
    }

    Write-Step "Restoring production on learn.iovenko.eu"
    $restoreCommand = @'
set -eu
cd /opt/learn-words
docker compose up -d
test -f /opt/learn-words/learn.conf.proxy-production-backup
cp -a /opt/learn-words/learn.conf.proxy-production-backup /opt/proxy/nginx/conf.d/learn.conf
docker exec proxy-nginx nginx -t
docker exec proxy-nginx nginx -s reload
rm -f /etc/ssh/sshd_config.d/90-learn-words-tunnel.conf
sshd -t
systemctl reload ssh || systemctl reload sshd
rm -f /tmp/learn-words-tunnel.conf
while rule_number=$(ufw status numbered | sed -n '/learn-dev-tunnel/{s/^\[ *\([0-9][0-9]*\)\].*/\1/p;q}'); [ -n "$rule_number" ]; do
    ufw --force delete "$rule_number"
done
'@
    try {
        Invoke-Ssh $restoreCommand
        Write-Host "Production restored." -ForegroundColor Green
    }
    catch {
        Write-Warning "Automatic production restore failed: $($_.Exception.Message)"
        Write-Warning "Run .\restore-production.ps1 manually."
    }
}

try {
    Write-Step "Preflight checks"
    foreach ($requiredFile in @($Python, $RunFile, $TunnelConfig, $Key)) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            throw "Required file not found: $requiredFile"
        }
    }
    foreach ($command in @("ssh", "scp")) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
            throw "Command '$command' was not found. Install the Windows OpenSSH Client."
        }
    }
    $listener = Get-NetTCPConnection -State Listen -LocalPort $LocalPort -ErrorAction SilentlyContinue
    if ($listener) {
        $owner = ($listener | Select-Object -First 1).OwningProcess
        throw "Local port $LocalPort is already in use by PID $owner. Stop that process first."
    }

    Write-Host "Python: $Python"
    Write-Host "Tunnel: $Server -> local 127.0.0.1:$LocalPort"
    Write-Host "Public URL: $PublicUrl"

    Write-Step "Preparing VPS tunnel access"
    & ssh @SshOptions $Server "echo connected"
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot connect to $Server via SSH."
    }
    & scp @SshOptions $TunnelConfig "${Server}:${RemoteTempConfig}"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not upload the temporary Nginx configuration."
    }

    $prepareCommand = @'
set -eu
test -f /tmp/learn-words-tunnel.conf
test -f /opt/proxy/nginx/conf.d/learn.conf
mkdir -p /opt/learn-words
if [ ! -f /opt/learn-words/learn.conf.proxy-production-backup ]; then
    if grep -q '172.18.0.1:17001' /opt/proxy/nginx/conf.d/learn.conf; then
        echo 'Current Nginx config already points to the development tunnel and no production backup exists.' >&2
        exit 1
    fi
    cp -a /opt/proxy/nginx/conf.d/learn.conf /opt/learn-words/learn.conf.proxy-production-backup
fi
printf '%s\n' 'GatewayPorts clientspecified' > /etc/ssh/sshd_config.d/90-learn-words-tunnel.conf
sshd -t
systemctl reload ssh || systemctl reload sshd
network_id=$(docker network inspect family-call_internal --format '{{.Id}}')
bridge_name="br-$(printf '%s' "$network_id" | cut -c1-12)"
subnet=$(docker network inspect family-call_internal --format '{{(index .IPAM.Config 0).Subnet}}')
gateway=$(docker network inspect family-call_internal --format '{{(index .IPAM.Config 0).Gateway}}')
while rule_number=$(ufw status numbered | sed -n '/learn-dev-tunnel/{s/^\[ *\([0-9][0-9]*\)\].*/\1/p;q}'); [ -n "$rule_number" ]; do
    ufw --force delete "$rule_number"
done
ufw allow in on "$bridge_name" from "$subnet" to "$gateway" port 17001 proto tcp comment 'learn-dev-tunnel'
'@
    $RemotePrepared = $true
    Invoke-Ssh $prepareCommand

    Write-Step "Starting reverse SSH tunnel"
    $tunnelArguments = @(
        "-i `"$Key`"",
        "-N", "-T",
        "-o ExitOnForwardFailure=yes",
        "-o ServerAliveInterval=10",
        "-o ServerAliveCountMax=3",
        "-R 172.18.0.1:${RemotePort}:127.0.0.1:${LocalPort}",
        $Server
    ) -join " "
    $TunnelProcess = Start-Process -FilePath "ssh.exe" -ArgumentList $tunnelArguments -NoNewWindow -PassThru
    Wait-RemoteTunnelListener -Process $TunnelProcess
    Write-Host "VPS tunnel listener is ready." -ForegroundColor Green

    Write-Step "Starting local Learn Words"
    $env:FLASK_HOST = "127.0.0.1"
    $env:FLASK_PORT = [string]$LocalPort
    $env:FLASK_DEBUG = "0"
    $env:PUBLIC_BASE_URL = "https://learn.iovenko.eu"
    $LocalProcess = Start-Process `
        -FilePath $Python `
        -ArgumentList "`"$RunFile`"" `
        -WorkingDirectory $Root `
        -NoNewWindow `
        -PassThru

    Wait-HttpReady -Url $LocalUrl -Attempts 30 -DelaySeconds 1 -Process $LocalProcess
    Write-Host "Local application is ready." -ForegroundColor Green

    Wait-RemoteTunnelHttp -Process $TunnelProcess
    Write-Host "HTTP through the reverse tunnel is ready." -ForegroundColor Green

    Write-Step "Switching learn.iovenko.eu to the local project"
    $switchCommand = @'
set -eu
test -f /tmp/learn-words-tunnel.conf
cp -a /tmp/learn-words-tunnel.conf /opt/proxy/nginx/conf.d/learn.conf
docker exec proxy-nginx nginx -t
cd /opt/learn-words
docker compose stop
docker exec proxy-nginx nginx -s reload
'@
    Invoke-Ssh $switchCommand

    Wait-HttpReady -Url $PublicUrl -Attempts 20 -DelaySeconds 2 -Process $LocalProcess -SecondaryProcess $TunnelProcess
    Write-Host "`nREADY: $PublicUrl" -ForegroundColor Green
    Write-Host "The public domain now uses this local checkout."
    Write-Host "Press Ctrl+C to stop testing and restore production." -ForegroundColor Yellow

    while (-not $LocalProcess.HasExited -and -not $TunnelProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
    if ($LocalProcess.HasExited) {
        throw "Local project stopped with exit code $($LocalProcess.ExitCode)."
    }
    throw "SSH tunnel stopped with exit code $($TunnelProcess.ExitCode)."
}
catch {
    $failure = $_
    Write-Host "`nSTART FAILED: $($failure.Exception.Message)" -ForegroundColor Red
    if ($RemotePrepared) {
        Write-Host "Remote diagnostics:" -ForegroundColor Yellow
        $diagnostics = @'
echo '--- tunnel listener ---'
ss -ltnp | grep ':17001' || true
echo '--- active upstream ---'
grep -n 'proxy_pass' /opt/proxy/nginx/conf.d/learn.conf || true
echo '--- production container ---'
cd /opt/learn-words && docker compose ps || true
'@
        try {
            & ssh @SshOptions $Server $diagnostics
        }
        catch {
            Write-Warning "Could not collect remote diagnostics."
        }
    }
    throw $failure
}
finally {
    if ($RemotePrepared) {
        Restore-Production
    }
    if ($TunnelProcess -and -not $TunnelProcess.HasExited) {
        Stop-Process -Id $TunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($LocalProcess -and -not $LocalProcess.HasExited) {
        Stop-Process -Id $LocalProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Local project and tunnel stopped." -ForegroundColor Cyan
}
