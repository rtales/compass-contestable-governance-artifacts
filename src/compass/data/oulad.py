from __future__ import annotations

from pathlib import Path
import json
import zipfile
import numpy as np

from compass.utils.io import atomic_write_text
from compass.utils.hashing import sha256_bytes


def _one_hot(df_col, categories):
    # returns (n, k) float32
    idx = {c: i for i, c in enumerate(categories)}
    n = len(df_col)
    out = np.zeros((n, len(categories)), dtype=np.float32)
    for r, v in enumerate(df_col):
        out[r, idx.get(v, idx["UNKNOWN"])] = 1.0
    return out


def build_oulad_processed_from_zip(raw_zip: Path, out_dir: Path) -> None:
    """Deterministically build a processed OULAD dataset folder.

    Inputs:
      - raw_zip: datasets/anonymisedData.zip

    Output contract (out_dir):
      - processed/X.npz
      - processed/y.npy
      - processed/sensitive.npy
      - manifest.json
      - schema.json (feature names)

    Modeling choice (simple & reproducible):
      - Label y: 1 if final_result in {Pass, Distinction}, else 0.
      - Sensitive attribute: gender (F=0, M=1). Rows with other values are dropped.
      - Features: one-hot for categorical columns + numeric columns.
    """
    try:
        import pandas as pd
    except Exception as e:
        raise RuntimeError("pandas is required to process OULAD. Install with: pip install -e '.[full]'") from e

    with zipfile.ZipFile(raw_zip, "r") as z:
        with z.open("studentInfo.csv") as f:
            df = pd.read_csv(f)

    # Normalize missing
    cat_cols = [
        "code_module",
        "code_presentation",
        "region",
        "highest_education",
        "imd_band",
        "age_band",
        "disability",
    ]
    num_cols = ["num_of_prev_attempts", "studied_credits"]

    df = df.copy()
    for c in cat_cols:
        df[c] = df[c].astype(str).fillna("UNKNOWN").replace({"?": "UNKNOWN"}).str.strip()
        df[c] = df[c].where(df[c] != "", "UNKNOWN")

    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(float)

    # Sensitive: gender
    df["gender"] = df["gender"].astype(str).str.strip()
    df = df[df["gender"].isin(["F", "M"])].reset_index(drop=True)
    sensitive = (df["gender"].values == "M").astype(int)

    # Label
    df["final_result"] = df["final_result"].astype(str).str.strip()
    y = df["final_result"].isin(["Pass", "Distinction"]).astype(int).values

    # Build features
    parts = []
    feature_names = []

    for c in cat_cols:
        cats = sorted(df[c].unique().tolist())
        if "UNKNOWN" not in cats:
            cats = ["UNKNOWN"] + cats
        one = _one_hot(df[c].values.tolist(), cats)
        parts.append(one)
        feature_names.extend([f"{c}={v}" for v in cats])

    # numeric
    for c in num_cols:
        parts.append(df[c].values.astype(np.float32).reshape(-1, 1))
        feature_names.append(c)

    X = np.concatenate(parts, axis=1).astype(np.float32)

    processed = out_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(processed / "X.npz", X)
    np.save(processed / "y.npy", y.astype(np.int64))
    np.save(processed / "sensitive.npy", sensitive.astype(np.int64))

    manifest = {
        "dataset_id": "oulad_v1",
        "schema_version": 2,
        "format": "npz+npy",
        "raw_file": str(raw_zip),
        "n": int(X.shape[0]),
        "d": int(X.shape[1]),
        "label": {"name": "success", "definition": "1 if final_result in {Pass, Distinction} else 0"},
        "sensitive": {"name": "gender", "definition": "F=0, M=1"},
        "files": {
            "processed/X.npz": {"sha256": sha256_bytes((processed / "X.npz").read_bytes())},
            "processed/y.npy": {"sha256": sha256_bytes((processed / "y.npy").read_bytes())},
            "processed/sensitive.npy": {"sha256": sha256_bytes((processed / "sensitive.npy").read_bytes())},
        },
    }
    atomic_write_text(out_dir / "manifest.json", json.dumps(manifest, indent=2))
    atomic_write_text(out_dir / "schema.json", json.dumps({"feature_names": feature_names}, indent=2))
