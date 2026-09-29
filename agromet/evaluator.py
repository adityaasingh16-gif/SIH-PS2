"""Verification metrics and dynamic baseline comparison scorecards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


def _as_arrays(observed: Sequence[float], predicted: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    actual = np.asarray(observed, dtype=float)
    forecast = np.asarray(predicted, dtype=float)
    if actual.shape != forecast.shape:
        raise ValueError("Observed and predicted arrays must have the same shape.")
    if actual.size == 0:
        raise ValueError("Metric arrays cannot be empty.")
    return actual, forecast


def mae(observed: Sequence[float], predicted: Sequence[float]) -> float:
    actual, forecast = _as_arrays(observed, predicted)
    return float(np.mean(np.abs(forecast - actual)))


def rmse(observed: Sequence[float], predicted: Sequence[float]) -> float:
    actual, forecast = _as_arrays(observed, predicted)
    return float(np.sqrt(np.mean((forecast - actual) ** 2)))


def bias(observed: Sequence[float], predicted: Sequence[float]) -> float:
    actual, forecast = _as_arrays(observed, predicted)
    return float(np.mean(forecast - actual))


def pod(observed_event: Sequence[bool], predicted_event: Sequence[bool]) -> float:
    actual, forecast = _as_arrays(observed_event, predicted_event)
    hits = np.sum((actual == 1) & (forecast == 1))
    misses = np.sum((actual == 1) & (forecast == 0))
    return float(hits / (hits + misses)) if hits + misses else 0.0


def far(observed_event: Sequence[bool], predicted_event: Sequence[bool]) -> float:
    actual, forecast = _as_arrays(observed_event, predicted_event)
    false_alarms = np.sum((actual == 0) & (forecast == 1))
    hits = np.sum((actual == 1) & (forecast == 1))
    return float(false_alarms / (false_alarms + hits)) if false_alarms + hits else 0.0


def csi(observed_event: Sequence[bool], predicted_event: Sequence[bool]) -> float:
    actual, forecast = _as_arrays(observed_event, predicted_event)
    hits = np.sum((actual == 1) & (forecast == 1))
    misses = np.sum((actual == 1) & (forecast == 0))
    false_alarms = np.sum((actual == 0) & (forecast == 1))
    denominator = hits + misses + false_alarms
    return float(hits / denominator) if denominator else 0.0


def brier_score(observed_event: Sequence[bool], probability: Sequence[float]) -> float:
    actual, forecast_probability = _as_arrays(observed_event, probability)
    if np.any((forecast_probability < 0) | (forecast_probability > 1)):
        raise ValueError("Probabilities must be in [0, 1].")
    return float(np.mean((forecast_probability - actual) ** 2))


def brier_skill_score(
    observed_event: Sequence[bool],
    probability: Sequence[float],
    reference_probability: Sequence[float],
) -> float:
    reference = brier_score(observed_event, reference_probability)
    if reference == 0:
        return 0.0
    return float(1.0 - brier_score(observed_event, probability) / reference)


@dataclass(frozen=True, slots=True)
class ModelEvaluation:
    name: str
    mae: float
    rmse: float
    bias: float
    pod: float
    far: float
    csi: float
    brier_score: float
    brier_skill_vs_climatology: float
    brier_skill_vs_block: float


class ScorecardBuilder:
    """Create continuous and rainfall-threshold comparisons for B0/B1/B1b/B2/M1."""

    def evaluate(
        self,
        *,
        observed_weather: Sequence[float],
        predicted_weather: Sequence[float],
        observed_rain_event: Sequence[bool],
        predicted_rain_event: Sequence[bool],
        rain_probability: Sequence[float],
        climatology_probability: Sequence[float],
        block_probability: Sequence[float],
        name: str,
    ) -> ModelEvaluation:
        return ModelEvaluation(
            name=name,
            mae=mae(observed_weather, predicted_weather),
            rmse=rmse(observed_weather, predicted_weather),
            bias=bias(observed_weather, predicted_weather),
            pod=pod(observed_rain_event, predicted_rain_event),
            far=far(observed_rain_event, predicted_rain_event),
            csi=csi(observed_rain_event, predicted_rain_event),
            brier_score=brier_score(observed_rain_event, rain_probability),
            brier_skill_vs_climatology=brier_skill_score(
                observed_rain_event, rain_probability, climatology_probability
            ),
            brier_skill_vs_block=brier_skill_score(
                observed_rain_event, rain_probability, block_probability
            ),
        )

    def markdown(self, evaluations: Sequence[ModelEvaluation]) -> str:
        if not evaluations:
            return "# Agromet verification scorecard\n\n_No evaluation runs available._\n"
        lines = [
            "# Agromet verification scorecard",
            "",
            "Metrics are calculated against AWS ground truth. BSS is positive when the model improves on the named reference.",
            "",
            "| Model | MAE | RMSE | Bias | POD | FAR | CSI | BS | BSS vs B0 | BSS vs B1 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for item in evaluations:
            lines.append(
                f"| {item.name} | {item.mae:.3f} | {item.rmse:.3f} | {item.bias:.3f} | "
                f"{item.pod:.3f} | {item.far:.3f} | {item.csi:.3f} | {item.brier_score:.3f} | "
                f"{item.brier_skill_vs_climatology:.3f} | {item.brier_skill_vs_block:.3f} |"
            )
        return "\n".join(lines) + "\n"

    def compare_baselines(
        self,
        runs: Mapping[
            str,
            tuple[
                Sequence[float],
                Sequence[float],
                Sequence[bool],
                Sequence[bool],
                Sequence[float],
            ],
        ],
        *,
        climatology_probability: Sequence[float],
        block_probability: Sequence[float],
    ) -> str:
        """Build a scorecard for B0, B1, B1b, B2, and M1.

        Each run tuple is (weather_prediction, observed_weather, observed_event,
        predicted_event, calibrated_probability). The observed arrays are shared
        in normal use but are kept in the tuple to make each run self-contained.
        """

        evaluations: list[ModelEvaluation] = []
        first = next(iter(runs.values()), None)
        if first is None:
            return self.markdown([])
        # B0/B1 are included as named rows when their predictions are supplied.
        for name in ("B0", "B1", "B1b", "B2", "M1"):
            if name not in runs:
                continue
            (
                weather_prediction,
                observed_weather,
                observed_event,
                predicted_event,
                probability,
            ) = runs[name]
            evaluations.append(
                self.evaluate(
                    observed_weather=observed_weather,
                    predicted_weather=weather_prediction,
                    observed_rain_event=observed_event,
                    predicted_rain_event=predicted_event,
                    rain_probability=probability,
                    climatology_probability=climatology_probability,
                    block_probability=block_probability,
                    name=name,
                )
            )
        return self.markdown(evaluations)