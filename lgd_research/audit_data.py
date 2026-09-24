"""Pre-model feature support and independently recalculated recovery identities."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    'data/raw/lgd_workout_history.csv': 'd1ff68a25593693039ee00b0d6b7a1f84b226d2d0995d9e6a54a897fcf5de220',
    'lgd_research/data/r2_development.csv': 'b19f397ac75e39687efe5b35d940f6381597fc6800a037b6974b720383bd0216',
    'lgd_research/data/r2_selection.csv': '422b5c75d600675c0f498f6610d69fb8700650b92e006f7cfbc46d635991f652',
    'lgd_research/data/r2_final_holdout.csv': '093a0686316812d0cbf267c42b2a6551d6de6ba21a86529f0ba61f3e1fc2fc59',
    'lgd_research/data/r2_stress_combined.csv': '1222c6e8bdc1311d7a3476e7aeb08e9515e7023323aa67fc302f4087c3be6eed',
}
NAMES = ["H development", "H held out (historically viewed)", "R2 development", "R2 selection", "Current synthetic facilities"]


def load():
    h = pd.read_csv(ROOT / "data/raw/lgd_workout_history.csv")
    a, b = train_test_split(h, test_size=.25, random_state=42)
    return [a, b, pd.read_csv(HERE / "data/r2_development.csv"),
            pd.read_csv(HERE / "data/r2_selection.csv"),
            pd.read_csv(ROOT / "outputs/facility_lgd_predictions.csv")]


def main():
    frames = load()
    records = []
    features = ["ead_at_default", "collateral_coverage", "guarantee_coverage",
                "leverage_at_default", "current_ratio_at_default", "management_quality",
                "product_type", "industry", "collateral_type", "lien_rank",
                "security_quality", "guarantor_strength", "downturn_at_default"]
    for name, frame in zip(NAMES, frames):
        for feature in features:
            if feature not in frame:
                records.append(dict(population=name, feature=feature, n=len(frame), status="not recorded"))
                continue
            x = frame[feature]
            row = dict(population=name, feature=feature, n=len(frame), status="present",
                       missing=int(x.isna().sum()), zero_count=int((x == 0).sum()))
            if pd.api.types.is_numeric_dtype(x):
                row.update(mean=float(x.mean()), minimum=float(x.min()), p05=float(x.quantile(.05)),
                           median=float(x.median()), p95=float(x.quantile(.95)), maximum=float(x.max()))
            else:
                row.update(categories="; ".join(f"{k}: {v}" for k, v in x.value_counts().items()))
            records.append(row)
    pd.DataFrame(records).to_csv(HERE / "results/feature_support.csv", index=False)
    quality = []
    for name, f in zip(NAMES[:4], frames[:4]):
        assert f.facility_id.notna().all() and f.facility_id.is_unique
        assert f.economic_lgd.between(0, 1).all()
        assert (f.ead_at_default > 0).all()
        buckets = [1, 6, 12, 24, 36, 60]
        independent_pv = sum(f[f"recovery_cf_{t}m"] / ((1+f.discount_rate)**(t/12)) for t in buckets)
        # Published H cash flows and discount rates are rounded for storage.
        discrepancy = np.max(abs(independent_pv - f.pv_net_recovery))
        relative_discrepancy = np.max(abs(independent_pv - f.pv_net_recovery)/f.ead_at_default)
        # H stores a rounded rate (five decimals): a large-EAD absolute PV
        # difference can be tens of currency units while LGD changes <2e-5.
        bound = 2e-5 if name.startswith("H") else 1e-10
        assert relative_discrepancy < bound, (name, discrepancy, relative_discrepancy)
        quality.append(dict(population=name, n=len(f), severe_gt75=int((f.economic_lgd>.75).sum()),
                            cure=int(f.cure_flag.sum()), zero_guarantee=int((f.guarantee_coverage==0).sum()),
                            pv_max_absolute_discrepancy=float(discrepancy),
                            pv_max_discrepancy_per_ead=float(relative_discrepancy),
                            mean_lgd=float(f.economic_lgd.mean()), total_ead=float(f.ead_at_default.sum())))
    pd.DataFrame(quality).to_csv(HERE / "results/data_quality.csv", index=False)
    files = [ROOT / "data/raw/lgd_workout_history.csv", HERE / "data/r2_development.csv",
             HERE / "data/r2_selection.csv", HERE / "data/r2_final_holdout.csv",
             HERE / "data/r2_stress_combined.csv"]
    hashes = [dict(file=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                   bytes=p.stat().st_size) for p in files]
    for record in hashes:
        assert record['sha256'] == EXPECTED_HASHES[record['file']], f"Dataset changed: {record['file']}"
    pd.DataFrame(hashes).to_csv(HERE / "results/dataset_hashes.csv", index=False)
    print(pd.DataFrame(quality).to_string(index=False))


if __name__ == "__main__":
    (HERE / "results").mkdir(exist_ok=True)
    main()
