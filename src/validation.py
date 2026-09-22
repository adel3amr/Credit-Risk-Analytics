import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss, log_loss


def gini(y_true, y_prob):
    return 2 * roc_auc_score(y_true, y_prob) - 1


def ks_statistic(y_true, y_prob):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return np.max(np.abs(tpr - fpr))


def calibration_in_the_large(y_true, y_prob):
    """Observed default rate minus mean predicted PD; zero is ideal."""
    return float(np.mean(y_true) - np.mean(y_prob))


def calibration_table(y_true, y_prob, bins=10):
    """Equal-frequency reliability table for borrower-level PD validation."""
    frame = pd.DataFrame({
        "default": np.asarray(y_true),
        "predicted_pd": np.asarray(y_prob),
    })
    # Rank first so qcut remains stable when probabilities tie.
    frame["bucket"] = pd.qcut(
        frame["predicted_pd"].rank(method="first"),
        q=bins,
        labels=False,
    ) + 1
    return frame.groupby("bucket", as_index=False).agg(
        borrowers=("default", "size"),
        mean_predicted_pd=("predicted_pd", "mean"),
        observed_default_rate=("default", "mean"),
    )


def validation_summary(y_true, y_prob):
    return {
        "ROC_AUC": roc_auc_score(y_true, y_prob),
        "Gini": gini(y_true, y_prob),
        "KS": ks_statistic(y_true, y_prob),
        "Brier": brier_score_loss(y_true, y_prob),
        "LogLoss": log_loss(y_true, y_prob, labels=[0, 1]),
        "Mean_PD": float(np.mean(y_prob)),
        "Observed_DR": float(np.mean(y_true)),
        "Calibration_in_the_large": calibration_in_the_large(y_true, y_prob),
    }


def threshold_diagnostics(y_true, y_prob, thresholds=(0.05, 0.10)):
    """Reference classification diagnostics without threshold optimization.

    A PD model remains probabilistic. These fixed thresholds are operational
    illustrations only; they are not selected on the validation sample.
    """
    y=np.asarray(y_true).astype(int)
    p=np.asarray(y_prob, dtype=float)
    rows=[]
    for threshold in thresholds:
        flagged=p >= threshold
        tp=int(((y==1) & flagged).sum())
        fp=int(((y==0) & flagged).sum())
        tn=int(((y==0) & ~flagged).sum())
        fn=int(((y==1) & ~flagged).sum())
        rows.append({
            "threshold": threshold,
            "TN": tn, "FP": fp, "FN": fn, "TP": tp,
            "default_capture_recall": tp / max(tp+fn, 1),
            "precision": tp / max(tp+fp, 1),
            "specificity": tn / max(tn+fp, 1),
            "false_positive_rate": fp / max(fp+tn, 1),
            "flagged_population": flagged.mean(),
        })
    return pd.DataFrame(rows)
