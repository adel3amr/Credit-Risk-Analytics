"""Exact fixed-parameter refit check; no selection or final-outcome access."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import joblib
import numpy as np
from credit_platform.common import atomic_json,file_hash
from s2_remediation.evaluate import load,verify,verify_lock,OUT
from s2_remediation.model import build,features,predict


def main():
    verify();verify_lock()
    frame,outcomes=load('development')
    rebuilt=build(frame).fit(features(frame),outcomes.economic_lgd.to_numpy())
    audit,_=load('calibration')
    frozen=joblib.load(OUT/'model.joblib')
    error=float(np.max(np.abs(predict(frozen,audit)-predict(rebuilt,audit))))
    if error>1e-12: raise ValueError(f'Fixed candidate not reproduced: {error}')
    atomic_json(OUT/'reproducibility.json',dict(passed=True,
        max_calibration_prediction_difference=error,n=len(audit),
        training_data_manifest_sha256=file_hash(ROOT/'s2_remediation/data/manifest.json'),
        frozen_model_sha256=file_hash(OUT/'model.joblib'),
        final_outcomes_used=False,method='Identical development data, parameters, features and seed; no refit saved or selected'))
    print('Fixed candidate refit reproduced; maximum prediction difference:',error)


if __name__=='__main__':main()
