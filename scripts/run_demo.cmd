@echo off
setlocal
cd /d "%~dp0.."
echo SIH26074 Telangana Panchayat Agromet Portal
where uv >nul 2>nul
if errorlevel 1 (
  echo ERROR: uv is not installed. Run: pip install uv
  exit /b 1
)
if not exist data mkdir data
set AGROMET_DB_PATH=%CD%\data\agromet.sqlite3
set AGROMET_PANCHAYATS_FILE=%CD%\config\panchayats.mock.json
set AGROMET_FORECAST_PROVIDER=open_meteo
set AGROMET_MODEL_ARTIFACT=%CD%\agromet\models\m1-telangana-mock-v1\model_bundle.joblib
set AGROMET_SRTM_PATH=
set AGROMET_WATER_POINTS_FILE=
set AGROMET_API_KEY=
start "" "http://127.0.0.1:8000/"
uv run uvicorn agromet.main:app --host 127.0.0.1 --port 8000
