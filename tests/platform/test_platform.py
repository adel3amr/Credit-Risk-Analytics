import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from credit_platform.db import engine
from credit_platform import schema as s, security, artifacts, validation
from credit_platform.api import create_app
from credit_platform.contracts import BORROWER_FEATURES, PD_QUALITATIVE_FEATURES


@pytest.fixture
def db(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    db = engine(url)
    yield db
    db.dispose()


@pytest.fixture
def clients(db):
    c = TestClient(create_app(db))
    headers = {}
    for role in ("analyst", "manager", "validator", "audit", "admin"):
        token = security.issue(db, role, role)
        headers[role] = {"Authorization": "Bearer " + token}
    token = security.issue(db, "manager2", "manager")
    headers["manager2"] = {"Authorization": "Bearer " + token}
    return c, headers


def sample():
    features = {k: 0.0 for k in BORROWER_FEATURES}
    features.update({k: 3.0 for k in PD_QUALITATIVE_FEATURES})
    features.update(
        customer_concentration=0.3,
        supplier_concentration=0.2,
        key_person_dependency=0,
        ebitda_margin=0.2,
        leverage_ratio=2,
        current_ratio=1.3,
        debt_to_income=0.4,
        years_in_business=8,
        credit_utilization=0.5,
    )
    return {
        "name": "boundary cases",
        "source": "synthetic-test",
        "effective_date": "2026-09-24",
        "borrowers": [
            {
                "id": "B1",
                "industry": "Retail",
                "observed_at": "2026-09-24",
                "collateral_type": "Unsecured",
                "features": features,
            }
        ],
        "facilities": [
            {
                "id": "F1",
                "borrower_id": "B1",
                "observed_at": "2026-09-24",
                "product": "Term Loan",
                "drawn": 100.0,
                "limit": 100.0,
                "face": 0.0,
                "remaining_months": 24.0,
                "collateral_type": "Unsecured",
                "collateral_coverage": 0.0,
                "guarantee_coverage": 0.0,
                "lien_rank": "Unsecured",
            }
        ],
    }


def create_run(c, h, data=None, key="test-run-1", purpose="reference"):
    response = c.post("/api/v1/datasets", json=data or sample(), headers=h["analyst"])
    assert response.status_code == 201, response.text
    return c.post(
        "/api/v1/runs",
        json={
            "dataset_id": response.json()["id"],
            "request_key": key,
            "purpose": purpose,
        },
        headers=h["analyst"],
    )


def test_auth_and_rbac(clients):
    c, h = clients
    for path in (
        "datasets",
        "borrowers",
        "facilities",
        "runs",
        "models",
        "findings",
        "audit",
    ):
        assert c.get("/api/v1/" + path).status_code == 401
    assert (
        c.get("/api/v1/me", headers={"Authorization": "Bearer fake"}).status_code == 401
    )
    assert (
        c.post("/api/v1/datasets", json=sample(), headers=h["audit"]).status_code == 403
    )
    assert c.get("/api/v1/audit", headers=h["analyst"]).status_code == 403
    assert c.get("/api/v1/gates", headers=h["audit"]).json()["bank_use"] == "BLOCKED"
    assert c.get("/health/ready").status_code == 200
    assert c.get("/").status_code == 200
    assert c.get("/static/app.js").status_code == 200
    assert c.get("/static/not-a-file").status_code == 404


def test_revocation_and_expiry(db, clients):
    c, h = clients
    security.revoke(db, "analyst")
    assert c.get("/api/v1/me", headers=h["analyst"]).status_code == 401
    with db.begin() as conn:
        conn.execute(
            update(s.principals)
            .where(s.principals.c.name == "manager")
            .values(expires_at="2000-01-01T00:00:00+00:00")
        )
    assert c.get("/api/v1/me", headers=h["manager"]).status_code == 401


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "future",
        "duplicate",
        "orphan",
        "outcome",
        "negative",
        "category",
        "nan",
        "bad_security",
    ],
)
def test_dq_rejects(clients, mutation):
    c, h = clients
    d = sample()
    if mutation == "missing":
        del d["borrowers"][0]["features"]["current_ratio"]
    if mutation == "future":
        d["borrowers"][0]["observed_at"] = "2027-01-01"
    if mutation == "duplicate":
        d["facilities"] *= 2
    if mutation == "orphan":
        d["facilities"][0]["borrower_id"] = "unknown"
    if mutation == "outcome":
        d["borrowers"][0]["features"]["default"] = 1
    if mutation == "negative":
        d["facilities"][0]["drawn"] = -1
    if mutation == "category":
        d["facilities"][0]["product"] = "Unknown"
    if mutation == "nan":
        d["facilities"][0]["drawn"] = "NaN"
    if mutation == "bad_security":
        d["facilities"][0]["collateral_coverage"] = 1
    assert c.post("/api/v1/datasets", json=d, headers=h["analyst"]).status_code == 422
    assert c.get("/api/v1/datasets", headers=h["audit"]).json() == []
    assert (
        c.get("/api/v1/audit/verify", headers=h["audit"]).json()["status"] == "VERIFIED"
    )


def test_reference_and_bank_gate(clients):
    c, h = clients
    result = create_run(c, h)
    assert result.status_code == 200, result.text
    run = result.json()
    assert run["status"] == "SUCCEEDED", run
    id = run["id"]
    p = c.get(f"/api/v1/runs/{id}/portfolio", headers=h["audit"]).json()
    assert p["facility_count"] == 1 and 0 <= p["ecl"] <= 100
    trace = c.get(f"/api/v1/runs/{id}/facilities/F1", headers=h["audit"]).json()[
        "trace"
    ]
    assert trace["stage"] == "Stage 1" and trace["stage_reasons"] == [
        "no_stage2_or_stage3_trigger"
    ]
    assert trace["ecl"] == pytest.approx(trace["pd"] * trace["lgd"] * 100)
    assert create_run(c, h).json()["id"] == id
    blocked = create_run(c, h, key="test-bank-run", purpose="bank").json()
    assert blocked["status"] == "BLOCKED"
    assert (
        c.get(f"/api/v1/runs/{blocked['id']}/portfolio", headers=h["audit"]).status_code
        == 409
    )
    body = {
        "dataset_id": run["dataset_id"],
        "request_key": "test-run-1",
        "purpose": "bank",
    }
    assert c.post("/api/v1/runs", json=body, headers=h["analyst"]).status_code == 409
    assert (
        c.post(f"/api/v1/runs/{id}/validation", headers=h["analyst"]).status_code == 403
    )
    assert (
        c.post(f"/api/v1/runs/{id}/validation", headers=h["validator"]).json()[
            "payload"
        ]["maximum_ecl_error"]
        < 1e-8
    )


@pytest.mark.parametrize(
    "months,dpd,stage",
    [(8, 0, "Stage 1"), (9, 0, "Stage 2"), (9, 90, "Stage 3"), (0, 30, "Stage 2")],
)
def test_stage_watchlist_separation(clients, months, dpd, stage):
    c, h = clients
    d = sample()
    d["borrowers"][0]["features"].update(
        utilization_6m_change=0.2,
        avg_utilization_6m=0.9,
        consecutive_ews_months=months,
        days_past_due=dpd,
    )
    r = create_run(c, h, d).json()
    assert r["status"] == "SUCCEEDED", r
    t = c.get(f"/api/v1/runs/{r['id']}/facilities/F1", headers=h["audit"]).json()[
        "trace"
    ]
    assert t["stage"] == stage
    assert t["watchlist"] == (stage != "Stage 3")
    assert t["sicr"] == (stage == "Stage 2")


@pytest.mark.parametrize("exposure", [0, 0.01, 1000000000])
def test_exposure_edges(clients, exposure):
    c, h = clients
    d = sample()
    d["facilities"][0].update(drawn=exposure, limit=exposure)
    r = create_run(c, h, d).json()
    assert r["status"] == "SUCCEEDED"
    assert r["summary"]["ead"] == exposure and 0 <= r["summary"]["ecl"] <= exposure


def test_borrower_without_facility(clients):
    c, h = clients
    d = sample()
    d["facilities"] = []
    r = create_run(c, h, d).json()
    assert r["status"] == "SUCCEEDED" and r["summary"]["ead"] == 0


def test_two_person_override(clients):
    c, h = clients
    r = create_run(c, h).json()
    id = r["id"]
    body = {
        "run_id": id,
        "facility_id": "F1",
        "proposed_ecl": 50,
        "reason": "Documented reference review adjustment",
    }
    proposal = c.post("/api/v1/overrides", json=body, headers=h["manager"])
    assert proposal.status_code == 201, proposal.text
    oid = proposal.json()["id"]
    path = f"/api/v1/overrides/{oid}/approval"
    assert (
        c.post(path, json={"decision": "APPROVED"}, headers=h["manager"]).status_code
        == 409
    )
    assert (
        c.post(path, json={"decision": "APPROVED"}, headers=h["analyst"]).status_code
        == 403
    )
    assert (
        c.post(path, json={"decision": "APPROVED"}, headers=h["manager2"]).status_code
        == 200
    )
    assert (
        c.post(path, json={"decision": "APPROVED"}, headers=h["manager2"]).status_code
        == 409
    )
    p = c.get(f"/api/v1/runs/{id}/portfolio", headers=h["audit"]).json()
    assert p["controlled_reference_ecl"] == pytest.approx(50)
    assert p["reference_ecl"] == proposal.json()["original_ecl"]
    assert (
        c.post("/api/v1/overrides", json=body, headers=h["manager"]).status_code == 409
    )


def test_immutable_and_audit(db, clients):
    c, h = clients
    assert create_run(c, h).json()["status"] == "SUCCEEDED"
    with pytest.raises(IntegrityError), db.begin() as conn:
        conn.execute(update(s.datasets).values(source="rewritten"))
    with pytest.raises(IntegrityError), db.begin() as conn:
        conn.execute(update(s.decisions).values(ecl=0))
    assert (
        c.get("/api/v1/audit/verify", headers=h["audit"]).json()["status"] == "VERIFIED"
    )


def test_model_failure_saved(clients, monkeypatch):
    c, h = clients

    def broken():
        raise ValueError("Model artifact hash mismatch")

    monkeypatch.setattr(artifacts, "load", broken)
    r = create_run(c, h).json()
    assert r["status"] == "FAILED" and "hash mismatch" in r["summary"]["reason"]
    assert c.get(f"/api/v1/runs/{r['id']}/decisions", headers=h["audit"]).json() == []


def test_outcomes_and_tail_denominators(clients):
    c, h = clients
    r = create_run(c, h).json()
    path = f"/api/v1/runs/{r['id']}/outcomes"
    data = {
        "outcomes": [
            {"facility_id": "F1", "realized_lgd": 1, "resolved_at": "2027-01-01"}
        ]
    }
    assert c.post(path, json=data, headers=h["analyst"]).status_code == 403
    v = c.post(path, json=data, headers=h["validator"])
    assert v.status_code == 200, v.text
    cohort = next(
        x for x in v.json()["payload"]["metrics"] if x["cohort"] == "realized_gt75"
    )
    assert cohort["n"] == 1 and cohort["ead"] == 100 and cohort["bias"] <= 0
    data["outcomes"][0]["resolved_at"] = "2020-01-01"
    assert c.post(path, json=data, headers=h["validator"]).status_code == 422


def test_failed_database_readiness(tmp_path):
    c = TestClient(create_app(engine("sqlite:///" + str(tmp_path / "empty.db"))))
    assert c.get("/health/ready").status_code == 503


def test_metric_zero_weights():
    result = validation.loss_metrics([0, 1], [0, 1], [0, 0])
    assert result[0]["bias"] == 0 and result[0]["ead_weighted_bias"] is None
    with pytest.raises(ValueError):
        validation.loss_metrics([1], [float("nan")], [1])


def test_history_cure_and_movement(clients):
    c, h = clients
    d = sample()
    d["borrowers"][0]["features"]["days_past_due"] = 30
    first = create_run(c, h, d, key="period-first").json()
    d["effective_date"] = "2026-10-24"
    d["borrowers"][0]["observed_at"] = "2026-10-24"
    d["facilities"][0]["observed_at"] = "2026-10-24"
    d["borrowers"][0]["features"]["days_past_due"] = 0
    second = create_run(c, h, d, key="period-second").json()
    movement = c.get(
        f"/api/v1/runs/{second['id']}/movement/{first['id']}", headers=h["audit"]
    ).json()
    assert movement["stage_migrations"] == [
        {"from": "Stage 2", "to": "Stage 1", "facilities": 1}
    ]
    assert movement["ecl_change"] < 0
    history = c.get(
        "/api/v1/borrowers/B1/history",
        params={"as_of": "2026-09-24", "known_at": "2099-01-01T00:00:00Z"},
        headers=h["audit"],
    ).json()
    assert len(history) == 1 and history[0]["stage"] == "Stage 2"
    assert (
        c.get(
            "/api/v1/borrowers/B1/history",
            params={"as_of": "2026-10-24", "known_at": "2000-01-01T00:00:00Z"},
            headers=h["audit"],
        ).json()
        == []
    )


