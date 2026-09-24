"""Fail-closed, evidence-based research promotion gate; no numeric pass tuning."""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def assess():
    reasons=[]
    lock = HERE/'FINAL_EVALUATION_LOCK.md'
    final = HERE/'results/final_scorecard.csv'
    if not lock.exists() or not final.exists():
        reasons.append('Precommitted independent research evaluation missing')
    if final.exists():
        f=pd.read_csv(final)
        subset=f[(f.model=='two-stage enhanced R2')&(f.cohort=='realized_gt75')]
        if len(subset)!=1:
            reasons.append('Severe-loss result missing')
        else:
            reasons.append(f'Severe realized LGD >75% has prediction-minus-actual bias {subset.iloc[0].bias:+.4f} over {int(subset.iloc[0].n)} cases')
    live=ROOT/'outputs/facility_lgd_predictions.csv'
    if not live.exists():
        reasons.append('Current-facility input dataset missing')
    else:
        missing={'security_quality','guarantor_strength','downturn_at_default'}-set(pd.read_csv(live,nrows=1).columns)
        if missing: reasons.append(f'Research feature inputs absent from current portfolio: {sorted(missing)}')
    reasons.append('No observed institution-specific recovery vintages or independent bank-methodology approval')
    return dict(status='BLOCKED',incumbent_reference='0dfe4c8',research_branch='research/lgd-tail-programme',
                methodology_promoted=False, reasons=reasons)


if __name__=='__main__':
    print(json.dumps(assess(),indent=2))
    raise SystemExit(2)
