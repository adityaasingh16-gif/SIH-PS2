# Telangana Panchayat Agromet Downscaling

This package implements the SIH26074 pilot architecture:

- `data_engine.py` builds feature matrices from block/grid forecasts, Panchayat
  DEM attributes, previous-day AWS residuals, lag/lead forecasts, and optional
  satellite features. It applies the standard environmental lapse rate of
  `-6.5 °C/km`.
- `modeling_engine.py` trains LightGBM quantile regressors for P10/P50/P90
  continuous forecasts and calibrated LightGBM rainfall threshold classifiers.
  Physical bounds and block-mean conservation are applied after inference.
- `advisory_engine.py` contains deterministic rules for spraying windows, urea
  topdressing, rice blast risk, and FAO-56 Penman-Monteith ET0. Templates render
  the validated metrics in English, Telugu, or Hindi without changing them.
- `evaluator.py` calculates MAE, RMSE, Bias, POD, FAR, CSI, BS, BSS and produces
  the B0/B1/B1b/B2/M1 Markdown comparison scorecard.
- `main.py` exposes the Panchayat forecast and KVK review endpoints.
- `storage.py` persists forecasts, review decisions, and an audit event per decision.
- `ingestion.py` connects Open-Meteo, a configurable AWS residual endpoint, and
  local SRTM GeoTIFF terrain sampling.

## Run

```bash
python -m pip install -r agromet/requirements.txt
uvicorn agromet.main:app --host 0.0.0.0 --port 8000
```

The API persists pilot state in `agromet.sqlite3` by default. Set
`AGROMET_DB_PATH` to use another durable path. An optional JSON forecast file can
be loaded through `AGROMET_FORECAST_FILE`; it may contain either a list of
`PanchayatForecastResponse` objects or `{"forecasts": [...]}`.

For live refreshes, set `AGROMET_PANCHAYATS_FILE` to a registry such as:

```json
{
  "panchayats": [
    {
      "panchayat_id": "TG-001",
      "latitude": 17.4,
      "longitude": 78.4,
      "elevation_m": 540,
      "coarse_latitude": 17.5,
      "coarse_longitude": 78.5,
      "coarse_elevation_m": 480
    }
  ]
}
```

`POST /api/v1/forecast/panchayat/TG-001/refresh` fetches five days from
Open-Meteo by default, or from the configured IMD adapter when
`AGROMET_FORECAST_PROVIDER=imd` and `AGROMET_IMD_URL` are set. It applies
DEM/AWS inputs when configured, persists the forecast, and creates pending
deterministic advisories. Set `AGROMET_AWS_RESIDUAL_URL` for a JSON
station-residual endpoint and `AGROMET_SRTM_PATH` for a local SRTM GeoTIFF.
The live service reports `physics-baseline-live` until a trained M1 model bundle
is deployed. To use a trained bundle, set
`AGROMET_MODEL_ARTIFACT=agromet/demo_models/m1-demo-synthetic-26074-v1/model_bundle.joblib`.
The demo bundle is synthetic and must not be used to claim Telangana skill.

## Production build additions

### Real M1 training

Use `agromet.train_real` with a chronological labelled CSV:

```bash
uv run python -m agromet.train_real \
  --input data/tgdps_training.csv \
  --output-dir models/m1-2026-09 \
  --version m1-telangana-2026-09
```

The command requires the same `FeaturePipeline` feature schema, performs 60/20/20
chronological fit/calibration/holdout partitions, calibrates rainfall probabilities
only on the calibration period, and never uses holdout rows for training.

### Independent evaluation

Prepare a labelled evaluation CSV containing observed values and B0/B1/B1b/B2/M1
predictions/probabilities, then run:

```bash
uv run python -m agromet.evaluate_dataset \
  --input data/evaluation.csv \
  --output data/scorecard.json
```

Set `AGROMET_SCORECARD_FILE=data/scorecard.json` for the API scorecard endpoint.

### Scheduled refresh

For a small pilot:

```bash
uv run python -m agromet.scheduler --panchayat TG-001 --interval-minutes 360
```

For production, run the same one-shot command from Kubernetes CronJob, systemd
timer, Airflow, or another managed scheduler rather than embedding scheduling
inside the API process.

### Review API authentication

Set `AGROMET_API_KEY` and send `X-API-Key` on KVK queue/review requests. If the
variable is unset, authentication is disabled for local development.

### Container deployment

`Dockerfile`, `docker-compose.yml`, `.env.example`, and `docs/architecture.md`
are included. The pilot keeps SQLite as the default persistence backend; a
managed PostgreSQL repository should replace it before multi-instance deployment.
