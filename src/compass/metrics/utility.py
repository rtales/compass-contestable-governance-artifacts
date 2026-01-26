from __future__ import annotations

import numpy as np


def utility_at_k(y_true: np.ndarray, selected: np.ndarray) -> float:
    # fraction of positives among selected (precision-like). If none selected, 0.
    idx = np.where(selected)[0]
    if idx.size == 0:
        return 0.0
    return float(np.mean(y_true[idx]))


def coverage_rate(abstain: np.ndarray) -> float:
    return float(np.mean(~abstain))


def abstain_rate(abstain: np.ndarray) -> float:
    return float(np.mean(abstain))
