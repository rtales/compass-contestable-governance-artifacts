from __future__ import annotations

import numpy as np


def binary_entropy(p: np.ndarray, eps: float | None = None) -> np.ndarray:
    """Binary entropy in bits, robust at p=0/1.

    With float32, very small eps values (e.g., 1e-12) can round to 0 or 1.
    We therefore compute in float64 and use a practical default epsilon.
    """
    p64 = np.asarray(p, dtype=np.float64)
    if eps is None:
        eps = 1e-7
    p64 = np.clip(p64, eps, 1.0 - eps)
    return -(p64 * np.log2(p64) + (1.0 - p64) * np.log2(1.0 - p64))


def apply_topk_with_abstain(scores: np.ndarray, k: int, gamma_entropy: float | None) -> dict:
    n = scores.shape[0]
    ent = binary_entropy(scores)
    abstain = np.zeros(n, dtype=bool)
    if gamma_entropy is not None:
        abstain = ent > gamma_entropy

    eligible = np.where(~abstain)[0]
    # If fewer than k eligible, select all eligible
    order = eligible[np.argsort(scores[eligible])[::-1]]
    selected = np.zeros(n, dtype=bool)
    selected[order[: min(k, order.shape[0])]] = True

    return {
        "selected": selected,
        "abstain": abstain,
        "entropy": ent,
    }
