"""Train a small reproducible LightGBM demo bundle for local integration tests.

This command intentionally uses synthetic pilot data. It proves the model
serialization and API-loading path, but its metrics must not be interpreted as
Telangana skill scores until TGDPS AWS observations are supplied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .evaluator import brier_score, bias, mae, rmse
from .modeling_engine import (
    CONTINUOUS_VARIABLES,
    RAIN_THRESHOLDS_MM,
    CalibratedRainfallModel,
    QuantileDownscaler,
)

DEMO_FEATURES = (
    "tmax_lapse_adjusted_c",
    "tmin_lapse_adjusted_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
    "rain_mm",
    "elevation_delta_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "doy_sin",
    "doy_cos",
    "residual_tmax_c",
    "residual_tmin_c",
    "residual_relative_humidity_pct",
    "residual_wind_speed_kmh",
    "residual_rain_mm",
)


def make_synthetic_dataset(
    rows: int = 720,
    *,
    seed: int = 26074,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Create physically plausible, non-production demonstration records."""

    rng = np.random.default_rng(seed)
    elevation_delta = rng.normal(0.0, 250.0, rows)
    doy_angle = rng.uniform(0.0, 2.0 * np.pi, rows)
    rain_event = rng.random(rows) < 0.38
    rain_mm = np.where(
        rain_event,
        rng.gamma(shape=2.2, scale=7.0, size=rows),
        0.0,
    )
    rain_mm = np.where(rng.random(rows) < 0.04, rain_mm + 55.0, rain_mm)
    features = pd.DataFrame(
        {
            "tmax_lapse_adjusted_c": 31.0 + 5.0 * np.sin(doy_angle) + rng.normal(0, 1.3, rows),
            "tmin_lapse_adjusted_c": 20.0 + 3.5 * np.sin(doy_angle) + rng.normal(0, 0.9, rows),
            "relative_humidity_pct": np.clip(68.0 - 14.0 * np.sin(doy_angle) + rng.normal(0, 7, rows), 20, 100),
            "wind_speed_kmh": np.clip(rng.normal(9.0, 3.5, rows), 0, None),
            "rain_mm": rain_mm,
            "elevation_delta_m": elevation_delta,
            "slope_deg": np.clip(rng.normal(4.0, 2.0, rows), 0, 20),
            "aspect_sin": np.sin(doy_angle),
            "aspect_cos": np.cos(doy_angle),
            "doy_sin": np.sin(doy_angle),
            "doy_cos": np.cos(doy_angle),
            "residual_tmax_c": rng.normal(0, 0.7, rows),
            "residual_tmin_c": rng.normal(0, 0.5, rows),
            "residual_relative_humidity_pct": rng.normal(0, 3.0, rows),
            "residual_wind_speed_kmh": rng.normal(0, 1.0, rows),
            "residual_rain_mm": np.where(rain_event, rng.normal(0, 1.5, rows), 0.0),
        }
    )
    targets = pd.DataFrame(
        {
            "tmax_c": features["tmax_lapse_adjusted_c"]
            + features["residual_tmax_c"]
            + rng.normal(0, 1.1, rows),
            "tmin_c": features["tmin_lapse_adjusted_c"]
            + features["residual_tmin_c"]
            + rng.normal(0, 0.8, rows),
            "relative_humidity_pct": np.clip(
                features["relative_humidity_pct"]
                + features["residual_relative_humidity_pct"]
                + rng.normal(0, 4, rows),
                0,
                100,
            ),
            "wind_speed_kmh": np.clip(
                features["wind_speed_kmh"]
                + features["residual_wind_speed_kmh"]
                + rng.normal(0, 1.5, rows),
                0,
                None,
            ),
        }
    )
    return features.loc[:, DEMO_FEATURES], targets, pd.Series(rain_mm, name="rain_mm")


