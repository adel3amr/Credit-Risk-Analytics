"""Existing GB architecture extended only for reporting-date economic inputs."""
import numpy as np
from src.lgd_model import gradient_boosting_lgd_model, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from .economics import MACRO, validate

VERSION = 's2-observable-gb-1'
NUMERIC = NUMERIC_FEATURES + ['interest_rate'] + MACRO
FEATURES = NUMERIC + CATEGORICAL_FEATURES


def features(frame):
    validate(frame)
    result = frame[FEATURES].copy()
    if result.isna().any().any() or not np.isfinite(result[NUMERIC].to_numpy()).all():
        raise ValueError('Missing or nonfinite scoring inputs')
    return result


def build():
    pipeline = gradient_boosting_lgd_model()
    transformers = pipeline.named_steps['prep'].transformers
    pipeline.named_steps['prep'].transformers = [
        (name, transformer, NUMERIC if name=='num' else columns)
        for name,transformer,columns in transformers]
    return pipeline


def predict(model, frame):
    raw = np.asarray(model.predict(features(frame)),dtype=float)
    if raw.shape != (len(frame),) or not np.isfinite(raw).all():
        raise ValueError('Invalid LGD prediction')
    return raw.clip(0,1)
