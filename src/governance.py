"""Governance primitives for the V3 credit-risk interface.

The module deliberately separates model output, policy configuration and human
judgement. It is a lightweight portfolio-project implementation, not an IAM
or production workflow engine.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd

ROLE_FILE = Path(__file__).resolve().parents[1] / "config" / "access_roles.csv"

def load_roles(path=ROLE_FILE):
    return pd.read_csv(path).set_index("role")

def has_permission(role, permission, roles=None):
    roles = load_roles() if roles is None else roles
    if not roles.index.is_unique:
        return False
    if role not in roles.index or permission not in roles.columns:
        return False
    try:
        return bool(int(roles.at[role, permission]))
    except (TypeError, ValueError, KeyError):
        return False

@dataclass(frozen=True)
class OverrideRequest:
    customer_id: str
    override_type: str
    model_value: float | str
    proposed_value: float | str
    reason_code: str
    rationale: str
    proposed_by: str
    proposed_by_role: str

    def validate(self):
        if not has_permission(self.proposed_by_role, "propose_override"):
            raise PermissionError("Role cannot propose overrides")
        if self.model_value == self.proposed_value:
            raise ValueError("Override must differ from the model/policy output")
        if not self.reason_code or not self.rationale.strip():
            raise ValueError("Reason code and rationale are required")
        return self

def approve_override(request, approved_by, approver_role):
    request.validate()
    if not has_permission(approver_role, "approve_override"):
        raise PermissionError("Role cannot approve overrides")
    if approved_by == request.proposed_by:
        raise PermissionError("Maker-checker control: proposer cannot approve own override")
    return {
        **asdict(request),
        "status": "APPROVED",
        "approved_by": approved_by,
        "approver_role": approver_role,
        "approved_at_utc": datetime.now(timezone.utc).isoformat(),
    }

def validate_macro_scenarios(scenarios):
    required = {"scenario","weight","real_gdp_growth_pct","unemployment_rate_pct","policy_rate_pct","inflation_pct"}
    missing = required.difference(scenarios.columns)
    if missing:
        raise ValueError(f"Missing macro fields: {sorted(missing)}")
    if (scenarios["weight"] < 0).any() or abs(float(scenarios["weight"].sum()) - 1.0) > 1e-9:
        raise ValueError("Macro weights must be non-negative and sum to 1.0")
    if scenarios["scenario"].str.lower().duplicated().any():
        raise ValueError("Scenario names must be unique")
    return True

def append_audit_event(path, event):
    """Append-only JSONL audit helper for the demo interface."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return payload
