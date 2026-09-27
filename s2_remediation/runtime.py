"""Controlled scoring boundary: approval and support precede any usable result."""
import json
import joblib
from credit_platform.common import ROOT
from .evaluate import OUT,verify_lock
from .model import predict,VERSION


def score(frame):
    verify_lock()
    registry=json.loads((OUT/'registry.json').read_text())
    if registry['model_id']!=VERSION or registry['status']!='PROMOTED_SYNTHETIC_REFERENCE':
        raise ValueError('S2-R1 promotion gate is blocked')
    support=joblib.load(OUT/'support.joblib')
    support.require(frame)
    return predict(joblib.load(OUT/'model.joblib'),frame)
