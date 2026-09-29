"""Operational forecast refresh scheduler.

Uses the standard library so the pilot can run under systemd, cron, Kubernetes,
or as a long-running process. It calls the same application refresh function.
"""
from __future__ import annotations
import argparse, time
from datetime import datetime, timezone
from .main import refresh_panchayat

def run_once(panchayat_ids: list[str]) -> None:
    for pid in panchayat_ids:
        try:
            result=refresh_panchayat(pid)
            print(f"{datetime.now(timezone.utc).isoformat()} refreshed {pid} {result.model_version}")
        except Exception as exc:
            print(f"{datetime.now(timezone.utc).isoformat()} refresh failed {pid}: {exc}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panchayat",action="append",dest="panchayat_ids",required=True)
    ap.add_argument("--interval-minutes",type=int,default=0)
    args=ap.parse_args()
    if args.interval_minutes<=0: run_once(args.panchayat_ids); return
    while True:
        run_once(args.panchayat_ids); time.sleep(args.interval_minutes*60)
if __name__=="__main__": main()
