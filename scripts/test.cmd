@echo off
setlocal
cd /d "%~dp0.."
where uv >nul 2>nul
if errorlevel 1 (
  echo ERROR: uv is not installed. Run: pip install uv
  exit /b 1
)
uv sync --all-groups
uv run pytest -q
