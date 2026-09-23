"""LGD governance diagnostics: cash, feature importance, legacy bridge and industry cuts."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from lgd_model import gradient_boosting_lgd_model, NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET
from ecl import load_macro_scenarios

OUT = ROOT / "outputs"

def weighted_avg(x, value, weight):
    w = x[weight].clip(lower=0)
    return float(np.average(x[value], weights=w)) if w.sum() > 0 else np.nan

def main():
    # 1) Holdout permutation importance: conceptual raw features, not one-hot columns.
    hist = pd.read_csv(ROOT / "data/raw/lgd_workout_history.csv")
    train_idx, test_idx = train_test_split(hist.index, test_size=.25, random_state=42)
    train, test = hist.loc[train_idx], hist.loc[test_idx]
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    model = gradient_boosting_lgd_model()
    model.fit(train[features], train[TARGET])
    pi = permutation_importance(
        model, test[features], test[TARGET], scoring="neg_mean_absolute_error",
        n_repeats=20, random_state=20260923, n_jobs=-1,
    )
    imp = pd.DataFrame({
        "feature": features,
        "mae_increase_mean": pi.importances_mean,
        "mae_increase_std": pi.importances_std,
    }).sort_values("mae_increase_mean", ascending=False)
    positive = imp["mae_increase_mean"].clip(lower=0)
    imp["relative_importance"] = positive / positive.sum() if positive.sum() else 0.0
    imp.to_csv(OUT / "lgd_permutation_importance.csv", index=False)

    # 2) Same-population borrower comparison.
    x = pd.read_csv(ROOT / "data/processed/scored_portfolio.csv").copy()
    x["old_loss_amount"] = x["lgd_legacy_proxy"] * x["ead"]
    x["new_loss_amount"] = x["modelled_lgd"] * x["ead"]

    # Cash deep dive by recognized coverage. 100% is deliberately isolated.
    cash = x.loc[x["collateral_type"].eq("Cash")].copy()
    cash["cash_coverage_bucket"] = pd.cut(
        cash["recognized_collateral_coverage"],
        bins=[-np.inf,.75,.99,.999999,np.inf],
        labels=["<75%","75%-<99%","99%-<100%","100%"],
        right=False,
    )
    cash_summary = cash.groupby("cash_coverage_bucket", observed=False).apply(
        lambda g: pd.Series({
            "borrowers": len(g),
            "ead": g["ead"].sum(),
            "mean_recognized_coverage": g["recognized_collateral_coverage"].mean(),
            "ead_weighted_old_lgd": weighted_avg(g,"lgd_legacy_proxy","ead"),
            "ead_weighted_new_lgd": weighted_avg(g,"modelled_lgd","ead"),
            "old_expected_loss_amount": g["old_loss_amount"].sum(),
            "new_expected_loss_amount": g["new_loss_amount"].sum(),
        }), include_groups=False
    ).reset_index()
    cash_summary["new_minus_old_lgd_pp"] = 100 * (
        cash_summary["ead_weighted_new_lgd"] - cash_summary["ead_weighted_old_lgd"]
    )
    cash_summary.to_csv(OUT / "cash_lgd_deep_dive.csv", index=False)

    # 3) Industry comparison of legacy vs workout LGD.
    industry = x.groupby("industry", observed=False).apply(
        lambda g: pd.Series({
            "borrowers": len(g),
            "ead": g["ead"].sum(),
            "ead_weighted_old_lgd": weighted_avg(g,"lgd_legacy_proxy","ead"),
            "ead_weighted_new_lgd": weighted_avg(g,"modelled_lgd","ead"),
            "old_loss_amount": g["old_loss_amount"].sum(),
            "new_loss_amount": g["new_loss_amount"].sum(),
            "stage2_ead_share": g.loc[g["stage"].eq("Stage 2"),"ead"].sum()/max(g["ead"].sum(),1),
            "stage3_ead_share": g.loc[g["stage"].eq("Stage 3"),"ead"].sum()/max(g["ead"].sum(),1),
            "ecl": g["ecl"].sum(),
            "ecl_to_ead": g["ecl"].sum()/max(g["ead"].sum(),1),
        }), include_groups=False
    ).reset_index()
    industry["new_minus_old_lgd_pp"] = 100*(industry["ead_weighted_new_lgd"]-industry["ead_weighted_old_lgd"])
    industry.to_csv(OUT / "lgd_industry_comparison.csv", index=False)

    # 4) ECL bridge on the SAME V4 population.
    # A = legacy collateral LGD + legacy borrower maturity; Stage 3 retains the
    # old direct collateral-workout cash shortfall.
    scenarios = load_macro_scenarios()
    weights = dict(zip(scenarios["scenario"], scenarios["weight"]))
    legacy_lifetime_pd = sum(
        float(weights[s]) * x[f"lifetime_pd_{s}"] for s in weights
    )
    old_old = x["forward_looking_pd_12m"] * x["lgd_legacy_proxy"] * x["ead"]
    s2 = x["stage"].eq("Stage 2")
    s3 = x["stage"].eq("Stage 3")
    old_old.loc[s2] = (legacy_lifetime_pd * x["lgd_legacy_proxy"] * x["ead"]).loc[s2]
    old_old.loc[s3] = x.loc[s3, "stage3_direct_workout_ecl"]

    # B already exists: new workout LGD + old borrower maturity.
    new_lgd_old_term = x["ecl_legacy_borrower_term"]
    # C governed V4: new workout LGD + facility remaining maturity.
    new_lgd_facility = x["ecl"]

    bridge = pd.DataFrame([
        ("A_legacy_lgd_legacy_term", old_old.sum()),
        ("B_workout_lgd_legacy_term", new_lgd_old_term.sum()),
        ("C_workout_lgd_facility_term", new_lgd_facility.sum()),
    ], columns=["step","total_ecl"])
    bridge["change_vs_prior"] = bridge["total_ecl"].diff()
    bridge["change_vs_A"] = bridge["total_ecl"] - bridge.loc[0,"total_ecl"]
    bridge.to_csv(OUT / "ecl_methodology_bridge.csv", index=False)

    stage_bridge=[]
    for stage in ["Stage 1","Stage 2","Stage 3"]:
        m=x["stage"].eq(stage)
        stage_bridge.append({
            "stage":stage, "ead":x.loc[m,"ead"].sum(),
            "A_legacy_lgd_legacy_term":old_old.loc[m].sum(),
            "B_workout_lgd_legacy_term":new_lgd_old_term.loc[m].sum(),
            "C_workout_lgd_facility_term":new_lgd_facility.loc[m].sum(),
        })
    pd.DataFrame(stage_bridge).to_csv(OUT / "ecl_methodology_bridge_by_stage.csv", index=False)

    # 5) Portfolio peer-comparison inputs: exposure-weighted staging and coverage.
    total_ead=x["ead"].sum()
    peer=[]
    for stage in ["Stage 1","Stage 2","Stage 3"]:
        g=x.loc[x["stage"].eq(stage)]
        peer.append({
            "stage":stage, "borrower_share":len(g)/len(x),
            "ead_share":g["ead"].sum()/total_ead,
            "ecl_coverage":g["ecl"].sum()/max(g["ead"].sum(),1),
            "ead_weighted_lgd":weighted_avg(g,"modelled_lgd","ead"),
        })
    pd.DataFrame(peer).to_csv(OUT / "portfolio_peer_metrics.csv", index=False)

    print("\nLGD PERMUTATION IMPORTANCE\n", imp.round(5).to_string(index=False))
    print("\nCASH LGD DEEP DIVE\n", cash_summary.round(5).to_string(index=False))
    print("\nECL METHODOLOGY BRIDGE\n", bridge.round(2).to_string(index=False))
    print("\nINDUSTRY LGD COMPARISON\n", industry.round(5).to_string(index=False))

if __name__ == "__main__":
    main()
