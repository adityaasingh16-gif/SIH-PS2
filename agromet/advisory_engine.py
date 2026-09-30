"""Deterministic, reviewable agrometeorological advisory rules."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field


class AdvisoryKind(str, Enum):
    SPRAYING_WINDOW = "spraying_window"
    UREA_TOPDRESSING = "urea_topdressing"
    RICE_BLAST = "rice_blast"
    COTTON_BOLLWORM = "cotton_bollworm"
    HEAVY_RAIN_DRAINAGE = "heavy_rain_drainage"
    HEAT_STRESS = "heat_stress"
    HIGH_WIND_WARNING = "high_wind_warning"


class AdvisoryStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"


class ForecastDay(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    valid_date: date
    tmax_c: float
    tmin_c: float
    relative_humidity_pct: float = Field(ge=0.0, le=100.0)
    wind_speed_kmh: float = Field(ge=0.0)
    rain_probability_next_6h: float = Field(ge=0.0, le=1.0)
    rain_probability_15_6mm: float = Field(ge=0.0, le=1.0)


class ET0Inputs(BaseModel):
    """Daily FAO-56 Penman-Monteith inputs in SI-compatible units."""

    model_config = ConfigDict(extra="forbid", strict=True)

    tmax_c: float
    tmin_c: float
    relative_humidity_pct: float = Field(ge=0.0, le=100.0)
    wind_speed_2m_ms: float = Field(ge=0.0)
    net_radiation_mj_m2_day: float = Field(ge=0.0)
    elevation_m: float = Field(ge=-500.0)


class Advisory(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    advisory_id: str
    panchayat_id: str
    kind: AdvisoryKind
    status: AdvisoryStatus = AdvisoryStatus.PENDING_REVIEW
    rule: str
    trigger_metrics: dict[str, float | int | str]
    valid_from: date
    valid_to: date
    message_key: str
    reviewer_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdvisoryBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    panchayat_id: str
    generated_at: date
    advisories: list[Advisory]


class LocalizedAdvisory(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    advisory_id: str
    language: Literal["en", "te", "hi"]
    text: str
    source_metrics: dict[str, float | int | str]


def calculate_et0_fao56(inputs: ET0Inputs) -> float:
    """Calculate daily reference ET0 (mm/day) using FAO-56 Eq. 6.

    The caller supplies net radiation, so the method is usable with satellite or
    station radiation products without embedding a radiation provider.
    """

    t_mean = (inputs.tmax_c + inputs.tmin_c) / 2.0
    delta = (
        4098
        * (0.6108 * (2.718281828459045 ** (17.27 * t_mean / (t_mean + 237.3))))
        / (t_mean + 237.3) ** 2
    )
    pressure_kpa = 101.3 * ((293.0 - 0.0065 * inputs.elevation_m) / 293.0) ** 5.26
    gamma = 0.000665 * pressure_kpa
    saturation_tmax = 0.6108 * (
        2.718281828459045 ** (17.27 * inputs.tmax_c / (inputs.tmax_c + 237.3))
    )
    saturation_tmin = 0.6108 * (
        2.718281828459045 ** (17.27 * inputs.tmin_c / (inputs.tmin_c + 237.3))
    )
    saturation_vapour_pressure = (saturation_tmax + saturation_tmin) / 2.0
    actual_vapour_pressure = saturation_vapour_pressure * (
        inputs.relative_humidity_pct / 100.0
    )
    vapour_pressure_deficit = max(0.0, saturation_vapour_pressure - actual_vapour_pressure)
    numerator = (
        0.408 * delta * inputs.net_radiation_mj_m2_day
        + gamma * (900.0 / (t_mean + 273.0)) * inputs.wind_speed_2m_ms * vapour_pressure_deficit
    )
    denominator = delta + gamma * (1.0 + 0.34 * inputs.wind_speed_2m_ms)
    return max(0.0, numerator / denominator) if denominator > 0 else 0.0


class AdvisoryEngine:
    """Generate only rule-derived outputs; language rendering is separate."""

    def generate(
        self,
        panchayat_id: str,
        forecast: Sequence[ForecastDay],
        *,
        et0_inputs: ET0Inputs | None = None,
        generated_at: date | None = None,
    ) -> AdvisoryBatch:
        if not forecast:
            raise ValueError("At least one forecast day is required.")
        ordered = sorted(forecast, key=lambda item: item.valid_date)
        advisories: list[Advisory] = []

        first = ordered[0]
        if (
            2.0 <= first.wind_speed_kmh <= 12.0
            and 50.0 <= first.relative_humidity_pct <= 80.0
            and first.rain_probability_next_6h < 0.20
        ):
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.SPRAYING_WINDOW,
                    first.valid_date,
                    first.valid_date,
                    "spraying_window_ready",
                    "wind_2_12_kmh_rh_50_80_rain_lt_20pct",
                    {
                        "wind_speed_kmh": first.wind_speed_kmh,
                        "relative_humidity_pct": first.relative_humidity_pct,
                        "rain_probability_next_6h": first.rain_probability_next_6h,
                    },
                )
            )

        heavy_probability_48h = self._aggregate_heavy_probability(ordered[:2])
        if heavy_probability_48h >= 0.60:
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.UREA_TOPDRESSING,
                    ordered[0].valid_date,
                    ordered[min(1, len(ordered) - 1)].valid_date,
                    "urea_topdressing_delay",
                    "probability_rain_ge_15_6mm_48h_ge_60pct",
                    {"probability_rain_ge_15_6mm_48h": heavy_probability_48h},
                )
            )

        for start, end in self._rice_blast_windows(ordered):
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.RICE_BLAST,
                    start.valid_date,
                    end.valid_date,
                    "rice_blast_risk",
                    "rh_ge_90_temp_20_28_for_at_least_3_days",
                    {
                        "consecutive_days": (end.valid_date - start.valid_date).days + 1,
                        "minimum_relative_humidity_pct": min(
                            day.relative_humidity_pct
                            for day in ordered
                            if start.valid_date <= day.valid_date <= end.valid_date
                        ),
                    },
                )
            )

        # Cotton bollworm / sucking pest risk: Sustained warm & humid conditions
        cotton_days = [d for d in ordered if d.relative_humidity_pct >= 70.0 and 22.0 <= d.tmin_c <= 32.0]
        if len(cotton_days) >= 2:
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.COTTON_BOLLWORM,
                    cotton_days[0].valid_date,
                    cotton_days[-1].valid_date,
                    "cotton_bollworm_risk",
                    "rh_ge_70_temp_22_32_warm_humid",
                    {
                        "humidity_pct": cotton_days[0].relative_humidity_pct,
                        "consecutive_days": len(cotton_days),
                    },
                )
            )

        # Heavy rain & waterlogging drainage alert
        high_rain_days = [d for d in ordered if d.rain_probability_15_6mm >= 0.50]
        if high_rain_days:
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.HEAVY_RAIN_DRAINAGE,
                    high_rain_days[0].valid_date,
                    high_rain_days[-1].valid_date,
                    "heavy_rain_drainage_alert",
                    "heavy_rain_probability_ge_50pct",
                    {
                        "rain_probability": high_rain_days[0].rain_probability_15_6mm,
                    },
                )
            )

        # Extreme Heat stress alert
        hot_days = [d for d in ordered if d.tmax_c >= 38.0]
        if hot_days:
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.HEAT_STRESS,
                    hot_days[0].valid_date,
                    hot_days[-1].valid_date,
                    "heat_stress_precautions",
                    "tmax_ge_38c",
                    {
                        "tmax_c": hot_days[0].tmax_c,
                    },
                )
            )

        # High wind speed alert
        windy_days = [d for d in ordered if d.wind_speed_kmh >= 22.0]
        if windy_days:
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.HIGH_WIND_WARNING,
                    windy_days[0].valid_date,
                    windy_days[-1].valid_date,
                    "high_wind_lodging_risk",
                    "wind_speed_ge_22kmh",
                    {
                        "wind_speed_kmh": windy_days[0].wind_speed_kmh,
                    },
                )
            )

        if et0_inputs is not None:
            et0 = calculate_et0_fao56(et0_inputs)
            advisories.append(
                self._advisory(
                    panchayat_id,
                    AdvisoryKind.SPRAYING_WINDOW,
                    first.valid_date,
                    first.valid_date,
                    "et0_reference",
                    "fao_56_penman_monteith",
                    {"et0_mm_day": et0},
                )
            )

        return AdvisoryBatch(
            panchayat_id=panchayat_id,
            generated_at=generated_at or first.valid_date,
            advisories=advisories,
        )

    @staticmethod
    def _aggregate_heavy_probability(forecast: Sequence[ForecastDay]) -> float:
        no_event = 1.0
        for day in forecast:
            no_event *= 1.0 - day.rain_probability_15_6mm
        return 1.0 - no_event

    @staticmethod
    def _rice_blast_windows(
        forecast: Sequence[ForecastDay],
    ) -> list[tuple[ForecastDay, ForecastDay]]:
        windows: list[tuple[ForecastDay, ForecastDay]] = []
        run: list[ForecastDay] = []
        for day in forecast:
            qualifies = (
                day.relative_humidity_pct >= 90.0
                and 20.0 <= day.tmin_c <= 28.0
                and 20.0 <= day.tmax_c <= 28.0
            )
            if qualifies:
                run.append(day)
            else:
                if len(run) >= 3:
                    windows.append((run[0], run[-1]))
                run = []
        if len(run) >= 3:
            windows.append((run[0], run[-1]))
        return windows

    @staticmethod
    def _advisory(
        panchayat_id: str,
        kind: AdvisoryKind,
        valid_from: date,
        valid_to: date,
        message_key: str,
        rule: str,
        metrics: Mapping[str, float | int | str],
    ) -> Advisory:
        return Advisory(
            advisory_id=f"{panchayat_id}:{kind.value}:{valid_from.isoformat()}",
            panchayat_id=panchayat_id,
            kind=kind,
            rule=rule,
            trigger_metrics=dict(metrics),
            valid_from=valid_from,
            valid_to=valid_to,
            message_key=message_key,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


class TemplateLocalizer:
    """Translate approved structured outputs without changing their metrics."""

    _TEMPLATES: Mapping[str, Mapping[str, str]] = {
        "en": {
            "spraying_window_ready": "Spraying window is suitable: wind {wind_speed_kmh:.1f} km/h, RH {relative_humidity_pct:.0f}%, rain probability {rain_probability_next_6h:.0%}.",
            "urea_topdressing_delay": "Delay urea topdressing: probability of rain >=15.6 mm in 48 hours is {probability_rain_ge_15_6mm_48h:.0%}.",
            "rice_blast_risk": "Rice blast risk is elevated for {consecutive_days} consecutive days. Minimum RH is {minimum_relative_humidity_pct:.0f}%.",
            "cotton_bollworm_risk": "Cotton pest/bollworm risk elevated due to warm humid weather (RH {humidity_pct:.0f}%). Inspect squares & bolls.",
            "heavy_rain_drainage_alert": "Heavy rainfall expected ({rain_probability:.0%} chance). Ensure field drainage channels are clear to prevent waterlogging.",
            "heat_stress_precautions": "Heat stress warning (Max Temp {tmax_c:.1f}°C). Provide light, frequent evening irrigation and mulch crops.",
            "high_wind_lodging_risk": "High wind velocity ({wind_speed_kmh:.1f} km/h). Postpone foliar spraying and provide staking support for tall crops.",
            "et0_reference": "Reference evapotranspiration is {et0_mm_day:.2f} mm/day.",
        },
        "te": {
            "spraying_window_ready": "పిచికారీకి అనుకూల సమయం: గాలి {wind_speed_kmh:.1f} కి.మీ/గం, RH {relative_humidity_pct:.0f}%, వర్షం అవకాశం {rain_probability_next_6h:.0%}.",
            "urea_topdressing_delay": "యూరియా పై ఎరువు వేయడం ఆలస్యం చేయండి: 48 గంటల్లో 15.6 మి.మీ లేదా అంతకంటే ఎక్కువ వర్షం అవకాశం {probability_rain_ge_15_6mm_48h:.0%}.",
            "rice_blast_risk": "వరి బ్లాస్ట్ వ్యాధి ప్రమాదం ఎక్కువగా ఉంది: వరుసగా {consecutive_days} రోజులు. కనిష్ఠ RH {minimum_relative_humidity_pct:.0f}%.",
            "cotton_bollworm_risk": "పత్తిలో పురుగుల/కాయతొలుచు పురుగు ఉధృతి అవకాశం (తేమ {humidity_pct:.0f}%). పంటను గమనించండి.",
            "heavy_rain_drainage_alert": "భారీ వర్ష సూచన ({rain_probability:.0%} అవకాశం). పొలంలో నీరు నిల్వ ఉండకుండా మురుగు కాలువలు సిద్ధం చేసుకోండి.",
            "heat_stress_precautions": "ఎండ తీవ్రత హెచ్చరిక (గరిష్ఠ ఉష్ణోగ్రత {tmax_c:.1f}°C). సాయంత్రం వేళల్లో తేలికపాటి నీటి తడులు ఇవ్వండి.",
            "high_wind_lodging_risk": "ఈదురు గాలుల ప్రమాదం ({wind_speed_kmh:.1f} కి.మీ/గం). పురుగుమందుల పిచికారీని వాయిదా వేయండి.",
            "et0_reference": "సూచిక ఆవిరీభవన-ఉత్సర్జన {et0_mm_day:.2f} మి.మీ/రోజు.",
        },
        "hi": {
            "spraying_window_ready": "छिड़काव के लिए समय उपयुक्त है: हवा {wind_speed_kmh:.1f} किमी/घंटा, RH {relative_humidity_pct:.0f}%, वर्षा की संभावना {rain_probability_next_6h:.0%}।",
            "urea_topdressing_delay": "यूरिया की टॉप ड्रेसिंग स्थगित करें: 48 घंटे में 15.6 मिमी या अधिक वर्षा की संभावना {probability_rain_ge_15_6mm_48h:.0%} है।",
            "rice_blast_risk": "धान ब्लास्ट रोग का जोखिम बढ़ा हुआ है: लगातार {consecutive_days} दिन। न्यूनतम RH {minimum_relative_humidity_pct:.0f}% है।",
            "cotton_bollworm_risk": "कपास में कीट/गुलाबी सुंडी का प्रकोप संभव (नमी {humidity_pct:.0f}%)। खेतों का नियमित निरीक्षण करें।",
            "heavy_rain_drainage_alert": "भारी वर्षा की संभावना ({rain_probability:.0%})। जलभराव रोकने के लिए जल निकासी नालियां साफ रखें।",
            "heat_stress_precautions": "तापमान वृद्धि/लू की चेतावनी (अधिकतम {tmax_c:.1f}°C)। शाम के समय हल्की सिंचाई करें।",
            "high_wind_lodging_risk": "तेज हवा का खतरा ({wind_speed_kmh:.1f} किमी/घंटा)। छिड़काव स्थगित रखें एवं सहारा प्रदान करें।",
            "et0_reference": "संदर्भ वाष्पोत्सर्जन {et0_mm_day:.2f} मिमी/दिन है।",
        },
    }

    def render(self, advisory: Advisory, language: Literal["en", "te", "hi"]) -> LocalizedAdvisory:
        template = self._TEMPLATES.get(language, self._TEMPLATES["en"]).get(advisory.message_key)
        if template is None:
            template = self._TEMPLATES["en"].get(advisory.message_key, "Advisory: {rule}")
        numeric_metrics = {
            key: value
            for key, value in advisory.trigger_metrics.items()
            if isinstance(value, (int, float))
        }
        try:
            text = template.format(**numeric_metrics)
        except Exception:
            text = template
        return LocalizedAdvisory(
            advisory_id=advisory.advisory_id,
            language=language,
            text=text,
            source_metrics=dict(advisory.trigger_metrics),
        )