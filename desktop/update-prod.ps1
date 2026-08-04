#Requires -Version 5.1
<#
.SYNOPSIS
  Pull main and rebuild promocode-checker prod stack on Windows Server.

.EXAMPLE
  cd C:\Projects\promocode-checker\desktop
  .\update-prod.ps1
#>
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infra = Join-Path $RepoRoot "infra"
$envFile = Join-Path $infra ".env.prod"

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing $envFile — copy .env.prod.example and fill secrets first."
}

Push-Location $RepoRoot
try {
    Write-Host ">>> git checkout main && pull"
    git checkout main
    git pull origin main

    Set-Location $infra
    if ($SkipBuild) {
        Write-Host ">>> docker compose up -d (no rebuild)"
        docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
    }
    else {
        Write-Host ">>> docker compose up -d --build"
        docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
    }

    Write-Host ">>> health"
    Start-Sleep -Seconds 3
    Invoke-RestMethod http://127.0.0.1:8020/health | ConvertTo-Json -Compress

    Write-Host ">>> reconcile (last 20 lines)"
    docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail 20 reconcile
}
finally {
    Pop-Location
}

Write-Host "Done. Cashier: http://127.0.0.1:8020/  Admin: http://127.0.0.1:8020/admin/login"
