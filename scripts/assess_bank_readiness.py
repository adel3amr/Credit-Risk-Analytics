"""Machine-readable deployment gate; keeps synthetic demonstrations runnable.

Usage: python scripts/assess_bank_readiness.py --purpose bank
The bank mode deliberately fails without institution-specific workout evidence
and an independent approval record. A user-supplied flag cannot waive it.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def assessment():
    path = ROOT / "outputs/lgd_independent_vintage_assessment.csv"
    if not path.is_file():
        return {"status": "BLOCKED", "reason": "Independent LGD assessment missing"}
    df = pd.read_csv(path)
    tail = df.loc[(df.model == "support_corrected") &
                  (df.vintage == "separate_live_profile_seed") &
                  (df.cohort == "realized_above_75pct")]
    if len(tail) != 1:
        return {"status": "BLOCKED", "reason": "Severe-loss validation missing"}
    return {
        "status": "BLOCKED",
        "reason": "Synthetic-only workout data; unresolved severe-loss validation and no institution-specific independent approval",
        "observed_severe_cases": int(tail.iloc[0].facilities),
        "severe_bias_prediction_minus_actual": float(tail.iloc[0].bias),
        "evidence": str(path.relative_to(ROOT)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--purpose", choices=["demo", "bank"], required=True)
    args = parser.parse_args()
    result = assessment()
    result["purpose"] = args.purpose
    result["demo_execution"] = "ALLOWED" if args.purpose == "demo" else "NOT_APPLICABLE"
    print(json.dumps(result, indent=2))
    if args.purpose == "bank":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
