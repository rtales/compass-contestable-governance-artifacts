from __future__ import annotations

from pathlib import Path
import json
import numpy as np

from compass.utils.io import atomic_write_text
from compass.utils.hashing import sha256_bytes


def _one_hot(values, categories):
    idx = {c: i for i, c in enumerate(categories)}
    n = len(values)
    out = np.zeros((n, len(categories)), dtype=np.float32)
    unk_i = idx.get("UNKNOWN", None)
    for r, v in enumerate(values):
        j = idx.get(v, unk_i if unk_i is not None else 0)
        out[r, j] = 1.0
    return out


def build_assistments_processed_from_csv(raw_csv: Path, out_dir: Path) -> None:
    """Deterministically build a processed ASSISTments Skill Builder 2009–2010 dataset folder.

    Input:
      - raw_csv: datasets/skill_builder_data.csv

    Output (out_dir):
      - processed/X.npz
      - processed/y.npy
      - processed/sensitive.npy
      - manifest.json
      - schema.json

    Modeling choice (simple & reproducible):
      - Each row is an interaction.
      - Label y: `correct` (0/1).
      - Sensitive attribute: `school_id % 2` (0/1), deterministic proxy to exercise fairness constraints.
      - Features:
          numeric: attempt_count, log1p(ms_first_response), hint_count, hint_total,
                   log1p(overlap_time), opportunity, original, skill_id_mod_1000
          categorical (one-hot): tutor_mode, answer_type, type
    """
    try:
        import pandas as pd
    except Exception as e:
        raise RuntimeError(
            "pandas is required to process ASSISTments. Install with: pip install -e '.[full]'"
        ) from e

    def _read_csv_robust(path: Path):
        # ASSISTments CSVs are sometimes not UTF-8 (often cp1252/latin-1).
        # Use a deterministic set of encodings; replace invalid bytes; skip malformed lines.
        encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
        last_err = None
        for enc in encodings:
            try:
                return pd.read_csv(
                    path,
                    encoding=enc,
                    encoding_errors="replace",
                    low_memory=False,
                    on_bad_lines="skip",
                )
            except UnicodeDecodeError as e:
                last_err = e
                continue
            except TypeError:
                # Older pandas: encoding_errors may not exist; retry without it.
                try:
                    return pd.read_csv(path, encoding=enc, low_memory=False, on_bad_lines="skip")
                except UnicodeDecodeError as e:
                    last_err = e
                    continue
        raise RuntimeError(f"Failed to decode CSV with encodings {encodings}. Last error: {last_err}")

    df = _read_csv_robust(raw_csv)

    # Minimal cleaning
    df = df.copy()

    # Required columns sanity (keep deterministic behavior)
    required = ["correct", "school_id", "attempt_count", "ms_first_response", "hint_count",
                "hint_total", "overlap_time", "opportunity", "original",
                "tutor_mode", "answer_type", "type", "skill_id"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"ASSISTments CSV missing required columns: {missing}")

    # Label and sensitive
    df["correct"] = pd.to_numeric(df["correct"], errors="coerce").fillna(0).astype(int)
    y = df["correct"].clip(0, 1).to_numpy(dtype=np.int64)

    df["school_id"] = pd.to_numeric(df["school_id"], errors="coerce").fillna(0).astype(int)
    sensitive = (df["school_id"].to_numpy(dtype=np.int64) % 2).astype(np.int64)

    # Numeric features (bounded + log1p for time)
    def num(col, fill=0.0):
        return pd.to_numeric(df[col], errors="coerce").fillna(fill).astype(float)

    attempt = num("attempt_count", 0.0).clip(0, 50).to_numpy(dtype=np.float32)
    ms_first = np.log1p(num("ms_first_response", 0.0).clip(0, 300000).to_numpy(dtype=np.float32))
    hint_count = num("hint_count", 0.0).clip(0, 50).to_numpy(dtype=np.float32)
    hint_total = num("hint_total", 0.0).clip(0, 50).to_numpy(dtype=np.float32)
    overlap = np.log1p(num("overlap_time", 0.0).clip(0, 300000).to_numpy(dtype=np.float32))
    opportunity = num("opportunity", 0.0).clip(0, 100).to_numpy(dtype=np.float32)
    original = num("original", 0.0).clip(0, 1).to_numpy(dtype=np.float32)

    skill_id_mod_1000 = (num("skill_id", 0.0).fillna(0).astype(int).to_numpy() % 1000).astype(np.float32)

    # Categorical one-hot (fixed category sets for determinism)
    tutor_mode_cats = ["tutor", "test", "UNKNOWN"]
    answer_type_cats = ["choice", "string", "numeric", "UNKNOWN"]
    type_cats = ["Algebra", "Geometry", "Arithmetic", "Other", "UNKNOWN"]

    tutor = df["tutor_mode"].astype(str).fillna("UNKNOWN").replace({"nan": "UNKNOWN"}).to_list()
    ans = df["answer_type"].astype(str).fillna("UNKNOWN").replace({"nan": "UNKNOWN"}).to_list()
    typ = df["type"].astype(str).fillna("UNKNOWN").replace({"nan": "UNKNOWN"}).to_list()

    X_cat = np.concatenate(
        [
            _one_hot(tutor, tutor_mode_cats),
            _one_hot(ans, answer_type_cats),
            _one_hot(typ, type_cats),
        ],
        axis=1,
    ).astype(np.float32)

    X_num = np.stack(
        [attempt, ms_first, hint_count, hint_total, overlap, opportunity, original, skill_id_mod_1000],
        axis=1,
    ).astype(np.float32)

    X = np.concatenate([X_num, X_cat], axis=1).astype(np.float32)

    processed = out_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    # Persist arrays
    np.save(processed / "y.npy", y)
    np.save(processed / "sensitive.npy", sensitive)
    np.savez_compressed(processed / "X.npz", X)

    # Deterministic schema + manifest
    schema = {
        "dataset_id": "assistments_2009_2010_v1",
        "format": "npz+npy",
        "X": {"path": "processed/X.npz", "key": "arr_0", "dtype": "float32", "shape": list(X.shape)},
        "y": {"path": "processed/y.npy", "dtype": "int64", "shape": list(y.shape)},
        "sensitive": {"path": "processed/sensitive.npy", "dtype": "int64", "shape": list(sensitive.shape)},
        "features": {
            "numeric": ["attempt_count", "log1p_ms_first_response", "hint_count", "hint_total",
                        "log1p_overlap_time", "opportunity", "original", "skill_id_mod_1000"],
            "categorical_one_hot": {
                "tutor_mode": tutor_mode_cats,
                "answer_type": answer_type_cats,
                "type": type_cats,
            },
        },
        "label": {"name": "correct", "positive": 1},
        "sensitive": {"name": "school_id_mod2", "values": [0, 1], "note": "Deterministic proxy; not a demographic attribute."},
        "preprocessing": {
            "encoding_try_order": ["utf-8", "utf-8-sig", "cp1252", "latin-1"],
            "encoding_errors": "replace",
            "on_bad_lines": "skip",
        },
    }

    raw_bytes = raw_csv.read_bytes()
    manifest = {
        "source_raw": str(raw_csv),
        "raw_sha256": sha256_bytes(raw_bytes),
        "n_rows_raw": int(df.shape[0]),
        "n_rows_processed": int(X.shape[0]),
        "n_features": int(X.shape[1]),
    }

    atomic_write_text(out_dir / "schema.json", json.dumps(schema, indent=2, sort_keys=True))
    atomic_write_text(out_dir / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
