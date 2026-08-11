#Requires -Version 5.1
<#
.SYNOPSIS
  Copy staff_cards.csv into the prod app container and import preprod_calibration (LIVE).

.EXAMPLE
  cd D:\CursorProjects\promocode-checker\desktop
  .\import-staff-calibration.ps1
#>
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$CsvPath = "",
    [switch]$SkipDryRun,
    [switch]$ImportOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infra = Join-Path $RepoRoot "infra"
$envFile = Join-Path $infra ".env.prod"
$defaultCsv = Join-Path $RepoRoot "data\input\staff_cards.csv"
$exampleCsv = Join-Path $RepoRoot "docs\examples\staff_cards.example.csv"

if (-not $CsvPath) {
    if (Test-Path -LiteralPath $defaultCsv) {
        $CsvPath = $defaultCsv
    }
    else {
        $CsvPath = $exampleCsv
    }
}

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing $envFile"
}
if (-not (Test-Path -LiteralPath $CsvPath)) {
    throw "Missing CSV: $CsvPath"
}

Push-Location $infra
try {
    Write-Host "[calibration] mkdir /app/data/input"
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec app sh -c "mkdir -p /app/data/input"
    if ($LASTEXITCODE -ne 0) { throw "mkdir failed (exit $LASTEXITCODE)" }

    Write-Host "[calibration] cp $CsvPath -> app:/app/data/input/staff_cards.csv"
    docker compose --env-file .env.prod -f docker-compose.prod.yml cp $CsvPath "app:/app/data/input/staff_cards.csv"
    if ($LASTEXITCODE -ne 0) { throw "cp failed (exit $LASTEXITCODE)" }

    $importCmd = "python /app/scripts/import_segment_promocodes.py --file /app/data/input/staff_cards.csv --campaign-code preprod_calibration --campaign-name 'Preprod calibration' --kind LIVE"

    if (-not $SkipDryRun -and -not $ImportOnly) {
        Write-Host "[calibration] dry-run"
        docker compose --env-file .env.prod -f docker-compose.prod.yml exec app sh -c "$importCmd --dry-run"
        if ($LASTEXITCODE -ne 0) { throw "dry-run failed (exit $LASTEXITCODE)" }
    }

    Write-Host "[calibration] import"
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec app sh -c "$importCmd"
    if ($LASTEXITCODE -ne 0) { throw "import failed (exit $LASTEXITCODE)" }

    Write-Host "Done. Next: Admin Working data -> LIVE; keep PROMO_ENFORCEMENT_MODE=monitor."
}
finally {
    Pop-Location
}
