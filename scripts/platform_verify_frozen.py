"""Read-only hash gate. Never repair, overwrite or regenerate frozen evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = ROOT / "lgd_research/results/dataset_hashes.csv"
import csv

results = []
for row in csv.DictReader(manifest.open()):
    p = ROOT / row["file"]
    actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    results.append(
        {
            "file": row["file"],
            "expected": row["sha256"],
            "actual": actual,
            "match": actual == row["sha256"],
        }
    )
print(json.dumps(results, indent=2))
if not all(r["match"] for r in results):
    raise SystemExit(2)
