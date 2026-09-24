"""Trusted local reference artifact build; never deserialize user-supplied models."""

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from .common import ROOT, atomic_json, file_hash
from src.data_preparation import prepare_data, pd_feature_columns
from src.pd_model import logistic_model
from src.lgd_model import gradient_boosting_lgd_model

MODEL_DIR = ROOT / "models/platform"
SOURCES = [
    "src/pd_model.py",
    "src/lgd_model.py",
    "src/ecl.py",
    "src/early_warning.py",
    "src/scorecard.py",
    "src/facility_ecl.py",
]


def build():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    data = ROOT / "data/raw/sme_credit_portfolio.csv"
    workout = ROOT / "data/raw/lgd_workout_history.csv"
    expected = {
        data: "2312db398a92c242abec665af6e1e7535b18e47349cfaf0cdf48e8ed3f83c8cd",
        workout: "d1ff68a25593693039ee00b0d6b7a1f84b226d2d0995d9e6a54a897fcf5de220",
    }
    for path, sha in expected.items():
        if file_hash(path) != sha:
            raise ValueError(f"Frozen training data hash mismatch: {path.name}")
    raw = pd.read_csv(data)
    frame = prepare_data(raw)
    columns = pd_feature_columns(frame)
    x, _, y, _ = train_test_split(
        frame[columns],
        frame["default"],
        test_size=0.25,
        stratify=frame["default"],
        random_state=42,
    )
    pd_model = logistic_model().fit(x, y)
    h = pd.read_csv(workout)
    lgd_model = gradient_boosting_lgd_model().fit(h, h.economic_lgd)
    manifest = {
        "version": "reference-v5-0dfe4c8",
        "status": "REFERENCE",
        "bank_gate": "BLOCKED",
        "pd_columns": columns,
        "industries": sorted(raw.industry.unique()),
        "data": {str(p.relative_to(ROOT)): sha for p, sha in expected.items()},
        "sources": {p: file_hash(ROOT / p) for p in SOURCES},
        "artifacts": {},
    }
    for name, model in [("pd", pd_model), ("lgd", lgd_model)]:
        target = MODEL_DIR / f"{name}.joblib"
        temp = target.with_suffix(".tmp")
        joblib.dump(model, temp)
        temp.replace(target)
        manifest["artifacts"][name] = file_hash(target)
    atomic_json(MODEL_DIR / "manifest.json", manifest)
    return manifest


def load():
    import json

    manifest = json.loads((MODEL_DIR / "manifest.json").read_text())
    if manifest["status"] != "REFERENCE" or manifest["bank_gate"] != "BLOCKED":
        raise ValueError("Unapproved artifact manifest")
    for p, sha in manifest["sources"].items():
        if p not in SOURCES or file_hash(ROOT / p) != sha:
            raise ValueError("Risk source hash mismatch")
    if set(manifest["sources"]) != set(SOURCES):
        raise ValueError("Incomplete source manifest")
    models = {}
    for name in ("pd", "lgd"):
        path = MODEL_DIR / f"{name}.joblib"
        if file_hash(path) != manifest["artifacts"][name]:
            raise ValueError("Model artifact hash mismatch")
        models[name] = joblib.load(path)
    return models, manifest
