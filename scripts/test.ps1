param([switch]$WithBrowser)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location "$root\backend"
uv run ruff check app tests
uv run pytest -q
Pop-Location
Push-Location "$root\frontend"
npm run typecheck
npm run build
npm test
Pop-Location
if ($WithBrowser) { & "$PSScriptRoot\browser-smoke.ps1" }
Write-Host "CodeMesh fast test suite passed." -ForegroundColor Green
