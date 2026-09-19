$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Bootstrapping CodeMesh dependencies..." -ForegroundColor Cyan
uv sync --directory "$root\backend" --dev
Push-Location "$root\frontend"
npm install
Pop-Location
Write-Host "Bootstrap complete. Run .\scripts\doctor.ps1 next." -ForegroundColor Green

