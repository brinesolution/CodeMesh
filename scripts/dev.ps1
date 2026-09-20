$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
& "$PSScriptRoot\doctor.ps1"
if ($LASTEXITCODE -ne 0) { throw "Doctor found required local tools missing." }
try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null }
catch { throw "Ollama is not reachable. Start Ollama before launching CodeMesh." }
if (Test-Path "$root\.codemesh-processes.json") { Write-Host "CodeMesh process record already exists; run .\scripts\stop.ps1 first." -ForegroundColor Yellow; exit 1 }
$uv = (Get-Command uv.exe -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$backend = Start-Process -FilePath $uv -ArgumentList @("run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory "$root\backend" -WindowStyle Hidden -PassThru
$frontend = Start-Process -FilePath $npm -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") -WorkingDirectory "$root\frontend" -WindowStyle Hidden -PassThru
@{ backend = $backend.Id; frontend = $frontend.Id } | ConvertTo-Json | Set-Content "$root\.codemesh-processes.json"
Start-Sleep -Seconds 2
Write-Host "CodeMesh backend: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "CodeMesh frontend: http://127.0.0.1:5173" -ForegroundColor Green
