$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$record = "$root\.codemesh-processes.json"
$ids = [System.Collections.Generic.HashSet[int]]::new()

function Add-ProcessTree {
    param([int]$ProcessId)
    if ($ProcessId -le 0 -or -not $ids.Add($ProcessId)) { return }
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue |
        ForEach-Object { Add-ProcessTree -ProcessId ([int]$_.ProcessId) }
}

if (Test-Path $record) {
    $processes = Get-Content -Raw $record | ConvertFrom-Json
    foreach ($id in @($processes.backend, $processes.frontend)) {
        if ($id) { Add-ProcessTree -ProcessId ([int]$id) }
    }
}

# Start-Process may leave the actual server child running after its launcher exits.
# Recover only CodeMesh processes that still own the documented local ports.
foreach ($connection in Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" -ErrorAction SilentlyContinue
    if ($process.CommandLine -and $process.CommandLine.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        Add-ProcessTree -ProcessId ([int]$connection.OwningProcess)
    }
}

foreach ($id in $ids | Sort-Object -Descending) {
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}
if (Test-Path $record) { Remove-Item -LiteralPath $record -Force -ErrorAction SilentlyContinue }
Write-Host "Stopped CodeMesh-owned processes." -ForegroundColor Green
