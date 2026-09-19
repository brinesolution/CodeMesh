$ErrorActionPreference = "Stop"
$models = @("qwen3:0.6b", "smollm2:1.7b", "qwen3:1.7b", "qwen2.5-coder:3b")
$maxAttempts = 3
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw "Ollama CLI is not installed." }
try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null }
catch { throw "Ollama is not reachable. Start the Ollama application, then run this script again." }
foreach ($model in $models) {
    Write-Host "Pulling or verifying $model" -ForegroundColor Cyan
    $succeeded = $false
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        & ollama pull $model
        if ($LASTEXITCODE -eq 0) {
            $succeeded = $true
            break
        }
        if ($attempt -lt $maxAttempts) {
            Write-Warning "Pull attempt $attempt/$maxAttempts failed for $model; retrying resumable download."
            Start-Sleep -Seconds 5
        }
    }
    if (-not $succeeded) { throw "Model pull failed after $maxAttempts attempts: $model" }
    Write-Host "PASS $model" -ForegroundColor Green
}
Write-Host "All configured models are available." -ForegroundColor Green
