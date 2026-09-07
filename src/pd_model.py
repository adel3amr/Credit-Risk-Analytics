from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

def logistic_model():
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median")),
        ("scaler",StandardScaler()),
        ("model",LogisticRegression(max_iter=2000,class_weight="balanced"))
    ])

def random_forest_model():
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median")),
        ("model",RandomForestClassifier(
            n_estimators=350,max_depth=7,min_samples_leaf=20,
            class_weight="balanced",random_state=42,n_jobs=-1))
    ])

def gradient_boosting_model():
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median")),
        ("model",GradientBoostingClassifier(
            n_estimators=250,max_depth=3,learning_rate=.04,random_state=42))
    ])
