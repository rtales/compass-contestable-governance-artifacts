from __future__ import annotations

from pathlib import Path
import numpy as np


def load_processed(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load processed dataset in either NPY/NPZ or CSV format.

    Required outputs are:
      - X: features
      - y: label (0/1)
      - sensitive: group (0/1)

    Supported file layouts:
      A) Fast path:
         - X.npz  (compressed; preferred key is 'arr_0')
         - y.npy
         - sensitive.npy

      B) Compatibility path:
         - X.csv
         - y.csv
         - sensitive.csv

    NPZ key tolerance:
      - Prefer 'arr_0' (default for np.savez_compressed(X))
      - Fall back to 'X' (common for np.savez_compressed(..., X=X))
      - Fall back to first key in the archive
    """
    x_npz = processed_dir / "X.npz"
    y_npy = processed_dir / "y.npy"
    s_npy = processed_dir / "sensitive.npy"

    if x_npz.exists() and y_npy.exists() and s_npy.exists():
        npz = np.load(x_npz)
        key = "arr_0"
        if key not in npz.files:
            if "X" in npz.files:
                key = "X"
            elif len(npz.files) > 0:
                key = npz.files[0]
            else:
                raise KeyError("X.npz contains no arrays")
        X = npz[key].astype(np.float32)
        y = np.load(y_npy).astype(int).reshape(-1)
        s = np.load(s_npy).astype(int).reshape(-1)
        return X, y, s

    # fallback CSV
    x_csv = processed_dir / "X.csv"
    y_csv = processed_dir / "y.csv"
    s_csv = processed_dir / "sensitive.csv"
    if not x_csv.exists() or not y_csv.exists() or not s_csv.exists():
        raise FileNotFoundError(
            "Processed dataset must contain either (X.npz,y.npy,sensitive.npy) or (X.csv,y.csv,sensitive.csv)."
        )

    X = np.loadtxt(x_csv, delimiter=",").astype(np.float32)
    y = np.loadtxt(y_csv, delimiter=",").astype(int).reshape(-1)
    s = np.loadtxt(s_csv, delimiter=",").astype(int).reshape(-1)
    return X, y, s
