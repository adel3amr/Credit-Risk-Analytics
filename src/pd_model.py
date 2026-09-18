from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier


def logistic_model():
    """Interpretable PD model with probabilities suitable for calibration review.

    Deliberately unweighted: class_weight='balanced' changes the effective class
    prior and can materially distort raw predict_proba values when they are used
    as PDs. Imbalance is handled through ranking metrics and calibration review.
    """
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000))
    ])


def random_forest_model():
    """Non-linear challenger; kept unweighted for probability comparability."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            n_estimators=350, max_depth=7, min_samples_leaf=20,
            random_state=42, n_jobs=-1))
    ])


def gradient_boosting_model():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", GradientBoostingClassifier(
            n_estimators=250, max_depth=3, learning_rate=.04, random_state=42))
    ])
