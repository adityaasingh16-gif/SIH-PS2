"""Probabilistic downscaling, calibration, and physical post-processing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
except (ImportError, OSError):  # pragma: no cover - depends on deployment environment
    # LightGBM loads a native OpenMP library at import time. Keeping this
    # optional lets ET0, rules, feature QA, and the API run without the trainer.
    LGBMClassifier = None  # type: ignore[assignment,misc]
    LGBMRegressor = None  # type: ignore[assignment,misc]

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ModelDependencyError(RuntimeError):
    """Raised when training is requested without LightGBM installed."""


class ModelNotFittedError(RuntimeError):
    """Raised when inference is requested before fitting."""


CONTINUOUS_VARIABLES = (
    "tmax_c",
    "tmin_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
)
RAIN_THRESHOLDS_MM: Mapping[str, float] = {
    "light": 1.0,
    "moderate": 2.5,
    "heavy": 15.6,
    "very_heavy": 64.5,
}


@dataclass(frozen=True, slots=True)
class QuantileForecast:
    """P10/P50/P90 forecast for one continuous variable."""

    p10: float
    p50: float
    p90: float


@dataclass(frozen=True, slots=True)
class DownscaledPrediction:
    """One Panchayat-level prediction after physical constraints."""

    continuous: Mapping[str, QuantileForecast]
    rainfall_probabilities: Mapping[str, float]
    rain_mm: float


class QuantileDownscaler:
    """One LightGBM quantile regressor per variable and requested alpha."""

    def __init__(
        self,
        *,
        alphas: Sequence[float] = (0.10, 0.50, 0.90),
        random_state: int = 42,
    ) -> None:
        self.alphas = tuple(alphas)
        self.random_state = random_state
        self._models: dict[str, dict[float, object]] = {}
        self.feature_columns: tuple[str, ...] = ()

    def fit(self, features: pd.DataFrame, targets: pd.DataFrame) -> "QuantileDownscaler":
        if LGBMRegressor is None:
            raise ModelDependencyError(
                "LightGBM is required for training. Install requirements.txt first."
            )
        missing = [name for name in CONTINUOUS_VARIABLES if name not in targets]
        if missing:
            raise ValueError(f"Missing continuous training targets: {missing}")
        self.feature_columns = tuple(features.columns)
        for variable in CONTINUOUS_VARIABLES:
            self._models[variable] = {}
            for alpha in self.alphas:
                model = LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=250,
                    learning_rate=0.04,
                    num_leaves=31,
                    random_state=self.random_state,
                    verbosity=-1,
                )
                model.fit(features, targets[variable])
                self._models[variable][alpha] = model
        return self

    def predict(self, features: pd.DataFrame) -> dict[str, QuantileForecast]:
        if not self._models:
            raise ModelNotFittedError("Call QuantileDownscaler.fit before predict.")
        aligned = features.loc[:, self.feature_columns]
        result: dict[str, QuantileForecast] = {}
        for variable in CONTINUOUS_VARIABLES:
            values = {
                alpha: float(np.asarray(model.predict(aligned))[0])
                for alpha, model in self._models[variable].items()
            }
            result[variable] = QuantileForecast(
                p10=values.get(0.10, values[min(values)]),
                p50=values.get(0.50, values[min(values)]),
                p90=values.get(0.90, values[max(values)]),
            )
        return result


class CalibratedRainfallModel:
    """Rain-threshold LightGBM classifier with isotonic or Platt calibration."""

    def __init__(
        self,
        threshold_name: str,
        threshold_mm: float,
        *,
        calibration: str = "isotonic",
        random_state: int = 42,
    ) -> None:
        if calibration not in {"isotonic", "platt"}:
            raise ValueError("calibration must be 'isotonic' or 'platt'")
        self.threshold_name = threshold_name
        self.threshold_mm = threshold_mm
        self.calibration = calibration
        self.random_state = random_state
        self._classifier: object | None = None
        self._calibrator: IsotonicRegression | LogisticRegression | None = None
        self.feature_columns: tuple[str, ...] = ()

    def fit(
        self,
        features: pd.DataFrame,
        rain_mm: pd.Series,
        *,
        calibration_features: pd.DataFrame | None = None,
        calibration_rain_mm: pd.Series | None = None,
    ) -> "CalibratedRainfallModel":
        if LGBMClassifier is None:
            raise ModelDependencyError(
                "LightGBM is required for rainfall model training."
            )
        labels = (rain_mm.to_numpy() >= self.threshold_mm).astype(int)
        if np.unique(labels).size < 2:
            raise ValueError(
                f"Rain threshold '{self.threshold_name}' needs both positive and negative samples."
            )
        self.feature_columns = tuple(features.columns)
        classifier = LGBMClassifier(
            objective="binary",
            n_estimators=250,
            learning_rate=0.04,
            num_leaves=31,
            random_state=self.random_state,
            verbosity=-1,
        )
        classifier.fit(features, labels)
        self._classifier = classifier

        calibration_features = calibration_features if calibration_features is not None else features
        calibration_rain_mm = (
            calibration_rain_mm if calibration_rain_mm is not None else rain_mm
        )
        calibration_labels = (
            calibration_rain_mm.to_numpy() >= self.threshold_mm
        ).astype(int)
        raw = np.asarray(classifier.predict_proba(calibration_features))[:, 1]
        if self.calibration == "isotonic":
            calibrator: IsotonicRegression | LogisticRegression = IsotonicRegression(
                y_min=0.0, y_max=1.0, out_of_bounds="clip"
            )
            calibrator.fit(raw, calibration_labels)
        else:
            calibrator = LogisticRegression()
            calibrator.fit(raw.reshape(-1, 1), calibration_labels)
        self._calibrator = calibrator
        return self

    def predict_probability(self, features: pd.DataFrame) -> float:
        if self._classifier is None or self._calibrator is None:
            raise ModelNotFittedError(
                f"Rain model '{self.threshold_name}' is not fitted."
            )
        aligned = features.loc[:, self.feature_columns]
        raw = float(np.asarray(self._classifier.predict_proba(aligned))[0, 1])
        if isinstance(self._calibrator, IsotonicRegression):
            calibrated = float(self._calibrator.predict([raw])[0])
        else:
            calibrated = float(self._calibrator.predict_proba([[raw]])[0, 1])
        return float(np.clip(calibrated, 0.0, 1.0))


def apply_physical_constraints(
    continuous: Mapping[str, QuantileForecast],
    *,
    rain_mm: float,
) -> tuple[dict[str, QuantileForecast], float]:
    """Apply meteorological bounds and preserve quantile ordering."""

    constrained: dict[str, QuantileForecast] = {}
    for variable, forecast in continuous.items():
        values = np.sort(
            np.asarray([forecast.p10, forecast.p50, forecast.p90], dtype=float)
        )
        if variable == "relative_humidity_pct":
            values = np.clip(values, 0.0, 100.0)
        elif variable == "wind_speed_kmh":
            values = np.maximum(values, 0.0)
        constrained[variable] = QuantileForecast(*map(float, values))

    if "tmin_c" in constrained and "tmax_c" in constrained:
        tmin = constrained["tmin_c"]
        tmax = constrained["tmax_c"]
        corrected_tmax = np.maximum(
            np.asarray([tmax.p10, tmax.p50, tmax.p90]),
            np.asarray([tmin.p10, tmin.p50, tmin.p90]),
        )
        constrained["tmax_c"] = QuantileForecast(*map(float, corrected_tmax))
    return constrained, max(0.0, float(rain_mm))


def conserve_block_mean(
    values: Sequence[float],
    block_mean: float,
    *,
    variance_retention: float = 0.85,
) -> np.ndarray:
    """Correct the Panchayat mean while retaining bounded local variability."""

    if not 0.0 <= variance_retention <= 1.0:
        raise ValueError("variance_retention must be between 0 and 1.")
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return array
    local_mean = float(np.mean(array))
    centered = array - local_mean
    return float(block_mean) + centered * variance_retention


class DownscalingEngine:
    """Coordinates continuous models, calibrated rain probabilities, and physics."""

    def __init__(
        self,
        quantile_model: QuantileDownscaler,
        rainfall_models: Mapping[str, CalibratedRainfallModel],
    ) -> None:
        self.quantile_model = quantile_model
        self.rainfall_models = dict(rainfall_models)

    def predict(self, features: pd.DataFrame) -> DownscaledPrediction:
        continuous = self.quantile_model.predict(features.iloc[[0]])
        rain_probabilities = {
            name: model.predict_probability(features.iloc[[0]])
            for name, model in self.rainfall_models.items()
        }
        expected_rain = sum(
            probability * RAIN_THRESHOLDS_MM.get(name, 0.0)
            for name, probability in rain_probabilities.items()
        )
        continuous, rain_mm = apply_physical_constraints(
            continuous, rain_mm=expected_rain
        )
        return DownscaledPrediction(continuous, rain_probabilities, rain_mm)


def load_model_bundle(path: str | Path) -> tuple[DownscalingEngine, str]:
    """Load a versioned model bundle produced by a training job."""

    try:
        import joblib
    except ImportError as exc:  # pragma: no cover - package install concern
        raise ModelDependencyError("joblib is required to load a model bundle.") from exc
    bundle = joblib.load(path)
    if not isinstance(bundle, dict):
        raise ModelDependencyError("Model bundle must be a dictionary.")
    if "quantile_model" not in bundle or "rainfall_models" not in bundle:
        raise ModelDependencyError(
            "Model bundle must contain quantile_model and rainfall_models."
        )
    return (
        DownscalingEngine(bundle["quantile_model"], bundle["rainfall_models"]),
        str(bundle.get("model_version", "m1-unversioned")),
    )


def physics_baseline_predict(features: pd.DataFrame) -> DownscaledPrediction:
    """Return a transparent live-ingestion baseline when M1 artifacts are absent.

    This is not presented as a trained replacement for LightGBM. It provides a
    physically adjusted, operationally useful forecast and keeps the API
    available while a versioned M1 model bundle is being deployed.
    """

    if features.empty:
        raise ValueError("At least one feature row is required.")
    row = features.iloc[0]

    def interval(center: float, spread: float) -> QuantileForecast:
        return QuantileForecast(
            p10=float(center - spread),
            p50=float(center),
            p90=float(center + spread),
        )

    tmax = float(row["tmax_lapse_adjusted_c"]) + float(row.get("residual_tmax_c", 0.0))
    tmin = float(row["tmin_lapse_adjusted_c"]) + float(row.get("residual_tmin_c", 0.0))
    humidity = float(row["relative_humidity_pct"]) + float(
        row.get("residual_relative_humidity_pct", 0.0)
    )
    wind = max(0.0, float(row["wind_speed_kmh"]) + float(row.get("residual_wind_speed_kmh", 0.0)))
    rain = max(0.0, float(row["rain_mm"]) + float(row.get("residual_rain_mm", 0.0)))
    continuous = {
        "tmax_c": interval(tmax, 1.5),
        "tmin_c": interval(tmin, 1.5),
        "relative_humidity_pct": interval(float(np.clip(humidity, 0.0, 100.0)), 5.0),
        "wind_speed_kmh": interval(wind, 2.0),
    }
    continuous, rain = apply_physical_constraints(continuous, rain_mm=rain)
    probabilities = {
        name: float(np.clip(0.02 if rain <= 0 else rain / threshold, 0.02, 0.98))
        for name, threshold in RAIN_THRESHOLDS_MM.items()
    }
    return DownscaledPrediction(continuous, probabilities, rain)