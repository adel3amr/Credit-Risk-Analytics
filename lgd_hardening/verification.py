"""Integrity, independent arithmetic and factual local-test evidence snapshot."""
import json
import os
import re
import subprocess
import sys
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,file_hash,atomic_json
from s2_remediation.evaluate import verify,verify_lock
from .audit import OUT


def main():
    verify();verify_lock()
    run=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True,
        env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'})
    output=run.stdout+run.stderr
    print(output,flush=True)
    (OUT/'pytest.txt').write_text(output)
    matches=re.findall(r'(\d+) passed',output)
    if run.returncode or not matches or re.search(r'\d+ skipped',output):
        raise ValueError('Complete test suite did not pass without skips; do not publish signoff')
    rows=[]
    for cohort in ['current','promotion']:
        original=pd.read_csv(ROOT/f's2_remediation/results/{cohort}_predictions.csv')
        trial=pd.read_csv(OUT/f'{cohort}_calibration_engineering.csv')
        if not original[['facility_id','scenario']].equals(trial[['facility_id','scenario']]):
            raise ValueError('Prediction identity mismatch')
        for scenario,g in trial.groupby('scenario'):
            for model in ['incumbent','original_s2','corrected','calibrated']:
                e=g[model]-g.actual;c=g[model]-g.conditional_mean
                rows.append(dict(cohort=cohort,scenario=scenario,model=model,n=len(g),
                    mae=float(np.abs(e).mean()),rmse=float(np.sqrt(np.mean(e**2))),
                    realized_bias=float(e.mean()),conditional_bias=float(c.mean()),
                    role='KNOWN ENGINEERING; NOT NEW FINAL'))
    pd.DataFrame(rows).to_csv(OUT/'independent_metric_recalculation.csv',index=False)
    ecl=pd.read_csv(ROOT/'s2_remediation/results/scenario_ecl.csv')
    independent=.2*ecl.ecl_upside+.6*ecl.ecl_baseline+.2*ecl.ecl_downside
    discrepancy=float(np.max(np.abs(independent-ecl.corrected_ecl)))
    aggregation=float(abs(ecl.groupby('borrower_id').corrected_ecl.sum().sum()-ecl.corrected_ecl.sum()))
    if discrepancy>1e-7 or aggregation>1e-6:raise ValueError('ECL reconciliation failed')
    atomic_json(OUT/'verification.json',dict(
        local_tests={'command':'OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python -m pytest -q',
                     'observed_passed':int(matches[-1]),'exit_code':run.returncode,
                     'observed_failed':0,'observed_skipped':0,
                     'output_sha256':file_hash(OUT/'pytest.txt'),
                     'warning':'See captured pytest.txt'},
        source_hashes={str(p.relative_to(ROOT)):file_hash(p) for directory in ['lgd_hardening','credit_platform','tests/platform']
                       for p in sorted((ROOT/directory).glob('*.py'))},
        ecl_arithmetic_error=discrepancy,borrower_portfolio_error=aggregation,
        frozen_predecessor_hashes_verified=True,new_final_holdout_opened=False,
        external_ci_run=False,bank_gate='BLOCKED'))
    print('Frozen evidence, independent metrics and ECL arithmetic verified')


if __name__=='__main__':main()