def test_terminal_run_immutable(db, clients):
    c, h = clients
    r = create_run(c, h).json()
    with pytest.raises(IntegrityError), db.begin() as conn:
        conn.execute(
            update(s.runs)
            .where(s.runs.c.id == r["id"])
            .values(summary={"rewritten": True})
        )


def test_full_guarantee_and_cash(clients):
    c, h = clients
    d = sample()
    d["facilities"][0].update(
        collateral_type="Cash",
        collateral_coverage=1,
        guarantee_coverage=1,
        lien_rank="First",
    )
    d["borrowers"][0]["collateral_type"] = "Cash"
    d["borrowers"][0]["features"]["recognized_collateral_coverage"] = 1
    r = create_run(c, h, d).json()
    assert r["status"] == "SUCCEEDED"
    t = c.get(f"/api/v1/runs/{r['id']}/facilities/F1", headers=h["audit"]).json()[
        "trace"
    ]
    assert t["risk_rating"] == 1 and 0 <= t["lgd"] <= 1


def test_corrupt_artifact_rejected(tmp_path, monkeypatch):
    import shutil

    for name in ("manifest.json", "pd.joblib", "lgd.joblib"):
        shutil.copy2(artifacts.MODEL_DIR / name, tmp_path / name)
    (tmp_path / "pd.joblib").write_bytes(b"corrupt")
    monkeypatch.setattr(artifacts, "MODEL_DIR", tmp_path)
    with pytest.raises(ValueError, match="hash mismatch"):
        artifacts.load()


def test_missing_configuration_failed_run(clients, monkeypatch):
    from credit_platform import risk

    c, h = clients

    def missing():
        raise FileNotFoundError("Scenario configuration unavailable")

    monkeypatch.setattr(risk, "policy", missing)
    assert create_run(c, h).json()["status"] == "FAILED"


def test_backup_restore(db, clients, tmp_path):
    import sqlite3
    from credit_platform import audit

    c, h = clients
    assert create_run(c, h).json()["status"] == "SUCCEEDED"
    backup = tmp_path / "restored.db"
    with sqlite3.connect(db.url.database) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    restored = engine("sqlite:///" + str(backup))
    with db.connect() as a, restored.connect() as b:
        assert audit.verify(a) == audit.verify(b)
    rc = TestClient(create_app(restored))
    assert len(rc.get("/api/v1/runs", headers=h["audit"]).json()) == 1
    restored.dispose()


def test_zero_and_total_loss_arithmetic():
    traces = []
    for stage in ("Stage 1", "Stage 2", "Stage 3"):
        for pd in (0, 1):
            for lgd in (0, 1):
                effective = 1 if stage == "Stage 3" else pd
                traces.append(
                    {
                        "stage": stage,
                        "pd": pd,
                        "lgd": lgd,
                        "ead": 100,
                        "remaining_months": 24,
                        "ecl": effective * lgd * 100,
                    }
                )
    assert validation.reconcile(traces)["maximum_ecl_error"] == 0


@pytest.mark.parametrize('field,value', [('stage','Stage 4'),('pd',float('nan')),('lgd',float('inf')),('ead',-1),('remaining_months',-1)])
def test_independent_reconciliation_fails_closed(field,value):
    trace={'stage':'Stage 1','pd':.1,'lgd':.5,'ead':100,'ecl':5,'remaining_months':12}
    trace[field]=value
    with pytest.raises(ValueError):validation.reconcile([trace])


def test_blocked_run_cannot_receive_successful_validation(clients):
    c,h=clients
    run=create_run(c,h,key='blocked-validation',purpose='bank').json()
    response=c.post(f'/api/v1/runs/{run["id"]}/validation',headers=h['validator'])
    assert response.status_code==409
    assert c.get('/api/v1/validation',headers=h['audit']).json()==[]
