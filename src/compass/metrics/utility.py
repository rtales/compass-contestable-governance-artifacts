from __future__ import annotations

import numpy as np


def utility_at_k(y_true: np.ndarray, selected: np.ndarray) -> float | None:
    # Undefined when selection is empty; never report fabricated precision.
    idx = np.where(selected)[0]
    if idx.size == 0:
        return None
    return float(np.mean(y_true[idx]))


def coverage_rate(abstain: np.ndarray) -> float:
    return float(np.mean(~abstain))


def abstain_rate(abstain: np.ndarray) -> float:
    return float(np.mean(abstain))
