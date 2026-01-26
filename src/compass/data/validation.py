from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np

from compass.data.io import load_processed


@dataclass
class ValidationReport:
    ok: bool
    issues: list[str]
    summary: dict

    def to_text(self) -> str:
        lines = [f"ok={self.ok}"]
        if self.issues:
            lines.append("issues:")
            for i in self.issues:
                lines.append(f"  - {i}")
        lines.append("summary:")
        for k, v in self.summary.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)


def validate_processed_dataset(dataset_dir: Path) -> ValidationReport:
    issues: list[str] = []
    manifest = dataset_dir / "manifest.json"
    if not manifest.exists():
        issues.append("missing manifest.json")
        return ValidationReport(False, issues, {})

    m = json.loads(manifest.read_text(encoding="utf-8"))
    processed = dataset_dir / "processed"
    if not processed.exists():
        issues.append("missing processed/ directory")
        return ValidationReport(False, issues, {"dataset_id": m.get("dataset_id")})

    # Contract: must load CSV schema
    try:
        X, y, s = load_processed(processed)
    except Exception as e:
        issues.append(f"cannot load processed dataset: {e}")
        return ValidationReport(False, issues, {"dataset_id": m.get("dataset_id")})

    if X.ndim != 2:
        issues.append("X must be 2D")
    if y.ndim != 1:
        issues.append("y must be 1D")
    if s.ndim != 1:
        issues.append("sensitive must be 1D")
    if len(y) != X.shape[0] or len(s) != X.shape[0]:
        issues.append("length mismatch between X, y, sensitive")

    summary = {
        "dataset_id": m.get("dataset_id"),
        "n": int(X.shape[0]),
        "d": int(X.shape[1]),
        "y_pos_rate": float(np.mean(y)),
        "s_rate": float(np.mean(s)),
    }
    return ValidationReport(len(issues) == 0, issues, summary)
