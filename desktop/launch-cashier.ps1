#Requires -Version 5.1
<#
.SYNOPSIS
  Launch Promocode Checker cashier UI in Edge/Chrome app mode for RDP cashiers.
#>
param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot "config.json"),
    [string]$PointId,
    [string]$CashierBaseUrl,
    [switch]$NoWait
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Config {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config not found: $Path. Copy config.example.json to config.json and edit pointId / cashierBaseUrl."
    }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    return $raw | ConvertFrom-Json
}

function Resolve-BrowserExecutable {
    param([string]$Preference)

    $edgeCandidates = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    )
    $chromeCandidates = @(
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    )

    switch ($Preference.ToLowerInvariant()) {
        "edge" {
            foreach ($path in $edgeCandidates) {
                if (Test-Path -LiteralPath $path) { return $path }
            }
            throw "Microsoft Edge not found."
        }
        "chrome" {
            foreach ($path in $chromeCandidates) {
                if (Test-Path -LiteralPath $path) { return $path }
            }
            throw "Google Chrome not found."
        }
        default {
            foreach ($path in ($edgeCandidates + $chromeCandidates)) {
                if (Test-Path -LiteralPath $path) { return $path }
            }
            throw "No supported browser found (Edge or Chrome)."
        }
    }
}

function Build-CashierUrl {
    param(
        [string]$BaseUrl,
        [string]$ShopPointId
    )
    $trimmed = $BaseUrl.TrimEnd("/")
    $encodedPoint = [uri]::EscapeDataString($ShopPointId)
    return "$trimmed/?point_id=$encodedPoint"
}

$config = Read-Config -Path $ConfigPath
$shopPoint = if ($PSBoundParameters.ContainsKey("PointId")) { $PointId } else { [string]$config.pointId }
$baseUrl = if ($PSBoundParameters.ContainsKey("CashierBaseUrl")) { $CashierBaseUrl } else { [string]$config.cashierBaseUrl }
$fullscreen = [bool]$config.fullscreen
$browserPref = if ($config.browser) { [string]$config.browser } else { "auto" }

if ([string]::IsNullOrWhiteSpace($shopPoint)) {
    throw "pointId is required in config.json or -PointId."
}
if ([string]::IsNullOrWhiteSpace($baseUrl)) {
    throw "cashierBaseUrl is required in config.json or -CashierBaseUrl."
}

$cashierUrl = Build-CashierUrl -BaseUrl $baseUrl -ShopPointId $shopPoint
$browser = Resolve-BrowserExecutable -Preference $browserPref

$args = @("--app=$cashierUrl")
if ($fullscreen) {
    $args += "--start-fullscreen"
}

Write-Host "Launching cashier for shop '$shopPoint'"
Write-Host "URL: $cashierUrl"
Write-Host "Browser: $browser"

$process = Start-Process -FilePath $browser -ArgumentList $args -PassThru
if (-not $NoWait) {
    $process.WaitForExit()
}
