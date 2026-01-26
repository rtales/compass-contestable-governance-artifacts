from __future__ import annotations

import numpy as np

from compass.models.base import BaseModel


class SklearnLogReg(BaseModel):
    """Logistic regression baseline (scikit-learn) with scaling for stability.

    We wrap LogisticRegression in a StandardScaler pipeline to improve convergence
    and make behavior more robust across datasets.
    """

    def __init__(self, max_iter: int = 1000, C: float = 1.0):
        self.max_iter = int(max_iter)
        self.C = float(C)
        self._m = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnLogReg":
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import make_pipeline
        except Exception as e:
            raise RuntimeError(
                "scikit-learn is required for SklearnLogReg. Install with extras: pip install -e '.[full]'"
            ) from e

        clf = LogisticRegression(max_iter=self.max_iter, C=self.C, solver="lbfgs")
        self._m = make_pipeline(StandardScaler(), clf)
        self._m.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self._m is None:
            raise RuntimeError("Model not fit.")
        p = self._m.predict_proba(X)[:, 1]
        return np.clip(p.astype(np.float32), 0.0, 1.0)
