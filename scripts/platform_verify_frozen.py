"""Read-only hash gate. Never repair, overwrite or regenerate frozen evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = ROOT / "lgd_research/results/dataset_hashes.csv"
import csv

expected = {row["file"]: row["sha256"] for row in csv.DictReader(manifest.open())}
# Include borrower and conduct sources, not only workout/research populations.
for row in json.loads((ROOT / "platform_evidence/baseline_hashes.json").read_text()):
    if row["file"].startswith("data/raw/"):
        if row["file"] in expected and expected[row["file"]] != row["sha256"]:
            raise ValueError("Conflicting frozen manifests")
        expected[row["file"]] = row["sha256"]
results = []
for name, sha in sorted(expected.items()):
    row = {"file": name, "sha256": sha}
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
