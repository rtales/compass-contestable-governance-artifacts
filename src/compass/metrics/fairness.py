from __future__ import annotations

import numpy as np


def tpr_at_k(y_true: np.ndarray, selected: np.ndarray, group: np.ndarray, group_value: int) -> float:
    g = group == group_value
    positives = np.where(g & (y_true == 1))[0]
    if positives.size == 0:
        return 0.0
    return float(np.mean(selected[positives]))


def delta_eopp_at_k(y_true: np.ndarray, selected: np.ndarray, group: np.ndarray) -> float:
    # Equal Opportunity difference: TPR(group=1) - TPR(group=0)
    tpr1 = tpr_at_k(y_true, selected, group, 1)
    tpr0 = tpr_at_k(y_true, selected, group, 0)
    return float(tpr1 - tpr0)
