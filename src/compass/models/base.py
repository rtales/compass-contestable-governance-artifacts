from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class ModelResult:
    scores: np.ndarray  # in [0,1]


class BaseModel:
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseModel":
        raise NotImplementedError

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError
