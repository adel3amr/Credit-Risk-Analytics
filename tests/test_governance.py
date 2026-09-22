from pathlib import Path
import pandas as pd
import pytest
from src.governance import (
    OverrideRequest, approve_override, has_permission,
    validate_macro_scenarios, append_audit_event,
)

def test_rbac_and_maker_checker(tmp_path):
    assert has_permission("Credit Analyst", "propose_override")
    assert not has_permission("Credit Analyst", "approve_override")
    assert has_permission("Risk Manager", "approve_override")
    req = OverrideRequest("C001","PD",0.04,0.06,"QUALITATIVE_RISK","Management weakness","analyst1","Credit Analyst")
    approved = approve_override(req,"manager1","Risk Manager")
    assert approved["model_value"] == 0.04
    assert approved["proposed_value"] == 0.06
    assert approved["status"] == "APPROVED"
    with pytest.raises(PermissionError):
        approve_override(req,"analyst1","Risk Manager")

def test_macro_weights():
    good = pd.DataFrame({
        "scenario":["upside","baseline","downside"], "weight":[.2,.6,.2],
        "real_gdp_growth_pct":[2,1,-1], "unemployment_rate_pct":[5.5,6,7.5],
        "policy_rate_pct":[2,2.5,3.5], "inflation_pct":[1.8,2,3.2],
    })
    assert validate_macro_scenarios(good)
    bad = good.copy(); bad.loc[0,"weight"] = .3
    with pytest.raises(ValueError):
        validate_macro_scenarios(bad)

def test_append_only_audit(tmp_path):
    p=tmp_path/"audit.jsonl"
    append_audit_event(p,{"actor":"analyst1","action":"PROPOSE_OVERRIDE"})
    append_audit_event(p,{"actor":"manager1","action":"APPROVE_OVERRIDE"})
    assert len(p.read_text().strip().splitlines()) == 2
