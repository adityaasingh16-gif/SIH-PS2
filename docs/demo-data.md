# Demo dataset (DEMO / SYNTHETIC DATA)

Everything created by `scripts/seed_demo_data.py` is synthetic. It is **not** IMD data, **not** Government of Telangana data and **not** real farmer records. The UI shows a "DEMO ENVIRONMENT" strip whenever the dataset is loaded.

    python scripts/seed_demo_data.py --with-accounts   # seed / reset (uses $AGROMET_DB_PATH)
    python scripts/seed_demo_data.py --purge           # remove demo rows only
    AGROMET_DEMO_SEED=0                                # make the Docker start-up seed a no-op

* Idempotent: every row created is listed in `demo_seed_manifest`; each run removes exactly those rows and recreates them.
* Live (non-demo) forecasts are never overwritten unless `--force` is passed.
* Re-running after a rehearsal resets advisories to their seeded state (including a live approval you made).
* Uses the app's own ForecastStore, AdvisoryEngine, TemplateLocalizer, AdvisoryReviewStore and risk function.
* The risk score is the app's rule-derived score (levels: low <35, moderate 35-59, high 60-79, critical >=80); it is not an ML output.

## 12 seeded Panchayats

| ID | Panchayat | District | Crop | Scenario | Peak risk |
|---|---|---|---|---|---|
| 206001 | Nalgonda-Rural | Nalgonda | Paddy | Heavy rain (hero story) | HIGH 64.5 |
| 205001 | Hanamkonda | Warangal | Chillies | Cyclonic rain | CRITICAL 80.0 |
| 201003 | Kowkuntla | Rangareddy | Paddy | Disease-favourable | MODERATE 40.0 |
| 202003 | Parigi | Vikarabad | Maize | Moderate heavy rain | MODERATE 39.1 |
| 203001 | Sangareddy-Rural | Sangareddy | Soybean | Warm, humid | LOW 31.4 |
| 204001 | Jadcherla | Mahabubnagar | Groundnut | Unsettled | LOW 17.6 |
| 201004 / 201010 | Aloor / Shamshabad | Rangareddy | Cotton / Chillies | Heat stress | LOW 16.0 |
| 201006 / 202001 | Shabad / Vikarabad-Rural | Rangareddy / Vikarabad | Maize / Red gram | Dry spell | LOW 11.7 |
| 201001 / 201008 | Chevella-A / Moinabad | Rangareddy | Cotton / Red gram | Normal | LOW 2.4 |

Crop-plot details (stage, sowing date, area, irrigation, soil) are stored only in the demo manifest because the
application has no crop-record table.