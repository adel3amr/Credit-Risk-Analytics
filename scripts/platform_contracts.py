"""Build inspectable contracts from the frozen sources and measured feature support."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from sklearn.model_selection import train_test_split
from credit_platform.common import ROOT, atomic_json
from credit_platform.contracts import BORROWER_FEATURES, PD_FEATURES, EWS_FEATURES
from src.lgd_model import NUMERIC_FEATURES, CATEGORICAL_FEATURES


def main():
    raw = pd.read_csv(ROOT / "data/raw/sme_credit_portfolio.csv")
    h = pd.read_csv(ROOT / "data/raw/lgd_workout_history.csv")
    live = pd.read_csv(ROOT / "outputs/facility_lgd_predictions.csv")
    pdtrain, pdtest = train_test_split(
        raw, test_size=0.25, stratify=raw.default, random_state=42
    )
    lgdtrain, lgdtest = train_test_split(h, test_size=0.25, random_state=42)
    definitions = {
        "ebitda_margin": "EBITDA / revenue",
        "leverage_ratio": "Debt / EBITDA synthetic leverage ratio",
        "current_ratio": "Current assets / current liabilities",
        "debt_to_income": "Debt service/income proxy in frozen generator",
        "collateral_coverage": "Nominal collateral / exposure",
        "years_in_business": "Completed operating years",
        "credit_utilization": "Current utilization ratio",
        "delinquencies_12m": "Delinquency event count in trailing 12 months",
        "previous_defaults": "Known prior default count",
        "days_past_due": "Current days past due",
        "management_quality": "Management assessment 1 weak to 5 strong",
        "governance_quality": "Governance assessment 1..5",
        "financial_reporting_quality": "Financial reporting assessment 1..5",
        "market_position": "Market position assessment 1..5",
        "sponsor_support": "Sponsor support assessment 1..5",
        "customer_concentration": "Largest-customer concentration fraction",
        "supplier_concentration": "Supplier concentration fraction",
        "key_person_dependency": "Binary key-person dependence",
        "audit_quality": "Audit assessment 1..3",
        "utilization_6m_change": "Current utilization minus six-month-prior utilization",
        "avg_utilization_6m": "Six-month mean utilization",
        "months_above_80_utilization": "Count of last six months with utilization >=80%",
        "limit_breach_count": "Limit breach count in conduct source window",
        "consecutive_ews_months": "Trailing consecutive deterioration months, maximum 36",
        "current_credit_impaired": "Reporting-date credit impairment flag",
        "write_off_flag": "Reporting-date write-off flag",
        "recognized_collateral_coverage": "Eligible recognized collateral / exposure",
        "ead_at_default": "Facility reporting exposure used as LGD exposure proxy",
        "guarantee_coverage": "Guarantee coverage / EAD; V5 synthetic product mapping",
        "leverage_at_default": "Reporting leverage mapped to default-training input",
        "current_ratio_at_default": "Reporting liquidity mapped to default-training input",
        "product_type": "Facility product category",
        "industry": "Borrower sector category",
        "collateral_type": "Security type category",
        "lien_rank": "Facility recovery priority",
    }

    def support(frame, key):
        if key not in frame:
            return {"available": False}
        x = frame[key]
        record = {"available": True, "n": len(x), "missing": int(x.isna().sum())}
        if pd.api.types.is_numeric_dtype(x):
            record.update(
                minimum=float(x.min()),
                maximum=float(x.max()),
                zero_count=int(x.eq(0).sum()),
            )
        else:
            record["categories"] = sorted(x.dropna().unique().tolist())
        return record

    records = []
    for family, features, dev, test, current in [
        ("PD", PD_FEATURES + ["industry"], pdtrain, pdtest, raw),
        ("SICR_STAGING_EWS_RATING", BORROWER_FEATURES, pdtrain, pdtest, raw),
        ("LGD", NUMERIC_FEATURES + CATEGORICAL_FEATURES, lgdtrain, lgdtest, live),
    ]:
        for key in features:
            records.append(
                {
                    "feature": key,
                    "business_definition": definitions[key],
                    "model": family,
                    "source_system": "synthetic_v5; institution mapping not configured",
                    "source_entity": "facility" if family == "LGD" else "borrower",
                    "source_field": key,
                    "transformation": "See risk.score and frozen ColumnTransformer; numeric imputer/scaler and categorical encoding are retained",
                    "classification": "DERIVABLE AT PREDICTION TIME"
                    if key
                    in [
                        "ead_at_default",
                        "leverage_at_default",
                        "current_ratio_at_default",
                        *EWS_FEATURES,
                    ]
                    else "REQUIRES NEW DATA CAPTURE",
                    "prediction_time": "reporting date; reject observed_at after effective date",
                    "refresh_frequency": "per reporting snapshot; institution SLA unapproved",
                    "historical_availability": "synthetic only",
                    "development": support(dev, key),
                    "validation": support(test, key),
                    "current_synthetic": support(current, key),
                    "production_support": {
                        "available": False,
                        "reason": "No institution feed or validation",
                    },
                    "allowed_range": "Canonical contracts.py; observed bounds are support diagnostics, not policy limits",
                    "allowed_categories": support(dev, key).get("categories", []),
                    "dq_controls": "Finite, required, category/range/source date and referential validation",
                    "fallback": "Reject missing canonical inputs; no silent model scoring defaults",
                    "lineage": "dataset hash → source snapshot → feature → artifact hash → run → decision",
                    "sensitivity": "CONFIDENTIAL if institutional; INTERNAL synthetic",
                }
            )
    for key in ["security_quality", "guarantor_strength", "downturn_at_default"]:
        records.append(
            {
                "feature": key,
                "model": "R2 research challengers",
                "classification": "REQUIRES NEW DATA CAPTURE",
                "business_definition": "Research proxy; institutional definition and measurement validation required",
                "development": {"available": True, "population": "R2 synthetic"},
                "validation": {"available": True, "population": "R2 synthetic final"},
                "current_synthetic": {"available": False},
                "production_support": {"available": False},
                "fallback": "BLOCK promotion",
            }
        )
    for key in [
        "cure_flag",
        "resolution_months",
        "market_shock",
        "bank_shock",
        "collection_shock",
        "economic_lgd",
        "recovery_cashflows",
    ]:
        records.append(
            {
                "feature": key,
                "model": "Oracle / validation targets only",
                "classification": "FUTURE / POST-OUTCOME — PROHIBITED",
                "prediction_time": False,
                "fallback": "Reject from canonical prediction inputs",
            }
        )
    atomic_json(ROOT / "credit_platform/contracts/model_features.json", records)
    title = "# Model feature contracts\n\nGenerated by `python scripts/platform_contracts.py`. Machine-readable detail: `credit_platform/contracts/model_features.json`. Synthetic current availability is **not** institutional production availability. No reference model is approved for bank use.\n\n"
    title += "| Model | Feature | Definition | Classification |\n|---|---|---|---|\n"
    title += "\n".join(
        f"| {r['model']} | {r['feature']} | {r.get('business_definition', 'Future outcome; validation only')} | {r['classification']} |"
        for r in records
    )
    title += "\n\n## EAD / ECL / scenario contracts\n\nEAD consumes drawn, limit, product and face at reporting date: term uses drawn; OVD uses limit; trade uses face × frozen CCF (.20/.50/1), rounded to cents. Missing and negative amounts reject. ECL consumes governed forward PD, LGD, EAD, assigned stage and remaining months. PD/LGD must be finite fractions, stage must be one of three values, maturity nonnegative. Stage 2 retains constant hazard on weighted PD; it is not a new scenario-lifetime methodology. Scenarios require exactly one baseline, unique names, finite values and nonnegative weights summing to one.\n\nInstitution-specific refresh SLAs, data ownership, guarantee enforceability and measurement definitions remain capture/qualification requirements. Future data may be used for outcome validation, never scoring.\n"
    (ROOT / "MODEL_FEATURE_CONTRACTS.md").write_text(title)
    (ROOT / "DATA_DICTIONARY.md").write_text(
        "# Data dictionary\n\nCanonical version 1 is defined by `credit_platform/domain.py`; relational types/keys by `credit_platform/schema.py`. Model features and definitions are enumerated in MODEL_FEATURE_CONTRACTS.md and its JSON contract.\n\n| Field | Definition / type / unit | Controls |\n|---|---|---|\n| id, borrower_id | Stable source identifiers, string | Unique per snapshot; facilities require borrower FK |\n| effective_date | Business reporting date, ISO date | No future-observed inputs |\n| recorded_at | UTC system ingestion timestamp | Immutable, separate from business date |\n| observed_at | Source information date | Must not exceed reporting date |\n| source | Mapping/source identity | Required; hash provenance |\n| drawn, limit, face | Nonnegative monetary inputs | Same synthetic currency unit per reference portfolio; no FX conversion |\n| remaining_months | Nonnegative contractual remaining months | Required; no silent default |\n| collateral_type, coverage, lien_rank | Facility security terms | Unsecured means zero collateral and unsecured lien |\n| guarantee_coverage | Fraction 0..1 | Synthetic V5 product mapping, not proof of enforceability |\n| source_hash, hash | SHA-256 canonical JSON | Verified on reads and trace reconstruction |\n| models / versions | Model and source hashes | Trusted local files only; status REFERENCE |\n| stage_reasons / ews | Trigger-level policy evidence | Retained inside immutable trace |\n| original_ecl / proposed_ecl | Original result and requested reference adjustment | Original never overwritten; different manager approval |\n\nAll current data are synthetic, INTERNAL. Future borrower/facility/financial data should be CONFIDENTIAL; credentials RESTRICTED. Statistical support minima/maxima are observed, not approval thresholds. Generator field rules remain in scripts/generate_sme_portfolio.py and scripts/generate_lgd_workout_history.py; R2 recovery assumptions remain separate.\n"
    )


if __name__ == "__main__":
    main()
