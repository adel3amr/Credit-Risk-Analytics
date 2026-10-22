"""WN-1 evidence must be portable across Git's Windows LF/CRLF checkout modes."""

import hashlib
import json

import pytest

from credit_platform import workout_evidence


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def frozen_checkout(tmp_path, monkeypatch):
    base = tmp_path / "workout_vnext"
    (base / "data").mkdir(parents=True)
    (base / "results").mkdir(parents=True)
    sources = {
        "data/manifest.json": b'{\n  "version": "WN-1"\n}\n',
        "results/LOCK.json": b'{\n  "candidate": "component"\n}\n',
        "results/decision.json": b'{\n  "status": "BLOCKED"\n}\n',
        "results/ecl_bridge.json": b'{\n  "ecl": 0\n}\n',
        "results/ledger_audit.json": b'{\n  "audited": true\n}\n',
        "results/metrics.csv": b"metric,value\nrmse,0.15\n",
        "results/component.joblib": b"\x80\x04\x00\r\n\x00binary\x00\n",
    }
    for name, data in sources.items():
        path = base / name
        path.write_bytes(data)
    hashes = {name: _digest(raw) for name, raw in sources.items()}
    lock_path = base / "EVIDENCE_LOCK.json"
    lock_path.write_text(json.dumps({"files": hashes}, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(workout_evidence, "ROOT", tmp_path)
    return base, hashes


def test_all_raw_evidence_validates(frozen_checkout):
    _, hashes = frozen_checkout
    evidence, source = workout_evidence.get()
    assert evidence["model_lock_hash"] == hashes["results/LOCK.json"]
    assert evidence["manifest_hash"] == hashes["data/manifest.json"]
    assert source["type"] == "frozen_workout_validation"


def test_windows_crlf_checkout_passes_without_changing_frozen_hashes(frozen_checkout):
    base, hashes = frozen_checkout
    # Git's core.autocrlf may convert locked text files on checkout.
    for name in hashes:
        if name.endswith((".json", ".csv")):
            path = base / name
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    path = base / "EVIDENCE_LOCK.json"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

    evidence, source = workout_evidence.get()
    assert evidence["model_lock_hash"] == hashes["results/LOCK.json"]
    assert evidence["manifest_hash"] == hashes["data/manifest.json"]
    assert source["hash"] == _digest(path.read_bytes().replace(b"\r\n", b"\n"))


def test_tampered_frozen_text_still_fails(frozen_checkout):
    base, _ = frozen_checkout
    path = base / "data" / "manifest.json"
    path.write_bytes(path.read_bytes().replace(b"WN-1", b"WN-2").replace(b"\n", b"\r\n"))
    with pytest.raises(ValueError, match="WN-1 evidence hash mismatch"):
        workout_evidence.get()


def test_tampered_frozen_binary_still_fails(frozen_checkout):
    base, _ = frozen_checkout
    path = base / "results" / "component.joblib"
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    with pytest.raises(ValueError, match="WN-1 evidence hash mismatch"):
        workout_evidence.get()
