"""Local operator commands; credentials are printed once and never stored in cleartext."""

import argparse
import json
import pandas as pd
from sqlalchemy import select
from . import artifacts, security, service, schema as s, audit, governance
from .common import ROOT, atomic_json, file_hash
from .contracts import BORROWER_FEATURES
from .domain import DatasetInput, RunInput
from .db import engine, require_schema


def map_reference(reporting_date="2026-09-24"):
    raw_path = ROOT / "data/raw/sme_credit_portfolio.csv"
    if (
        file_hash(raw_path)
        != "2312db398a92c242abec665af6e1e7535b18e47349cfaf0cdf48e8ed3f83c8cd"
    ):
        raise ValueError("Source dataset identity mismatch")
    raw = pd.read_csv(raw_path).set_index("customer_id")
    selected = pd.read_csv(ROOT / "outputs/borrower_audit_trace.csv")
    fs = pd.read_csv(ROOT / "outputs/facility_lgd_predictions.csv")
    borrowers = []
    facilities = []
    for id in selected.customer_id:
        b = raw.loc[id]
        borrowers.append(
            {
                "id": id,
                "industry": b.industry,
                "observed_at": reporting_date,
                "collateral_type": b.collateral_type,
                "features": {k: float(b[k]) for k in BORROWER_FEATURES},
            }
        )
    for _, f in fs.iterrows():
        b = raw.loc[f.customer_id]
        direct = f.product_type in ("Term Loan", "OVD")
        facilities.append(
            {
                "id": f.facility_id,
                "borrower_id": f.customer_id,
                "observed_at": reporting_date,
                "product": f.product_type,
                "drawn": float(
                    b.loan_ead
                    if f.product_type == "Term Loan"
                    else b.ovd
                    if f.product_type == "OVD"
                    else 0
                ),
                "limit": float(
                    b.loan_limit
                    if f.product_type == "Term Loan"
                    else b.ovd_ead
                    if f.product_type == "OVD"
                    else 0
                ),
                "face": float(b.trade if not direct else 0),
                "remaining_months": float(f.remaining_months),
                "collateral_type": f.collateral_type,
                "collateral_coverage": float(f.collateral_coverage),
                "guarantee_coverage": float(f.guarantee_coverage),
                "lien_rank": f.lien_rank,
            }
        )
    return service.normalized(
        DatasetInput.model_validate(
            {
                "name": "V5 holdout reference",
                "source": "synthetic-v5:" + file_hash(raw_path),
                "effective_date": reporting_date,
                "borrowers": borrowers,
                "facilities": facilities,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-models")
    p = sub.add_parser("issue-token")
    p.add_argument("--name", required=True)
    p.add_argument("--role", choices=security.PERMISSIONS, required=True)
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("revoke-token")
    p.add_argument("--name", required=True)
    p = sub.add_parser("export-reference")
    p.add_argument("--output", required=True)
    p.add_argument("--date", default="2026-09-24")
    p = sub.add_parser("run-reference")
    p.add_argument("--operator", required=True)
    p.add_argument("--date", default="2026-09-24")
    sub.add_parser("audit-verify")
    sub.add_parser("seed-governance")
    args = parser.parse_args()
    if args.command == "build-models":
        print(json.dumps(artifacts.build(), indent=2))
        return
    if args.command == "export-reference":
        atomic_json(args.output, map_reference(args.date).model_dump(mode="json"))
        return
    db = engine()
    require_schema(db)
    if args.command == "issue-token":
        print(security.issue(db, args.name, args.role, args.days))
        return
    if args.command == "revoke-token":
        security.revoke(db, args.name)
        return
    if args.command == "seed-governance":
        governance.seed(db, "local-operator")
        return
    if args.command == "audit-verify":
        with db.connect() as conn:
            print(json.dumps(audit.verify(conn)))
        return
    with db.connect() as conn:
        p = (
            conn.execute(
                select(s.principals).where(
                    s.principals.c.name == args.operator, s.principals.c.active == 1
                )
            )
            .mappings()
            .one()
        )
        if "run" not in security.PERMISSIONS[p["role"]]:
            raise ValueError("Operator cannot run calculations")
    d = service.ingest(db, map_reference(args.date), p["id"])
    run = service.execute(
        db, RunInput(dataset_id=d["id"], request_key="reference-" + d["hash"]), p["id"]
    )
    print(json.dumps(run, indent=2))
    if run["status"] != "SUCCEEDED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
