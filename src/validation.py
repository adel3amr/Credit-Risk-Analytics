import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss


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
        "Mean_PD": float(np.mean(y_prob)),
        "Observed_DR": float(np.mean(y_true)),
        "Calibration_in_the_large": calibration_in_the_large(y_true, y_prob),
    }
