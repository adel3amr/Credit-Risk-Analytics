"""Independent arithmetic: deliberately does not import production risk functions."""

import math
from collections import Counter


def reconcile(traces):
    maximum = 0.0
    for t in traces:
        if t["stage"] not in ("Stage 1", "Stage 2", "Stage 3"):
            raise ValueError("Invalid stage in independent reconciliation")
        for field in ("pd", "lgd", "ead", "ecl", "remaining_months"):
            value = t[field]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Nonfinite or nonnumeric reconciliation input")
            if value < 0 or (field in ("pd", "lgd") and value > 1):
                raise ValueError("Reconciliation input outside permitted range")
        effective = (
            1
            if t["stage"] == "Stage 3"
            else (
                1 - (1 - t["pd"]) ** (t["remaining_months"] / 12)
                if t["stage"] == "Stage 2"
                else t["pd"]
            )
        )
        maximum = max(maximum, abs(effective * t["lgd"] * t["ead"] - t["ecl"]))
    if maximum > 1e-7:
        raise ValueError("Independent ECL reconciliation failed")
    return {
        "facility_count": len(traces),
        "maximum_ecl_error": maximum,
        "ead": math.fsum(t["ead"] for t in traces),
        "ecl": math.fsum(t["ecl"] for t in traces),
        "stages": dict(Counter(t["stage"] for t in traces)),
    }


def loss_metrics(actual, predicted, exposures):
    if len(actual) != len(predicted) or len(actual) != len(exposures) or not actual:
        raise ValueError("Equal nonempty samples required")
    for x in [*actual, *predicted, *exposures]:
        if not math.isfinite(x):
            raise ValueError("Nonfinite validation data")
    if any(x < 0 or x > 1 for x in [*actual, *predicted]) or any(
        x < 0 for x in exposures
    ):
        raise ValueError("Invalid validation range")
    out = []
    total = math.fsum(exposures)
    for name, indices in [
        ("all", list(range(len(actual)))),
        *[
            (f"realized_gt{int(q * 100)}", [i for i, a in enumerate(actual) if a > q])
            for q in (0.6, 0.75, 0.9)
        ],
        ("realized_le10", [i for i, a in enumerate(actual) if a <= 0.1]),
        (
            "predicted_top10",
            sorted(range(len(actual)), key=lambda i: predicted[i], reverse=True)[
                : max(1, math.ceil(len(actual) * 0.1))
            ],
        ),
    ]:
        if not indices:
            out.append(
                {"cohort": name, "n": 0, "bias": None, "reason": "No observations"}
            )
            continue
        errors = [predicted[i] - actual[i] for i in indices]
        n = len(indices)
        ead = math.fsum(exposures[i] for i in indices)
        out.append(
            {
                "cohort": name,
                "n": n,
                "observation_share": n / len(actual),
                "ead": ead,
                "ead_share": ead / total if total else None,
                "mae": math.fsum(abs(e) for e in errors) / n,
                "rmse": math.sqrt(math.fsum(e * e for e in errors) / n),
                "bias": math.fsum(errors) / n,
                "mean_predicted": math.fsum(predicted[i] for i in indices) / n,
                "mean_realized": math.fsum(actual[i] for i in indices) / n,
                "ead_weighted_bias": math.fsum(
                    (predicted[i] - actual[i]) * exposures[i] for i in indices
                )
                / ead
                if ead
                else None,
            }
        )
    return out


def monitor(traces):
    n = len(traces)
    return {
        "n": n,
        "zero_guarantee_share": sum(
            t["source_facility"]["guarantee_coverage"] == 0 for t in traces
        )
        / n
        if n
        else None,
        "mean_lgd": math.fsum(t["lgd"] for t in traces) / n if n else None,
        "stage_counts": dict(Counter(t["stage"] for t in traces)),
        "alerts": [
            "Reference LGD training has virtually no zero-guarantee support",
            "No institutional outcome validation; bank use blocked",
        ],
        "classification": "support diagnostics, not outcome validation",
    }


def concentrations(traces):
    result = {}
    for label, key in [
        ("industry", lambda t: t["source_borrower"]["industry"]),
        ("product", lambda t: t["source_facility"]["product"]),
        ("collateral", lambda t: t["source_facility"]["collateral_type"]),
        ("stage", lambda t: t["stage"]),
    ]:
        groups = {}
        for t in traces:
            groups.setdefault(key(t), []).append(t)
        result[label] = []
        for name, group in groups.items():
            total = math.fsum(t["ead"] for t in group)
            result[label].append(
                {
                    "segment": name,
                    "facilities": len(group),
                    "ead": total,
                    "ecl": math.fsum(t["ecl"] for t in group),
                    "weighted_pd": math.fsum(t["pd"] * t["ead"] for t in group) / total
                    if total
                    else None,
                    "weighted_lgd": math.fsum(t["lgd"] * t["ead"] for t in group)
                    / total
                    if total
                    else None,
                }
            )
    return result


def movements(previous, current):
    a = {t["facility_id"]: t for t in previous}
    b = {t["facility_id"]: t for t in current}
    total = {
        "new_exposures": 0.0,
        "exited_exposures": 0.0,
        "effective_pd_stage_maturity": 0.0,
        "lgd": 0.0,
        "ead": 0.0,
    }
    migrations = Counter()
    for id in a.keys() | b.keys():
        if id not in a:
            total["new_exposures"] += b[id]["ecl"]
            continue
        if id not in b:
            total["exited_exposures"] -= a[id]["ecl"]
            continue
        x, y = a[id], b[id]
        migrations[(x["stage"], y["stage"])] += 1
        total["effective_pd_stage_maturity"] += (
            (y["effective_pd"] - x["effective_pd"]) * x["lgd"] * x["ead"]
        )
        total["lgd"] += y["effective_pd"] * (y["lgd"] - x["lgd"]) * x["ead"]
        total["ead"] += y["effective_pd"] * y["lgd"] * (y["ead"] - x["ead"])
    change = math.fsum(t["ecl"] for t in current) - math.fsum(
        t["ecl"] for t in previous
    )
    if not math.isclose(math.fsum(total.values()), change, rel_tol=1e-10, abs_tol=1e-7):
        raise ValueError("Movement reconciliation failed")
    return {
        "ecl_change": change,
        "attribution": total,
        "order": "effective PD (including stage/maturity), then LGD, then EAD; ordered attribution is not causal",
        "stage_migrations": [
            {"from": x, "to": y, "facilities": n} for (x, y), n in migrations.items()
        ],
    }
