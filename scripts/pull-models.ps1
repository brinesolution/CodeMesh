$ErrorActionPreference = "Stop"
$models = @("qwen3:0.6b", "smollm2:1.7b", "qwen3:1.7b", "qwen2.5-coder:3b")
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw "Ollama CLI is not installed." }
try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null }
catch { throw "Ollama is not reachable. Start the Ollama application, then run this script again." }
foreach ($model in $models) {
    Write-Host "Pulling or verifying $model" -ForegroundColor Cyan
    & ollama pull $model
    if ($LASTEXITCODE -ne 0) { throw "Model pull failed: $model" }
    Write-Host "PASS $model" -ForegroundColor Green
}
Write-Host "All configured models are available." -ForegroundColor Green

