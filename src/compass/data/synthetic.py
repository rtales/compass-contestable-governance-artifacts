from __future__ import annotations

from pathlib import Path
import json
import numpy as np

from compass.utils.hashing import sha256_bytes
from compass.utils.io import atomic_write_text


def generate_synthetic(seed: int = 42, n: int = 5000, d: int = 20) -> dict:
    rng = np.random.default_rng(seed)
    # sensitive attribute: two groups
    s = (rng.random(n) > 0.5).astype(int)
    # features with a mild group shift
    X = rng.normal(size=(n, d)).astype(np.float32)
    X[:, 0] += (s * 0.3).astype(np.float32)
    # label depends on linear score + bias, with mild group-dependent noise
    w = rng.normal(size=(d,)).astype(np.float32)
    logits = X @ w + (s * 0.2).astype(np.float32) + rng.normal(scale=0.5, size=n).astype(np.float32)
    p = 1.0 / (1.0 + np.exp(-logits))
    y = (p > 0.5).astype(int)
    return {"X": X, "y": y, "sensitive": s}


def build_synthetic_snapshot(unpack_dir: Path) -> None:
    processed = unpack_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    data = generate_synthetic(seed=42, n=5000, d=20)
    X = data["X"]; y = data["y"]; s = data["sensitive"]

    # store as CSV for maximum compatibility (core profile)
    x_path = processed / "X.csv"
    y_path = processed / "y.csv"
    s_path = processed / "sensitive.csv"

    np.savetxt(x_path, X, delimiter=",")
    np.savetxt(y_path, y.reshape(-1, 1), delimiter=",", fmt="%d")
    np.savetxt(s_path, s.reshape(-1, 1), delimiter=",", fmt="%d")

    manifest = {
        "dataset_id": "synthetic_v1",
        "schema_version": 1,
        "format": "csv",
        "seed": 42,
        "n": int(X.shape[0]),
        "d": int(X.shape[1]),
        "files": {
            "X.csv": {"sha256": sha256_bytes(x_path.read_bytes())},
            "y.csv": {"sha256": sha256_bytes(y_path.read_bytes())},
            "sensitive.csv": {"sha256": sha256_bytes(s_path.read_bytes())},
        },
    }
    atomic_write_text(unpack_dir / "manifest.json", json.dumps(manifest, indent=2))
