"""Train a real M1 bundle from a tabular historical dataset.

Expected columns are the feature columns produced by FeaturePipeline plus:
tmax_c, tmin_c, relative_humidity_pct, wind_speed_kmh, rain_mm, valid_date.
The command performs chronological fit/calibration/holdout splits and writes a
versioned joblib bundle plus metrics/model card. It refuses random row splits.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .modeling_engine import CONTINUOUS_VARIABLES, RAIN_THRESHOLDS_MM, QuantileDownscaler, CalibratedRainfallModel
from .evaluator import mae, rmse, bias, brier_score

DEFAULT_FEATURES = (
    "tmax_lapse_adjusted_c","tmin_lapse_adjusted_c","relative_humidity_pct",
    "wind_speed_kmh","rain_mm","elevation_delta_m","slope_deg","aspect_sin",
    "aspect_cos","doy_sin","doy_cos","residual_tmax_c","residual_tmin_c",
    "residual_relative_humidity_pct","residual_wind_speed_kmh","residual_rain_mm",
    "tmax_c_lag1","tmax_c_lead1","tmin_c_lag1","tmin_c_lead1",
    "relative_humidity_pct_lag1","relative_humidity_pct_lead1",
    "wind_speed_kmh_lag1","wind_speed_kmh_lead1","rain_mm_lag1","rain_mm_lead1",
)

def _split_temporal(df: pd.DataFrame, train_fraction: float, calibration_fraction: float, min_partition_rows: int = 30):
    ordered = df.sort_values("valid_date").reset_index(drop=True)
    n=len(ordered); n_fit=int(n*train_fraction); n_cal=int(n*calibration_fraction)
    if min(n_fit,n_cal,n-n_fit-n_cal) < min_partition_rows:
        raise ValueError(f"Need at least {min_partition_rows} rows in each fit, calibration and holdout partition.")
    return ordered.iloc[:n_fit], ordered.iloc[n_fit:n_fit+n_cal], ordered.iloc[n_fit+n_cal:]

def train_real_bundle(input_path: Path, output_dir: Path, version: str, feature_columns=DEFAULT_FEATURES, min_partition_rows: int = 30) -> dict:
    df = pd.read_csv(input_path)
    required=set(feature_columns)|set(CONTINUOUS_VARIABLES)|{"rain_mm","valid_date"}
    missing=sorted(required-set(df.columns))
    if missing: raise ValueError(f"Dataset missing required columns: {missing}")
    df["valid_date"]=pd.to_datetime(df["valid_date"], errors="raise")
    df=df.replace([np.inf,-np.inf],np.nan).dropna(subset=list(required)).copy()
    if len(df)<90: raise ValueError("At least 90 valid historical rows are required.")
    fit, cal, hold = _split_temporal(df, .60, .20, min_partition_rows=min_partition_rows)
    xfit,xcal,xhold=[x.loc[:,feature_columns] for x in (fit,cal,hold)]
    yfit,ycal,yhold=[x.loc[:,CONTINUOUS_VARIABLES] for x in (fit,cal,hold)]
    q=QuantileDownscaler().fit(xfit,yfit)
    rains={}
    for name,threshold in RAIN_THRESHOLDS_MM.items():
        fit_events=(fit["rain_mm"].to_numpy() >= threshold).astype(int)
        cal_events=(cal["rain_mm"].to_numpy() >= threshold).astype(int)
        if np.unique(fit_events).size < 2 or np.unique(cal_events).size < 2:
            raise ValueError(
                f"Rain threshold '{name}' does not have both classes in fit and calibration "
                "periods; expand the historical training window."
            )
        rains[name]=CalibratedRainfallModel(name,threshold,calibration="isotonic").fit(
            xfit,fit["rain_mm"],calibration_features=xcal,calibration_rain_mm=cal["rain_mm"])
    bundle={"model_version":version,"backend":"lightgbm","feature_columns":list(feature_columns),
            "quantile_model":q,"rainfall_models":rains,"training_data_end":str(fit["valid_date"].max().date()),
            "calibration_data_end":str(cal["valid_date"].max().date()),
            "holdout_data_start":str(hold["valid_date"].min().date())}
    output_dir.mkdir(parents=True,exist_ok=True); joblib.dump(bundle,output_dir/"model_bundle.joblib",compress=3)
    preds={v:np.array([q.predict(xhold.iloc[[i]])[v].p50 for i in range(len(xhold))]) for v in CONTINUOUS_VARIABLES}
    metrics={"model_version":version,"rows":{"fit":len(fit),"calibration":len(cal),"holdout":len(hold)},
             "date_ranges":{"fit":[str(fit.valid_date.min().date()),str(fit.valid_date.max().date())],
                            "calibration":[str(cal.valid_date.min().date()),str(cal.valid_date.max().date())],
                            "holdout":[str(hold.valid_date.min().date()),str(hold.valid_date.max().date())]},
             "continuous_holdout":{v:{"mae":mae(yhold[v],preds[v]),"rmse":rmse(yhold[v],preds[v]),"bias":bias(yhold[v],preds[v])} for v in CONTINUOUS_VARIABLES},
             "rainfall_holdout_brier":{}}
    for name,threshold in RAIN_THRESHOLDS_MM.items():
        p=np.array([rains[name].predict_probability(xhold.iloc[[i]]) for i in range(len(xhold))])
        metrics["rainfall_holdout_brier"][name]=brier_score((hold["rain_mm"].to_numpy()>=threshold),p)
    (output_dir/"training_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    (output_dir/"MODEL_CARD.md").write_text(
        f"# {version}\n\nReal-data M1 LightGBM + calibrated rainfall bundle.\n\n"
        f"Temporal partitions: fit {len(fit)}, calibration {len(cal)}, holdout {len(hold)}.\n"
        f"Holdout starts {hold.valid_date.min().date()} and is never used for fitting/calibration.\n",encoding="utf-8")
    return metrics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True); ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--version",required=True)
    ap.add_argument("--min-partition-rows", type=int, default=30,
                    help="Minimum rows per temporal partition; lower only for small synthetic/demo datasets.")
    args=ap.parse_args()
    print(json.dumps(train_real_bundle(args.input,args.output_dir,args.version,
                                       min_partition_rows=args.min_partition_rows),indent=2))
if __name__=="__main__": main()
