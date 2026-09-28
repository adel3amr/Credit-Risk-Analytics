"""Current controlled successor entry point; old research modules stay frozen."""
import joblib
from s2_remediation.evaluate import OUT,verify_lock
from s2_remediation.model import predict
from .release import require_promotion


def score(frame):
    verify_lock()
    require_promotion(OUT)
    support=joblib.load(OUT/'support.joblib')
    support.require(frame)
    return predict(joblib.load(OUT/'model.joblib'),frame)
