"""Generate the operational B0/B1/B1b/B2/M1 scorecard from a labelled CSV.

The CSV contains one row per forecast case. For each variable use columns
``observed_<name>``, ``<model>_<name>``; rainfall event columns are
``observed_event_<threshold>`` and probabilities
``<model>_prob_<threshold>``. This keeps evaluation independent of the API.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
from .evaluator import ScorecardBuilder, mae, rmse, bias, brier_score, brier_skill_score

MODELS=("B0","B1","B1b","B2","M1")
VARS=("tmax_c","tmin_c","relative_humidity_pct","wind_speed_kmh")
THRESHOLDS=("light","moderate","heavy","very_heavy")

def evaluate_csv(path: Path) -> dict:
    df=pd.read_csv(path)
    result={"continuous":{},"rainfall":{}}
    for model in MODELS:
        result["continuous"][model]={}
        for var in VARS:
            o=df[f"observed_{var}"].to_numpy(float); p=df[f"{model}_{var}"].to_numpy(float)
            result["continuous"][model][var]={"mae":mae(o,p),"rmse":rmse(o,p),"bias":bias(o,p)}
    for threshold in THRESHOLDS:
        event=df[f"observed_event_{threshold}"].astype(bool).to_numpy()
        result["rainfall"][threshold]={}
        clim=float(event.mean())
        for model in MODELS:
            prob=df[f"{model}_prob_{threshold}"].to_numpy(float)
            bs=brier_score(event,prob)
            result["rainfall"][threshold][model]={"bs":bs,"bss_vs_climatology":brier_skill_score(event,prob,[clim]*len(event))}
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    payload=evaluate_csv(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(json.dumps(payload,indent=2))
if __name__=="__main__": main()
