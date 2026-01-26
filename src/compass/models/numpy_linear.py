from __future__ import annotations

import numpy as np

from compass.models.base import BaseModel


class NumpyLinearProb(BaseModel):
    """Deterministic baseline: ridge regression + sigmoid.

    Works in the 'core' dependency profile (numpy only).
    """
    def __init__(self, l2: float = 1e-3):
        self.l2 = float(l2)
        self.w: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NumpyLinearProb":
        Xb = np.concatenate([X, np.ones((X.shape[0], 1), dtype=X.dtype)], axis=1)
        # closed-form ridge: w = (X^T X + l2 I)^-1 X^T y
        XtX = Xb.T @ Xb
        reg = self.l2 * np.eye(XtX.shape[0], dtype=XtX.dtype)
        w = np.linalg.solve(XtX + reg, Xb.T @ y.astype(XtX.dtype))
        self.w = w
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.w is None:
            raise RuntimeError("Model not fit.")
        Xb = np.concatenate([X, np.ones((X.shape[0], 1), dtype=X.dtype)], axis=1)
        logits = Xb @ self.w
        p = 1.0 / (1.0 + np.exp(-logits))
        return np.clip(p.astype(np.float32), 0.0, 1.0)
