# SIH26074 Agromet — Windows quick start

## 1. Install uv

```powershell
py -m pip install uv
```

## 2. Sync runtime + test dependencies

From the project root:

```powershell
uv sync --all-groups
```

## 3. Run tests

```powershell
.\scripts\test.ps1
```

## 4. Start the trained M1 demo

```powershell
.\scripts\run_demo.ps1
```

Open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/healthz

The demo script configures the correct registry and trained model automatically.

## 5. Refresh Panchayat 201001

In Swagger, use:

```text
POST /api/v1/forecast/panchayat/{panchayat_id}/refresh
```

with:

```text
panchayat_id = 201001
```

Or PowerShell:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/forecast/panchayat/201001/refresh"
```

Then retrieve:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/forecast/panchayat/201001"
```

## Why `0.0.0.0` failed in the browser

`0.0.0.0` is a server bind address. Use `127.0.0.1` or `localhost` in the browser.

## Why the earlier 404 occurred

`GET /api/v1/forecast/panchayat/201001` returns 404 until a forecast has been stored. Run the refresh endpoint first, or use `?refresh=true`.

## Why the earlier startup traceback occurred

The command configured:

```text
training_data/panchayats.json
```

but that file does not exist. The supplied development registry is:

```text
training_data/panchayat_registry.csv
```

The API now supports that CSV format, and the packaged demo uses the merged:

```text
config/panchayats.mock.json
```

## PowerShell syntax

Do not use Bash:

```bash
export AGROMET_MODEL_ARTIFACT=...
```

Use PowerShell:

```powershell
$env:AGROMET_MODEL_ARTIFACT="..."
```

The included `run_demo.ps1` does this automatically.


## Built-in Portal

After `uv sync --all-groups`, the project can be launched without PowerShell scripts:

```bat
scripts\run_demo.cmd
```

It opens the government-style pilot portal at:

`http://127.0.0.1:8000/`

Swagger API documentation remains available at:

`http://127.0.0.1:8000/docs`

Run tests without PowerShell execution-policy issues:

```bat
scripts\test.cmd
```

The application defaults to the bundled mock Panchayat registry and the clearly-labelled synthetic M1 model when no environment variables are supplied. This is for demonstration only; connect approved IMD/TGDPS/AWS data and a validated model before operational use.
