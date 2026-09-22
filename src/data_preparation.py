import pandas as pd
from sklearn.model_selection import train_test_split

TARGET = "default"

# Explicit feature governance: PD is driven by borrower fundamentals and current
# observed behaviour. Product amounts/EAD mechanics, future outcomes, impairment
# flags, pricing and trajectory indicators belong to separate risk components.
PD_BASE_FEATURES = [
    "ebitda_margin",
    "leverage_ratio",
    "current_ratio",
    "debt_to_income",
    "collateral_coverage",
    "years_in_business",
    "credit_utilization",
    "delinquencies_12m",
    "previous_defaults",
    "days_past_due",
]


def load_data(path):
    return pd.read_csv(path)


def prepare_data(df):
    out = df.copy()
    out = pd.get_dummies(out, columns=["industry"], drop_first=True)
    return out


def pd_feature_columns(df):
    """Return the governed borrower-PD feature set; new columns are opt-in."""
    missing = [c for c in PD_BASE_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing governed PD features: {missing}")
    approved = list(PD_BASE_FEATURES)
    industry_cols = sorted(c for c in df.columns if c.startswith("industry_"))
    return approved + industry_cols


def split_data(df, target=TARGET, test_size=0.25, random_state=42):
    X = df[pd_feature_columns(df)]
    y = df[target]
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
