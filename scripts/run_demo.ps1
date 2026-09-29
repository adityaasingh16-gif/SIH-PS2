$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "SIH26074 Agromet demo"
Write-Host "Project: $ProjectRoot"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not installed. Install it with: pip install uv"
}

$env:AGROMET_DB_PATH = Join-Path $ProjectRoot "data\agromet.sqlite3"
$env:AGROMET_PANCHAYATS_FILE = Join-Path $ProjectRoot "config\panchayats.mock.json"
$env:AGROMET_FORECAST_PROVIDER = "open_meteo"
$env:AGROMET_MODEL_ARTIFACT = Join-Path $ProjectRoot "agromet\models\m1-telangana-mock-v1\model_bundle.joblib"
$env:AGROMET_SRTM_PATH = ""
$env:AGROMET_WATER_POINTS_FILE = ""
$env:AGROMET_API_KEY = ""

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "data") | Out-Null

Write-Host ""
Write-Host "Model: $env:AGROMET_MODEL_ARTIFACT"
Write-Host "Registry: $env:AGROMET_PANCHAYATS_FILE"
Write-Host "Starting portal at http://127.0.0.1:8000/"
Write-Host "API documentation at http://127.0.0.1:8000/docs"
Write-Host ""

uv run uvicorn agromet.main:app --host 127.0.0.1 --port 8000
