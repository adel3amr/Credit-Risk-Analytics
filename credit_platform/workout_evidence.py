"""Read hash-locked WN-1 evidence without training or scoring mutation.

A Windows checkout may write LF text files with CRLF endings. Accept that
single transport-only transformation for JSON/CSV evidence; binaries still
require exact byte-for-byte matches. Locked expected hashes never change.
"""

import json
from pathlib import Path

from .common import ROOT, frozen_text_hash
from .service import NotFound
from workout_vnext.generate import sha


_TEXT_EVIDENCE_SUFFIXES = {".json", ".csv"}


def _verify_frozen(path: Path, expected: str) -> str:
    """Return the lock digest only for identical or newline-equivalent bytes."""
    if sha(path) == expected:
        return expected
    if path.suffix.lower() in _TEXT_EVIDENCE_SUFFIXES:
        if frozen_text_hash(path) == expected:
            return expected
    raise ValueError("WN-1 evidence hash mismatch: " + str(path))


def get():
    base = ROOT / "workout_vnext"
    path = base / "EVIDENCE_LOCK.json"
    if not path.exists():
        raise NotFound("WN-1 validation closeout is unavailable")

    lock = json.loads(path.read_text(encoding="utf-8"))
    for name, digest in lock["files"].items():
        _verify_frozen(base / name, digest)

    evidence = {
        name: json.loads((base / "results" / filename).read_text(encoding="utf-8"))
        for name, filename in [
            ("decision", "decision.json"),
            ("ecl", "ecl_bridge.json"),
            ("ledger", "ledger_audit.json"),
        ]
    }
    # Return lock identities, not the checkout-specific CRLF byte hashes.
    evidence["manifest_hash"] = lock["files"]["data/manifest.json"]
    evidence["model_lock_hash"] = lock["files"]["results/LOCK.json"]
    return evidence, {
        "type": "frozen_workout_validation",
        "path": "workout_vnext/EVIDENCE_LOCK.json",
        "hash": frozen_text_hash(path),
    }
