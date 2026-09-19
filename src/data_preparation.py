import pandas as pd
from sklearn.model_selection import train_test_split

TARGET = "default"

# PD is a borrower-default model. Keep outcome/identifier fields and the separate
# ECL risk parameters (EAD/LGD) out of the PD feature matrix.
PD_EXCLUDED_COLUMNS = {
    TARGET,
    "customer_id",
    "pd_true",
    "ead",
    "lgd",
}


def load_data(path):
    return pd.read_csv(path)


def prepare_data(df):
    out = df.copy()
    out = pd.get_dummies(out, columns=["industry"], drop_first=True)
    return out


def pd_feature_columns(df):
    return [c for c in df.columns if c not in PD_EXCLUDED_COLUMNS]


def split_data(df, target=TARGET, test_size=0.25, random_state=42):
    cols = [c for c in pd_feature_columns(df) if c != target]
    X = df[cols]
    y = df[target]
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