def train_demo_bundle(output_dir: Path, *, seed: int = 26074) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    features, targets, rain_mm = make_synthetic_dataset(seed=seed)
    (
        x_train,
        x_holdout,
        y_train,
        y_holdout,
        rain_train,
        rain_holdout,
    ) = train_test_split(
        features,
        targets,
        rain_mm,
        test_size=0.25,
        random_state=seed,
    )
    x_fit, x_calibration, fit_targets, calibration_targets = train_test_split(
        x_train,
        y_train.join(rain_train),
        test_size=0.25,
        random_state=seed,
    )
    rain_fit = fit_targets["rain_mm"]
    rain_calibration = calibration_targets["rain_mm"]
    y_fit = fit_targets.loc[:, CONTINUOUS_VARIABLES]
    y_calibration = calibration_targets.loc[:, CONTINUOUS_VARIABLES]

    quantile_model = QuantileDownscaler(random_state=seed).fit(x_fit, y_fit)
    rainfall_models: dict[str, CalibratedRainfallModel] = {}
    for threshold_name, threshold_mm in RAIN_THRESHOLDS_MM.items():
        rainfall_models[threshold_name] = CalibratedRainfallModel(
            threshold_name,
            threshold_mm,
            calibration="isotonic",
            random_state=seed,
        ).fit(
            x_fit,
            rain_fit,
            calibration_features=x_calibration,
            calibration_rain_mm=rain_calibration,
        )

    bundle = {
        "model_version": "m1-demo-synthetic-26074-v1",
        "backend": "lightgbm",
        "feature_columns": list(DEMO_FEATURES),
        "quantile_model": quantile_model,
        "rainfall_models": rainfall_models,
    }
    joblib.dump(bundle, output_dir / "model_bundle.joblib", compress=3)

    predictions = {
        variable: np.asarray(
            [
                quantile_model.predict(x_holdout.iloc[[index]])[variable].p50
                for index in range(len(x_holdout))
            ]
        )
        for variable in CONTINUOUS_VARIABLES
    }
    metrics: dict[str, object] = {
        "model_version": bundle["model_version"],
        "backend": bundle["backend"],
        "training_rows": int(len(x_fit)),
        "calibration_rows": int(len(x_calibration)),
        "holdout_rows": int(len(x_holdout)),
        "continuous_holdout": {
            variable: {
                "mae": mae(y_holdout[variable], predictions[variable]),
                "rmse": rmse(y_holdout[variable], predictions[variable]),
                "bias": bias(y_holdout[variable], predictions[variable]),
            }
            for variable in CONTINUOUS_VARIABLES
        },
        "rainfall_holdout_brier": {},
        "disclaimer": "Synthetic demonstration only; do not report as TGDPS skill.",
    }
    for threshold_name, threshold_mm in RAIN_THRESHOLDS_MM.items():
        probabilities = np.asarray(
            [
                rainfall_models[threshold_name].predict_probability(x_holdout.iloc[[index]])
                for index in range(len(x_holdout))
            ]
        )
        observed = (rain_holdout.to_numpy() >= threshold_mm).astype(int)
        metrics["rainfall_holdout_brier"][threshold_name] = brier_score(observed, probabilities)

    (output_dir / "training_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    (output_dir / "MODEL_CARD.md").write_text(
        "# M1 Demo Model Card\n\n"
        f"- Version: `{bundle['model_version']}`\n"
        "- Backend: LightGBM quantile regressors plus isotonic rainfall calibration\n"
        f"- Fit rows: {len(x_fit)}; calibration rows: {len(x_calibration)}; holdout rows: {len(x_holdout)}\n"
        "- Data: deterministic synthetic pilot data generated by `agromet.train_demo`\n\n"
        "This bundle validates the training, serialization, and API-loading path. "
        "It is not a Telangana performance claim and must be retrained with TGDPS AWS "
        "observations before operational advisory use.\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the reproducible Agromet demo bundle.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("agromet/demo_models/m1-demo-synthetic-26074-v1"),
    )
    parser.add_argument("--seed", type=int, default=26074)
    args = parser.parse_args()
    metrics = train_demo_bundle(args.output_dir, seed=args.seed)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()