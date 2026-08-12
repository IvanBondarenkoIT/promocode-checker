#Requires -Version 5.1
<#
.SYNOPSIS
  Run direct Firebird ERP probe inside the prod reconcile container.

.EXAMPLE
  cd C:\Projects\promocode-checker\desktop
  .\check-erp.ps1
  .\check-erp.ps1 -CustomerIds "21470,12523" -Days 30
#>
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$CustomerIds = "",
    [int]$Days = 7
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infra = Join-Path $RepoRoot "infra"
$envFile = Join-Path $infra ".env.prod"
if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing $envFile"
}

Push-Location $infra
try {
    $cmd = "python /app/scripts/probe_erp_direct.py --days $Days"
    if ($CustomerIds) {
        $cmd += " --customer-ids $CustomerIds"
    }
    Write-Host "[erp] $cmd"
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec reconcile sh -c $cmd
    if ($LASTEXITCODE -ne 0) { throw "ERP probe failed (exit $LASTEXITCODE)" }
}
finally {
    Pop-Location
}
