import pandas as pd
from sklearn.model_selection import train_test_split

TARGET = "default"

def load_data(path):
    return pd.read_csv(path)

def prepare_data(df):
    out = df.copy()
    out = pd.get_dummies(out, columns=["industry"], drop_first=True)
    return out

def split_data(df, target=TARGET, test_size=0.25, random_state=42):
    X=df.drop(columns=[target, "customer_id", "pd_true"], errors="ignore")
    y=df[target]
    return train_test_split(X,y,test_size=test_size,stratify=y,random_state=random_state)
