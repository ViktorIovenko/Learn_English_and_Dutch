param(
    [string]$Key = "$HOME\Desktop\id_ed25519",
    [string]$Server = "root@204.168.186.69"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Key -PathType Leaf)) {
    throw "SSH key not found: $Key"
}

$command = @'
set -eu
cp -a /opt/learn-words/learn.conf.proxy-production-backup /opt/proxy/nginx/conf.d/learn.conf
docker exec proxy-nginx nginx -t
docker exec proxy-nginx nginx -s reload
rm -f /etc/ssh/sshd_config.d/90-learn-words-tunnel.conf
sshd -t
systemctl reload ssh || systemctl reload sshd
cd /opt/learn-words
docker compose up -d
docker compose ps
'@

Write-Host "Restoring production Learn Words on the VPS..." -ForegroundColor Cyan
& ssh -i $Key -o BatchMode=yes -o ConnectTimeout=15 $Server $command
if ($LASTEXITCODE -ne 0) {
    throw "Production restore failed with exit code $LASTEXITCODE"
}
