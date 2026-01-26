from __future__ import annotations

from compass.models.numpy_linear import NumpyLinearProb
from compass.models.sklearn_logreg import SklearnLogReg


def build_model(model_type: str, params: dict):
    if model_type == "numpy_linear":
        return NumpyLinearProb(**params)
    if model_type == "sklearn_logreg":
        return SklearnLogReg(**params)
    raise ValueError(f"Unknown model.type: {model_type}")
