param(
    [string]$Url = "http://127.0.0.1:5173",
    [string]$Session = "codemesh-smoke"
)

$ErrorActionPreference = "Stop"

function Invoke-PlaywrightCli {
    param([string[]]$Arguments)
    $output = & npm exec --yes --package=@playwright/cli -- playwright-cli "-s=$Session" @Arguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw $output }
    return $output
}

try {
    Invoke-PlaywrightCli @("open", $Url) | Out-Null
    $initial = Invoke-PlaywrightCli @("snapshot")
    if ($initial -notmatch "CodeMesh" -or $initial -notmatch "Routing mode") {
        throw "The initial CodeMesh shell did not render."
    }

    Invoke-PlaywrightCli @("select", 'select[aria-label="Routing mode"]', "conversation") | Out-Null
    Invoke-PlaywrightCli @("fill", 'textarea[aria-label="Message"]', "Explain cloud computing in two sentences.") | Out-Null
    Invoke-PlaywrightCli @("click", 'button:has-text("Send")') | Out-Null
    Start-Sleep -Seconds 12
    $chat = Invoke-PlaywrightCli @("snapshot")
    if ($chat -notmatch "CodeMesh" -or $chat -notmatch "Conversation Expert") {
        throw "The live chat response did not render."
    }

    Invoke-PlaywrightCli @("click", 'header.topbar button[aria-label="Open system telemetry"]') | Out-Null
    $telemetry = Invoke-PlaywrightCli @("snapshot")
    if ($telemetry -notmatch "System telemetry" -or $telemetry -notmatch "NVIDIA") {
        throw "The telemetry drawer did not expose live runtime data."
    }

    Invoke-PlaywrightCli @("click", 'button[aria-label="Close telemetry"]') | Out-Null
    Invoke-PlaywrightCli @("resize", "390", "844") | Out-Null
    $mobile = Invoke-PlaywrightCli @("snapshot")
    if ($mobile -notmatch "Open sidebar") {
        throw "The mobile layout did not expose the sidebar control."
    }
    Write-Host "PASS browser shell, streamed chat, telemetry, and mobile layout" -ForegroundColor Green
}
finally {
    & npm exec --yes --package=@playwright/cli -- playwright-cli "-s=$Session" close 2>$null | Out-Null
}
