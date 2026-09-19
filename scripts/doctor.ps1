$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$failures = 0

function Check-Tool([string]$name, [string]$command, [switch]$Required) {
    $resolved = Get-Command $command -ErrorAction SilentlyContinue
    if ($resolved) { Write-Host "PASS $name ($($resolved.Source))" -ForegroundColor Green }
    elseif ($Required) { Write-Host "FAIL $name is required" -ForegroundColor Red; $script:failures++ }
    else { Write-Host "WARN $name is not installed" -ForegroundColor Yellow }
}

Write-Host "CodeMesh doctor - $root" -ForegroundColor Cyan
Write-Host "Windows: $([Environment]::OSVersion.VersionString)"
Check-Tool "Git" "git" -Required
Check-Tool "Python" "python" -Required
Check-Tool "Node" "node" -Required
Check-Tool "npm" "npm" -Required
Check-Tool "uv" "uv"
Check-Tool "Ollama" "ollama" -Required
try { Write-Host "INFO Python $(& python --version 2>&1)" } catch { }
try { Write-Host "INFO Node $(& node --version 2>&1)" } catch { }
try { Write-Host "INFO Git $(& git --version 2>&1)" } catch { }
try { Write-Host "INFO Ollama $(& ollama --version 2>&1)" } catch { }

$ram = Get-CimInstance Win32_ComputerSystem
Write-Host "INFO RAM $([math]::Round($ram.TotalPhysicalMemory / 1GB, 1)) GB"
$drive = Get-PSDrive -Name (Split-Path $root -Qualifier).TrimEnd(':')
Write-Host "INFO Free disk $([math]::Round($drive.Free / 1GB, 1)) GB"
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpu = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1
    Write-Host "PASS NVIDIA $gpu" -ForegroundColor Green
} else { Write-Host "WARN nvidia-smi unavailable" -ForegroundColor Yellow }

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    Write-Host "PASS Ollama API reachable" -ForegroundColor Green
    $names = @($health.models | ForEach-Object { $_.name })
    foreach ($model in @("qwen3:0.6b", "smollm2:1.7b", "qwen3:1.7b", "qwen2.5-coder:3b")) {
        if ($names -contains $model) { Write-Host "PASS model $model" -ForegroundColor Green }
        else { Write-Host "WARN model missing $model" -ForegroundColor Yellow }
    }
} catch { Write-Host "WARN Ollama API is not reachable; start Ollama before live work" -ForegroundColor Yellow }
if ($failures -gt 0) { exit 1 }
exit 0

