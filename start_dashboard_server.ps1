$ErrorActionPreference = "Stop"

$expectedBuild = "2026-07-24.2"
$htmlFile = "BBtech_Dashboard_Auto_google_sheet_sync_fixed.html"
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $htmlFile))) {
    $htmlFile = "index.html"
}

$python = "C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

function Test-DashboardBuild([string]$baseUrl) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri ($baseUrl + "/build") -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content.Trim() -eq $expectedBuild
    } catch {
        return $false
    }
}

$baseUrl = "http://127.0.0.1:8765"
$dashboardUrl = $baseUrl + "/" + $htmlFile

if (-not (Test-DashboardBuild $baseUrl)) {
    Start-Process -FilePath $python `
        -ArgumentList "dashboard_proxy_server.py", "8765" `
        -WorkingDirectory $PSScriptRoot `
        -WindowStyle Hidden

    $urlFile = Join-Path $PSScriptRoot "dashboard_server_url.txt"
    $ready = $false
    for ($attempt = 0; $attempt -lt 48; $attempt++) {
        Start-Sleep -Milliseconds 250
        if (-not (Test-Path -LiteralPath $urlFile)) { continue }
        $candidateUrl = [IO.File]::ReadAllText($urlFile).Trim()
        if (-not $candidateUrl) { continue }
        try {
            $candidateUri = [Uri]$candidateUrl
            $candidateBase = $candidateUri.GetLeftPart([UriPartial]::Authority)
            if (Test-DashboardBuild $candidateBase) {
                $baseUrl = $candidateBase
                $dashboardUrl = $candidateUrl
                $ready = $true
                break
            }
        } catch {}
    }
    if (-not $ready) {
        throw "BBTECH dashboard server did not start."
    }
}

$launchUrl = $dashboardUrl + "?v=" + $expectedBuild
$chromeCandidates = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
)
$chrome = $chromeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($chrome) {
    Start-Process -FilePath $chrome -ArgumentList "--new-window", $launchUrl
} else {
    Start-Process $launchUrl
}
