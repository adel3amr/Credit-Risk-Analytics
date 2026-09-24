"""Protect observable support and the synthetic-only operating boundary."""
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_live_profile_recovers_zero_guarantee_population(tmp_path):
    target = tmp_path / "resolved.csv"
    subprocess.run([sys.executable, str(ROOT / "scripts/generate_lgd_workout_history.py"),
                    "--n", "1000", "--seed", "435", "--guarantee-profile", "live",
                    "--output", str(target)], check=True, capture_output=True, text=True)
    frame = pd.read_csv(target)
    expected = {"Term Loan": 0., "OVD": 0., "Import LC": .20,
                "Performance Guarantee": .35, "Financial Guarantee": .55}
    assert set(frame.product_type) == set(expected)
    assert frame.groupby("product_type").guarantee_coverage.nunique().eq(1).all()
    for product, coverage in expected.items():
        assert (frame.loc[frame.product_type == product, "guarantee_coverage"] == coverage).all()
    assert frame.economic_lgd.between(0, 1).all()
    assert frame["recovery_cf_60m"].notna().all()


def test_bank_mode_blocks_synthetic_model():
    run = subprocess.run([sys.executable, str(ROOT / "scripts/assess_bank_readiness.py"),
                          "--purpose", "bank"], capture_output=True, text=True)
    assert run.returncode == 2
    assert '"status": "BLOCKED"' in run.stdout
