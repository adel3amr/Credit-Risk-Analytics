"""Rebuild V5 from source with the frozen seeds, methodology and execution order."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    'scripts/generate_sme_portfolio.py',
    'scripts/generate_lgd_workout_history.py',
    'notebooks/lgd_model_pipeline.py',
    'notebooks/credit_risk_pipeline.py',
    'notebooks/lgd_governance_diagnostics.py',
    'notebooks/hybrid_pd_experiment.py',
    'scripts/validate_v5.py',
]

if __name__ == '__main__':
    for step in STEPS:
        print(f'Running {step}', flush=True)
        subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT, check=True)
