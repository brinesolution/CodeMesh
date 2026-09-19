$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$record = "$root\.codemesh-processes.json"
if (-not (Test-Path $record)) { Write-Host "No CodeMesh-owned process record found." -ForegroundColor Yellow; exit 0 }
$processes = Get-Content -Raw $record | ConvertFrom-Json
foreach ($id in @($processes.backend, $processes.frontend)) {
    if ($id) { Stop-Process -Id ([int]$id) -Force -ErrorAction SilentlyContinue }
}
Remove-Item -LiteralPath $record -Force -ErrorAction SilentlyContinue
Write-Host "Stopped CodeMesh-owned processes." -ForegroundColor Green

