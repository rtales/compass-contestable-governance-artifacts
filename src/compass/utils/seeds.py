"""Seed utilities for deterministic/offline runs.

This module is intentionally lightweight and avoids hard dependencies.
If optional libraries (e.g., torch) are present, we seed them too.
"""

from __future__ import annotations

import os
import random

import numpy as np


def set_global_seed(seed: int, *, deterministic: bool = True) -> None:
    """Set seeds across common RNG sources to improve reproducibility.

    Parameters
    ----------
    seed:
        Integer seed.
    deterministic:
        If True, enables best-effort deterministic settings for optional libs.
    """
    if seed is None:
        raise ValueError("seed must not be None")

    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Optional: PyTorch
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            try:
                torch.use_deterministic_algorithms(True)
            except Exception:
                pass
    except Exception:
        # torch not installed or not usable; ignore
        pass

