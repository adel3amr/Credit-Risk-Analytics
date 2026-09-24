"""Development and selection only. Final holdout is absent by construction.

Fixed designs, no grid search or iterations against an outcome-selected tail.
Run the separate final_evaluation.py exactly once after the decision is frozen.
"""
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from lgd_model import NUMERIC_FEATURES, CATEGORICAL_FEATURES, gradient_boosting_lgd_model  # noqa: E402
from lgd_research.generate_r2 import DEPLOYABLE, generate  # noqa: E402

Y = "economic_lgd"
NEW_NUM = ["security_quality", "guarantor_strength", "downturn_at_default"]
ORACLE_NUM = ["cure_flag", "months_to_resolution", "market_realization_shock",
              "guarantee_realization_shock", "collection_realization_shock"]


def model(num=NUMERIC_FEATURES, cat=CATEGORICAL_FEATURES, kind="mean"):
    prep = ColumnTransformer([
        ("n", Pipeline([("fill", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num),
        ("c", Pipeline([("fill", SimpleImputer(strategy="most_frequent")),
                        ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat),
    ], sparse_threshold=0)
    if kind == "mean":
        reg = GradientBoostingRegressor(n_estimators=220, max_depth=3, learning_rate=.035,
                                        min_samples_leaf=25, random_state=42)
    elif kind == "huber":
        reg = GradientBoostingRegressor(loss="huber", alpha=.9, n_estimators=220,
                                        max_depth=3, learning_rate=.035, min_samples_leaf=25, random_state=42)
    elif kind == "quantile":
        reg = GradientBoostingRegressor(loss="quantile", alpha=.9, n_estimators=220,
                                        max_depth=3, learning_rate=.035, min_samples_leaf=25, random_state=42)
    elif kind == "rf":
        reg = RandomForestRegressor(n_estimators=180, max_depth=10, min_samples_leaf=15,
                                    max_features=.75, random_state=42, n_jobs=-1)
    else:
        raise ValueError(kind)
    return Pipeline([("prep", prep), ("reg", reg)])


class SegmentMean:
    def fit(self, data):
        self.global_mean = data[Y].mean()
        self.means = data.groupby(["collateral_type", "product_type"])[Y].mean()
        return self

    def predict(self, data):
        return np.array([self.means.get((x.collateral_type, x.product_type), self.global_mean)
                         for x in data.itertuples(index=False)])


class TwoStage:
    """Probabilistic severe-regime mixture; .75 fixed before selection."""
    def __init__(self, num=NUMERIC_FEATURES, cat=CATEGORICAL_FEATURES):
        self.num, self.cat = num, cat

    def fit(self, data):
        self.prob = Pipeline([
            ("prep", model(self.num, self.cat).named_steps["prep"]),
            ("reg", LogisticRegression(max_iter=500, C=1, random_state=42)),
        ]).fit(data, data[Y] > .75)
        self.low = model(self.num, self.cat).fit(data.loc[data[Y] <= .75], data.loc[data[Y] <= .75, Y])
        self.high = model(self.num, self.cat).fit(data.loc[data[Y] > .75], data.loc[data[Y] > .75, Y])
        return self

    def predict(self, data):
        p = self.prob.predict_proba(data)[:, 1]
        return np.clip((1-p)*self.low.predict(data)+p*self.high.predict(data), 0, 1)


class Component:
    """Forecast component recoveries and timing separately; bounded cash budget."""
    def fit(self, data):
        self.parts = ["collateral_recovery", "guarantee_recovery", "unsecured_recovery",
                      "cure_recovery", "workout_cost", "months_to_resolution"]
        self.models = {}
        for part in self.parts:
            target = data[part] if part == "months_to_resolution" else data[part]/data.ead_at_default
            m = model(NUMERIC_FEATURES+NEW_NUM, CATEGORICAL_FEATURES)
            # Fewer trees on each component, fixed before validation.
            m.named_steps["reg"].set_params(n_estimators=120)
            self.models[part] = m.fit(data, target)
        self.discount = float(data.discount_rate.mean())
        return self

    def predict(self, data):
        parts = {k: np.maximum(m.predict(data), 0) for k, m in self.models.items()}
        recovery = sum(parts[k] for k in self.parts[:4])
        recovery = np.minimum(recovery, 1.)
        months = np.clip(parts["months_to_resolution"], 1, 60)
        buckets = np.array([1, 6, 12, 24, 36, 60])
        weights = np.exp(-abs(months[:, None]-buckets[None, :])/9)
        weights /= weights.sum(axis=1, keepdims=True)
        net = recovery[:, None]*weights
        cash = data.collateral_type.eq("Cash").to_numpy()
        net[cash, 0] -= parts["workout_cost"][cash]
        net[~cash, 2] -= parts["workout_cost"][~cash]
        return np.clip(1-np.sum(net/(1+self.discount)**(buckets[None, :]/12), axis=1), 0, 1)


def predict(fitted, frame):
    return np.clip(np.asarray(fitted.predict(frame)), 0, 1)


def score(y, p, ead, label, population):
    rows = []
    y, p, ead = map(np.asarray, (y, p, ead))
    for cohort, mask in [("all", np.ones(len(y), bool)), ("realized_gt60", y > .6),
                         ("realized_gt75", y > .75), ("realized_gt90", y > .9),
                         ("predicted_top10", p >= np.quantile(p, .9)),
                         ("realized_le20", y <= .2)]:
        if mask.sum() < 10:
            continue
        d = p[mask]-y[mask]
        rows.append(dict(model=label, population=population, cohort=cohort,
                         n=int(mask.sum()), fraction=float(mask.mean()), ead=float(ead[mask].sum()),
                         ead_fraction=float(ead[mask].sum()/ead.sum()),
                         actual=float(y[mask].mean()), predicted=float(p[mask].mean()),
                         mae=float(np.mean(abs(d))), rmse=float(np.sqrt(np.mean(d*d))),
                         bias=float(d.mean()), ead_weighted_bias=float(np.average(d, weights=ead[mask]))))
    return rows


def fit_and_record(rows, predictions, name, candidate, train, evals):
    fitted = candidate.fit(train) if isinstance(candidate, (TwoStage, SegmentMean, Component)) else candidate.fit(train, train[Y])
    for pop, data in evals.items():
        p = predict(fitted, data)
        rows.extend(score(data[Y], p, data.ead_at_default, name, pop))
        predictions.extend([dict(model=name, population=pop, facility_id=i, prediction=float(z))
                            for i, z in zip(data.facility_id, p)])
    return fitted


def main():
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    h = pd.read_csv(ROOT / "data/raw/lgd_workout_history.csv")
    h_dev, h_old = train_test_split(h, test_size=.25, random_state=42)
    r_dev = pd.read_csv(HERE / "data/r2_development.csv")
    r_select = pd.read_csv(HERE / "data/r2_selection.csv")
    assert set(r_dev.facility_id).isdisjoint(r_select.facility_id)
    assert set(h_dev.facility_id).isdisjoint(h_old.facility_id)
    r_equal = r_dev.sample(n=len(h_dev), random_state=17)
    evals = {"H previously viewed": h_old, "R2 selection": r_select}
    rows, preds = [], []
    designs = [
        ("A V5 H", gradient_boosting_lgd_model(), h_dev),
        ("B V5 R2 equal N", gradient_boosting_lgd_model(), r_equal),
        ("C two-stage H", TwoStage(), h_dev),
        ("D two-stage R2 equal N", TwoStage(), r_equal),
        ("mean R2", SegmentMean(), r_dev),
        ("V5 R2 full", gradient_boosting_lgd_model(), r_dev),
        ("Huber R2", model(kind="huber"), r_dev),
        ("RF R2", model(kind="rf"), r_dev),
        ("two-stage enhanced R2", TwoStage(NUMERIC_FEATURES+NEW_NUM, CATEGORICAL_FEATURES), r_dev),
        ("GB enhanced R2", model(NUMERIC_FEATURES+NEW_NUM, CATEGORICAL_FEATURES), r_dev),
        ("component R2", Component(), r_dev),
        ("oracle FUTURE INFORMATION", model(NUMERIC_FEATURES+NEW_NUM+ORACLE_NUM, CATEGORICAL_FEATURES), r_dev),
        ("quantile p90 RISK ONLY", model(NUMERIC_FEATURES+NEW_NUM, CATEGORICAL_FEATURES, kind="quantile"), r_dev),
    ]
    fitted = {}
    for name, candidate, train in designs:
        print("Fitting", name, flush=True)
        # R2-only features and realized oracle fields are not in H historical data.
        populations = evals if name in ["A V5 H", "B V5 R2 equal N", "C two-stage H",
                                        "D two-stage R2 equal N", "mean R2", "V5 R2 full",
                                        "Huber R2", "RF R2"] else {"R2 selection": r_select}
        fitted[name] = fit_and_record(rows, preds, name, candidate, train, populations)
    for dropped, num, cat in [
        ("collateral", [x for x in NUMERIC_FEATURES+NEW_NUM if x not in ["collateral_coverage", "security_quality"]],
         [x for x in CATEGORICAL_FEATURES if x not in ["collateral_type", "lien_rank"]]),
        ("guarantee", [x for x in NUMERIC_FEATURES+NEW_NUM if x not in ["guarantee_coverage", "guarantor_strength"]], CATEGORICAL_FEATURES),
        ("facility", [x for x in NUMERIC_FEATURES+NEW_NUM if x != "ead_at_default"],
         [x for x in CATEGORICAL_FEATURES if x != "product_type"]),
        ("borrower", [x for x in NUMERIC_FEATURES+NEW_NUM if x not in ["leverage_at_default", "current_ratio_at_default", "management_quality"]],
         [x for x in CATEGORICAL_FEATURES if x != "industry"]),
        ("new information", NUMERIC_FEATURES, CATEGORICAL_FEATURES),
    ]:
        fit_and_record(rows, preds, "ablate "+dropped, model(num, cat), r_dev, {"R2 selection": r_select})
    # Economic stress is always separated from ordinary validation.
    stress_rows = []
    ordinary = generate(3000, 20261104, "paired_ordinary")
    for scenario in ["collateral", "guarantee", "recovery", "timing", "cost", "combined"]:
        stressed = generate(3000, 20261104, "paired_stress", scenario)
        for name in ["A V5 H", "GB enhanced R2", "two-stage enhanced R2", "component R2"]:
            baseline, adverse = predict(fitted[name], ordinary), predict(fitted[name], stressed)
            stress_rows.append(dict(scenario=scenario, model=name, n=len(stressed),
                                    actual_shift=float((stressed[Y]-ordinary[Y]).mean()),
                                    forecast_shift=float((adverse-baseline).mean()),
                                    nonpositive_response_share=float(np.mean(adverse <= baseline))))
    pd.DataFrame(rows).to_csv(out / "development_scorecard.csv", index=False)
    pd.DataFrame(preds).to_csv(out / "selection_predictions.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(out / "stress_responses.csv", index=False)
    for name in ["A V5 H", "V5 R2 full", "GB enhanced R2"]:
        joblib.dump(fitted[name], out / (name.lower().replace(" ", "_")+".joblib"))
    print(pd.DataFrame(rows).query("population == 'R2 selection' and cohort in ['all','realized_gt75']")
          [["model", "cohort", "n", "mae", "rmse", "bias"]].to_string(index=False))


if __name__ == "__main__":
    main()
