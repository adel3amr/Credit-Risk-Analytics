"""Reference registry seeding; immutable research blockers, never automatic promotion."""

from sqlalchemy import select
from . import schema as s, audit
from .common import now, ROOT, file_hash

FINDINGS = [
    (
        "PLAT-001",
        "LGD",
        "High",
        "Severe-loss residual bias persists; no challenger promoted",
        "lgd_research/LGD_FINDINGS_REGISTER.md",
    ),
    (
        "PLAT-002",
        "Features",
        "Critical",
        "Research quality inputs absent from current scoring population",
        "lgd_research/LGD_FEATURE_SUPPORT_MATRIX.md",
    ),
    (
        "PLAT-003",
        "Data",
        "High",
        "Synthetic evidence is not institution-specific empirical validation",
        "AUTHORITATIVE_BASELINE_RECONCILIATION.md",
    ),
    (
        "PLAT-004",
        "Deployment",
        "High",
        "PostgreSQL, TLS/SSO and browser deployment qualification require environment evidence",
        "LIMITATIONS.md",
    ),
    (
        "PLAT-005",
        "Integrity",
        "High",
        "Original working R2 development file truncated; intact committed snapshot isolated",
        "AUTHORITATIVE_BASELINE_RECONCILIATION.md",
    ),
]


def seed(db, actor):
    with db.begin() as conn:
        for id, component, severity, description, path in FINDINGS:
            if conn.execute(
                select(s.findings.c.id).where(s.findings.c.id == id)
            ).first():
                continue
            conn.execute(
                s.findings.insert().values(
                    id=id,
                    component=component,
                    severity=severity,
                    description=description,
                    evidence={"path": path, "sha256": file_hash(ROOT / path)},
                    owner="Reference platform owner",
                    recorded_at=now(),
                )
            )
            audit.append(conn, actor, "BASELINE_FINDING", id, {"severity": severity})
        for name in [
            "two-stage enhanced R2",
            "component R2",
            "GB enhanced R2",
            "oracle FUTURE INFORMATION",
            "quantile p90 RISK ONLY",
        ]:
            id = "research:" + name
            if conn.execute(select(s.models.c.id).where(s.models.c.id == id)).first():
                continue
            path = "lgd_research/results/final_scorecard.csv"
            conn.execute(
                s.models.insert().values(
                    id=id,
                    family="LGD",
                    version="R2-ae9942a",
                    status="BLOCKED",
                    recorded_at=now(),
                    manifest={
                        "purpose": "research diagnostic",
                        "evidence": path,
                        "evidence_hash": file_hash(ROOT / path),
                        "reason": "No deployment promotion; see research feature and model findings",
                        "owner": "Reference research programme",
                        "development": "R2 synthetic 9000",
                        "validation": "R2 final 3000",
                        "target": "economic LGD",
                        "effective_for_bank_use": False,
                    },
                )
            )
            audit.append(conn, actor, "BLOCKED_RESEARCH_REGISTRY", id, {})

        # Additive, hash-versioned blocked registry entry. Historical entries untouched.
        from .workout_evidence import get
        evidence, source = get()
        model_hash = evidence["model_lock_hash"]
        mid = "research:WN-1:" + model_hash
        if not conn.execute(select(s.models.c.id).where(s.models.c.id == mid)).first():
            conn.execute(s.models.insert().values(id=mid, family="LGD", version="WN-1",
                status="BLOCKED", recorded_at=now(), manifest={"target":"remaining discounted workout loss",
                "methodology":"workout_vnext/PROTOCOL.md", "owner":"Reference research programme",
                "development":"WN-1:4800 borrowers", "validation":"WN-1:1600 borrowers",
                "final":"WN-1:1600 borrowers,2018–2020", "source":source, "decision":evidence["decision"],
                "artifact_lock_hash":model_hash, "effective_for_bank_use":False}))
            audit.append(conn, actor, "BLOCKED_RESEARCH_REGISTRY", mid, {"source":source})
        for fid, description in [("WN-001","Component failed calibration/noninferiority and stress gates"),
                                 ("WN-002","Resolved-only selection; institutional capture and joint support unvalidated"),
                                 ("WN-003","Security valuation and nominal guarantees may persist after realization/payout; not residual available cover")]:
            if not conn.execute(select(s.findings.c.id).where(s.findings.c.id==fid)).first():
                conn.execute(s.findings.insert().values(id=fid,component="LGD WN-1",severity="High",
                    description=description,evidence=source,owner="Reference research programme",recorded_at=now()))
                audit.append(conn,actor,"RESEARCH_FINDING",fid,{"source":source})
