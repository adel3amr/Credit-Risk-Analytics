import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss

def gini(y_true, y_prob):
    return 2*roc_auc_score(y_true,y_prob)-1

def ks_statistic(y_true,y_prob):
    fpr,tpr,_=roc_curve(y_true,y_prob)
    return np.max(np.abs(tpr-fpr))

def validation_summary(y_true,y_prob):
    return {
        "ROC_AUC": roc_auc_score(y_true,y_prob),
        "Gini": gini(y_true,y_prob),
        "KS": ks_statistic(y_true,y_prob),
        "Brier": brier_score_loss(y_true,y_prob)
    }
