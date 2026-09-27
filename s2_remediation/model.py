"""Constrained S2 successor. No calibration offsets or outcome-derived features."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from economic_lgd.model import FEATURES, NUMERIC, features
from src.lgd_model import CATEGORICAL_FEATURES

VERSION = 's2-r1-monotone-gb-1'
SIGNS = {'output_growth_pct':-1,'unemployment_pct':1,
         'collateral_change_pct':-1,'liquidity':-1,
         'collateral_coverage':-1,'guarantee_coverage':-1}


def build(frame):
    x=features(frame)
    categories=[sorted(x[c].unique()) for c in CATEGORICAL_FEATURES]
    prep=ColumnTransformer([
        ('num','passthrough',NUMERIC),
        ('cat',OneHotEncoder(categories=categories,handle_unknown='error',sparse_output=False),CATEGORICAL_FEATURES)])
    signs=[SIGNS.get(c,0) for c in NUMERIC]+[0]*sum(map(len,categories))
    return Pipeline([('prep',prep),('model',HistGradientBoostingRegressor(
        loss='squared_error',max_iter=350,learning_rate=.05,max_leaf_nodes=31,
        min_samples_leaf=80,l2_regularization=5,random_state=94001,
        early_stopping=False,monotonic_cst=signs))])


def predict(model, frame):
    x=features(frame)
    if ((x.guarantee_coverage<0)|(x.guarantee_coverage>1)|
        (x.collateral_coverage<0)|(x.ead_at_default<=0)|(x.interest_rate<0)).any():
        raise ValueError('Invalid recovery contract')
    p=np.asarray(model.predict(x),dtype=float)
    if p.shape!=(len(x),) or not np.isfinite(p).all():
        raise ValueError('Invalid prediction')
    return p.clip(0,1)
