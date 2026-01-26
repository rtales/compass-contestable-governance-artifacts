from pathlib import Path
import json

from compass.data.synthetic import build_synthetic_snapshot
from compass.data.validation import validate_processed_dataset


def test_synthetic_snapshot_build(tmp_path: Path):
    d = tmp_path / "synthetic_v1"
    build_synthetic_snapshot(d)
    assert (d / "manifest.json").exists()
    report = validate_processed_dataset(d)
    assert report.ok, report.to_text()
