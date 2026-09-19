$ErrorActionPreference = "Stop"
$expected = @("qwen3:0.6b", "smollm2:1.7b", "qwen3:1.7b", "qwen2.5-coder:3b")
$payload = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
$installed = @($payload.models | ForEach-Object { $_.name })
$missing = @($expected | Where-Object { $installed -notcontains $_ })
if ($missing.Count -gt 0) { Write-Host "Missing: $($missing -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "PASS all four CodeMesh models installed" -ForegroundColor Green

