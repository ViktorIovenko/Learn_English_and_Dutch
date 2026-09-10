param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 4173
)

$siteRoot = Join-Path $PSScriptRoot 'website'
if (-not (Test-Path -LiteralPath $siteRoot -PathType Container)) {
  throw "Website directory not found: $siteRoot"
}

Write-Host "ParallelLingvo local preview: http://localhost:$Port/ru/"
Write-Host 'Press Ctrl+C to stop.'
py -3 -m http.server $Port --directory $siteRoot
